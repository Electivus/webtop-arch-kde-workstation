#!/usr/bin/env bash
set -euo pipefail
stage=${1:?choose renamed or successor}
case "$stage" in renamed | successor) ;; *) exit 1 ;; esac
repository=/config/projects/replacement-repo
export GNUPGHOME=/tmp/workstation-replacement-key
mkdir -p "$repository" "$GNUPGHOME"
chmod 700 "$GNUPGHOME"
if [[ ! -f "$GNUPGHOME/fixture-fingerprint" ]]; then
    gpg --batch --pinentry-mode loopback --passphrase '' --quick-generate-key \
        'Electivus package acceptance fixture' ed25519 sign 1d
    fingerprint=$(gpg --batch --with-colons --list-secret-keys | awk -F: '$1 == "fpr" {print $10; exit}')
    printf '%s\n' "$fingerprint" >"$GNUPGHOME/fixture-fingerprint"
    gpg --batch --export "$fingerprint" >"$GNUPGHOME/fixture.pub"
    pacman-key --init
    pacman-key --add "$GNUPGHOME/fixture.pub"
    pacman-key --lsign-key "$fingerprint"
    printf '\n[workstation-replacement-fixture]\nSigLevel = Required DatabaseRequired\nServer = file://%s\n' \
        "$repository" >>/etc/pacman.conf
fi
fingerprint=$(cat "$GNUPGHOME/fixture-fingerprint")
artifacts=(/tmp/replacement-package/workstation-image-"$stage"-*.pkg.tar.zst)
[[ ${#artifacts[@]} == 1 && -f "${artifacts[0]}" ]]
archive="$repository/$(basename "${artifacts[0]}")"
cp -- "${artifacts[0]}" "$archive"
gpg --batch --yes --detach-sign "$archive"
repo-add --sign --key "$fingerprint" "$repository/workstation-replacement-fixture.db.tar.gz" "$archive"
