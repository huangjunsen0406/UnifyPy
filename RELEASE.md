# 发布指引（UnifyPy 2.0）

本文档说明如何将本项目发布到 PyPI，以及相应的版本管理与校验流程。默认使用 GitHub Actions 自动发布工作流（.github/workflows/publish.yml）。

## 先决条件
- Python 3.8+
- 仓库已启用 GitHub Actions
- 在仓库 Settings → Secrets and variables → Actions 配置 Secret：
  - `PYPI_API_TOKEN`：PyPI 的 API Token（首次发布建议使用 Entire account token；项目创建后可改为 Project-scoped token）
  - （可选）`TEST_PYPI_API_TOKEN`：TestPyPI 的 API Token（手动测试发布时使用）

## 版本规范
- 采用语义化版本（SemVer）：`MAJOR.MINOR.PATCH`，例如 `2.0.1`
- 版本号需唯一（PyPI 禁止重复版本）
- 本仓库提供版本号修改脚本：
  - `python scripts/release/bump_version.py 2.0.1`

## 发布方式 A：打 tag 自动发布（推荐）
1) 选择新版本号（示例：`2.0.1`）
2) 本地更新版本并提交
```bash
python scripts/release/bump_version.py 2.0.1
git add pyproject.toml
git commit -m "chore(release): bump version to 2.0.1"
```
3) 创建并推送 tag
```bash
git tag v2.0.1
git push origin HEAD --tags
```
4) 打开 GitHub → Actions → Publish，观察工作流执行
   - 工作流包含版本校验脚本：`scripts/release/check_tag.py`（确保 tag 与版本一致）
   - 构建 sdist+wheel，twine check 后，用 `PYPI_API_TOKEN` 上传至 PyPI

## 发布方式 B：Actions 手动触发（无需本地 bump）
1) 打开 GitHub → Actions → Publish → Run workflow
2) 输入项：
   - `target`: 选择 `pypi`
   - `version`: 例如 `2.0.1`（不填则使用当前 pyproject.toml 的版本）
3) 点击 Run workflow
   - 若填写了 `version`，工作流会先自动 bump 版本，再构建并上传

## 可选：本地构建与校验（发布前自检）
```bash
pip install build twine
python -m build
python -m twine check dist/*
# 如需测试上传到 TestPyPI（本地）
# python -m twine upload --repository testpypi dist/*
```

## 发布后验证
```bash
pip install -U unifypy
unifypy --help
```

## 故障排查
- 版本重复：确保 `pyproject.toml` 的 `version` 从未在 PyPI 使用过
- 401/403：检查 `PYPI_API_TOKEN` 是否有效且存放在仓库 Secrets；twine 使用 `__token__` + 你的 Token
- 资源缺失：`MANIFEST.in` 已包含 `unifypy/templates/*` 与 `unifypy/tools/*`（含 create-dmg 资源与哨兵文件），若安装后缺资源，重新构建并确认 `twine check` 通过
- 工作流未触发：
  - 确认 publish.yml 已在默认分支
  - 打 tag 需在工作流文件存在之后创建；旧 tag 不会触发新工作流
  - Settings → Actions → General：启用 Actions 且允许该工作流运行
  - tag 需匹配模式 `v*.*.*`（如 `v2.0.1`）

## 重要说明
- 入口：`unifypy` 命令（对应 `unifypy.__main__:main`）
- 代码路径：统一使用 `unifypy/*`；仅支持 64 位架构（x64/arm64）
- 格式范围：Windows EXE、macOS DMG、Linux DEB/RPM
- Linux ARM64：需在 ARM64 环境或 ARM64 容器中构建（不能仅修改配置伪装架构）

## 版本管理小技巧
- 建议在合并发布分支前本地执行一次：
```bash
pip install -e .
unifypy --help
```
- 若需要预先在 TestPyPI 验证：
  - 在仓库 Secrets 添加 `TEST_PYPI_API_TOKEN`
  - 手动触发 Publish，`target` 选择 `testpypi`，可选填写 `version`

## 变更记录（可选）
- 维护 `CHANGELOG.md` 或 GitHub Releases 的 Release Notes，记录每次版本改动点
