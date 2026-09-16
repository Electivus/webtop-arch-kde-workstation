ARG BASE_IMAGE
FROM ${BASE_IMAGE}

ARG VERSION=development
ARG REVISION=unknown
ARG BASE_IMAGE
ARG BASE_DIGEST=unknown
LABEL org.opencontainers.image.title="Electivus Arch KDE Salesforce" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.revision="${REVISION}" \
      org.opencontainers.image.base.name="${BASE_IMAGE}" \
      org.opencontainers.image.base.digest="${BASE_DIGEST}" \
      io.electivus.workstation.variant="salesforce"

RUN --mount=type=secret,id=corporate_ca \
    if [ -s /run/secrets/corporate_ca ]; then \
      cp /run/secrets/corporate_ca /etc/ca-certificates/trust-source/anchors/electivus-build.crt; \
      update-ca-trust; \
    fi && \
    timeout 20m pacman -Syu --disable-download-timeout --noprogressbar --noconfirm --needed \
      nodejs-lts-krypton npm jdk21-openjdk libxkbfile libsecret && \
    rm -f /etc/ca-certificates/trust-source/anchors/electivus-build.crt && update-ca-trust && \
    rm -f /var/cache/pacman/pkg/*.pkg.tar.*

ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk \
    NODE_USE_SYSTEM_CA=1 \
    DONT_PROMPT_WSL_INSTALL=1 \
    SF_AUTOUPDATE_DISABLE=true \
    SF_DISABLE_TELEMETRY=true \
    EDITOR="code-insiders --wait" \
    VISUAL="code-insiders --wait"

COPY --chmod=755 images/salesforce/root/usr/local/bin/ /usr/local/bin/
COPY images/salesforce/root/usr/share/ /usr/share/
COPY images/salesforce/root/etc/ /etc/
RUN update-mime-database /usr/share/mime && update-desktop-database /usr/share/applications
RUN pacman -Q >/etc/electivus/image-packages.txt
