#!/usr/bin/python3
"""Check the GUI process as well as the local web frontend."""

import os
from pathlib import Path
import ssl
import sys
import urllib.error
import urllib.request


def main():
    try:
        pid = Path("/tmp/rapid-photo-web.pid").read_text().strip()
        if not pid.isdecimal():
            return 1
        command = Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\0")
        if b"/usr/bin/rapid-photo-downloader" not in command:
            return 1
        state = next(
            line.split(":", 1)[1].strip()
            for line in Path(f"/proc/{pid}/status").read_text().splitlines()
            if line.startswith("State:")
        )
        if state.startswith(("T", "Z", "X")):
            return 1
        secure = os.environ.get("SECURE_CONNECTION", "0").lower() in (
            "1", "true", "yes", "on", "enable", "enabled", "y",
        )
        scheme = "https" if secure else "http"
        port = int(os.environ.get("WEB_LISTENING_PORT", "5800"))
        # This is a loopback availability check, including self-signed HTTPS.
        context = ssl._create_unverified_context() if secure else None
        try:
            with urllib.request.urlopen(
                f"{scheme}://127.0.0.1:{port}/", timeout=3, context=context
            ):
                return 0
        except urllib.error.HTTPError as error:
            return 0 if error.code in (401, 403) else 1
    except (OSError, ValueError, urllib.error.URLError):
        return 1


if __name__ == "__main__":
    sys.exit(main())
