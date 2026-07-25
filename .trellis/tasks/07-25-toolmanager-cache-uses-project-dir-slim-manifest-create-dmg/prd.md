# ToolManager cache project_dir + slim MANIFEST

## Goal

Stop ToolManager from attaching CacheManager to process cwd; slim sdist/wheel of create-dmg tests/examples noise.

## Requirements

1. **R1** `ToolManager.__init__(..., project_dir: Optional[str] = None)` — CacheManager uses `project_dir or Path.cwd()`.
2. **R2** Call sites that have project context pass it (EnvironmentPlugin / wherever ToolManager() is constructed).
3. **R3** MANIFEST.in: exclude create-dmg tests, examples, doc-project if present; keep create-dmg script + support needed at runtime.
4. **R4** tests + pytest green.

## AC
- [ ] ToolManager accepts project_dir for cache
- [ ] Environment plugin passes project_dir
- [ ] MANIFEST excludes junk create-dmg paths
- [ ] pytest green
