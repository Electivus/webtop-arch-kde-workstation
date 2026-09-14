#!/usr/bin/env bash
set -euo pipefail

chsh -s /bin/zsh abc
if [[ ! -e /config/.zshrc ]]; then
    install -m 644 -o abc -g abc /etc/electivus/default.zshrc /config/.zshrc
fi
