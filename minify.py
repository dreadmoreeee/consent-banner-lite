"""Build consent-banner-lite.min.js and consent-banner-lite.min.css.

    python minify.py            # write the .min files and print their sizes
    python minify.py --check    # exit 1 if the .min files are out of date

A deliberately small minifier with no dependencies: it removes comments
(except /*! license */) and collapses whitespace. It understands string
literals but not regular expression literals, so the source uses none, and
every statement ends with a semicolon.
"""

from __future__ import annotations

import gzip
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NAME = "consent-banner-lite"
WORD = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_$")


def _join(out: list[str], nxt: str) -> None:
    """Add one space only where dropping the whitespace would change meaning."""
    prev = out[-1][-1] if out and out[-1] else ""
    if (prev in WORD and nxt in WORD) or (prev in "+-" and nxt in "+-"):
        out.append(" ")


def minify_js(src: str) -> str:
    out: list[str] = []
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        if c in "'\"`":
            j = i + 1
            while j < n and src[j] != c:
                j += 2 if src[j] == "\\" else 1
            out.append(src[i : j + 1])
            i = j + 1
        elif src.startswith("/*", i):
            j = src.index("*/", i + 2) + 2
            if src.startswith("/*!", i):
                out.append(src[i:j] + "\n")
            i = j
        elif src.startswith("//", i):
            j = src.find("\n", i)
            i = n if j < 0 else j
        elif c.isspace():
            while i < n and src[i].isspace():
                i += 1
            if i < n and not src.startswith("//", i) and not src.startswith("/*", i):
                _join(out, src[i])
        else:
            out.append(c)
            i += 1
    return "".join(out).strip() + "\n"


def minify_css(src: str) -> str:
    out: list[str] = []
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        if c in "'\"":
            j = src.index(c, i + 1)
            out.append(src[i : j + 1])
            i = j + 1
        elif src.startswith("/*", i):
            j = src.index("*/", i + 2) + 2
            if src.startswith("/*!", i):
                out.append(src[i:j] + "\n")
            i = j
        elif c.isspace():
            while i < n and src[i].isspace():
                i += 1
            prev = out[-1][-1] if out and out[-1] else ""
            if i < n and prev not in "{};:,>\n" and src[i] not in "{};,>":
                out.append(" ")
        else:
            out.append(c)
            i += 1
    text = "".join(out).replace(";}", "}")
    return text.strip() + "\n"


def build() -> dict[str, str]:
    js = (HERE / f"{NAME}.js").read_text(encoding="ascii")
    css = (HERE / f"{NAME}.css").read_text(encoding="ascii")
    return {f"{NAME}.min.js": minify_js(js), f"{NAME}.min.css": minify_css(css)}


def gz_size(text: str) -> int:
    return len(gzip.compress(text.encode("ascii"), compresslevel=9, mtime=0))


def main(argv: list[str]) -> int:
    outputs = build()
    if "--check" in argv:
        stale = [name for name, text in outputs.items()
                 if not (HERE / name).is_file() or (HERE / name).read_text(encoding="ascii") != text]
        for name in stale:
            print(f"out of date: {name} (run python minify.py)")
        return 1 if stale else 0
    for name, text in outputs.items():
        (HERE / name).write_text(text, encoding="ascii", newline="\n")
        print(f"{name}: {len(text)} bytes, {gz_size(text)} bytes gzipped")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
