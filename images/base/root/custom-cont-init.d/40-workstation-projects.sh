#!/usr/bin/env bash
set -euo pipefail

if [[ ! -e /config/projects ]]; then
    install -d -m 755 -o abc -g abc /config/projects
fi
if mountpoint -q /exchange && [[ ! -e /config/WindowsExchange && ! -L /config/WindowsExchange ]]; then
    ln -s /exchange /config/WindowsExchange
    chown -h abc:abc /config/WindowsExchange
fi

# Grant the desktop user membership in the existing socket group without
# changing ownership or permissions on the notebook's Docker socket.
if [[ -S /var/run/docker.sock ]]; then
    socket_gid=$(stat -c %g /var/run/docker.sock)
    socket_group=$(getent group "$socket_gid" | cut -d: -f1 || true)
    if [[ -z "$socket_group" ]]; then
        groupadd --gid "$socket_gid" workstation-docker
        socket_group=workstation-docker
    fi
    usermod -aG "$socket_group" abc
fi
