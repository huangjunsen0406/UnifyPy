# Database Guidelines

> Database patterns and conventions for this project.

---

## Status: N/A

**UnifyPy has no application database.**

This project is a CLI packaging orchestrator (PyInstaller + platform installers). Runtime state is:

- User / project **JSON config** (e.g. `build.json`)
- Filesystem **build outputs** (`dist/`, caches under project / tool cache)
- In-memory **`BuildContext`** for a single run

There is no ORM, no SQL, no migrations, and no multi-tenant data store.

---

## Rules

1. **Do not introduce** an application database, ORM, or migration framework without an explicit product decision documented outside this bootstrap.
2. **Do not invent** repository/DAO layers “for consistency” with web backends — they do not match this codebase.
3. Persist packaging state with **files and caches** already used by the project (`utils/cache_manager.py`, config on disk, tool cache), not a DB.

---

## If a future product need appears

Before adding any DB:

1. Record the decision (problem, alternatives, chosen store).
2. Replace this file with real guidelines (ORM, migrations, naming, transactions).
3. Update `.trellis/spec/backend/index.md` status from **N/A** to **Filled**.

Until then, treat this document as intentionally empty of DB patterns.
