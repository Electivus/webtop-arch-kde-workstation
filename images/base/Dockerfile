FROM lscr.io/linuxserver/webtop:arch-kde@sha256:ed197a60c161b5d45a0d0137a5c47ecd136964c57791bf3151d01ad41ac6b988

ARG VERSION=development
ARG REVISION=unknown
LABEL org.opencontainers.image.title="Electivus Arch KDE Base" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.revision="${REVISION}" \
      org.opencontainers.image.source="https://github.com/manoelcalixto/webtop-arch-kde-workstation" \
      org.opencontainers.image.base.name="lscr.io/linuxserver/webtop:arch-kde" \
      org.opencontainers.image.base.digest="sha256:ed197a60c161b5d45a0d0137a5c47ecd136964c57791bf3151d01ad41ac6b988" \
      io.electivus.workstation.variant="base"

ENV TITLE="Electivus Workstation" \
    START_DOCKER=false \
    PIXELFLUX_WAYLAND=false \
    DISABLE_DRI3=true \
    DISABLE_ZINK=true \
    SELKIES_MANUAL_WIDTH=1920 \
    SELKIES_MANUAL_HEIGHT=1080 \
    SELKIES_FRAMERATE=30 \
    SELKIES_SECOND_SCREEN=false \
    TZ=America/Bahia \
    SHELL=/bin/bash \
    LC_ALL="" \
    LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_TIME=pt_BR.UTF-8 \
    LC_NUMERIC=pt_BR.UTF-8 \
    LC_MONETARY=pt_BR.UTF-8 \
    LC_MEASUREMENT=pt_BR.UTF-8 \
    LC_PAPER=pt_BR.UTF-8

COPY --chmod=755 images/base/root/custom-cont-init.d/ /custom-cont-init.d/
COPY --chmod=755 images/base/root/usr/local/bin/ /usr/local/bin/

HEALTHCHECK --interval=10s --timeout=8s --start-period=90s --retries=6 \
    CMD ["workstation-healthcheck"]
