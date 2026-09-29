#!/usr/bin/env python3
"""Add a 'filename:' comment at the top of each file, or update an existing one.

The header is 'ParentDir/filename', or just 'filename' for files directly in the root.
If the top line (after any shebang/doctype preamble) is already a 'filename:' comment,
it is replaced when it differs.

Usage:
  add-path-header [paths...] [--root DIR] [--dry-run] [--verbose]

Paths default to '.', directories are walked recursively.
Root defaults to the git repo root, else cwd.
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

HASH = ("# ", "")
SLASH = ("// ", "")
BLOCK = ("/* ", " */")
HTML = ("<!-- ", " -->")
DASH = ("-- ", "")

STYLES = {
    **dict.fromkeys(".py .sh .bash .zsh .rb .pl .r .yaml .yml .toml .conf .gd .cfg .ps1 .cmake".split(), HASH),
    **dict.fromkeys(".js .mjs .cjs .ts .jsx .tsx .c .h .cc .cpp .cxx .hpp .hh .java .go .rs .swift .kt .kts .cs .scala .dart .php .gdshader .glsl .scss .less .cu".split(), SLASH),
    **dict.fromkeys(".css".split(), BLOCK),
    **dict.fromkeys(".html .htm .xml .md .vue .svelte .svg".split(), HTML),
    **dict.fromkeys(".sql .lua .hs".split(), DASH),
    ".tex": ("% ", ""),
    ".ini": ("; ", ""),
    ".f90": ("! ", ""),
}
NAMES = {"Dockerfile": HASH, "Makefile": HASH, "CMakeLists.txt": HASH, ".bashrc": HASH}
SKIP_DIRS = {".git", "node_modules", ".godot", ".import", "__pycache__", ".venv", "venv", "dist", "build"}
PREAMBLE = ("#!", "<?xml", "<?php", "<!DOCTYPE", "<!doctype")
TAG = "filename:"


def git_root(start: Path):
    try:
        out = subprocess.run(["git", "-C", str(start), "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, check=True)
        return Path(out.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def header_path(p: Path, root: Path) -> str:
    rp = p.resolve()
    if rp.parent == root:
        return rp.name
    return f"{rp.parent.name}/{rp.name}"


def is_filename_comment(line: str, style) -> bool:
    s = line.strip()
    opener = style[0].strip()
    if not s.startswith(opener):
        return False
    return s[len(opener):].lstrip().startswith(TAG)


def process(p: Path, root: Path, dry: bool) -> str:
    style = NAMES.get(p.name) or STYLES.get(p.suffix.lower())
    if not style:
        return "unsupported"
    raw = p.read_bytes()
    if b"\0" in raw[:8192]:
        return "binary"
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return "non-utf8"

    bom = text.startswith("\ufeff")
    if bom:
        text = text[1:]

    nl = "\r\n" if "\r\n" in text else "\n"
    lines = text.splitlines(keepends=True)
    header = f"{style[0]}{TAG} {header_path(p, root)}{style[1]}"

    idx = 1 if lines and lines[0].lstrip().startswith(PREAMBLE) else 0
    if idx and not lines[0].endswith(("\n", "\r")):
        lines[0] += nl

    if idx < len(lines) and is_filename_comment(lines[idx], style):
        if lines[idx].rstrip("\r\n") == header:
            return "exists"
        lines[idx] = header + nl
        status = "updated"
    else:
        lines.insert(idx, header + nl)
        status = "added"

    if not dry:
        with open(p, "w", encoding="utf-8", newline="") as f:
            f.write(("\ufeff" if bom else "") + "".join(lines))
    return status


def iter_files(paths):
    for arg in paths:
        p = Path(arg)
        if p.is_file():
            yield p
        elif p.is_dir():
            for dirpath, dirnames, filenames in os.walk(p):
                dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
                for fn in filenames:
                    yield Path(dirpath) / fn
        else:
            print(f"missing: {arg}", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*", default=["."])
    ap.add_argument("--root", type=Path, help="root dir; files directly in it get just the filename (default: git root or cwd)")
    ap.add_argument("-n", "--dry-run", action="store_true")
    ap.add_argument("-v", "--verbose", action="store_true", help="also report skipped/unchanged files")
    a = ap.parse_args()

    root = (a.root or git_root(Path.cwd()) or Path.cwd()).resolve()
    counts = {}
    for f in iter_files(a.paths):
        status = process(f, root, a.dry_run)
        counts[status] = counts.get(status, 0) + 1
        if status in ("added", "updated") or a.verbose:
            print(f"{status:12} {f}")
    print(("[dry-run] " if a.dry_run else "") + ", ".join(f"{k}: {v}" for k, v in sorted(counts.items())),
          file=sys.stderr)


if __name__ == "__main__":
    main()
