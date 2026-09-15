ARG BASE_IMAGE=electivus/webtop-arch-kde-base:stable
FROM ${BASE_IMAGE}
COPY --chown=abc:abc PKGBUILD example.c /tmp/replacement-package/
COPY repository.sh /tmp/replacement-repository.sh
RUN mkdir -p /tmp/replacement-build-home && chown abc:abc /tmp/replacement-build-home && \
    for stage in original renamed successor; do \
        s6-setuidgid abc env HOME=/tmp/replacement-build-home WORKSTATION_REPLACEMENT_STAGE="$stage" \
          makepkg --dir /tmp/replacement-package --force --cleanbuild --noconfirm || exit 1; \
    done && \
    pacman -U --noconfirm /tmp/replacement-package/workstation-image-original-*.pkg.tar.zst && \
    pacman -Q >/etc/electivus/image-packages.txt
LABEL org.opencontainers.image.version="package-replacement-fixture"
