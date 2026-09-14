package main

import (
	"crypto/sha1"
	"crypto/x509"
	"fmt"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"syscall"
	"unsafe"
)

func systemDLL(name string) *syscall.LazyDLL {
	return syscall.NewLazyDLL(filepath.Join(os.Getenv("SystemRoot"), "System32", name))
}

func openURL(address string) error {
	verb, err := syscall.UTF16PtrFromString("open")
	if err != nil {
		return err
	}
	target, err := syscall.UTF16PtrFromString(address)
	if err != nil {
		return err
	}
	result, _, callErr := systemDLL("shell32.dll").NewProc("ShellExecuteW").Call(0, uintptr(unsafe.Pointer(verb)), uintptr(unsafe.Pointer(target)), 0, 0, 1)
	if result <= 32 {
		return fmt.Errorf("open browser: %d (%v)", result, callErr)
	}
	return nil
}

type guid struct {
	Data1        uint32
	Data2, Data3 uint16
	Data4        [8]byte
}
type comObject struct{ methods *[21]uintptr }

func comCall(object *comObject, method int, arguments ...uintptr) error {
	args := append([]uintptr{uintptr(unsafe.Pointer(object))}, arguments...)
	result, _, _ := syscall.SyscallN(object.methods[method], args...)
	if int32(result) < 0 {
		return fmt.Errorf("Windows Shell operation failed: 0x%08x", uint32(result))
	}
	return nil
}

func createShortcut(path, executable, directory string) error {
	// Use the native Shell COM API; no scripting host or PowerShell process.
	runtime.LockOSThread()
	defer runtime.UnlockOSThread()
	ole := systemDLL("ole32.dll")
	result, _, _ := ole.NewProc("CoInitializeEx").Call(0, 2)
	if int32(result) < 0 {
		return fmt.Errorf("initialize Windows Shell: 0x%08x", result)
	}
	defer ole.NewProc("CoUninitialize").Call()
	tail := [8]byte{0xc0, 0, 0, 0, 0, 0, 0, 0x46}
	class, shellInterface, persistInterface := guid{0x00021401, 0, 0, tail}, guid{0x000214f9, 0, 0, tail}, guid{0x0000010b, 0, 0, tail}
	var link *comObject
	result, _, _ = ole.NewProc("CoCreateInstance").Call(uintptr(unsafe.Pointer(&class)), 0, 1, uintptr(unsafe.Pointer(&shellInterface)), uintptr(unsafe.Pointer(&link)))
	if int32(result) < 0 {
		return fmt.Errorf("create Windows shortcut: 0x%08x", result)
	}
	defer comCall(link, 2)
	arguments := []string{"start", "--profile", directory, "--open-browser"}
	for i := range arguments {
		arguments[i] = syscall.EscapeArg(arguments[i])
	}
	values := []struct {
		method int
		text   string
	}{{20, executable}, {9, directory}, {11, strings.Join(arguments, " ")}, {7, "Start the local Electivus workstation"}}
	for _, value := range values {
		text, err := syscall.UTF16PtrFromString(value.text)
		if err != nil {
			return err
		}
		if err := comCall(link, value.method, uintptr(unsafe.Pointer(text))); err != nil {
			return err
		}
		runtime.KeepAlive(text)
	}
	var persist *comObject
	if err := comCall(link, 0, uintptr(unsafe.Pointer(&persistInterface)), uintptr(unsafe.Pointer(&persist))); err != nil {
		return err
	}
	defer comCall(persist, 2)
	output, err := syscall.UTF16PtrFromString(path)
	if err != nil {
		return err
	}
	err = comCall(persist, 6, uintptr(unsafe.Pointer(output)), 1)
	runtime.KeepAlive(output)
	return err
}

func setCertificateTrust(cert *x509.Certificate, remove bool) error {
	crypt := systemDLL("crypt32.dll")
	rootName, _ := syscall.UTF16PtrFromString("Root")
	// CERT_STORE_PROV_SYSTEM_REGISTRY_W opens only the physical current-user
	// store. The logical SYSTEM_W collection also includes inherited roots.
	store, _, callErr := crypt.NewProc("CertOpenStore").Call(13, 0, 0, 0x00010000|0x00004000, uintptr(unsafe.Pointer(rootName)))
	if store == 0 {
		return fmt.Errorf("open current-user certificate store: %w", callErr)
	}
	defer crypt.NewProc("CertCloseStore").Call(store, 0)
	if !remove {
		result, _, callErr := crypt.NewProc("CertAddEncodedCertificateToStore").Call(store, 0x00010001,
			uintptr(unsafe.Pointer(&cert.Raw[0])), uintptr(len(cert.Raw)), 3, 0)
		runtime.KeepAlive(cert)
		if result == 0 {
			return fmt.Errorf("trust localhost certificate: %w", callErr)
		}
		return nil
	}
	fingerprint := sha1.Sum(cert.Raw)
	blob := struct {
		Size uint32
		Data *byte
	}{uint32(len(fingerprint)), &fingerprint[0]}
	found, _, callErr := crypt.NewProc("CertFindCertificateInStore").Call(store, 0x00010001, 0, 0x00010000, uintptr(unsafe.Pointer(&blob)), 0)
	runtime.KeepAlive(blob)
	if found == 0 {
		if errno, ok := callErr.(syscall.Errno); ok && uint32(errno) == 0x80092004 {
			return nil
		} // CRYPT_E_NOT_FOUND
		return fmt.Errorf("find localhost certificate: %w", callErr)
	}
	result, _, callErr := crypt.NewProc("CertDeleteCertificateFromStore").Call(found)
	if result == 0 {
		return fmt.Errorf("remove localhost certificate: %w", callErr)
	}
	return nil
}
