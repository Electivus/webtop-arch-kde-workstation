package main

import (
	"bytes"
	"context"
	"crypto/rand"
	"crypto/sha1"
	"crypto/sha256"
	"crypto/x509"
	"encoding/hex"
	"encoding/json"
	"encoding/pem"
	"errors"
	"flag"
	"fmt"
	"io"
	"net"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"runtime"
	"strings"
	"time"
)

const ownerLabel = "io.electivus.workstation.installation"

type profile struct {
	Schema         int    `json:"schema"`
	InstallationID string `json:"installationId"`
	Name           string `json:"name"`
	Image          string `json:"image"`
	ImageID        string `json:"imageId,omitempty"`
	Port           int    `json:"port"`
	MemoryMiB      int    `json:"memoryMiB"`
	CPUs           int    `json:"cpus"`
	HomeVolume     string `json:"homeVolume"`
	DockerContext  string `json:"dockerContext"`
	Exchange       string `json:"exchange,omitempty"`
}

type containerInfo struct {
	ID           string `json:"Id"`
	Image        string
	Architecture string
	OS           string `json:"Os"`
	RepoDigests  []string
	Config       struct{ Labels map[string]string }
	State        struct {
		Running bool
		Health  *struct{ Status string }
	}
}

type engineInfo struct {
	Context   string `json:"context"`
	OS        string `json:"os"`
	Kernel    string `json:"kernel"`
	CPUs      int    `json:"cpus"`
	MemoryMiB int64  `json:"memoryMiB"`
	Backend   string `json:"backend"`
}

type options struct {
	directory       string
	name            string
	image           string
	port            int
	memory          int
	cpus            int
	noShortcut      bool
	openBrowser     bool
	prepareStatus   bool
	exchange        string
	networkConfig   string
	clearNetwork    bool
	checkNetwork    bool
	networkURL      string
	listBackups     bool
	backupDirectory string
	backupSource    string
	restorePackages bool
	registerPackage string
	packageSource   string
	pullImage       bool
}

