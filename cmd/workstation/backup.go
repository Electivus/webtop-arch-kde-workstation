package main

import (
	"context"
	"crypto/rand"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"encoding/pem"
	"errors"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"time"
)

type backupSummary struct {
	ID        string `json:"id"`
	CreatedAt string `json:"createdAt"`
	ImageID   string `json:"imageId"`
	Variant   string `json:"variant"`
	Bytes     int64  `json:"bytes"`
}

type backupManifest struct {
	backupSummary
	Schema       int               `json:"schema"`
	SHA256       string            `json:"sha256"`
	Profile      profile           `json:"profile"`
	HostFiles    map[string][]byte `json:"hostFiles"`
	Applications json.RawMessage   `json:"applications"`
}

var backupID = regexp.MustCompile(`^[0-9]{8}T[0-9]{6}\.[0-9]{9}Z-[0-9a-f]{12}$`)
var imageID = regexp.MustCompile(`^sha256:[0-9a-f]{64}$`)

func validHomeVolume(p profile) bool {
	return p.HomeVolume == p.Name+"-home" || regexp.MustCompile("^"+regexp.QuoteMeta(p.Name)+"-home-[0-9a-f]{12}$").MatchString(p.HomeVolume)
}

func randomSuffix() (string, error) {
	var random [6]byte
	if _, err := rand.Read(random[:]); err != nil {
		return "", err
	}
	return hex.EncodeToString(random[:]), nil
}

func atomicFile(filename string, data []byte) error {
	file, err := os.CreateTemp(filepath.Dir(filename), ".workstation-write-*")
	if err != nil {
		return err
	}
	defer os.Remove(file.Name())
	if _, err := file.Write(data); err != nil {
		file.Close()
		return err
	}
	if err := file.Sync(); err != nil {
		file.Close()
		return err
	}
	if err := file.Close(); err != nil {
		return err
	}
	return os.Rename(file.Name(), filename)
}

func removeWithin(parent, directory string) error {
	root, err := filepath.EvalSymlinks(parent)
	if err != nil {
		return err
	}
	target, err := filepath.EvalSymlinks(directory)
	if errors.Is(err, os.ErrNotExist) {
		return nil
	}
	if err != nil {
		return err
	}
	relative, err := filepath.Rel(root, target)
	if err != nil || relative == "." || !filepath.IsLocal(relative) {
		return errors.New("refusing to remove a directory outside backup storage")
	}
	return os.RemoveAll(directory)
}

func readBackup(directory string) (backupManifest, error) {
	var manifest backupManifest
	file, err := os.Open(filepath.Join(directory, "manifest.json"))
	if err != nil {
		return manifest, fmt.Errorf("incomplete backup: %w", err)
	}
	data, readErr := io.ReadAll(io.LimitReader(file, 64*1024*1024+1))
	file.Close()
	if readErr != nil || len(data) > 64*1024*1024 {
		return manifest, errors.New("invalid or incomplete backup manifest")
	}
	checksumFile, err := os.Open(filepath.Join(directory, "manifest.sha256"))
	if err != nil {
		return manifest, fmt.Errorf("incomplete backup manifest checksum: %w", err)
	}
	checksum, checksumErr := io.ReadAll(io.LimitReader(checksumFile, 67))
	checksumFile.Close()
	manifestHash := sha256.Sum256(data)
	if checksumErr != nil || len(checksum) > 66 || strings.TrimSpace(string(checksum)) != hex.EncodeToString(manifestHash[:]) {
		return manifest, errors.New("backup manifest checksum does not match; current data was not changed")
	}
	if json.Unmarshal(data, &manifest) != nil ||
		manifest.Schema != 1 || !backupID.MatchString(manifest.ID) || filepath.Base(directory) != manifest.ID ||
		(manifest.Variant != "base" && manifest.Variant != "salesforce") ||
		!imageID.MatchString(manifest.ImageID) || manifest.Bytes <= 0 ||
		!regexp.MustCompile(`^[0-9a-f]{64}$`).MatchString(manifest.SHA256) {
		return manifest, errors.New("invalid or incomplete backup manifest")
	}
	p := manifest.Profile
	if p.Schema != 1 || !regexp.MustCompile(`^[0-9a-f]{32}$`).MatchString(p.InstallationID) ||
		!validName(p.Name) || !validHomeVolume(p) || p.Image == "" || p.DockerContext == "" ||
		(p.ImageID != "" && !imageID.MatchString(p.ImageID)) ||
		p.Port < 1024 || p.Port > 65535 || p.MemoryMiB < 1024 || p.CPUs < 1 {
		return manifest, errors.New("invalid or incomplete backup profile; current data was not changed")
	}
	if _, err := time.Parse(time.RFC3339Nano, manifest.CreatedAt); err != nil {
		return manifest, errors.New("invalid backup date")
	}
	archive, err := os.Open(filepath.Join(directory, "home.tar"))
	if err != nil {
		return manifest, fmt.Errorf("incomplete backup archive: %w", err)
	}
	defer archive.Close()
	info, err := archive.Stat()
	if err != nil || !info.Mode().IsRegular() || info.Size() != manifest.Bytes {
		return manifest, errors.New("incomplete backup archive: size does not match")
	}
	hash := sha256.New()
	if _, err := io.Copy(hash, archive); err != nil {
		return manifest, err
	}
	if hex.EncodeToString(hash.Sum(nil)) != manifest.SHA256 {
		return manifest, errors.New("backup checksum does not match; current data was not changed")
	}
	return manifest, nil
}

