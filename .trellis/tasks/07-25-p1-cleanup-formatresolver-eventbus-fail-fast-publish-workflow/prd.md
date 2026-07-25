# P1 cleanup: FormatResolver, EventBus fail-fast, publish workflow

## Goal

Reduce duplication and footguns from the audit P1 list: single format resolution helper, EventBus fail-fast within an event, retire/rename dead parallel CacheManager confusion, replace deprecated create-release action.

## Requirements

1. **R1 FormatResolver** — one module (e.g. `unifypy/core/formats.py`) used by EnvironmentPlugin and PackagingPlugin for requested formats (CLI `--format` > `platforms.*.formats` > key scan > defaults).
2. **R2 EventBus fail-fast** — on handler exception, record error and **stop** remaining handlers for that event (default). Optional collect-all later not required.
3. **R3 parallel_builder.CacheManager** — rename to `DownloadCache` or remove if unused; avoid two classes named CacheManager.
4. **R4 publish.yml** — replace `actions/create-release@v1` with `softprops/action-gh-release@v2` (or `gh release create`).
5. **R5 tests** — FormatResolver unit tests; EventBus fail-fast unit test.

## Acceptance Criteria

- [ ] No duplicate format-list methods in env/packaging plugins
- [ ] Second subscriber not called if first raises
- [ ] Only one CacheManager name in utils (project cache); parallel one renamed or gone
- [ ] publish workflow has no create-release@v1
- [ ] pytest green

## Out of Scope

- Full platform name mac/macos unification (larger)
- Giant module splits
- Notarization

## Technical Notes

- packaging_plugin._get_requested_formats vs environment_plugin._get_formats_from_config
- event_bus.py emit loop
- parallel_builder.py class CacheManager ~274