func main() {
	result, err := run(os.Args[1:])
	if errors.Is(err, flag.ErrHelp) {
		return
	}
	if err != nil {
		fmt.Fprintln(os.Stderr, "workstation:", err)
		os.Exit(1)
	}
	encoder := json.NewEncoder(os.Stdout)
	encoder.SetIndent("", "  ")
	if err := encoder.Encode(result); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func run(args []string) (any, error) {
	if len(args) == 0 {
		return nil, errors.New("usage: workstation.cmd install|start|stop|status|prepare|update-apps|update-image|network|packages|backup|restore|certificate|trust|untrust [options]")
	}
	cache, _ := os.UserCacheDir()
	opts := options{}
	flags := flag.NewFlagSet(args[0], flag.ContinueOnError)
	flags.StringVar(&opts.directory, "profile", filepath.Join(cache, "Electivus", "Workstation", "base"), "installation directory")
	flags.StringVar(&opts.name, "name", "electivus-workstation-base", "Docker resource name")
	defaultImage := ""
	if args[0] == "install" {
		defaultImage = "electivus/webtop-arch-kde-base:stable"
	}
	flags.StringVar(&opts.image, "image", defaultImage, "workstation image tag or digest")
	flags.BoolVar(&opts.pullImage, "pull", true, "resolve the selected update image from its registry; use --pull=false for an already loaded image")
	flags.IntVar(&opts.port, "port", 3001, "localhost HTTPS port")
	flags.IntVar(&opts.memory, "memory", 6144, "container memory limit in MiB")
	flags.IntVar(&opts.cpus, "cpus", 4, "container CPU limit")
	flags.BoolVar(&opts.noShortcut, "no-shortcut", false, "omit the Windows shortcut")
	flags.BoolVar(&opts.openBrowser, "open-browser", false, "open the local desktop after startup")
	flags.BoolVar(&opts.prepareStatus, "status", false, "report application preparation or update without starting it")
	flags.StringVar(&opts.exchange, "exchange", "", "existing host directory for bidirectional file exchange")
	flags.StringVar(&opts.networkConfig, "network-config", "", "local JSON with optional proxy, noProxy and caFiles")
	flags.BoolVar(&opts.clearNetwork, "clear", false, "remove this installation's network options on next start")
	flags.BoolVar(&opts.checkNetwork, "check", false, "check preparation and Git connectivity from the workstation")
	flags.StringVar(&opts.networkURL, "url", "https://github.com/git/git.git", "HTTPS endpoint for the connectivity check")
	flags.BoolVar(&opts.listBackups, "list", false, "list completed personal backups")
	flags.StringVar(&opts.backupDirectory, "backup-directory", "", "backup storage directory (default: profile/backups)")
	flags.StringVar(&opts.backupSource, "backup", "", "completed backup directory to restore")
	flags.BoolVar(&opts.restorePackages, "restore", false, "restore recorded extra Arch packages")
	flags.StringVar(&opts.registerPackage, "register", "", "extra package whose build source should be recorded")
	flags.StringVar(&opts.packageSource, "source", "", "persistent Linux directory containing the package PKGBUILD")
	if err := flags.Parse(args[1:]); err != nil {
		return nil, err
	}
	if flags.NArg() != 0 {
		return nil, fmt.Errorf("unexpected arguments: %v", flags.Args())
	}
	directory, err := filepath.Abs(opts.directory)
	if err != nil {
		return nil, err
	}
	opts.directory = directory
	if args[0] == "install" {
		return install(opts)
	}
	p, err := readProfile(directory)
	if err != nil {
		return nil, err
	}
	readOnly := args[0] == "status" || (args[0] == "packages" && !opts.restorePackages && opts.registerPackage == "") || (args[0] == "backup" && opts.listBackups) ||
		((args[0] == "prepare" || args[0] == "update-apps" || args[0] == "update-image") && opts.prepareStatus) ||
		(args[0] == "network" && opts.networkConfig == "" && !opts.clearNetwork)
	if !readOnly {
		operationLock, err := os.OpenFile(filepath.Join(directory, ".operation.lock"), os.O_CREATE|os.O_RDWR, 0600)
		if err != nil {
			return nil, fmt.Errorf("open installation operation lock: %w", err)
		}
		defer operationLock.Close()
		lockErr := lockOperationFile(operationLock, true)
		if args[0] == "certificate" || args[0] == "trust" || args[0] == "untrust" {
			// The shortcut starts asynchronously. Let its final certificate export
			// finish before the user's certificate command acquires this same lock.
			deadline := time.Now().Add(10 * time.Second)
			for lockErr != nil && time.Now().Before(deadline) {
				time.Sleep(100 * time.Millisecond)
				lockErr = lockOperationFile(operationLock, true)
			}
		}
		if lockErr != nil {
			return nil, fmt.Errorf("another workstation operation is active; wait for it to finish and retry: %w", lockErr)
		}
		p, err = readProfile(directory)
		if err != nil {
			return nil, err
		}
	}
	switch args[0] {
	case "start":
		return start(p, directory, opts.openBrowser)
	case "status":
		return status(p)
	case "prepare":
		return prepare(p, opts.prepareStatus)
	case "update-apps":
		return updateApplications(p, opts)
	case "update-image":
		return updateImage(p, opts)
	case "network":
		return network(p, opts)
	case "packages":
		return packages(p, opts)
	case "backup":
		return backup(p, opts)
	case "restore":
		return restoreBackup(p, opts)
	case "stop":
		c, err := ownedContainer(p)
		if err != nil {
			return nil, err
		}
		if c != nil && c.State.Running {
			if _, err := docker(p.DockerContext, "container", "stop", "--time", "30", p.Name); err != nil {
				return nil, err
			}
		}
		return status(p)
	case "untrust":
		return untrust(directory)
	case "certificate", "trust":
		details, cert, err := certificate(p, directory)
		if err != nil {
			return nil, err
		}
		if args[0] == "certificate" {
			return details, nil
		}
		if err := setCertificateTrust(cert, false); err != nil {
			return nil, err
		}
		return map[string]any{"state": "trusted", "store": "CurrentUser/Root", "certificate": details}, nil
	default:
		return nil, fmt.Errorf("unknown command %q", args[0])
	}
}

func docker(dockerContext string, args ...string) ([]byte, error) {
	invocation := args
	if dockerContext != "" {
		invocation = append([]string{"--context", dockerContext}, args...)
	}
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Minute)
	defer cancel()
	command := exec.CommandContext(ctx, "docker", invocation...)
	var stderr bytes.Buffer
	command.Stderr = &stderr
	if len(args) > 0 && args[0] == "pull" {
		command.Stderr = io.MultiWriter(os.Stderr, &stderr)
	}
	output, err := command.Output()
	if err != nil {
		return nil, fmt.Errorf("docker %s failed: %w: %s", args[0], err, strings.TrimSpace(stderr.String()))
	}
	return bytes.TrimSpace(output), nil
}

