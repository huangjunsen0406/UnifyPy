#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""macOS notarization helpers via xcrun notarytool + stapler."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional


def can_notarize() -> bool:
    """Return True if ``xcrun notarytool`` appears available."""
    if shutil.which("xcrun") is None:
        return False
    try:
        result = subprocess.run(
            ["xcrun", "notarytool", "--help"],
            capture_output=True,
            timeout=15,
        )
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def resolve_notarize_credentials(
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Optional[str]]:
    """Resolve notarization credentials from config and environment.

    Config path: ``platforms.macos.notarize`` with keys:
      apple_id, team_id, password_env, profile

    Environment:
      UNIFYPY_APPLE_ID, UNIFYPY_TEAM_ID, UNIFYPY_APPLE_PASSWORD,
      UNIFYPY_NOTARY_PROFILE
    """
    notarize_cfg: Dict[str, Any] = {}
    if config:
        platforms = config.get("platforms") or {}
        macos = platforms.get("macos") or config.get("macos") or {}
        notarize_cfg = macos.get("notarize") or {}

    profile = (
        notarize_cfg.get("profile")
        or os.environ.get("UNIFYPY_NOTARY_PROFILE")
    )
    apple_id = (
        notarize_cfg.get("apple_id")
        or os.environ.get("UNIFYPY_APPLE_ID")
    )
    team_id = (
        notarize_cfg.get("team_id")
        or os.environ.get("UNIFYPY_TEAM_ID")
    )
    password_env = notarize_cfg.get("password_env") or "UNIFYPY_APPLE_PASSWORD"
    password = os.environ.get(password_env) or os.environ.get(
        "UNIFYPY_APPLE_PASSWORD"
    )

    return {
        "profile": profile,
        "apple_id": apple_id,
        "team_id": team_id,
        "password": password,
        "password_env": password_env,
    }


def credentials_ready(creds: Dict[str, Optional[str]]) -> bool:
    """True if either keychain profile or apple_id+team_id+password present."""
    if creds.get("profile"):
        return True
    return bool(creds.get("apple_id") and creds.get("team_id") and creds.get("password"))


def notarize_and_staple(
    path: Path,
    apple_id: Optional[str] = None,
    team_id: Optional[str] = None,
    password: Optional[str] = None,
    profile: Optional[str] = None,
    progress: Any = None,
) -> bool:
    """Submit *path* to Apple notary service, wait, then staple.

    Args:
        path: .dmg or .app path to notarize
        apple_id / team_id / password: Apple ID credentials
        profile: Keychain profile name (preferred when set)
        progress: Optional progress manager with info/warning methods

    Returns:
        bool: True on success

    Raises:
        RuntimeError: when tools missing, credentials missing, or notary fails
    """
    path = Path(path)
    if not path.exists():
        raise RuntimeError(f"Notarize target does not exist: {path}")

    if not can_notarize():
        raise RuntimeError(
            "xcrun notarytool 不可用。请安装 Xcode Command Line Tools。"
        )

    if profile:
        submit_cmd = [
            "xcrun",
            "notarytool",
            "submit",
            str(path),
            "--keychain-profile",
            profile,
            "--wait",
        ]
    elif apple_id and team_id and password:
        submit_cmd = [
            "xcrun",
            "notarytool",
            "submit",
            str(path),
            "--apple-id",
            apple_id,
            "--team-id",
            team_id,
            "--password",
            password,
            "--wait",
        ]
    else:
        raise RuntimeError(
            "缺少公证凭据。请设置 platforms.macos.notarize "
            "(apple_id/team_id/password_env 或 profile)，"
            "或环境变量 UNIFYPY_APPLE_ID / UNIFYPY_TEAM_ID / "
            "UNIFYPY_APPLE_PASSWORD / UNIFYPY_NOTARY_PROFILE。"
            "注意：ad-hoc 签名的应用无法公证，需要配置 codesign identity。"
        )

    if progress:
        progress.info(f"提交公证: {path}")
    else:
        from unifypy.core import logutil

        logutil.info(f"提交公证: {path}")

    try:
        result = subprocess.run(
            submit_cmd,
            capture_output=True,
            text=True,
            timeout=3600,
        )
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(f"notarytool 超时: {e}") from e

    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"notarytool 提交失败: {detail}")

    staple_cmd = ["xcrun", "stapler", "staple", str(path)]
    if progress:
        progress.info(f"装订公证票据: {path}")
    try:
        staple = subprocess.run(
            staple_cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(f"stapler 超时: {e}") from e

    if staple.returncode != 0:
        detail = (staple.stderr or staple.stdout or "").strip()
        raise RuntimeError(f"stapler staple 失败: {detail}")

    if progress:
        progress.info(f"公证完成: {path}")
    return True
