//go:build !windows

package main

import (
	"crypto/x509"
	"errors"
	"os"
	"syscall"
)

func lockOperationFile(file *os.File, exclusive bool) error {
	mode := syscall.LOCK_SH
	if exclusive {
		mode = syscall.LOCK_EX
	}
	return syscall.Flock(int(file.Fd()), mode|syscall.LOCK_NB)
}

func operationLockBusy(err error) bool {
	return errors.Is(err, syscall.EWOULDBLOCK)
}

func availableDiskBytes(directory string) (uint64, error) {
	var info syscall.Statfs_t
	if err := syscall.Statfs(directory, &info); err != nil {
		return 0, err
	}
	return info.Bavail * uint64(info.Bsize), nil
}

func createShortcut(string, string, string) error {
	return errors.New("Windows shortcut requires Windows")
}
func openURL(string) error { return errors.New("open the URL manually on this development platform") }
func setCertificateTrust(*x509.Certificate, bool) error {
	return errors.New("certificate trust commands require Windows")
}
