package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"
)

func imageDetails(reference string, image containerInfo) map[string]any {
	digests := image.RepoDigests
	if digests == nil {
		digests = []string{}
	}
	return map[string]any{"image": reference, "imageId": image.ID, "repositoryDigests": digests,
		"version": image.Config.Labels["org.opencontainers.image.version"],
		"variant": image.Config.Labels["io.electivus.workstation.variant"]}
}

func updateImage(p profile, opts options) (any, error) {
	filename := filepath.Join(opts.directory, "image-update.json")
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
	if opts.image == "" {
		return nil, errors.New("update-image requires --image with the chosen tag or digest")
	}
	c, err := ownedContainer(p)
	if err != nil {
		return nil, err
	}
	previous, err := status(p)
	if err != nil {
		return nil, err
	}
	report := map[string]any{"state": "running", "step": "resolve", "usable": false,
		"requestedImage": opts.image, "previous": previous, "startedAt": time.Now().UTC().Format(time.RFC3339Nano)}
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
	resumeOriginal := func(cause error) (any, error) {
		if c != nil && c.State.Running {
			// Preserve the original runtime's applied network after a failed
			// backup or removal, including pending host configuration changes.
			_, resumeErr := docker(p.DockerContext, "container", "start", c.ID)
			cause = errors.Join(cause, resumeErr)
		}
		return fail(cause)
	}
	if err := persist(); err != nil {
		return nil, err
	}
	if opts.pullImage {
		if _, err := docker(p.DockerContext, "pull", "--platform", "linux/amd64", opts.image); err != nil {
			return fail(err)
		}
	}
	selected := p
	selected.Image, selected.ImageID = opts.image, ""
	candidate, err := snapshotImage(selected, nil)
	if err != nil {
		return fail(err)
	}
	original, err := snapshotImage(p, c)
	if err != nil {
		return fail(err)
	}
	if candidate.Config.Labels["io.electivus.workstation.variant"] != original.Config.Labels["io.electivus.workstation.variant"] {
		return fail(errors.New("image update must keep the workstation variant; install a separate profile for another variant"))
	}
	if candidate.Config.Labels["org.opencontainers.image.version"] == "" {
		return fail(errors.New("selected image does not declare a workstation version"))
	}
	selected.ImageID = candidate.ID
	for key, value := range imageDetails(p.Image, original) {
		previous.(map[string]any)[key] = value
	}
	report["selected"], report["step"] = imageDetails(opts.image, candidate), "backup"
	if err := persist(); err != nil {
		return fail(err)
	}
	copy, err := backup(p, options{directory: opts.directory, backupDirectory: opts.backupDirectory})
	if err != nil {
		return resumeOriginal(fmt.Errorf("image update backup failed: %w", err))
	}
	report["backup"], report["step"] = copy, "replace"
	if err := persist(); err != nil {
		return resumeOriginal(err)
	}
	if c != nil {
		if _, err := docker(p.DockerContext, "container", "rm", c.ID); err != nil {
			return resumeOriginal(err)
		}
	}
	if err := saveProfile(selected, opts.directory); err != nil {
		if c != nil && c.State.Running {
			_, resumeErr := start(p, opts.directory, false)
			err = errors.Join(err, resumeErr)
		}
		return fail(err)
	}
	report["step"] = "start"
	if err := persist(); err != nil {
		return fail(err)
	}
	current, err := start(selected, opts.directory, false)
	report["current"] = current
	if err != nil {
		return fail(err)
	}
	report["step"] = "packages"
	if err := persist(); err != nil {
		return fail(err)
	}
	restored, err := packages(selected, options{restorePackages: true})
	report["packages"] = restored
	if err != nil {
		return fail(err)
	}
	report["step"] = "applications"
	if err := persist(); err != nil {
		return fail(err)
	}
	applications, err := runApplications(selected)
	report["applications"] = applications
	if err != nil {
		return fail(fmt.Errorf("provided application check failed: %w", err))
	}
	report["step"] = "checks"
	checks := map[string]any{}
	report["checks"] = checks
	if err := persist(); err != nil {
		return fail(err)
	}
	for _, check := range []struct {
		name, user string
		args       []string
	}{
		{"desktop", "root", []string{"workstation-healthcheck"}},
		{"git", "abc", []string{"git", "--version"}},
		{"shell", "abc", []string{"zsh", "--version"}},
		{"terminal", "abc", []string{"konsole", "--version"}},
		{"docker", "abc", []string{"workstation-docker-check"}},
		{"browser", "abc", []string{"google-chrome", "--headless", "--disable-gpu",
			"--user-data-dir=/tmp/workstation-image-validation", "--dump-dom", "data:text/html,<p>workstation-image-check</p>"}},
	} {
		args := append([]string{"exec", "--user", check.user, p.Name, "timeout", "45"}, check.args...)
		output, err := docker(p.DockerContext, args...)
		if err == nil && check.name == "browser" && !strings.Contains(string(output), "<p>workstation-image-check</p>") {
			err = errors.New("Chrome did not render the verification page")
		}
		if err != nil {
			checks[check.name] = map[string]any{"state": "failed", "error": err.Error()}
			return fail(fmt.Errorf("provided component %s failed verification: %w", check.name, err))
		}
		checks[check.name] = map[string]any{"state": "passed", "output": string(output)}
		if err := persist(); err != nil {
			return fail(err)
		}
	}
	report["state"], report["step"], report["usable"] = "completed", "ready", true
	if restored.(map[string]any)["state"] == "partial" {
		report["state"] = "partial"
	}
	report["completedAt"] = time.Now().UTC().Format(time.RFC3339Nano)
	if err := persist(); err != nil {
		return nil, err
	}
	return report, nil
}
