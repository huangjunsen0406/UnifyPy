#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Bump version in pyproject.toml.

Usage:
  python scripts/release/bump_version.py 2.0.1
"""

import re
import sys
from pathlib import Path


def main():
    if len(sys.argv) != 2:
        print("Usage: bump_version.py <new_version>")
        return 2
    new_version = sys.argv[1].strip()
    if not re.match(r"^\d+\.\d+\.\d+$", new_version):
        print(f"Invalid version: {new_version}")
        return 2

    p = Path("pyproject.toml")
    content = p.read_text(encoding="utf-8")
    pattern = re.compile(r"(?m)^(version\s*=\s*)\"[^\"]+\"")

    def _repl(m: re.Match) -> str:
        # Use a function replacement to avoid backslash-escape issues
        return f'{m.group(1)}"{new_version}"'

    new_content, n = pattern.subn(_repl, content)
    if n == 0:
        print("version field not found in pyproject.toml")
        return 2
    p.write_text(new_content, encoding="utf-8")
    print(f"Updated version to {new_version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
