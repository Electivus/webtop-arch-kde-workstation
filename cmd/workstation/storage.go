package main

import (
	"bytes"
	"encoding/csv"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"runtime"
	"strings"
)

func exchangeDirectory(directory string) (string, error) {
	if directory == "" {
		return "", nil
	}
	absolute, err := filepath.Abs(directory)
	if err != nil {
		return "", err
	}
	info, err := os.Stat(absolute)
	if err != nil {
		return "", fmt.Errorf("exchange directory is unavailable: %s: %w; create or reconnect the directory before starting", absolute, err)
	}
	if !info.IsDir() {
		return "", fmt.Errorf("exchange path must be a directory: %s", absolute)
	}
	if err := checkDockerSharing(absolute); err != nil {
		return "", err
	}
	return absolute, nil
}

func checkDockerSharing(directory string) error {
	if runtime.GOOS != "windows" {
		return nil
	}
	var settings struct {
		FilesharingDirectories []string
		UseLibkrun             *bool
		WslEngineEnabled       *bool
	}
	data, err := os.ReadFile(filepath.Join(os.Getenv("APPDATA"), "Docker", "settings-store.json"))
	if err != nil || json.Unmarshal(data, &settings) != nil {
		// Unknown Desktop versions are checked by the actual mount probe.
		return nil
	}
	requiresSharing := settings.UseLibkrun != nil && *settings.UseLibkrun ||
		settings.WslEngineEnabled != nil && !*settings.WslEngineEnabled
	if !requiresSharing {
		return nil
	}
	for _, shared := range settings.FilesharingDirectories {
		relative, err := filepath.Rel(shared, directory)
		if err == nil && filepath.IsLocal(relative) {
			return nil
		}
	}
	return fmt.Errorf("exchange directory %s is not shared; add it in Docker Desktop Settings > Resources > File sharing, apply the change, then retry", directory)
}

func exchangeMount(directory string) string {
	// Docker parses --mount as CSV; a Windows directory may contain commas.
	var output bytes.Buffer
	writer := csv.NewWriter(&output)
	_ = writer.Write([]string{"type=bind", "src=" + directory, "dst=/exchange"})
	writer.Flush()
	return strings.TrimSuffix(output.String(), "\n")
}

func verifyExchange(p profile) error {
	if p.Exchange == "" {
		return nil
	}
	probe, err := os.CreateTemp(p.Exchange, ".workstation-exchange-*")
	if err != nil {
		return fmt.Errorf("exchange directory must be writable by Windows: %w", err)
	}
	defer os.Remove(probe.Name())
	challenge := p.InstallationID
	_, writeErr := probe.WriteString(challenge)
	closeErr := probe.Close()
	if writeErr != nil {
		return writeErr
	}
	if closeErr != nil {
		return closeErr
	}
	// This random, temporary probe contains no private data. On Linux CI the
	// runner and the workstation have different UIDs.
	if err := os.Chmod(probe.Name(), 0666); err != nil {
		return err
	}
	_, err = docker(p.DockerContext, "run", "--rm", "--network", "none", "--user", "1000:1000",
		"--label", ownerLabel+"="+p.InstallationID, "--mount", exchangeMount(p.Exchange),
		"--entrypoint", "/bin/sh", p.Image, "-c",
		`test "$(cat "/exchange/$1")" = "$2" && printf '%s' '-container' >> "/exchange/$1"`,
		"exchange-probe", filepath.Base(probe.Name()), challenge)
	if err != nil {
		return fmt.Errorf("Docker cannot read/write exchange directory %s; check directory permissions and Docker Desktop Settings > Resources > File sharing for your backend (Hyper-V requires sharing): %w", p.Exchange, err)
	}
	observed, err := os.ReadFile(probe.Name())
	if err != nil || string(observed) != challenge+"-container" {
		return fmt.Errorf("Docker exchange mapping did not return the written probe to %s; check Docker Desktop file sharing", p.Exchange)
	}
	return nil
}
