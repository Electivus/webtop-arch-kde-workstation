# Container sandbox policy

`seccomp.json` derives from [Moby's default profile at
61eaf32614c7c71b60bd8927d3e6a4ffc8ff1f31](https://github.com/moby/profiles/blob/61eaf32614c7c71b60bd8927d3e6a4ffc8ff1f31/seccomp/default.json),
licensed under Apache 2.0; see `MOBY-LICENSE`.

The only behavioral change allows `clone`, `setns` and `unshare`, following
[Microsoft's Chromium sandbox recipe](https://playwright.dev/docs/docker).
This permits the unprivileged desktop user to create the browser's user/PID/network
namespaces. The remaining Moby deny-by-default rules and Linux capability checks
continue to apply. The launcher adds no capabilities and does not use privileged
mode, host IPC, `seccomp=unconfined`, or `--no-sandbox`.
