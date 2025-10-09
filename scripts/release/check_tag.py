#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Check that tag (e.g., v2.0.1) matches pyproject.toml version.

Usage:
  python scripts/release/check_tag.py v2.0.1
or relies on env GITHUB_REF like refs/tags/v2.0.1
"""

import os
import re
import sys
from pathlib import Path


def get_tag(argv):
    if len(argv) >= 2:
        return argv[1]
    ref = os.getenv("GITHUB_REF", "")
    m = re.search(r"refs/tags/(v\d+\.\d+\.\d+)$", ref)
    return m.group(1) if m else None


def read_version():
    m = re.search(r"^version\s*=\s*\"([^\"]+)\"", Path("pyproject.toml").read_text(encoding="utf-8"), re.M)
    return m.group(1) if m else None


def main():
    tag = get_tag(sys.argv)
    if not tag:
        print("No tag provided or GITHUB_REF missing")
        return 2
    version = read_version()
    if not version:
        print("version not found in pyproject.toml")
        return 2
    if tag != f"v{version}":
        print(f"Tag {tag} does not match version {version}")
        return 2
    print(f"Tag {tag} matches version {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