func completedBackups(directory, installationID string) ([]backupSummary, []string, error) {
	entries, err := os.ReadDir(directory)
	if err != nil && !errors.Is(err, os.ErrNotExist) {
		return nil, nil, err
	}
	backups, incomplete := []backupSummary{}, []string{}
	for _, entry := range entries {
		if !entry.IsDir() || entry.Type()&os.ModeSymlink != 0 {
			continue
		}
		if strings.HasPrefix(entry.Name(), ".incomplete-") {
			incomplete = append(incomplete, entry.Name())
			continue
		}
		if !backupID.MatchString(entry.Name()) {
			continue
		}
		manifest, err := readBackup(filepath.Join(directory, entry.Name()))
		if err != nil {
			incomplete = append(incomplete, entry.Name())
			continue
		}
		if manifest.Profile.InstallationID != installationID {
			continue
		}
		backups = append(backups, manifest.backupSummary)
	}
	sort.Slice(backups, func(i, j int) bool { return backups[i].ID > backups[j].ID })
	return backups, incomplete, nil
}

func personalVolume(p profile) error {
	var volumes []struct{ Labels map[string]string }
	if err := dockerJSON(p, &volumes, "volume", "inspect", p.HomeVolume); err != nil {
		return fmt.Errorf("personal volume unavailable; start the workstation once before backup: %w", err)
	}
	if len(volumes) != 1 || volumes[0].Labels[ownerLabel] != p.InstallationID {
		return errors.New("personal volume belongs to another installation")
	}
	return nil
}

func otherVolumeWriters(p profile, allowed string) error {
	ids, err := docker(p.DockerContext, "container", "ls", "--filter", "volume="+p.HomeVolume, "--format", "{{.ID}}")
	if err != nil {
		return err
	}
	if len(ids) == 0 {
		return nil
	}
	var containers []struct {
		Name   string
		State  struct{ Running bool }
		Mounts []struct {
			Name string
			RW   bool
		}
	}
	if err := dockerJSON(p, &containers, append([]string{"container", "inspect"}, strings.Fields(string(ids))...)...); err != nil {
		return err
	}
	for _, container := range containers {
		if !container.State.Running || strings.TrimPrefix(container.Name, "/") == allowed {
			continue
		}
		for _, mount := range container.Mounts {
			if mount.Name == p.HomeVolume && mount.RW {
				return fmt.Errorf("container %s can write the personal volume; stop its project/service before backup or restore", strings.TrimPrefix(container.Name, "/"))
			}
		}
	}
	return nil
}

func stopForSnapshot(p profile, c *containerInfo) error {
	if err := otherVolumeWriters(p, p.Name); err != nil {
		return err
	}
	if c != nil && c.State.Running {
		fmt.Fprintln(os.Stderr, "Stopping the workstation for a consistent copy. Only saved files are included; processes are not backed up.")
		if _, err := docker(p.DockerContext, "container", "stop", "--time", "30", p.Name); err != nil {
			return err
		}
	}
	return otherVolumeWriters(p, "")
}

func snapshotImage(p profile, c *containerInfo) (containerInfo, error) {
	reference, err := selectedImageReference(p, c)
	if err != nil {
		return containerInfo{}, err
	}
	return inspectWorkstationImage(p, reference)
}

