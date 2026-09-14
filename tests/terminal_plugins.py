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

    def read_for(seconds=0.5):
        output = bytearray()
        until = time.monotonic() + seconds
        while time.monotonic() < until:
            readable, _, _ = select.select([terminal], [], [], min(0.1, max(0, until - time.monotonic())))
            if readable:
                output.extend(os.read(terminal, 65536))
        return bytes(output)

    def type_text(value):
        os.write(terminal, value)
        return read_for()

    try:
        read_for(2)
        valid = type_text(b"printf")
        assert b"\x1b[32m" in valid, repr(valid)
        type_text(b"\x15")
        invalid = type_text(b"workstation_command_does_not_exist")
        assert b"\x1b[31m" in invalid, repr(invalid)
        type_text(b"\x15")
        type_text(b"printf 'workstation-suggestion-accepted\\n'\r")
        suggestion = type_text(b"printf 'workstation-sugg")
        assert b"estion-accepted" in suggestion, repr(suggestion)
        # Right Arrow must accept the history suffix, including the closing quote.
        accepted = type_text(b"\x1b[C\r")
        plain = re.sub(rb"\x1b\].*?(?:\x07|\x1b\\)", b"", accepted, flags=re.S)
        plain = re.sub(rb"\x1b\[[0-?]*[ -/]*[@-~]", b"", plain)
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
