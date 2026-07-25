# Fix hardcoded absolute path in PyInstaller spec generation

## Problem
`pyinstaller_plugin.py:51` uses `.resolve()` which expands `entry` to a machine-specific absolute path (e.g. `/Users/junsen/Desktop/workspace/py-xiaozhi/main.py`). This path gets baked into the generated `.spec` file. When CI runs on a different machine, the path doesn't exist and PyInstaller fails.

## Root Cause
```python
entry = str((ctx.project_dir / ctx.config.get("entry")).resolve())
```
`.resolve()` produces an absolute path tied to the build machine. Since PyInstaller is already executed with `cwd=ctx.project_dir` (line 114), a relative path would work correctly.

## Fix
1. **`pyinstaller_plugin.py:51`**: Use the config entry value directly (relative path) instead of resolving to absolute.
2. **`config_builder.py` path validation**: `_format_tuples_list` and `_validate_path_item` use bare `os.path.exists()` which won't find relative paths unless cwd matches. These need to resolve against project_dir for validation, but still write relative paths into the spec.

## Scope
- `unifypy/plugins/pyinstaller_plugin.py` — line 51
- `unifypy/pyinstaller/config_builder.py` — `_format_tuples_list`, `_validate_path_item`, `build_spec_file_content`
- Bump version and release
