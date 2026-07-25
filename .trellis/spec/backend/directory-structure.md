# Directory Structure

> How UnifyPy backend / packaging code is organized.

---

## Overview

UnifyPy is a **CLI packaging orchestrator** (PyInstaller + platform installers). There is no web API layer and no application database. Code lives under the `unifypy/` package; unit tests live under `tests/`.

Architecture sketch:

```text
CLI (__main__ / argument_parser)
  → BuildContext
  → Engine + EventBus
  → Plugins (lifecycle stages)
  → Platform packagers (via PackagerRegistry)
  → Utils (tools, progress, cache, runners)
```

---

## Directory Layout

```text
unifypy/
  __init__.py              # package version (__version__)
  __main__.py              # CLI entry: parse args → Engine.run()
  core/                    # engine, config, events, environment, version
    engine.py              # lifecycle event order
    event_bus.py           # subscribe/emit with priority
    events.py              # event name constants
    plugin.py              # BasePlugin + PluginManager (builtin registration)
    context.py             # BuildContext (args, paths, errors, progress)
    config.py              # load/merge/validate build config
    environment.py         # EnvironmentManager (project_dir-aware)
    platforms.py           # normalize_platform helpers
    formats.py             # resolve requested installer formats
    logutil.py             # library warnings without full logging setup
    macos_permissions.py   # macOS permission / Info.plist mapping
    version.py             # get_version() single source of truth
    validators/            # tool / env validation helpers
  plugins/                 # lifecycle plugins (subscribe to EventBus)
    progress_plugin.py
    dry_run_plugin.py
    config_plugin.py
    environment_plugin.py
    prepare_plugin.py
    pyinstaller_plugin.py
    packaging_plugin.py    # GENERATE_INSTALLERS → packagers
    summary_plugin.py
    cleanup_plugin.py
    rollback_plugin.py
    auto_rollback_plugin.py
    windows_language_plugin.py
    external_plugins_loader.py
  platforms/               # OS-specific packagers
    base.py                # BasePackager (requires real project_dir)
    registry.py            # PackagerRegistry (format → class)
    windows/
      inno_setup.py        # exe / Inno Setup
    macos/
      dmg_packager.py
      post_processor.py
    linux/
      appimage_packager.py
      deb_packager.py
      rpm_packager.py
  pyinstaller/             # PyInstaller config / .spec generation
    config_builder.py
  utils/                   # shared helpers (not platform packagers)
    tool_manager.py        # download/install packaging tools (hash-gated)
    cache_manager.py
    command_runner.py      # SilentRunner; shell=False default
    progress.py            # ProgressManager (user-facing stages)
    file_ops.py
    rollback.py
    parallel_builder.py
    entitlements_generator.py
    info_plist_updater.py
    macos_codesign.py
    icon_converter.py
    ...
  cli/                     # argument parsing + interactive wizard
    argument_parser.py
    interactive/           # wizard, menus, project scanner
  templates/               # Inno Setup ISS templates
    setup.iss.template
    ChineseSimplified.isl.template
  tools/
    create-dmg/            # vendored create-dmg runtime (macOS)

tests/                     # pytest unit tests (no network preferred)
docs/                      # user docs (optional)
scripts/                   # release helpers (e.g. bump_version)
```

---

## Module Responsibilities

| Area | Responsibility |
|------|----------------|
| `core/` | Orchestration primitives: engine, bus, context, config, env, version |
| `plugins/` | Lifecycle stages bound to EventBus events |
| `platforms/` | Concrete installer formats per OS |
| `pyinstaller/` | Build PyInstaller args / spec content |
| `utils/` | Reusable tools used by plugins and packagers |
| `cli/` | User input: flags and interactive config wizard |
| `templates/` | Static templates rendered into build outputs |
| `tools/` | Vendored third-party packaging helpers |
| `tests/` | Unit tests for contracts (paths, safety, merge, CLI) |

There is **no business-domain / DB layer**. Config is JSON (`build.json` etc.), not a database.

---

## Where New Code Goes

