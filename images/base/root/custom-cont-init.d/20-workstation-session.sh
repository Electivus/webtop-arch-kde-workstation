#!/usr/bin/env bash
set -euo pipefail

# Upstream derives LANGUAGE/LANG from even an empty LC_ALL. Restore the
# category-specific locale before the desktop services are started.
rm -f /run/s6/container_environment/LC_ALL
printf '%s' en_US.UTF-8 >/run/s6/container_environment/LANG
printf '%s' en_US:en >/run/s6/container_environment/LANGUAGE
unset LC_ALL
export LANG=en_US.UTF-8 LANGUAGE=en_US:en

install -d -o abc -g abc /config/.config /config/.local/state/electivus
if [[ ! -f /config/.config/plasma-localerc ]]; then
    cat >/config/.config/plasma-localerc <<'EOF'
[Formats]
LANG=en_US.UTF-8
LC_TIME=pt_BR.UTF-8
LC_NUMERIC=pt_BR.UTF-8
LC_MONETARY=pt_BR.UTF-8
LC_MEASUREMENT=pt_BR.UTF-8
LC_PAPER=pt_BR.UTF-8

[Translations]
LANGUAGE=en_US
EOF
    chown abc:abc /config/.config/plasma-localerc
fi
if [[ ! -f /config/.config/kxkbrc ]]; then
    cat >/config/.config/kxkbrc <<'EOF'
[Layout]
Use=true
Model=abnt2
LayoutList=br
VariantList=
Options=
ResetOldOptions=true
EOF
    chown abc:abc /config/.config/kxkbrc
fi

# Replace the upstream certificate, then renew on startup within 30 days of
# expiry. The private key remains in the home volume, outside image layers.
if [[ ! -f /config/.local/state/electivus/localhost-certificate-v1 || ! -s /config/ssl/cert.key ]] ||
    ! openssl x509 -in /config/ssl/cert.pem -checkend 2592000 -noout >/dev/null 2>&1; then
    install -d -m 700 -o abc -g abc /config/ssl
    openssl req -new -x509 -newkey rsa:3072 -sha256 -days 825 -noenc \
        -subj /CN=localhost \
        -addext 'subjectAltName=DNS:localhost,IP:127.0.0.1' \
        -addext 'basicConstraints=critical,CA:FALSE' \
        -addext 'keyUsage=critical,digitalSignature,keyEncipherment' \
        -addext 'extendedKeyUsage=serverAuth' \
        -keyout /config/ssl/cert.key.new -out /config/ssl/cert.pem.new
    chmod 600 /config/ssl/cert.key.new
    mv /config/ssl/cert.key.new /config/ssl/cert.key
    mv /config/ssl/cert.pem.new /config/ssl/cert.pem
    chown abc:abc /config/ssl/cert.key /config/ssl/cert.pem
    touch /config/.local/state/electivus/localhost-certificate-v1
    chown abc:abc /config/.local/state/electivus/localhost-certificate-v1
fi
