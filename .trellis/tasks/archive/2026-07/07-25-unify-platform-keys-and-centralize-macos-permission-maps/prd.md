# Unify platform keys and centralize macOS permission maps

## Goal

Eliminate dual platform naming (`mac`/`win` vs `macos`/`windows`) in EnvironmentManager and centralize macOS config→Info.plist permission key mapping used in 4+ places.

## Requirements

### R1 EnvironmentManager platform keys
- Use `normalize_platform()` so `current_platform` is `windows` | `macos` | `linux`.
- Keep **internal_key** short forms for filenames: map windows→`win`, macos→`mac`, linux→`linux` when building keys like `mac-arm64`, `win-x64`.
- Update all branches that compare `== "mac"` / `== "win"` to `macos` / `windows`.
- Prefer `normalize_arch()` from platforms.py where it replaces local arch normalize (optional if risky; at least platform string unify).

### R2 Permission map single source
- Add `unifypy/core/macos_permissions.py` (or `platforms/macos/permissions.py`) with:
  - `CONFIG_TO_PLIST_MAPPING` — union of the most complete map (from entitlements_generator + info_plist keys)
- Wire consumers to import the shared map:
  - `entitlements_generator.CONFIG_TO_PLIST_MAPPING`
  - `info_plist_updater.PERMISSION_MAPPING`
  - `config_builder` permission dicts
  - `post_processor` verify permission_keys
- Do **not** merge PRIVACY_TO_ENTITLEMENTS_MAPPING into the same dict (different purpose); leave that on EntitlementsGenerator or import only config→plist.

### R3 Tests
- `test_environment_platform_keys.py` — EnvironmentManager.current_platform is windows/macos/linux; internal_key still starts with win-/mac-/linux-
- `test_macos_permissions_map.py` — shared map has core keys (microphone, camera, speech)

### R4 pytest green

## Out of Scope
- Full entitlements privacy→entitlement map refactor beyond sharing config→plist
- Bootstrap guidelines content dump

## AC
- [ ] No EnvironmentManager returning "mac"/"win" as current_platform
- [ ] Shared CONFIG_TO_PLIST used by at least info_plist + entitlements + config_builder + post_processor
- [ ] internal_key still uses short mac/win prefixes for compatibility
- [ ] pytest green