func dockerJSON(p profile, result any, args ...string) error {
	data, err := docker(p.DockerContext, args...)
	if err != nil {
		return err
	}
	return json.Unmarshal(data, result)
}

func readProfile(directory string) (profile, error) {
	var p profile
	data, err := os.ReadFile(filepath.Join(directory, "profile.json"))
	if err != nil {
		return p, fmt.Errorf("read installation profile (run install first): %w", err)
	}
	if err := json.Unmarshal(bytes.TrimPrefix(data, []byte{0xef, 0xbb, 0xbf}), &p); err != nil {
		return p, err
	}
	if p.Schema != 1 || p.InstallationID == "" || p.DockerContext == "" || !validName(p.Name) || !validHomeVolume(p) ||
		(p.ImageID != "" && !imageID.MatchString(p.ImageID)) {
		return p, errors.New("invalid installation profile")
	}
	return p, nil
}

func saveProfile(p profile, directory string) error {
	data, err := json.MarshalIndent(p, "", "  ")
	if err != nil {
		return err
	}
	return atomicFile(filepath.Join(directory, "profile.json"), append(data, '\n'))
}

func validName(name string) bool {
	return regexp.MustCompile(`^[a-z][a-z0-9-]{2,47}$`).MatchString(name)
}

func engine(p profile) (engineInfo, error) {
	var result engineInfo
	var contexts []struct {
		Endpoints map[string]struct{ Host string }
	}
	if err := dockerJSON(p, &contexts, "context", "inspect", p.DockerContext); err != nil {
		return result, err
	}
	if len(contexts) != 1 {
		return result, errors.New("cannot resolve Docker context")
	}
	endpoint := contexts[0].Endpoints["docker"].Host
	if !strings.HasPrefix(endpoint, "npipe:////./pipe/") && !strings.HasPrefix(endpoint, "unix:///") {
		return result, errors.New("choose a local Docker context; a remote daemon cannot provide a notebook-only desktop")
	}
	var info struct {
		OSType, Architecture, OperatingSystem, KernelVersion string
		NCPU                                                 int
		MemTotal                                             int64
	}
	if err := dockerJSON(p, &info, "info", "--format", "{{json .}}"); err != nil {
		return result, err
	}
	if info.OSType != "linux" || (info.Architecture != "x86_64" && info.Architecture != "amd64") {
		return result, errors.New("Docker must run Linux amd64 containers")
	}
	result = engineInfo{p.DockerContext, info.OperatingSystem, info.KernelVersion, info.NCPU, info.MemTotal / (1024 * 1024), "unknown"}
	if runtime.GOOS == "windows" {
		data, err := os.ReadFile(filepath.Join(os.Getenv("APPDATA"), "Docker", "settings-store.json"))
		var settings struct {
			UseLibkrun       *bool
			WslEngineEnabled *bool
		}
		if err == nil && json.Unmarshal(data, &settings) == nil {
			if settings.UseLibkrun != nil && *settings.UseLibkrun {
				result.Backend = "VMM (Docker Desktop setting)"
			} else if settings.WslEngineEnabled != nil && *settings.WslEngineEnabled {
				result.Backend = "WSL2 (Docker Desktop setting)"
			} else if settings.WslEngineEnabled != nil {
				result.Backend = "Hyper-V (Docker Desktop setting; validate on destination)"
			}
		}
	}
	return result, nil
}

