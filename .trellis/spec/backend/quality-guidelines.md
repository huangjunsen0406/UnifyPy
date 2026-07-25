# Quality Guidelines

> Code quality standards for UnifyPy (packaging orchestrator).

---

## Overview

UnifyPy is a CLI packaging tool (PyInstaller + platform installers). Prefer fail-closed security defaults, host-platform builds only, and unit tests for merge/path/safety contracts.

---

## Forbidden Patterns

### Don't: Silent tool install / sudo without explicit opt-in

```python
# Bad — auto install with no user flag
tool_manager.auto_install_tool("appimagetool")

# Bad — sudo without allow_auto_install
subprocess.run(["sudo", "apt-get", "install", "-y", "dpkg-dev"])
```

**Why**: CI and shared machines must not escalate privileges or execute downloaded binaries by default.

**Instead**: Gate on `allow_auto_install` (CLI `--allow-auto-install`). Inno Setup must never silent-download-and-execute; print manual install instructions only.

### Don't: Download binaries without SHA256 when auto-installing

```python
# Bad
_download_file(url, target)  # then chmod +x and run
```

**Instead**: Pass `expected_sha256=...`; on mismatch delete file and raise. Refuse if hash is missing/None for appimagetool assets.

### Don't: `shell=True` by default

`SilentRunner.run_command` defaults to `shell=False`. Prefer argv lists.

### Don't: Hardcode package version strings in multiple places

Use `unifypy.core.version.get_version()` / `unifypy.__version__`. `bump_version.py` must update `pyproject.toml` and `unifypy/__init__.py`.

### Don't: `EnvironmentManager(".")` for packagers

Always pass the user's `project_dir` into `BasePackager` / `EnvironmentManager`.

### Don't: Assume cross-OS or cross-arch builds from config alone

Config may describe all platforms; a single run only builds for the **host** OS/arch.

---

## Required Patterns

### Config path resolution

Relative `--config` paths resolve against `project_dir`, not only process cwd.

### macOS entitlements default

Default is **production** entitlements. Development entitlements only when `--development` (or debug) is set.

### macOS output verification

Non-onefile macOS builds verify `dist/{name}.app` (and display_name variant if present), not `dist/{name}/{name}` alone.

### RPM build env

When setting `env` for `rpmbuild` (e.g. `HOME`), pass `env=env` into `run_command`.

### Zip extraction

Never raw `extractall` of untrusted zips without validating members stay under the extract root (Zip Slip).

---

## Testing Requirements

- New safety/correctness contracts need unit tests under `tests/` (pytest).
- Prefer no network in tests; use fixtures and mocks for downloads.
- Run: `python -m pytest tests/ -q`

Minimum coverage themes:

- shell default False
- config path vs project_dir
- version alignment
- macOS verify paths
- download sha256 failure
- zip slip rejection
- entitlements development flag
- rpm env passed to runner

---

## Code Review Checklist

- [ ] Auto-install / download paths fail closed without `--allow-auto-install` and without hashes
- [ ] No new `shell=True` defaults
- [ ] Packagers receive real `project_dir`
- [ ] CLI: tool `--version` vs app `--app-version` not confused
- [ ] Tests updated for behavior changes
- [ ] README notes user-visible behavior changes
