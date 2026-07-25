# DEB package name validation, registry import errors, Info.plist post-update

## Goal

1. Validate Debian package names before building.
2. Log (not swallow silently) ImportError when loading packagers; register available ones individually.
3. Call `_update_info_plist` in macOS post-process before re-signing.

## Requirements

### R1 DEB package name
- Debian package name: `^[a-z0-9][a-z0-9+.-]*$`
- Validate in `DEBPackager.validate_config` for `package` or fallback name.
- Unit test for valid/invalid names (pure function if extracted).

### R2 Registry load
- Load each packager import separately so one failure doesn't drop all.
- On ImportError, use `logutil.warn` with module name; continue registering others.

### R3 Info.plist update in process_built_app
- After localized display name (or before sign), call `_update_info_plist(app_path, config)` so permission descriptions from config are applied when missing from BUNDLE.
- Then sign as now.
- If update fails, warn but still try sign (or return False on hard fail — prefer warn + continue).

### R4 tests + pytest green

## AC
- [ ] Invalid deb package names produce validation errors
- [ ] Registry registers remaining packagers if one import fails
- [ ] process_built_app invokes _update_info_plist
- [ ] pytest green
