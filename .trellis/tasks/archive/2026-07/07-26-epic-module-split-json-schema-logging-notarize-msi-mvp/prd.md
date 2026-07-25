# Epic: module split, JSON schema, logging, notarize, MSI MVP

## Goal

Deliver the remaining mid-term audit items in shippable slices:

1. Split giant modules without behavior change
2. Optional JSON Schema validation for build configs
3. Route library `print` noise through logging/logutil (keep interactive TUI prints)
4. macOS notarization scaffolding (notarytool) when credentials present
5. Windows MSI MVP via WiX (detect tools, generate minimal .wxs, document gaps)

## Phases

### Phase A — Module split (behavior-preserving)
- Split `config_builder.py` into options constants + builder (facade re-exports for imports)
- Split `tool_manager.py` into assets/constants, download helpers, installers, facade ToolManager
- Split `inno_setup.py` into detection/ISS builder helpers + packager class
- All existing imports keep working (`from unifypy.pyinstaller.config_builder import PyInstallerConfigBuilder` etc.)
- pytest green

### Phase B — JSON Schema
- Add `unifypy/schemas/build.schema.json` (draft-07) covering top-level + platforms + pyinstaller common keys
- Validate after load in ConfigManager (warnings for unknown keys optional; errors for type/required)
- Soft mode: invalid schema → ValueError with path; missing jsonschema package → skip with logutil.warn once
- Add optional dep `jsonschema` in pyproject optional-dependencies `schema` or include in main if light
- tests with valid/invalid fixtures

### Phase C — print → logging
- Expand `logutil` with info/debug/error
- Migrate non-interactive modules: post_processor, tool_manager messages, tool_validator, macos_codesign, info_plist_updater, rollback_plugin (non-CLI listing can stay print or use logutil)
- Keep interactive wizard/menu on print (TUI)
- ProgressManager remains for staged UX

### Phase D — Notarize MVP
- `unifypy/utils/macos_notarize.py`: submit via `xcrun notarytool`, wait, staple
- Config: `platforms.macos.notarize: { apple_id, team_id, password_env, profile }` or env `UNIFYPY_NOTARY_*`
- CLI: `--notarize` flag; only on macOS after dmg/app; skip with clear message if tools/creds missing
- Ad-hoc signed apps cannot notarize — document; require codesign identity in config for real notarize

### Phase E — MSI MVP
- `unifypy/platforms/windows/msi_packager.py` using WiX if `candle`/`light` on PATH
- Register format `msi` in registry
- Minimal WiX XML for installed files from onedir/onefile
- validate_config errors if WiX missing with install hints
- tests: registry supports msi; validate_config without wix

## Acceptance Criteria
- [ ] Three giant files reduced (facades + modules); public APIs stable
- [ ] Schema validates good config; rejects bad types/required
- [ ] Library modules prefer logutil over print (wizard excluded)
- [ ] `--notarize` path exists and fails gracefully without creds
- [ ] `msi` format registered; packager validates WiX presence
- [ ] pytest green; README short notes for schema/notarize/msi

## Out of Scope
- Full WiX UI polish / upgrade codes
- App Store submission
- Complete print migration of interactive CLI

## Decision
Implement all five phases in this task as sequential commits if needed, single PRD.
