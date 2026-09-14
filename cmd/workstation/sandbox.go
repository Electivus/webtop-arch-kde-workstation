package main

import (
	_ "embed"
	"os"
)

// Docker reads this client-side file before creating the container. Keep the
// policy inside the executable so a CMD-only installation needs no extra tools.
// Provenance and the three namespace permissions are in THIRD-PARTY.md.
//
//go:embed seccomp.json
var browserSeccomp []byte

func sandboxProfile(directory string) (string, error) {
	file, err := os.CreateTemp(directory, ".seccomp-*.json")
	if err != nil {
		return "", err
	}
	_, writeErr := file.Write(browserSeccomp)
	closeErr := file.Close()
	if writeErr != nil {
		os.Remove(file.Name())
		return "", writeErr
	}
	if closeErr != nil {
		os.Remove(file.Name())
		return "", closeErr
	}
	return file.Name(), nil
}
