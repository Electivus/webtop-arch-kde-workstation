"""Exercise visible Zsh editing behavior through an actual pseudo-terminal."""
import json
import os
import pty
import re
import select
import signal
import time


def main():
    pid, terminal = pty.fork()
    if pid == 0:
        os.environ["TERM"] = "xterm-256color"
        os.execlp("zsh", "zsh", "-i")

    def plain_text(output):
        output = re.sub(rb"\x1b\].*?(?:\x07|\x1b\\)", b"", output, flags=re.S)
        return re.sub(rb"\x1b\[[0-?]*[ -/]*[@-~]", b"", output)

    def read_until(expected, plain=False):
        output = bytearray()
        until = time.monotonic() + 20
        while time.monotonic() < until:
            readable, _, _ = select.select([terminal], [], [], min(0.1, max(0, until - time.monotonic())))
            if readable:
                output.extend(os.read(terminal, 65536))
                observed = plain_text(bytes(output)) if plain else bytes(output)
                if expected in observed:
                    return bytes(output)
        raise AssertionError(f"Terminal did not produce {expected!r}; received {bytes(output)!r}")

    def type_text(value, expected, plain=False):
        os.write(terminal, value)
        return read_until(expected, plain=plain)

    try:
        # Zsh enables bracketed paste when its line editor is ready. This
        # survives slow user startup commands and CPU contention in CI.
        read_until(b"\x1b[?2004h")
        valid = type_text(b"printf", b"\x1b[32m")
        assert b"\x1b[32m" in valid, repr(valid)
        invalid = type_text(b"\x15workstation_command_does_not_exist", b"\x1b[31m")
        assert b"\x1b[31m" in invalid, repr(invalid)
        type_text(b"\x15printf 'workstation-suggestion-accepted\\n'\r", b"\x1b[?2004h")
        suggestion = type_text(b"printf 'workstation-sugg", b"estion-accepted")
        assert b"estion-accepted" in suggestion, repr(suggestion)
        # Right Arrow must accept the history suffix, including the closing quote.
        accepted = type_text(b"\x1b[C\r", b"\r\nworkstation-suggestion-accepted\r\n", plain=True)
        plain = plain_text(accepted)
        assert b"\r\nworkstation-suggestion-accepted\r\n" in plain, repr(accepted)
        print(json.dumps({"syntaxHighlighting": "valid-green/invalid-red",
                          "autosuggestion": "history suffix displayed and accepted with Right Arrow"}))
    finally:
        # Interactive shells ignore SIGTERM; terminate only this owned PTY child.
        os.kill(pid, signal.SIGKILL)
        os.waitpid(pid, 0)
        os.close(terminal)


if __name__ == "__main__":
    main()
