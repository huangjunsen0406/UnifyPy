# Error Handling

> How errors are handled in UnifyPy.

---

## Overview

Build failures are collected on `BuildContext.errors` via the EventBus and surfaced through `ProgressManager` / exit code `1`. Prefer raising clear `RuntimeError` / `FileNotFoundError` / `ValueError` at stage boundaries rather than swallowing exceptions.

---

## Error Types

| Situation | Typical type | User-facing |
|-----------|--------------|-------------|
| Missing config / entry | `FileNotFoundError`, `ValueError` | progress / raise |
| Missing packaging tools | `RuntimeError` after install guidance print | print block + raise |
| Download hash mismatch | `RuntimeError` | raise; file deleted |
| Auto-install disabled | `RuntimeError` | instructions + mention `--allow-auto-install` |
| PyInstaller / packager failure | `RuntimeError` | stage error |
| Unsupported arch | `ValueError` / `RuntimeError` | environment check |

---

## Error Handling Patterns

### Tool validation

```text
missing tools
  → if allow_auto_install: try auto_install (except Inno silent install never)
  → still missing: print install instructions → RuntimeError
```

### Download verification

```text
stream download → sha256
  → mismatch or missing expected hash for pinned tool: unlink → RuntimeError
```

### Quiet mode

`--quiet` must not suppress error panels. Only reduce progress UI / info chatter.

### EventBus

Handlers that fail append to `ctx.errors`; Engine returns non-zero. Do not rely on silent `except Exception: pass` for user-visible failures.

---

## CLI Contracts (related errors)

| Flag | Role |
|------|------|
| `--version` | Tool version; exits |
| `--app-version` | Application version for the build (`dest=version`) |
| `--allow-auto-install` | Opt-in automatic tool install (still hash-gated) |
| `--development` | Opt-in macOS development entitlements |

---

## Common Mistakes

### Mistake: Default development entitlements

**Symptom**: Production builds ship debug-oriented entitlements.  
**Fix**: Default production; require `--development`.

### Mistake: Config relative to cwd only

**Symptom**: `unifypy /path/to/proj --config build.json` fails when cwd differs.  
**Fix**: Resolve relative config against `project_dir`.

### Mistake: Auto-install without hash pin

**Symptom**: Supply-chain risk or refuse-to-run with empty `sha256`.  
**Fix**: Pin URL + SHA256 before enabling download path.
