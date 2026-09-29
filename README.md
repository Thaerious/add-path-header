# add-path-header

Adds a `filename:` comment to the top of source files, or updates one that's already there.

    # filename: utils/helpers.py

The header is `ParentDir/filename`, or just `filename` for files directly in the root. Shebang, `<?xml`, `<?php`, and `<!DOCTYPE` lines stay first. BOM and line endings are preserved.

## Install

Requires Python 3.8+ and [pipx](https://pipx.pypa.io).

    sudo dnf install pipx        # Rocky/Fedora
    sudo apt install pipx        # Debian/Ubuntu
    pipx ensurepath              # then open a new terminal

    pipx install .               # from the repo root

## Usage

    add-path-header [paths...] [--root DIR] [-n] [-v]

- `paths`: files or directories; directories are walked recursively (default `.`)
- `--root DIR`: files directly in this dir get just the filename (default: git root, else cwd)
- `-n`, `--dry-run`: show changes without writing
- `-v`, `--verbose`: also report skipped and unchanged files

Examples:

    add-path-header -n            # preview the whole repo
    add-path-header src/          # one directory
    add-path-header main.py lib.c

The output lists each added or updated file, then a summary on stderr:

    added        src/main.py
    updated      lib/util.js
    added: 1, exists: 12, unsupported: 3, updated: 1

## Supported files

- `#`: py sh bash zsh rb pl r yaml yml toml conf cfg gd ps1 cmake, Dockerfile, Makefile, CMakeLists.txt, .bashrc
- `//`: js mjs cjs ts jsx tsx c h cc cpp cxx hpp hh cu java go rs swift kt kts cs scala dart php gdshader glsl scss less
- `/* */`: css
- `<!-- -->`: html htm xml md vue svelte svg
- `--`: sql lua hs
- `%`: tex
- `;`: ini
- `!`: f90

Binary, non-UTF-8, and unsupported files are skipped. These directories are skipped: .git node_modules .godot .import \_\_pycache\_\_ .venv venv dist build

## Update / Uninstall

    pipx install --force .       # reinstall after changes
    pipx uninstall add-path-header

## License

See [LICENSE](LICENSE).