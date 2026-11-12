"""Check an installed reviau the way a reviewer uses it.

Starts the ``reviau`` command found on the PATH, opens a folder with one clip
from the interface's API, renders its spectrogram, reviews it as correct and
checks that the clip was filed and the review recorded. CI runs it after the
installers, against the wheel being released; only the standard library is
used, so it needs nothing beyond the installed command.

    python scripts/smoke_test.py
"""

from __future__ import annotations

import json
import math
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import urllib.request
import wave
from pathlib import Path

PORT = 8799
BASE = f"http://127.0.0.1:{PORT}"


def call(path: str, body: dict | None = None, timeout: float = 120) -> bytes:
    data = None if body is None else json.dumps(body).encode()
    request = urllib.request.Request(
        BASE + path, data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def write_clip(path: Path, seconds: float = 2.0, rate: int = 16000) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frames = b"".join(
        struct.pack("<h", int(8000 * math.sin(2 * math.pi * 3000 * i / rate)))
        for i in range(int(seconds * rate))
    )
    with wave.open(str(path), "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(rate)
        out.writeframes(frames)


def main() -> int:
    exe = shutil.which("reviau")
    if not exe:
        print("error: the reviau command is not on the PATH", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory() as tmp:
        segments = Path(tmp) / "segments"
        write_clip(segments / "BOAALB" / "PONTO_A_20240115_053000.wav")

        server = subprocess.Popen(
            [exe, "--no-open", "--no-auth", "--port", str(PORT)]
        )
        try:
            for _ in range(90):
                if server.poll() is not None:
                    print("error: reviau exited before serving", file=sys.stderr)
                    return 1
                try:
                    boot = json.loads(call("/api/bootstrap", timeout=2))
                    break
                except OSError:
                    time.sleep(1)
            else:
                print("error: reviau did not answer", file=sys.stderr)
                return 1
            codes = [language["code"] for language in boot["languages"]]
            assert "pt-BR" in codes, codes

            state = json.loads(call("/api/open", {"path": str(segments)}))
            assert state["segment"]["label"] == "BOAALB", state["segment"]

            # The first spectrogram also loads librosa and its compiled parts.
            image = call("/api/spectrogram?index=0")
            assert image.startswith(b"\x89PNG"), image[:16]

            call("/api/review", {"relpath": state["segment"]["relpath"], "labels": ["BOAALB"]})
            filed = list((segments / "correct").rglob("*.wav"))
            assert filed, "the reviewed clip was not filed under correct/"
            assert (segments / "reviews.csv").is_file(), "reviews.csv was not written"
        finally:
            server.terminate()
            try:
                server.wait(timeout=20)
            except subprocess.TimeoutExpired:
                server.kill()

    print("reviau reviewed a clip: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
