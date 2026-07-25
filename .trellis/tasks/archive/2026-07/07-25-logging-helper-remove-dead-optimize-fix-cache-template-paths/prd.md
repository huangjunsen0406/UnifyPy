# Logging helper, remove dead optimize, fix cache template paths

## Goal

Clean remaining dead/misleading paths: remove no-op optimize at packaging stage, fix template hash paths for installed packages, dedupe dist dir creation, add a small logging helper for library warnings (config validate).

## Requirements

1. **R1** Remove `pb.optimize_pyinstaller_build(...)` call from packaging_plugin parallel path (it runs after exe is already built). Keep method on ParallelBuilder or delete if unused.
2. **R2** CacheManager template paths: resolve package templates via `Path(__file__).resolve().parents[...] / "templates"` or importlib.resources equivalent, not `project_dir/unifypy/templates`.
3. **R3** Remove duplicate `ensure_dir` for dist/installer from ConfigPlugin (Prepare owns dirs); keep Prepare ensure.
4. **R4** Add `unifypy/core/logutil.py` with simple `warn(msg)` that uses logging.getLogger("unifypy") and optionally print if no handlers; use it in ConfigManager validation warnings instead of bare print.
5. **R5** tests for template path resolution helper; pytest green.

## AC
- [ ] packaging parallel path does not call optimize_pyinstaller_build
- [ ] template hash looks under package install location
- [ ] ConfigPlugin does not create dist/installer
- [ ] config warnings go through logger
- [ ] pytest green

## Out of Scope
- Full migration of all print() to logging
- Giant module splits
