FROM alpine:3.24@sha256:28bd5fe8b56d1bd048e5babf5b10710ebe0bae67db86916198a6eec434943f8b
COPY --chmod=755 write-result.sh /usr/local/bin/write-result
WORKDIR /workspace
HEALTHCHECK --interval=1s --timeout=2s --retries=20 CMD test -s /workspace/result.txt
CMD ["write-result"]
