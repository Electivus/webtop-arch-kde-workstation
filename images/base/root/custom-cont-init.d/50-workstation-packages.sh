#!/usr/bin/env bash
set -euo pipefail

mkdir -p /run/electivus
touch /run/electivus/packages-ready
if ! workstation-packages capture >/dev/null; then
    echo 'Package inventory could not be refreshed; inspect workstation-packages status before recovery.' >&2
fi
