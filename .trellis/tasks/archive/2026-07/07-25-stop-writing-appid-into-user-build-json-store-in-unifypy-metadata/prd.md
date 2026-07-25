# Stop writing AppID into user build.json; store in .unifypy metadata

## Goal

Inno Setup AppID should persist in `.unifypy/metadata.json` only. Do not rewrite the user's `build.json` during builds (CI-friendly, no dirty tree).

## Requirements

1. **R1** `get_or_generate_app_id` continues to prefer config `platforms.windows.inno_setup.app_id` if user set it; else metadata; else generate and save metadata only.
2. **R2** Remove or no-op `update_build_config_with_app_id` write path from build flow in `inno_setup.py` — do not call it to mutate build.json. Optionally deprecate the method with a docstring "no longer used during builds".
3. **R3** When AppID is generated, `progress.info` that it was saved to `.unifypy/metadata.json` (not build.json).
4. **R4** tests: get_or_generate with empty config writes metadata only; does not require writing build.json.
5. pytest green.

## AC
- [ ] Building with windows/inno does not rewrite build.json AppID
- [ ] Generated AppID stored in project `.unifypy/metadata.json`
- [ ] Explicit config app_id still preferred
- [ ] pytest green

## Out of Scope
- Migrating existing build.json app_ids out of configs
