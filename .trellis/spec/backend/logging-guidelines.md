# Logging Guidelines

> How logging is done in this project.

---

## Overview

UnifyPy is primarily a CLI packaging tool. User-facing build progress uses `ProgressManager`. Library-level warnings (e.g. config validation) use `unifypy.core.logutil`.

---

## Library Warnings (`logutil`)

Use `unifypy.core.logutil` for library warnings that should not depend on a fully configured CLI progress UI:

```python
from unifypy.core import logutil

logutil.warn("图标文件不存在: icon.png")
```

Behavior:

- If the `unifypy` logger or root logger has handlers → `logger.warning(msg)`
- Otherwise → `print(f"警告: {msg}")` so CLI runs without logging config still show the message

Do **not** double-prefix with `警告:` when calling `logutil.warn`; the helper adds it on the print fallback.

---

## User-Facing Build Stages

Use `ProgressManager` (via `ctx.progress`) for build stages, success/failure of packaging steps, and interactive CLI feedback:

- `start_stage` / `complete_stage` / `update_stage`
- `info` / `warning` / `on_error`

---

## Log Levels

| Level | Use |
|-------|-----|
| warning | Config validation issues, missing optional files, partial failures |
| info | Stage progress (via ProgressManager), non-error status |
| error | Build failures (typically via ProgressManager.on_error) |

---

## What NOT to Log

- Secrets, credentials, signing passwords
- Full user home paths when avoidable in shared logs
- PII

---

## Out of Scope (current)

Full migration of all `print()` calls to logging is not required; prefer `logutil` for new library warnings and ProgressManager for build UX.