### New lifecycle stage / hook

1. Add event constant in `unifypy/core/events.py` if needed (or reuse existing).
2. Implement `BasePlugin` subclass under `unifypy/plugins/`.
3. Register it in `PluginManager.load_builtin_plugins()` in `unifypy/core/plugin.py`.
4. Subscribe handlers in `register(self, bus)` with an explicit `priority`.

```python
# unifypy/plugins/my_plugin.py
class MyPlugin(BasePlugin):
    name = "my"
    priority = 55

    def register(self, bus: EventBus):
        bus.subscribe(PREPARE, self.on_prepare, priority=self.priority)
```

External/third-party plugins are loaded via `external_plugins_loader.py` (do not hardcode every external plugin into `PluginManager` unless making it builtin).

### New installer format / packager

1. Subclass `BasePackager` under `unifypy/platforms/<os>/`.
2. Always accept and pass real `project_dir` into `BasePackager` / `EnvironmentManager` (never hardcode `"."` as project root).
3. Register in `PackagerRegistry._load_default_packagers()` in `unifypy/platforms/registry.py` (or call `register_packager` dynamically).

```text
("linux", "flatpak", "unifypy.platforms.linux.flatpak_packager", "FlatpakPackager")
```

4. Wire format resolution / config keys as needed in `core/formats.py` and packaging plugin usage.
5. Add unit tests under `tests/`.

### New CLI flag

- Define in `unifypy/cli/argument_parser.py`.
- Consume via `BuildContext` / `ctx.args` in the relevant plugin.
- Document user-visible behavior in README when it changes defaults.

### Shared helper (not a stage, not a packager)

- Prefer `unifypy/utils/`.
- Library warnings without ProgressManager: `unifypy.core.logutil`.

### Version string

- Single source: `unifypy.core.version.get_version()` / `unifypy.__version__`.
- Release bumps update `pyproject.toml` and `unifypy/__init__.py` via `scripts` helpers — do not scatter version literals.

---

## Naming Conventions

| Kind | Convention | Example |
|------|------------|---------|
| Modules / files | `snake_case.py` | `tool_manager.py` |
| Classes | `PascalCase` | `PackagingPlugin`, `DEBPackager` |
| Plugins | `*_plugin.py`, class `*Plugin` | `config_plugin.py` → `ConfigPlugin` |
| Packagers | `*_packager.py` or tool-named module | `dmg_packager.py`, `inno_setup.py` |
| Tests | `tests/test_<area>.py` | `test_download_sha256.py` |
| Event constants | `UPPER_SNAKE` in `events.py` | `GENERATE_INSTALLERS` |

---

## Examples (good references)

| Concern | Look at |
|---------|---------|
| CLI → engine bootstrap | `unifypy/__main__.py` |
| Plugin registration order | `unifypy/core/plugin.py` |
| Lifecycle emit order | `unifypy/core/engine.py` |
| Packager registration | `unifypy/platforms/registry.py` |
| Packager base + `project_dir` | `unifypy/platforms/base.py` |
| Installer stage orchestration | `unifypy/plugins/packaging_plugin.py` |
| Tool download / hash gate | `unifypy/utils/tool_manager.py` |
| Progress UX | `unifypy/utils/progress.py` |

---

## Common Mistakes

### Mistake: New packager under `utils/`

**Symptom**: Format logic mixed with generic helpers; hard to discover.  
**Fix**: Put packagers under `platforms/<os>/` and register in `PackagerRegistry`.

### Mistake: New plugin not registered in `PluginManager`

**Symptom**: Plugin class exists but never runs.  
**Fix**: Add to `load_builtin_plugins()` (or load via external plugin path).

### Mistake: `EnvironmentManager(".")` / missing `project_dir`

**Symptom**: Paths resolve against cwd instead of the user's project.  
**Fix**: Pass the real project directory into packagers and env managers.

### Mistake: Assuming a database or service layer

**Symptom**: Inventing ORM models / repositories for a packaging CLI.  
**Fix**: Persist only via config files, caches, and build outputs — no app DB.