func inspectWorkstationImage(p profile, reference string) (containerInfo, error) {
	var images []containerInfo
	if err := dockerJSON(p, &images, "image", "inspect", reference); err != nil {
		return containerInfo{}, err
	}
	if len(images) != 1 || images[0].OS != "linux" || images[0].Architecture != "amd64" || !imageID.MatchString(images[0].ID) {
		return containerInfo{}, errors.New("backup requires an available Linux amd64 workstation image")
	}
	variant := images[0].Config.Labels["io.electivus.workstation.variant"]
	if variant != "base" && variant != "salesforce" {
		return containerInfo{}, errors.New("backup image is not a workstation variant")
	}
	return images[0], nil
}

func volumeCommand(p profile, image, volume string, readOnly bool, program string, args ...string) []string {
	mount := "type=volume,src=" + volume + ",dst=/config,volume-nocopy"
	if readOnly {
		mount += ",readonly"
	}
	invocation := []string{"run", "--rm", "--interactive", "--network", "none", "--read-only", "--log-driver", "none", "--no-healthcheck",
		"--label", ownerLabel + "=" + p.InstallationID,
		"--mount", mount, "--entrypoint", program, image}
	return append(invocation, args...)
}

type transferDiagnostic struct {
	data    []byte
	omitted bool
}

func (d *transferDiagnostic) Write(data []byte) (int, error) {
	count := len(data)
	remaining := 16*1024 - len(d.data)
	if len(data) > remaining {
		data = data[:remaining]
		d.omitted = true
	}
	d.data = append(d.data, data...)
	// Always drain stderr so a long sequence of tar failures cannot stall Docker.
	return count, nil
}

func (d *transferDiagnostic) String() string {
	message := string(d.data)
	if d.omitted {
		message += "\n[additional diagnostic output omitted]"
	}
	return message
}

func streamVolume(p profile, input io.Reader, output io.Writer, args []string) error {
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Minute)
	defer cancel()
	command := exec.CommandContext(ctx, "docker", append([]string{"--context", p.DockerContext}, args...)...)
	var diagnostic transferDiagnostic
	command.Stdin, command.Stdout, command.Stderr = input, output, &diagnostic
	if err := command.Run(); err != nil {
		return fmt.Errorf("backup transfer failed (check disk space and archive integrity): %w: %s", err, strings.TrimSpace(diagnostic.String()))
	}
	return nil
}

func profileBackupFiles(directory string) (map[string][]byte, error) {
	files := map[string][]byte{}
	data, err := os.ReadFile(filepath.Join(directory, "network.json"))
	if err != nil && !errors.Is(err, os.ErrNotExist) {
		return nil, err
	}
	if err == nil {
		files["network.json"] = data
	}
	certificates, err := filepath.Glob(filepath.Join(directory, "certificates", "*.crt"))
	if err != nil {
		return nil, err
	}
	certificates = append(certificates, filepath.Join(directory, "localhost.crt"))
	for _, path := range certificates {
		data, err := os.ReadFile(path)
		if errors.Is(err, os.ErrNotExist) {
			continue
		}
		if err != nil {
			return nil, err
		}
		block, _ := pem.Decode(data)
		if block == nil || block.Type != "CERTIFICATE" {
			return nil, errors.New("invalid local certificate archive")
		}
		fingerprint := sha256.Sum256(block.Bytes)
		files["certificates/"+hex.EncodeToString(fingerprint[:])+".crt"] = data
	}
	return files, nil
}

