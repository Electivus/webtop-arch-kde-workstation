package main

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"os"
	"os/exec"
	"time"
)

func prepare(p profile, statusOnly bool) (any, error) {
	c, err := ownedContainer(p)
	if err != nil {
		return nil, err
	}
	if c == nil || !c.State.Running {
		return nil, errors.New("start the workstation before preparing applications")
	}
	args := []string{"--context", p.DockerContext, "exec", "--user", "abc", p.Name, "workstation-apps"}
	if statusOnly {
		args = append(args, "--status")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 25*time.Minute)
	defer cancel()
	command := exec.CommandContext(ctx, "docker", args...)
	var output bytes.Buffer
	command.Stdout, command.Stderr = &output, os.Stderr
	if err := command.Run(); err != nil {
		return nil, err
	}
	var result map[string]any
	if err := json.Unmarshal(output.Bytes(), &result); err != nil {
		return nil, err
	}
	return result, nil
}
