#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests: AppID stored in .unifypy/metadata.json, not build.json."""

import json
import re
import uuid
from pathlib import Path

from unifypy.utils.cache_manager import CacheManager


UUID_RE = re.compile(
    r"^[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}$"
)


def test_get_or_generate_writes_metadata_only(tmp_path):
    """Empty config: generate AppID into metadata; do not require build.json."""
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    # No build.json — generation must not depend on writing one
    build_json = project_dir / "build.json"
    assert not build_json.exists()

    cm = CacheManager(str(project_dir))
    config = {"name": "TestApp"}

    app_id = cm.get_or_generate_app_id(config)

    assert UUID_RE.match(app_id), f"expected UUID-like id, got {app_id!r}"
    assert not build_json.exists(), "must not create/write build.json"

    meta_path = project_dir / ".unifypy" / "metadata.json"
    assert meta_path.exists()
    metadata = json.loads(meta_path.read_text(encoding="utf-8"))
    assert metadata.get("app_id") == app_id


def test_get_or_generate_is_stable(tmp_path):
    """Second call returns the same AppID from metadata."""
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    cm = CacheManager(str(project_dir))
    config = {"name": "StableApp"}

    first = cm.get_or_generate_app_id(config)
    second = cm.get_or_generate_app_id({"name": "StableApp"})

    assert first == second
    assert UUID_RE.match(first)


def test_config_app_id_preferred(tmp_path):
    """Explicit platforms.windows.inno_setup.app_id is preferred."""
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    cm = CacheManager(str(project_dir))

    # Seed metadata with a different id
    prior = str(uuid.uuid4()).upper()
    cm.save_metadata({"app_id": prior, "platform_hashes": {}})

    explicit = "AAAAAAAA-BBBB-CCCC-DDDD-EEEEEEEEEEEE"
    config = {
        "name": "CfgApp",
        "platforms": {
            "windows": {
                "inno_setup": {
                    "app_id": explicit,
                }
            }
        },
    }

    result = cm.get_or_generate_app_id(config)
    assert result == explicit

    # Metadata should be synced to the config value
    metadata = cm.load_metadata()
    assert metadata.get("app_id") == explicit


def test_build_json_not_required_when_generating(tmp_path):
    """Generation succeeds with no build.json and leaves the tree free of one."""
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    cm = CacheManager(str(project_dir))

    app_id = cm.get_or_generate_app_id({"name": "NoBuildJson"})
    assert app_id
    assert not (project_dir / "build.json").exists()
    assert (project_dir / ".unifypy" / "metadata.json").exists()
