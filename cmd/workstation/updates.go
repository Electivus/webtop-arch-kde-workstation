package main

import (
	"errors"
	"fmt"
	"path/filepath"
	"time"
)

func updateApplications(p profile, opts options) (any, error) {
	filename := filepath.Join(opts.directory, "application-update.json")
	if opts.prepareStatus {
		return updateStatus(filename)
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
	journal, err := beginUpdateReport(filename, report)
	if err != nil {
		return nil, err
	}
	defer journal.lock.Close()
	persist, fail := journal.persist, journal.fail
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
