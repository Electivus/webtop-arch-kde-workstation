FROM golang:1.27.1-bookworm@sha256:648f440f42a0958804efb24df176f806f9d353b41f1c0627f666428e40310f6b AS commands
WORKDIR /src
COPY go.mod ./
COPY cmd/ ./cmd/
RUN test -z "$(gofmt -l cmd)" && go vet ./... && GOOS=windows GOARCH=amd64 go vet ./... && \
    CGO_ENABLED=0 GOOS=windows GOARCH=amd64 go build -trimpath -o /out/workstation.exe ./cmd/workstation && \
    CGO_ENABLED=0 go build -trimpath -o /out/workstation ./cmd/workstation
COPY distribution/windows/workstation.cmd /out/workstation.cmd
COPY distribution/windows/setup.cmd /out/setup.cmd
COPY cmd/workstation/MOBY-LICENSE cmd/workstation/THIRD-PARTY.md /out/licenses/
RUN cp /usr/local/go/LICENSE /out/licenses/GO-LICENSE

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

# A build-only CA secret supports intercepted corporate networks. It is
# removed in the same layer; public images retain only the normal trust roots.
RUN --mount=type=secret,id=corporate_ca \
    if [ -s /run/secrets/corporate_ca ]; then \
      cp /run/secrets/corporate_ca /etc/ca-certificates/trust-source/anchors/electivus-build.crt; \
      update-ca-trust; \
    fi && \
    timeout 20m pacman -Syu --disable-download-timeout --noprogressbar --noconfirm --needed \
      git binutils nss gtk3 alsa-lib libxss ttf-liberation zsh zsh-autosuggestions zsh-syntax-highlighting docker-buildx && \
    curl --fail --location --show-error --output /tmp/oh-my-zsh.tar.gz \
      https://codeload.github.com/ohmyzsh/ohmyzsh/tar.gz/e995678ca8ce65e8e06f7c89d120cf2c02cb5399 && \
    printf '%s  %s\n' 67f87b9b08d718f1aead7e408c52a276c63a7f96b831b185f5a6461631acb0cc /tmp/oh-my-zsh.tar.gz | sha256sum -c - && \
    mkdir -p /usr/share/oh-my-zsh && \
    tar -xzf /tmp/oh-my-zsh.tar.gz -C /usr/share/oh-my-zsh --strip-components=1 && \
    printf '%s\n' e995678ca8ce65e8e06f7c89d120cf2c02cb5399 >/usr/share/oh-my-zsh/COMMIT && \
    ln -s /usr/share/zsh/plugins/zsh-autosuggestions /usr/share/oh-my-zsh/plugins/zsh-autosuggestions && \
    ln -s /usr/share/zsh/plugins/zsh-syntax-highlighting /usr/share/oh-my-zsh/plugins/zsh-syntax-highlighting && \
    rm -f /etc/ca-certificates/trust-source/anchors/electivus-build.crt && update-ca-trust && \
    rm -f /tmp/oh-my-zsh.tar.gz /var/cache/pacman/pkg/*.pkg.tar.*

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
    SHELL=/bin/zsh \
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
COPY images/base/root/usr/share/applications/ /usr/share/applications/
COPY images/base/root/etc/xdg/autostart/ /etc/xdg/autostart/
COPY images/base/root/etc/electivus/ /etc/electivus/
COPY --from=commands /out/workstation.exe /out/workstation.cmd /out/setup.cmd /opt/electivus/windows/
COPY --from=commands /out/licenses/ /opt/electivus/windows/licenses/

HEALTHCHECK --interval=10s --timeout=8s --start-period=90s --retries=6 \
    CMD ["workstation-healthcheck"]
