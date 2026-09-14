//go:build !windows

package main

import (
	"crypto/x509"
	"errors"
)

func createShortcut(string, string, string) error {
	return errors.New("Windows shortcut requires Windows")
}
func openURL(string) error { return errors.New("open the URL manually on this development platform") }
func setCertificateTrust(*x509.Certificate, bool) error {
	return errors.New("certificate trust commands require Windows")
}
