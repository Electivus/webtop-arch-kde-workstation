FROM golang:1.27.1-bookworm@sha256:648f440f42a0958804efb24df176f806f9d353b41f1c0627f666428e40310f6b AS commands
WORKDIR /src
COPY go.mod ./
COPY cmd/ ./cmd/
RUN test -z "$(gofmt -l cmd)" && go vet ./... && GOOS=windows GOARCH=amd64 go vet ./... && \
    CGO_ENABLED=0 GOOS=windows GOARCH=amd64 go build -trimpath -o /out/workstation.exe ./cmd/workstation && \
    CGO_ENABLED=0 go build -trimpath -o /out/workstation ./cmd/workstation
COPY distribution/windows/workstation.cmd /out/workstation.cmd
COPY distribution/windows/setup.cmd /out/setup.cmd

FROM scratch AS commands-export
COPY --from=commands /out/ /

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
COPY --from=commands /out/workstation.exe /out/workstation.cmd /out/setup.cmd /opt/electivus/windows/

HEALTHCHECK --interval=10s --timeout=8s --start-period=90s --retries=6 \
    CMD ["workstation-healthcheck"]