func ownedContainer(p profile) (*containerInfo, error) {
	id, err := docker(p.DockerContext, "container", "ls", "--all", "--filter", "name=^/"+p.Name+"$", "--format", "{{.ID}}")
	if err != nil {
		return nil, err
	}
	if len(id) == 0 {
		return nil, nil
	}
	var containers []containerInfo
	if err := dockerJSON(p, &containers, "container", "inspect", string(id)); err != nil {
		return nil, err
	}
	if len(containers) != 1 {
		return nil, errors.New("unexpected container lookup result")
	}
	c := &containers[0]
	if c.Config.Labels[ownerLabel] != p.InstallationID {
		return nil, fmt.Errorf("container %s belongs to another installation", p.Name)
	}
	return c, nil
}

func install(opts options) (any, error) {
	if !validName(opts.name) || opts.port < 1024 || opts.port > 65535 || opts.memory < 1024 || opts.cpus < 1 || opts.image == "" {
		return nil, errors.New("invalid name, port, resource limits or image")
	}
	profileFile := filepath.Join(opts.directory, "profile.json")
	if _, err := os.Stat(profileFile); !errors.Is(err, os.ErrNotExist) {
		return nil, errors.New("profile already exists or cannot be accessed; use start or another directory")
	}
	selectedContext, err := docker("", "context", "show")
	if err != nil {
		return nil, err
	}
	var random [16]byte
	if _, err := rand.Read(random[:]); err != nil {
		return nil, err
	}
	exchange, err := exchangeDirectory(opts.exchange)
	if err != nil {
		return nil, err
	}
	networkConfig, err := importNetwork(opts.networkConfig)
	if err != nil {
		return nil, err
	}
	p := profile{Schema: 1, InstallationID: hex.EncodeToString(random[:]), Name: opts.name, Image: opts.image,
		Port: opts.port, MemoryMiB: opts.memory, CPUs: opts.cpus, HomeVolume: opts.name + "-home",
		DockerContext: string(selectedContext), Exchange: exchange}
	info, err := engine(p)
	if err != nil {
		return nil, err
	}
	if int64(p.MemoryMiB) > info.MemoryMiB || p.CPUs > info.CPUs {
		return nil, fmt.Errorf("limits exceed Docker VM (%d MiB, %d CPUs); adjust --memory/--cpus or Docker Desktop", info.MemoryMiB, info.CPUs)
	}
	if _, err := ownedContainer(p); err != nil {
		return nil, err
	}
	if !opts.noShortcut && runtime.GOOS != "windows" {
		return nil, errors.New("Windows shortcuts require Windows; use --no-shortcut for CI")
	}
	toolsDirectory := filepath.Join(opts.directory, "tools")
	if err := os.MkdirAll(toolsDirectory, 0700); err != nil {
		return nil, err
	}
	if opts.networkConfig != "" {
		if err := saveNetwork(opts.directory, networkConfig); err != nil {
			return nil, err
		}
	}
	executable, err := os.Executable()
	if err != nil {
		return nil, err
	}
	installedExecutable := filepath.Join(toolsDirectory, filepath.Base(executable))
	if err := copyProgram(executable, installedExecutable); err != nil {
		return nil, err
	}
	if runtime.GOOS == "windows" {
		if err := copyProgram(filepath.Join(filepath.Dir(executable), "workstation.cmd"), filepath.Join(toolsDirectory, "workstation.cmd")); err != nil {
			return nil, err
		}
	}
	shortcut := ""
	if !opts.noShortcut {
		shortcut = filepath.Join(opts.directory, "Start Workstation.lnk")
		if err := createShortcut(shortcut, installedExecutable, opts.directory); err != nil {
			return nil, err
		}
	}
	data, err := json.MarshalIndent(p, "", "  ")
	if err != nil {
		return nil, err
	}
	file, err := os.OpenFile(profileFile, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
	if err != nil {
		return nil, err
	}
	_, writeErr := file.Write(append(data, '\n'))
	closeErr := file.Close()
	if writeErr != nil {
		return nil, writeErr
	}
	if closeErr != nil {
		return nil, closeErr
	}
	return map[string]any{"state": "installed", "profile": opts.directory, "shortcut": shortcut, "url": url(p), "engine": info}, nil
}

func copyProgram(source, destination string) error {
	data, err := os.ReadFile(source)
	if err != nil {
		return err
	}
	existing, err := os.ReadFile(destination)
	if err == nil {
		if bytes.Equal(existing, data) {
			return nil
		}
		return fmt.Errorf("refusing to replace an existing file: %s", destination)
	}
	if !errors.Is(err, os.ErrNotExist) {
		return err
	}
	return os.WriteFile(destination, data, 0700)
}

func url(p profile) string { return fmt.Sprintf("https://localhost:%d/", p.Port) }

func status(p profile) (any, error) {
	info, err := engine(p)
	if err != nil {
		return nil, err
	}
	c, err := ownedContainer(p)
	if err != nil {
		return nil, err
	}
	state, healthy, id, imageID, version, upstream := "installed", false, "", "", "", ""
	if c != nil {
		state = "stopped"
		if c.State.Running {
			state = "running"
		}
		healthy = c.State.Running && c.State.Health != nil && c.State.Health.Status == "healthy"
		id, imageID = c.ID, c.Image
		version, upstream = c.Config.Labels["org.opencontainers.image.version"], c.Config.Labels["org.opencontainers.image.base.digest"]
	}
	return map[string]any{"state": state, "healthy": healthy, "container": p.Name, "containerId": id,
		"homeVolume": p.HomeVolume, "image": p.Image, "imageId": imageID, "version": version, "upstreamDigest": upstream,
		"url": url(p), "engine": info, "storage": map[string]string{"projects": "/config/projects", "exchange": p.Exchange},
		"limits": map[string]int{"memoryMiB": p.MemoryMiB, "cpus": p.CPUs}}, nil
}

func selectedImageReference(p profile, c *containerInfo) (string, error) {
	if c != nil {
		return c.Image, nil
	}
	if p.ImageID != "" {
		return p.ImageID, nil
	}
	volume, err := docker(p.DockerContext, "volume", "ls", "--quiet", "--filter", "name=^"+p.HomeVolume+"$")
	if err != nil {
		return "", err
	}
	if len(volume) != 0 {
		return "", errors.New("original image is unknown for this existing home; recover the original container or restore a completed backup from this installation before continuing")
	}
	return p.Image, nil
}

func start(p profile, directory string, open bool) (any, error) {
	info, err := engine(p)
	if err != nil {
		return nil, err
	}
	if int64(p.MemoryMiB) > info.MemoryMiB || p.CPUs > info.CPUs {
		return nil, errors.New("profile limits exceed the current Docker VM allocation")
	}
	if _, err := exchangeDirectory(p.Exchange); err != nil {
		return nil, err
	}
	c, err := ownedContainer(p)
	if err != nil {
		return nil, err
	}
	if c != nil && p.ImageID == "" {
		// Older profiles adopt the existing container's actual selection, even
		// if its original tag already points to another image.
		p.ImageID = c.Image
		if err := saveProfile(p, directory); err != nil {
			return nil, err
		}
	}
	if c == nil {
		reference, err := selectedImageReference(p, nil)
		if err != nil {
			return nil, err
		}
		var images []containerInfo
		err = dockerJSON(p, &images, "image", "inspect", reference)
		if err != nil && p.ImageID == "" && strings.Contains(err.Error(), "No such image") {
			fmt.Fprintln(os.Stderr, "Downloading", p.Image)
			if _, err := docker(p.DockerContext, "pull", "--platform", "linux/amd64", p.Image); err != nil {
				return nil, err
			}
			err = dockerJSON(p, &images, "image", "inspect", p.Image)
		}
		if err != nil {
			if p.ImageID != "" {
				return nil, fmt.Errorf("selected image %s is unavailable; load that image before starting or updating: %w", p.ImageID, err)
			}
			return nil, err
		}
		if len(images) != 1 {
			return nil, errors.New("cannot resolve workstation image")
		}
		variant := images[0].Config.Labels["io.electivus.workstation.variant"]
		if images[0].OS != "linux" || images[0].Architecture != "amd64" || (variant != "base" && variant != "salesforce") {
			return nil, errors.New("selected image is not an Electivus Linux amd64 workstation")
		}
		if err := verifyExchange(p); err != nil {
			return nil, err
		}
		// Save the initial selection before creating personal storage so an
		// interrupted first start cannot leave an existing home without its image.
		if p.ImageID == "" {
			p.ImageID = images[0].ID
			if err := saveProfile(p, directory); err != nil {
				return nil, err
			}
		}
		volume, err := docker(p.DockerContext, "volume", "ls", "--quiet", "--filter", "name=^"+p.HomeVolume+"$")
		if err != nil {
			return nil, err
		}
		if len(volume) != 0 {
			var volumes []struct{ Labels map[string]string }
			if err := dockerJSON(p, &volumes, "volume", "inspect", p.HomeVolume); err != nil {
				return nil, err
			}
			if len(volumes) != 1 || volumes[0].Labels[ownerLabel] != p.InstallationID {
				return nil, errors.New("home volume belongs to another installation")
			}
		} else {
			if _, err := docker(p.DockerContext, "volume", "create", "--label", ownerLabel+"="+p.InstallationID, p.HomeVolume); err != nil {
				return nil, err
			}
		}
		policy, err := sandboxProfile(directory)
		if err != nil {
			return nil, err
		}
		defer os.Remove(policy)
		args := []string{"create", "--name", p.Name, "--platform", "linux/amd64", "--restart", "no",
			"--security-opt", "seccomp=" + policy,
			"--label", ownerLabel + "=" + p.InstallationID, "--publish", fmt.Sprintf("127.0.0.1:%d:3001/tcp", p.Port),
			"--mount", "type=volume,src=" + p.HomeVolume + ",dst=/config", "--memory", fmt.Sprintf("%dm", p.MemoryMiB),
			"--mount", "type=bind,src=/var/run/docker.sock,dst=/var/run/docker.sock",
			"--env", "WORKSTATION_HOME_VOLUME=" + p.HomeVolume, "--env", "DOCKER_HOST=unix:///var/run/docker.sock",
			"--cpus", fmt.Sprint(p.CPUs), "--shm-size", "1g", "--env", "PUID=1000", "--env", "PGID=1000"}
		if p.Exchange != "" {
			args = append(args, "--mount", exchangeMount(p.Exchange))
		}
		args = append(args, p.ImageID)
		_, err = docker(p.DockerContext, args...)
		if err != nil {
			return nil, err
		}
	}
	if c == nil || !c.State.Running {
		if err := syncNetwork(p, directory); err != nil {
			return nil, err
		}
		if err := verifyExchange(p); err != nil {
			return nil, err
		}
		if _, err := docker(p.DockerContext, "container", "start", p.Name); err != nil {
			return nil, err
		}
	}
	deadline := time.Now().Add(4 * time.Minute)
	for time.Now().Before(deadline) {
		c, err = ownedContainer(p)
		if err != nil {
			return nil, err
		}
		if c == nil || !c.State.Running {
			return nil, fmt.Errorf("desktop stopped during startup; inspect docker --context %s logs %s", p.DockerContext, p.Name)
		}
		if c.State.Health != nil && c.State.Health.Status == "healthy" {
			previous, _ := os.ReadFile(filepath.Join(directory, "localhost.crt"))
			_, cert, err := certificate(p, directory)
			if err != nil {
				return nil, err
			}
			if old, err := parseLocalCertificate(previous, true); err == nil && !bytes.Equal(old.Raw, cert.Raw) {
				fmt.Fprintln(os.Stderr, "The localhost certificate was renewed. Run untrust, then trust for this profile to refresh Windows trust.")
			}
			if open {
				if err := openURL(url(p)); err != nil {
					return nil, err
				}
			}
			return status(p)
		}
		time.Sleep(2 * time.Second)
	}
	return nil, fmt.Errorf("desktop did not become healthy in four minutes; inspect docker --context %s logs %s", p.DockerContext, p.Name)
}

func certificate(p profile, directory string) (map[string]any, *x509.Certificate, error) {
	c, err := ownedContainer(p)
	if err != nil {
		return nil, nil, err
	}
	if c == nil {
		return nil, nil, errors.New("start the workstation once to generate its localhost certificate")
	}
	fetched, err := os.CreateTemp(directory, ".localhost-*.crt")
	if err != nil {
		return nil, nil, err
	}
	fetchedPath := fetched.Name()
	if err := fetched.Close(); err != nil {
		return nil, nil, err
	}
	defer os.Remove(fetchedPath)
	if _, err := docker(p.DockerContext, "cp", p.Name+":/config/ssl/cert.pem", fetchedPath); err != nil {
		return nil, nil, err
	}
	data, err := os.ReadFile(fetchedPath)
	if err != nil {
		return nil, nil, err
	}
	cert, err := parseLocalCertificate(data, false)
	if err != nil {
		return nil, nil, err
	}
	path := filepath.Join(directory, "localhost.crt")
	// Preserve a certificate cached by an older controller before replacing it.
	if previous, err := os.ReadFile(path); err == nil {
		if err := archiveCertificate(directory, previous); err != nil {
			return nil, nil, err
		}
	} else if !errors.Is(err, os.ErrNotExist) {
		return nil, nil, err
	}
	if err := archiveCertificate(directory, data); err != nil {
		return nil, nil, err
	}
	if err := os.Rename(fetchedPath, path); err != nil {
		return nil, nil, err
	}
	return certificateDetails(cert, path), cert, nil
}

func parseLocalCertificate(data []byte, allowExpired bool) (*x509.Certificate, error) {
	block, _ := pem.Decode(data)
	if block == nil {
		return nil, errors.New("invalid certificate PEM")
	}
	cert, err := x509.ParseCertificate(block.Bytes)
	if err != nil {
		return nil, err
	}
	if !cert.BasicConstraintsValid || cert.IsCA || len(cert.DNSNames) != 1 || cert.DNSNames[0] != "localhost" ||
		len(cert.IPAddresses) != 1 || !cert.IPAddresses[0].Equal(net.IPv4(127, 0, 0, 1)) {
		return nil, errors.New("certificate must be a localhost-only server leaf")
	}
	if !allowExpired && (time.Now().After(cert.NotAfter) || time.Now().Before(cert.NotBefore)) {
		return nil, errors.New("localhost certificate is outside its validity period; restart to renew it, then run trust")
	}
	if err := cert.CheckSignature(cert.SignatureAlgorithm, cert.RawTBSCertificate, cert.Signature); err != nil {
		return nil, err
	}
	return cert, nil
}

func certificateDetails(cert *x509.Certificate, path string) map[string]any {
	fingerprint, thumbprint := sha256.Sum256(cert.Raw), sha1.Sum(cert.Raw)
	return map[string]any{"file": path, "dnsName": "localhost", "subject": cert.Subject.String(), "sha256": strings.ToUpper(hex.EncodeToString(fingerprint[:])),
		"thumbprint": strings.ToUpper(hex.EncodeToString(thumbprint[:])), "expires": cert.NotAfter.UTC().Format(time.RFC3339)}
}

func archiveCertificate(directory string, data []byte) error {
	cert, err := parseLocalCertificate(data, true)
	if err != nil {
		return err
	}
	archive := filepath.Join(directory, "certificates")
	if err := os.MkdirAll(archive, 0700); err != nil {
		return err
	}
	fingerprint := sha256.Sum256(cert.Raw)
	return os.WriteFile(filepath.Join(archive, strings.ToUpper(hex.EncodeToString(fingerprint[:]))+".crt"), data, 0600)
}

func untrust(directory string) (any, error) {
	paths, err := filepath.Glob(filepath.Join(directory, "certificates", "*.crt"))
	if err != nil {
		return nil, err
	}
	paths = append([]string{filepath.Join(directory, "localhost.crt")}, paths...)
	seen := map[[32]byte]bool{}
	removed := []map[string]any{}
	for _, path := range paths {
		data, err := os.ReadFile(path)
		if errors.Is(err, os.ErrNotExist) {
			continue
		}
		if err != nil {
			return nil, err
		}
		// Removing obsolete trust must also work after a leaf has expired.
		cert, err := parseLocalCertificate(data, true)
		if err != nil {
			return nil, fmt.Errorf("read cached certificate %s: %w", path, err)
		}
		fingerprint := sha256.Sum256(cert.Raw)
		if seen[fingerprint] {
			continue
		}
		if err := setCertificateTrust(cert, true); err != nil {
			return nil, err
		}
		seen[fingerprint] = true
		removed = append(removed, certificateDetails(cert, path))
	}
	return map[string]any{"state": "untrusted", "store": "CurrentUser/Root", "certificates": removed}, nil
}
