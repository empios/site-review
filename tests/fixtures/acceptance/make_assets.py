"""Generate the large hero image for the acceptance site (not committed)."""
import os
import struct
import sys
import zlib
from pathlib import Path


def png(path: Path, w: int = 1100, h: int = 900) -> None:
    raw = b"".join(b"\x00" + os.urandom(w * 3) for _ in range(h))  # random RGB, incompressible
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    data = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) \
        + chunk(b"IDAT", zlib.compress(raw, 0)) + chunk(b"IEND", b"")
    path.write_bytes(data)


if __name__ == "__main__":
    root = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).parent)
    for target in (root / "site" / "hero.png", root / "repo" / "public" / "hero.png"):
        png(target)
        print(target, target.stat().st_size)
