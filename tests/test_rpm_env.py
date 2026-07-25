#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests that RPM packager passes env into run_command."""

from pathlib import Path
from unittest.mock import MagicMock

from unifypy.platforms.linux.rpm_packager import RPMPackager


def test_build_rpm_package_passes_env(tmp_path):
    runner = MagicMock()
    runner.run_command.return_value = False  # stop after call

    packager = RPMPackager(
        progress_manager=MagicMock(),
        runner=runner,
        tool_manager=MagicMock(),
        config={"name": "app", "version": "1.0.0"},
        project_dir=tmp_path,
    )

    rpmbuild_dir = tmp_path / "rpmbuild"
    rpmbuild_dir.mkdir()
    spec = tmp_path / "pkg.spec"
    spec.write_text("Name: app\n", encoding="utf-8")
    out = tmp_path / "out.rpm"

    packager._build_rpm_package(rpmbuild_dir, spec, out)

    assert runner.run_command.called
    kwargs = runner.run_command.call_args.kwargs
    # env may be positional or keyword depending on signature usage
    if "env" in kwargs:
        env = kwargs["env"]
    else:
        # positional after shell=False
        args = runner.run_command.call_args
        # call: command, stage, step_description, step_weight, shell=False, env=env
        env = kwargs.get("env") or (
            args[1].get("env") if len(args) > 1 and isinstance(args[1], dict) else None
        )
    assert env is not None
    assert "HOME" in env
    assert env["HOME"] == str(rpmbuild_dir.parent)


def test_base_packager_uses_project_dir(tmp_path):
    packager = RPMPackager(
        progress_manager=MagicMock(),
        runner=MagicMock(),
        tool_manager=MagicMock(),
        config={},
        project_dir=tmp_path,
    )
    assert Path(packager.env_manager.project_dir) == tmp_path.resolve()
