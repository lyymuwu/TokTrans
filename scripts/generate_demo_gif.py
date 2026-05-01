#!/usr/bin/env python3
"""Generate docs/demo.gif without third-party dependencies."""

from __future__ import annotations

from pathlib import Path

W, H = 640, 320
S = 3
OUT = Path(__file__).resolve().parents[1] / "docs" / "demo.gif"

PALETTE = [
    (247, 250, 252),  # 0 background
    (15, 23, 42),     # 1 dark terminal
    (226, 232, 240),  # 2 light text
    (112, 225, 161),  # 3 green
    (139, 212, 255),  # 4 blue
    (255, 200, 87),   # 5 yellow
    (239, 68, 68),    # 6 red
    (51, 65, 85),     # 7 slate
    (255, 255, 255),  # 8 white
    (47, 128, 237),   # 9 accent blue
    (27, 127, 90),    # 10 accent green
]

FONT = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01111", "10000", "10000", "10000", "10000", "10000", "01111"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01111", "10000", "10000", "10111", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
    "J": ["00111", "00010", "00010", "00010", "10010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "10101", "01010"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "10000", "11110", "00001", "00001", "11110"],
    "6": ["01110", "10000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00001", "01110"],
    "-": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
    ">": ["10000", "01000", "00100", "00010", "00100", "01000", "10000"],
    "/": ["00001", "00010", "00010", "00100", "01000", "01000", "10000"],
    ":": ["00000", "00100", "00100", "00000", "00100", "00100", "00000"],
    ".": ["00000", "00000", "00000", "00000", "00000", "01100", "01100"],
    "%": ["11001", "11010", "00010", "00100", "01000", "01011", "10011"],
    " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
}


def rect(img: bytearray, x: int, y: int, w: int, h: int, c: int) -> None:
    for yy in range(max(0, y), min(H, y + h)):
        row = yy * W
        for xx in range(max(0, x), min(W, x + w)):
            img[row + xx] = c


def text(img: bytearray, x: int, y: int, value: str, c: int, scale: int = 2) -> None:
    cursor = x
    for ch in value.upper():
        glyph = FONT.get(ch, FONT[" "])
        for gy, line in enumerate(glyph):
            for gx, bit in enumerate(line):
                if bit == "1":
                    rect(img, cursor + gx * scale, y + gy * scale, scale, scale, c)
        cursor += 6 * scale


def frame(step: int) -> bytearray:
    img = bytearray([0] * (W * H))
    rect(img, 32, 28, 576, 264, 1)
    rect(img, 32, 28, 576, 24, 7)
    rect(img, 45, 37, 8, 8, 6)
    rect(img, 61, 37, 8, 8, 5)
    rect(img, 77, 37, 8, 8, 3)
    text(img, 48, 72, "TOKTRANS DEMO", 4, 2)
    text(img, 48, 112, "$ CODEX-TS EXEC CHINESE PROMPT", 2, 2)
    if step >= 1:
        text(img, 70, 148, "DETECT: CHINESE", 5, 2)
    if step >= 2:
        text(img, 70, 176, "TRANSLATE -> ENGLISH", 3, 2)
    if step >= 3:
        text(img, 70, 204, "RUN REAL CODEX CLI", 4, 2)
    if step >= 4:
        text(img, 70, 232, "FINAL ANSWER -> CHINESE", 3, 2)
    if step >= 5:
        text(img, 70, 260, "VISIBLE PROMPT: 35 -> 24  31%", 5, 2)
    return img


def lzw_data(indices: bytes) -> bytes:
    min_code_size = 8
    clear = 1 << min_code_size
    eoi = clear + 1
    codes: list[int] = []
    count = 0
    for b in indices:
        if count == 0:
            codes.append(clear)
        codes.append(b)
        count += 1
        if count >= 250:
            count = 0
    codes.append(eoi)

    bits = 0
    nbits = 0
    out = bytearray()
    for code in codes:
        bits |= code << nbits
        nbits += 9
        while nbits >= 8:
            out.append(bits & 255)
            bits >>= 8
            nbits -= 8
    if nbits:
        out.append(bits & 255)
    blocks = bytearray()
    for i in range(0, len(out), 255):
        chunk = out[i:i + 255]
        blocks.append(len(chunk))
        blocks.extend(chunk)
    blocks.append(0)
    return bytes([min_code_size]) + bytes(blocks)


def write_gif(frames: list[bytearray]) -> None:
    palette = bytearray()
    for rgb in PALETTE:
        palette.extend(rgb)
    palette.extend(b"\x00\x00\x00" * (256 - len(PALETTE)))

    data = bytearray()
    data.extend(b"GIF89a")
    data.extend(W.to_bytes(2, "little"))
    data.extend(H.to_bytes(2, "little"))
    data.extend(bytes([0xF7, 0, 0]))
    data.extend(palette)
    data.extend(b"!\xFF\x0BNETSCAPE2.0\x03\x01\x00\x00\x00")
    for img in frames:
        data.extend(b"!\xF9\x04\x04")
        data.extend((130).to_bytes(2, "little"))
        data.extend(b"\x00\x00")
        data.extend(b",\x00\x00\x00\x00")
        data.extend(W.to_bytes(2, "little"))
        data.extend(H.to_bytes(2, "little"))
        data.extend(b"\x00")
        data.extend(lzw_data(bytes(img)))
    data.extend(b";")
    OUT.write_bytes(data)


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    write_gif([frame(i) for i in range(6)])
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
