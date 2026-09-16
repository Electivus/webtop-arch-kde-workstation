ARG BASE_IMAGE
FROM ${BASE_IMAGE}
ARG WORKSTATION_VERSION
LABEL org.opencontainers.image.version="${WORKSTATION_VERSION}"
ARG BROKEN_GIT=0
RUN if [ "${BROKEN_GIT}" = "1" ]; then \
      printf '%s\n' '#!/bin/sh' 'exit 73' > /usr/local/bin/git; \
      chmod 0755 /usr/local/bin/git; \
    fi
