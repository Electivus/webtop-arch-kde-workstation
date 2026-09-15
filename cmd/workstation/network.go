package main

import (
	"bytes"
	"context"
	"crypto/x509"
	"encoding/json"
	"encoding/pem"
	"errors"
	"fmt"
	"io"
	neturl "net/url"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"
)

type networkConfiguration struct {
	Proxy        string   `json:"proxy,omitempty"`
	NoProxy      []string `json:"noProxy,omitempty"`
	Certificates []string `json:"certificates,omitempty"`
}

func importNetwork(source string) (networkConfiguration, error) {
	var config networkConfiguration
	if source == "" {
		return config, nil
	}
	data, err := os.ReadFile(source)
	if err != nil {
		return config, errors.New("cannot read network configuration file")
	}
	var input struct {
		Proxy   string   `json:"proxy"`
		NoProxy []string `json:"noProxy"`
		CAFiles []string `json:"caFiles"`
	}
	decoder := json.NewDecoder(bytes.NewReader(bytes.TrimPrefix(data, []byte{0xef, 0xbb, 0xbf})))
	decoder.DisallowUnknownFields()
	if len(data) > 1024*1024 || decoder.Decode(&input) != nil || decoder.Decode(new(any)) != io.EOF {
		return config, errors.New("invalid network JSON; use proxy, noProxy and caFiles only")
	}
	if input.Proxy != "" {
		proxy, err := neturl.Parse(input.Proxy)
		if err != nil || proxy.Scheme != "http" || proxy.Hostname() == "" || proxy.RawQuery != "" || proxy.Fragment != "" || (proxy.Path != "" && proxy.Path != "/") || strings.ContainsAny(input.Proxy, "\r\n\x00") {
			return config, errors.New("proxy must be an HTTP CONNECT proxy URL, for example http://proxy.example:8080")
		}
		config.Proxy = strings.TrimSuffix(input.Proxy, "/")
	}
	for _, host := range input.NoProxy {
		if host == "" || strings.ContainsAny(host, "\r\n\x00,; \t") {
			return config, errors.New("noProxy must contain individual host or domain patterns")
		}
	}
	config.NoProxy = input.NoProxy
	if len(input.CAFiles) > 16 {
		return config, errors.New("at most sixteen CA files may be configured")
	}
	for _, filename := range input.CAFiles {
		if !filepath.IsAbs(filename) {
			filename = filepath.Join(filepath.Dir(source), filename)
		}
		bundle, err := os.ReadFile(filename)
		if err != nil || len(bundle) > 1024*1024 {
			return config, errors.New("cannot read CA file or CA file is too large")
		}
		count := 0
		for len(bytes.TrimSpace(bundle)) != 0 {
			block, rest := pem.Decode(bundle)
			if block == nil || block.Type != "CERTIFICATE" {
				return config, errors.New("CA files must contain only PEM certificates, without private keys")
			}
			cert, err := x509.ParseCertificate(block.Bytes)
			if err != nil || !cert.BasicConstraintsValid || !cert.IsCA || time.Now().Before(cert.NotBefore) || time.Now().After(cert.NotAfter) {
				return config, errors.New("CA certificate is invalid, expired, or is not a certificate authority")
			}
			config.Certificates = append(config.Certificates, string(pem.EncodeToMemory(block)))
			bundle, count = rest, count+1
		}
		if count == 0 {
			return config, errors.New("CA file is empty")
		}
	}
	return config, nil
}

func saveNetwork(directory string, config networkConfiguration) error {
	data, err := json.Marshal(config)
	if err != nil {
		return err
	}
	temporary, err := os.CreateTemp(directory, ".network-*.json")
	if err != nil {
		return err
	}
	defer os.Remove(temporary.Name())
	if _, err := temporary.Write(data); err != nil {
		temporary.Close()
		return err
	}
	if err := temporary.Close(); err != nil {
		return err
	}
	return os.Rename(temporary.Name(), filepath.Join(directory, "network.json"))
}

func syncNetwork(p profile, directory string) error {
	data, err := os.ReadFile(filepath.Join(directory, "network.json"))
	if errors.Is(err, os.ErrNotExist) {
		data, err = []byte("{}"), nil
	}
	if err != nil {
		return errors.New("cannot read the installation network configuration")
	}
	temporary, err := os.CreateTemp(directory, ".network-transfer-*.json")
	if err != nil {
		return err
	}
	defer os.Remove(temporary.Name())
	if _, err := temporary.Write(data); err != nil {
		temporary.Close()
		return err
	}
	if err := temporary.Close(); err != nil {
		return err
	}
	_, err = docker(p.DockerContext, "cp", temporary.Name(), p.Name+":/config/.electivus-network.json")
	return err
}

func network(p profile, opts options) (any, error) {
	if opts.networkConfig != "" && opts.clearNetwork {
		return nil, errors.New("choose --network-config or --clear")
	}
	c, err := ownedContainer(p)
	if err != nil {
		return nil, err
	}
	if opts.networkConfig != "" || opts.clearNetwork {
		config, err := importNetwork(opts.networkConfig)
		if err != nil {
			return nil, err
		}
		if err := saveNetwork(opts.directory, config); err != nil {
			return nil, err
		}
		return map[string]any{"state": "configured", "proxyConfigured": config.Proxy != "", "certificateCount": len(config.Certificates), "restartRequired": c != nil && c.State.Running}, nil
	}
	if opts.checkNetwork {
		if c == nil || !c.State.Running {
			return nil, errors.New("start the workstation before checking connectivity")
		}
		ctx, cancel := context.WithTimeout(context.Background(), 2*time.Minute)
		defer cancel()
		cmd := exec.CommandContext(ctx, "docker", "--context", p.DockerContext, "exec", "--user", "abc", p.Name, "workstation-network", "check", "--url", opts.networkURL)
		output, err := cmd.CombinedOutput()
		if err != nil {
			return nil, fmt.Errorf("connectivity check failed: %s", bytes.TrimSpace(output))
		}
		var result map[string]any
		if err := json.Unmarshal(output, &result); err != nil {
			return nil, errors.New("invalid connectivity report")
		}
		return result, nil
	}
	var config networkConfiguration
	data, err := os.ReadFile(filepath.Join(opts.directory, "network.json"))
	if err != nil && !errors.Is(err, os.ErrNotExist) {
		return nil, err
	}
	if len(data) != 0 && json.Unmarshal(data, &config) != nil {
		return nil, errors.New("invalid installation network configuration")
	}
	return map[string]any{"proxyConfigured": config.Proxy != "", "certificateCount": len(config.Certificates)}, nil
}
