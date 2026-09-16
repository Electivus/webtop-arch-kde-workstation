package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"time"
)

type updateJournal struct {
	filename string
	report   map[string]any
	lock     *os.File
}

func updateStatus(filename string) (any, error) {
	lock, err := os.OpenFile(filename+".lock", os.O_CREATE|os.O_RDWR, 0600)
	if err != nil {
		return nil, err
	}
	defer lock.Close()
	// Readers share this lock. Only the update process holds it exclusively,
	// and the OS releases it on process exit or reboot, without PID reuse.
	lockErr := lockOperationFile(lock, false)
	if lockErr != nil && !operationLockBusy(lockErr) {
		return nil, fmt.Errorf("check update process: %w", lockErr)
	}
	data, err := os.ReadFile(filename)
	if errors.Is(err, os.ErrNotExist) {
		return map[string]any{"state": "not-started"}, nil
	}
	if err != nil {
		return nil, err
	}
	var report map[string]any
	if err := json.Unmarshal(data, &report); err != nil {
		return nil, err
	}
	if report["state"] == "running" && lockErr == nil {
		report["state"] = "interrupted"
		report["error"] = "host update process ended before completion; inspect the last step and restore the recorded backup or explicitly retry the update"
	}
	return report, nil
}

func beginUpdateReport(filename string, report map[string]any) (*updateJournal, error) {
	lock, err := os.OpenFile(filename+".lock", os.O_CREATE|os.O_RDWR, 0600)
	if err != nil {
		return nil, err
	}
	deadline := time.Now().Add(5 * time.Second)
	for {
		err = lockOperationFile(lock, true)
		if !operationLockBusy(err) || !time.Now().Before(deadline) {
			break
		}
		// Allow an in-flight status reader to release its shared lock.
		time.Sleep(10 * time.Millisecond)
	}
	if err != nil {
		lock.Close()
		return nil, fmt.Errorf("lock update report: %w", err)
	}
	journal := &updateJournal{filename: filename, report: report, lock: lock}
	if err := journal.persist(); err != nil {
		lock.Close()
		return nil, err
	}
	return journal, nil
}

func (j *updateJournal) persist() error {
	data, err := json.MarshalIndent(j.report, "", "  ")
	if err != nil {
		return err
	}
	return atomicFile(j.filename, data)
}

func (j *updateJournal) fail(cause error) (any, error) {
	j.report["state"], j.report["error"] = "failed", cause.Error()
	j.report["completedAt"] = time.Now().UTC().Format(time.RFC3339Nano)
	return nil, errors.Join(cause, j.persist())
}
