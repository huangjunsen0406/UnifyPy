#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Download and zip helpers for ToolManager (pure functions)."""

import hashlib
from pathlib import Path
from typing import Optional
import zipfile

import requests


def download_file(
    url: str,
    target_path: Path,
    expected_sha256: Optional[str] = None,
) -> None:
    """Download a file and optionally verify SHA256.

    Args:
        url: Download URL
        target_path: Destination path
        expected_sha256: Expected SHA256 hex; when set, mismatch deletes file and raises

    Raises:
        RuntimeError: On hash mismatch
    """
    response = requests.get(url, stream=True, timeout=30)
    response.raise_for_status()

    target_path = Path(target_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    hasher = hashlib.sha256()
    try:
        with open(target_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if not chunk:
                    continue
                f.write(chunk)
                hasher.update(chunk)
    except Exception:
        if target_path.exists():
            try:
                target_path.unlink()
            except OSError:
                pass
        raise

    if expected_sha256:
        actual = hasher.hexdigest().lower()
        expected = expected_sha256.lower()
        if actual != expected:
            try:
                target_path.unlink()
            except OSError:
                pass
            raise RuntimeError(
                f"SHA256 校验失败: 期望 {expected}, 实际 {actual} (url={url})"
            )


def safe_extract_zip(zip_ref: zipfile.ZipFile, extract_dir: Path) -> None:
    """Extract zip members while rejecting Zip Slip path escapes.

    Args:
        zip_ref: Open ZipFile
        extract_dir: Destination directory

    Raises:
        RuntimeError: if any member path escapes extract_dir
    """
    extract_dir = Path(extract_dir).resolve()
    for member in zip_ref.infolist():
        member_path = Path(member.filename)
        # Reject absolute paths and parent traversal
        if member_path.is_absolute() or ".." in member_path.parts:
            raise RuntimeError(
                f"Zip Slip 风险: 拒绝解压路径 {member.filename!r}"
            )
        target = (extract_dir / member_path).resolve()
        try:
            target.relative_to(extract_dir)
        except ValueError:
            raise RuntimeError(
                f"Zip Slip 风险: 拒绝解压路径 {member.filename!r}"
            )
    zip_ref.extractall(extract_dir)
