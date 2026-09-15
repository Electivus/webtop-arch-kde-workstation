package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"time"
)

func updateApplications(p profile, opts options) (any, error) {
	filename := filepath.Join(opts.directory, "application-update.json")
	if opts.prepareStatus {
		data, err := os.ReadFile(filename)
		if errors.Is(err, os.ErrNotExist) {
			return map[string]any{"state": "not-started"}, nil
		}
		if err != nil {
			return nil, err
		}
		var result map[string]any
		err = json.Unmarshal(data, &result)
		return result, err
	}
	c, err := ownedContainer(p)
	if err != nil {
		return nil, err
	}
	if c == nil || !c.State.Running {
		return nil, errors.New("start the workstation before updating applications")
	}
	previous, err := status(p)
	if err != nil {
		return nil, err
	}
	report := map[string]any{"state": "running", "step": "backup", "previous": previous,
		"startedAt": time.Now().UTC().Format(time.RFC3339Nano)}
	persist := func() error {
		data, err := json.MarshalIndent(report, "", "  ")
		if err != nil {
			return err
		}
		return atomicFile(filename, data)
	}
	fail := func(cause error) (any, error) {
		report["state"], report["error"] = "failed", cause.Error()
		report["completedAt"] = time.Now().UTC().Format(time.RFC3339Nano)
		return nil, errors.Join(cause, persist())
	}
	if err := persist(); err != nil {
		return nil, err
	}
	copy, err := backup(p, options{directory: opts.directory, backupDirectory: opts.backupDirectory})
	if err != nil {
		// A snapshot can fail after stopping. Resume the same container without
		// applying pending network settings or changing its selected image.
		_, resumeErr := docker(p.DockerContext, "container", "start", c.ID)
		return fail(errors.Join(fmt.Errorf("application update backup failed: %w", err), resumeErr))
	}
	report["backup"], report["step"] = copy, "start"
	if err := persist(); err != nil {
		return fail(err)
	}
	if _, err := start(p, opts.directory, false); err != nil {
		return fail(err)
	}
	report["step"] = "applications"
	if err := persist(); err != nil {
		return fail(err)
	}
	applications, err := runApplications(p, "--update")
	report["applications"] = applications
	if err != nil {
		return fail(fmt.Errorf("application update failed; inspect update-apps --status and restore its backup if needed: %w", err))
	}
	report["state"], report["step"] = "completed", "ready"
	report["completedAt"] = time.Now().UTC().Format(time.RFC3339Nano)
	if err := persist(); err != nil {
		return nil, err
	}
	return report, nil
}
