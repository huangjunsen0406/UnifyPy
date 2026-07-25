# Pin appimagetool SHA256 and add CI pytest

## Goal

Make default auto-install of appimagetool actually work by pinning asset SHA256 hashes, and add a GitHub Actions CI job that runs pytest on PRs/pushes so regressions are caught before publish.

## Requirements

1. **R1** Fill `APPIMAGETOOL_ASSETS` with real sha256 for x86_64 and aarch64/arm64 (pin continuous or a fixed release; document refresh process in comment).
2. **R2** Add `.github/workflows/ci.yml` (or test job): checkout, setup-python, `pip install -e ".[dev]"`, `pytest tests/ -q` on ubuntu (and optionally macos).
3. **R3** Keep fail-closed if hash missing/mismatch.
4. **R4** Tests still pass; optional test that assets have non-None sha256.

## Acceptance Criteria

- [ ] APPIMAGETOOL_ASSETS[*].sha256 is non-empty hex for x86_64 and aarch64
- [ ] CI workflow runs pytest
- [ ] pytest green locally

## Out of Scope

- Full multi-OS packaging matrix
- Notarization
- Merging dual CacheManager

## Technical Notes

- Current URLs use continuous release (mutable); hashes must be refreshed when continuous updates
- publish.yml remains for release; ci.yml is quality gate
