# Fix rebuild UX: pyinstaller -y, summary paths, error hints

## Goal

Fix the rebuild/summary UX issues found during py-xiaozhi real packaging: non-empty dist fails without `--clean`, success summary shows wrong 128B path, and error hints mislead users.

## Requirements

1. **R1** Always pass PyInstaller overwrite flag when running via UnifyPy (`-y` / noconfirm) so rebuilds don't require empty dist when using cached `.spec`.
2. **R2** `SummaryPlugin` on macOS reports the real `.app` path (prefer `display_name.app` then `name.app`), not a tiny `dist/name` directory.
3. **R3** When PyInstaller fails with non-empty output directory, error message suggests `--clean` / overwrite, not "upgrade PyInstaller".
4. **R4** Unit tests for summary path selection and pyinstaller command includes `-y`.

## Acceptance Criteria

- [ ] Second build without `--clean` does not fail solely due to non-empty COLLECT dir (when using UnifyPy command path)
- [ ] Success table shows `dist/<display_name>.app` or `dist/<name>.app` on macOS when present
- [ ] Non-empty-dir failure text mentions `--clean` if still reachable
- [ ] pytest green

## Out of Scope

- appimagetool hash pinning
- Full CI matrix
- Archive other old tasks

## Technical Notes

- `unifypy/plugins/pyinstaller_plugin.py` command currently `["pyinstaller", str(spec_file)]`
- `unifypy/plugins/summary_plugin.py` onedir uses `dist_dir / app_name`
- User verified success with `--clean --development`