func backup(p profile, opts options) (any, error) {
	directory := opts.backupDirectory
	if directory == "" {
		directory = filepath.Join(opts.directory, "backups")
	}
	directory, err := filepath.Abs(directory)
	if err != nil {
		return nil, err
	}
	if opts.listBackups {
		backups, incomplete, err := completedBackups(directory, p.InstallationID)
		return map[string]any{"backups": backups, "incomplete": incomplete, "directory": directory}, err
	}
	c, err := ownedContainer(p)
	if err != nil {
		return nil, err
	}
	if err := personalVolume(p); err != nil {
		return nil, err
	}
	image, err := snapshotImage(p, c)
	if err != nil {
		return nil, err
	}
	if err := os.MkdirAll(directory, 0700); err != nil {
		return nil, fmt.Errorf("backup directory unavailable: %w", err)
	}
	estimate, err := docker(p.DockerContext, volumeCommand(p, image.ID, p.HomeVolume, true, "du", "-sb", "/config")...)
	if err != nil {
		return nil, err
	}
	var dataBytes uint64
	if _, err := fmt.Sscanf(string(estimate), "%d", &dataBytes); err != nil {
		return nil, errors.New("cannot estimate backup size")
	}
	available, err := availableDiskBytes(directory)
	if err != nil {
		return nil, err
	}
	required := dataBytes + dataBytes/10 + 64*1024*1024
	if available < required {
		return nil, fmt.Errorf("not enough free space for backup: estimated %d bytes required, %d available; existing backups and running workstation were preserved", required, available)
	}
	if err := stopForSnapshot(p, c); err != nil {
		return nil, err
	}
	suffix, err := randomSuffix()
	if err != nil {
		return nil, err
	}
	id := time.Now().UTC().Format("20060102T150405.000000000Z") + "-" + suffix
	staging, err := os.MkdirTemp(directory, ".incomplete-")
	if err != nil {
		return nil, err
	}
	defer removeWithin(directory, staging)
	hostFiles, err := profileBackupFiles(opts.directory)
	if err != nil {
		return nil, err
	}
	apps, err := docker(p.DockerContext, volumeCommand(p, image.ID, p.HomeVolume, true, "python3", "-c",
		`import pathlib,json; p=pathlib.Path('/config/.local/state/electivus/preparation.json'); d=json.loads(p.read_text()) if p.exists() else {}; print(json.dumps(d.get('apps',{})))`)...)
	if err != nil {
		return nil, err
	}
	archive, err := os.OpenFile(filepath.Join(staging, "home.tar"), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if err != nil {
		return nil, err
	}
	hash := sha256.New()
	transferErr := streamVolume(p, nil, io.MultiWriter(archive, hash), volumeCommand(p, image.ID, p.HomeVolume, true, "tar",
		"--xattrs", "--acls", "--numeric-owner", "--format=pax", "-cpf", "-", "-C", "/config", "."))
	syncErr := archive.Sync()
	info, statErr := archive.Stat()
	closeErr := archive.Close()
	for _, err := range []error{transferErr, syncErr, statErr, closeErr} {
		if err != nil {
			return nil, err
		}
	}
	if err := otherVolumeWriters(p, ""); err != nil {
		return nil, err
	}
	manifest := backupManifest{backupSummary{id, time.Now().UTC().Format(time.RFC3339Nano), image.ID,
		image.Config.Labels["io.electivus.workstation.variant"], info.Size()}, 1, hex.EncodeToString(hash.Sum(nil)), p, hostFiles, json.RawMessage(apps)}
	data, err := json.MarshalIndent(manifest, "", "  ")
	if err != nil {
		return nil, err
	}
	if err := atomicFile(filepath.Join(staging, "manifest.json"), data); err != nil {
		return nil, err
	}
	manifestHash := sha256.Sum256(data)
	if err := atomicFile(filepath.Join(staging, "manifest.sha256"), []byte(hex.EncodeToString(manifestHash[:])+"\n")); err != nil {
		return nil, err
	}
	destination := filepath.Join(directory, id)
	if err := os.Rename(staging, destination); err != nil {
		return nil, err
	}
	backups, _, err := completedBackups(directory, p.InstallationID)
	if err != nil {
		return nil, err
	}
	verified := false
	for _, candidate := range backups {
		verified = verified || candidate.ID == id
	}
	if !verified {
		return nil, errors.New("new backup failed integrity verification; existing backups were preserved")
	}
	for _, old := range backups[minimum(2, len(backups)):] {
		if err := removeWithin(directory, filepath.Join(directory, old.ID)); err != nil {
			return nil, fmt.Errorf("backup completed but retention cleanup failed: %w", err)
		}
	}
	return map[string]any{"state": "completed", "id": id, "directory": destination, "imageId": image.ID,
		"bytes": info.Size(), "workstationState": "stopped", "retained": minimum(2, len(backups))}, nil
}

func minimum(a, b int) int {
	if a < b {
		return a
	}
	return b
}

func restoreBackup(p profile, opts options) (any, error) {
	if opts.backupSource == "" {
		return nil, errors.New("restore requires --backup with a completed backup directory")
	}
	source, err := filepath.Abs(opts.backupSource)
	if err != nil {
		return nil, err
	}
	manifest, err := readBackup(source)
	if err != nil {
		return nil, err
	}
	c, err := ownedContainer(p)
	if err != nil {
		return nil, err
	}
	selected := p
	selected.Image = manifest.ImageID
	selected.ImageID = manifest.ImageID
	image, err := snapshotImage(selected, nil)
	if err != nil {
		return nil, fmt.Errorf("backup image unavailable; restore requires the recorded image: %w", err)
	}
	variant := image.Config.Labels["io.electivus.workstation.variant"]
	if variant != manifest.Variant {
		return nil, errors.New("recorded image does not match the backup variant")
	}
	oldImage, currentImageErr := snapshotImage(p, c)
	if currentImageErr != nil {
		// A backup from this installation records its variant even after the
		// container and the mutable image tag have disappeared.
		if c != nil || manifest.Profile.InstallationID != p.InstallationID {
			return nil, fmt.Errorf("cannot verify the target workstation variant: %w", currentImageErr)
		}
	} else if variant != oldImage.Config.Labels["io.electivus.workstation.variant"] {
		return nil, errors.New("backup and installation must use the same workstation variant")
	}
	for name := range manifest.HostFiles {
		if name != "network.json" && !regexp.MustCompile(`^certificates/[0-9a-f]{64}\.crt$`).MatchString(name) {
			return nil, errors.New("invalid backup profile file")
		}
	}
	previousVolume, err := docker(p.DockerContext, "volume", "ls", "--quiet", "--filter", "name=^"+p.HomeVolume+"$")
	if err != nil {
		return nil, err
	}
	if len(previousVolume) != 0 {
		if err := personalVolume(p); err != nil {
			return nil, err
		}
	}
	if err := stopForSnapshot(p, c); err != nil {
		return nil, err
	}
	suffix, err := randomSuffix()
	if err != nil {
		return nil, err
	}
	restoredVolume := p.Name + "-home-" + suffix
	if _, err := docker(p.DockerContext, "volume", "create", "--label", ownerLabel+"="+p.InstallationID, restoredVolume); err != nil {
		return nil, err
	}
	committed := false
	defer func() {
		if !committed {
			docker(p.DockerContext, "volume", "rm", restoredVolume)
		}
	}()
	archive, err := os.Open(filepath.Join(source, "home.tar"))
	if err != nil {
		return nil, err
	}
	extractedHash := sha256.New()
	err = streamVolume(p, io.TeeReader(archive, extractedHash), io.Discard, volumeCommand(p, image.ID, restoredVolume, false, "tar",
		"--xattrs", "--xattrs-include=*", "--acls", "--numeric-owner", "--same-owner", "-xpf", "-", "-C", "/config"))
	archive.Close()
	if err != nil {
		return nil, fmt.Errorf("restore failed; original personal volume was preserved: %w", err)
	}
	if hex.EncodeToString(extractedHash.Sum(nil)) != manifest.SHA256 {
		return nil, errors.New("backup archive changed during restore; original personal volume and profile were preserved")
	}
	originalNetwork, readErr := os.ReadFile(filepath.Join(opts.directory, "network.json"))
	if readErr != nil && !errors.Is(readErr, os.ErrNotExist) {
		return nil, readErr
	}
	defer func() {
		if !committed {
			if readErr == nil {
				atomicFile(filepath.Join(opts.directory, "network.json"), originalNetwork)
			} else {
				os.Remove(filepath.Join(opts.directory, "network.json"))
			}
		}
	}()
	if err := os.MkdirAll(filepath.Join(opts.directory, "certificates"), 0700); err != nil {
		return nil, err
	}
	for name, data := range manifest.HostFiles {
		if err := atomicFile(filepath.Join(opts.directory, filepath.FromSlash(name)), data); err != nil {
			return nil, err
		}
	}
	if _, exists := manifest.HostFiles["network.json"]; !exists {
		if err := os.Remove(filepath.Join(opts.directory, "network.json")); err != nil && !errors.Is(err, os.ErrNotExist) {
			return nil, err
		}
	}
	if c != nil {
		if _, err := docker(p.DockerContext, "container", "rm", p.Name); err != nil {
			return nil, err
		}
	}
	restored := manifest.Profile
	restored.Schema, restored.Name, restored.InstallationID = p.Schema, p.Name, p.InstallationID
	restored.DockerContext, restored.HomeVolume, restored.Image = p.DockerContext, restoredVolume, image.ID
	restored.ImageID = image.ID
	data, err := json.MarshalIndent(restored, "", "  ")
	if err != nil {
		return nil, err
	}
	if err := atomicFile(filepath.Join(opts.directory, "profile.json"), data); err != nil {
		return nil, err
	}
	committed = true
	result := map[string]any{"state": "restored", "id": manifest.ID, "imageId": image.ID, "homeVolume": restoredVolume,
		"workstationState": "stopped"}
	if len(previousVolume) != 0 {
		if _, err := docker(p.DockerContext, "volume", "rm", p.HomeVolume); err != nil {
			result["retainedPreviousVolume"] = p.HomeVolume
			result["cleanupNote"] = "Previous volume is still attached elsewhere; it was preserved."
		}
	}
	return result, nil
}
