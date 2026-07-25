#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Bump version in pyproject.toml and unifypy/__init__.py.

Usage:
  python scripts/release/bump_version.py 2.0.1
"""

import re
import sys
from pathlib import Path


def _update_pyproject(root: Path, new_version: str) -> None:
    p = root / "pyproject.toml"
    content = p.read_text(encoding="utf-8")
    pattern = re.compile(r'(?m)^(version\s*=\s*)"[^"]+"')

    def _repl(m: re.Match) -> str:
        return f'{m.group(1)}"{new_version}"'

    new_content, n = pattern.subn(_repl, content)
    if n == 0:
        raise SystemExit("version field not found in pyproject.toml")
    p.write_text(new_content, encoding="utf-8")


def _update_init(root: Path, new_version: str) -> None:
    p = root / "unifypy" / "__init__.py"
    content = p.read_text(encoding="utf-8")
    pattern = re.compile(r'(?m)^(__version__\s*=\s*)"[^"]+"')

    def _repl(m: re.Match) -> str:
        return f'{m.group(1)}"{new_version}"'

    new_content, n = pattern.subn(_repl, content)
    if n == 0:
        raise SystemExit("__version__ not found in unifypy/__init__.py")
    p.write_text(new_content, encoding="utf-8")


def main():
    if len(sys.argv) != 2:
        print("Usage: bump_version.py <new_version>")
        return 2
    new_version = sys.argv[1].strip()
    if not re.match(r"^\d+\.\d+\.\d+$", new_version):
        print(f"Invalid version: {new_version}")
        return 2

    root = Path(__file__).resolve().parents[2]
    _update_pyproject(root, new_version)
    _update_init(root, new_version)
    print(f"Updated version to {new_version} (pyproject.toml + unifypy/__init__.py)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
