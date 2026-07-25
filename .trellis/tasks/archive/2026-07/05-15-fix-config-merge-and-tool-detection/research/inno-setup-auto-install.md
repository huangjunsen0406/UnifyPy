# Research: Inno Setup Silent/Automatic Installation

- **Query**: Can Inno Setup be installed silently/automatically from the command line, without a GUI wizard?
- **Scope**: mixed (internal codebase + external docs)
- **Date**: 2026-05-15

## Findings

### 1. Silent Install Flags (Official)

Inno Setup's own installer is itself built with Inno Setup, so it supports all standard Inno Setup command-line parameters. The key flags are:

| Flag | Behavior |
|------|----------|
| `/VERYSILENT` | No UI at all -- no wizard, no progress window. Completely silent. |
| `/SILENT` | No wizard, but shows installation progress window. |
| `/SP-` | Suppresses "This will install... Do you wish to continue?" prompt. |
| `/SUPPRESSMSGBOXES` | Suppresses all message boxes (combine with `/SILENT` or `/VERYSILENT`). |
| `/NORESTART` | Prevents system restart after installation. |
| `/NOCANCEL` | Disables cancel button during installation. |
| `/DIR="path"` | Override default install directory (e.g., `/DIR="C:\InnoSetup"`). |
| `/CURRENTUSER` | Install for current user only (no admin needed, if supported by installer). |
| `/ALLUSERS` | Install for all users (requires admin). |
| `/LOG="filename"` | Write installation log to specified file. |
| `/TASKS="list"` | Select specific tasks (e.g., `/TASKS="!desktopicon"`). |

**Full silent install command:**
```cmd
innosetup-6.7.1.exe /VERYSILENT /SP- /SUPPRESSMSGBOXES /NORESTART /DIR="C:\Program Files (x86)\Inno Setup 6"
```

**Source**: https://jrsoftware.org/ishelp/topic_setupcmdline.htm

### 2. Portable/Standalone Version

There is **no official portable/standalone ZIP version** of Inno Setup. The only official distribution is the `.exe` installer.

However, **Scoop** effectively creates a portable installation by extracting the Inno Setup installer contents. Scoop's manifest uses the `"innosetup": true` flag, which tells Scoop to use its built-in Inno Setup unpacker (innounp or similar) to extract files without running the installer GUI. This results in a portable-like installation in Scoop's apps directory with `iscc.exe` directly usable from PATH.

The third-party tool `innounp` (Inno Setup Unpacker) can also extract Inno Setup installers without running them:
```cmd
innounp -x innosetup-6.7.1.exe
```

### 3. Package Manager Installation

#### Scoop (Recommended for CI/portable use)
```powershell
scoop bucket add extras
scoop install inno-setup
```
- **Package**: `extras/inno-setup`
- **Current version**: 6.7.1
- **Installs to**: `%USERPROFILE%\scoop\apps\inno-setup\current\`
- **Binary**: `iscc.exe` added to PATH automatically
- **No admin required**
- Manifest URL: https://raw.githubusercontent.com/ScoopInstaller/Extras/master/bucket/inno-setup.json

#### Chocolatey
```powershell
choco install innosetup -y
```
- **Package**: `innosetup`
- Installs to standard `Program Files` location
- Requires admin (elevated prompt)
- Package page: https://community.chocolatey.org/packages/innosetup

#### Winget
```powershell
winget install --id JordanRussell.InnoSetup -e --silent
```
- **Package ID**: `JordanRussell.InnoSetup`
- Uses the official installer with silent flags internally
- Available in winget-pkgs repository

### 4. Download URLs

| Version | URL |
|---------|-----|
| **6.7.1 (stable, latest)** | `https://github.com/jrsoftware/issrc/releases/download/is-6_7_1/innosetup-6.7.1.exe` |
| 6.7.1 signature | `https://github.com/jrsoftware/issrc/releases/download/is-6_7_1/innosetup-6.7.1.exe.issig` |
| 7.0.0-preview-3 (x64) | `https://github.com/jrsoftware/issrc/releases/download/is-7_0_0_2/innosetup-7.0.0-preview-3-x64.exe` |
| 7.0.0-preview-3 (x86) | `https://github.com/jrsoftware/issrc/releases/download/is-7_0_0_2/innosetup-7.0.0-preview-3-x86.exe` |
| **Download page** | `https://jrsoftware.org/isdl.php` |
| **Direct download (stable)** | `https://jrsoftware.org/download.php/is.exe` (redirects to latest stable) |

**URL pattern for constructing download links:**
```
https://github.com/jrsoftware/issrc/releases/download/is-{version_underscored}/innosetup-{version_dotted}.exe
```
Example: version `6.7.1` -> tag `is-6_7_1` -> `innosetup-6.7.1.exe`

### 5. CI/CD Examples

#### GitHub Actions -- Direct silent install
```yaml
- name: Install Inno Setup
  run: |
    Invoke-WebRequest -Uri "https://jrsoftware.org/download.php/is.exe" -OutFile "$env:TEMP\innosetup.exe"
    Start-Process -FilePath "$env:TEMP\innosetup.exe" -ArgumentList "/VERYSILENT /SP- /SUPPRESSMSGBOXES /NORESTART /DIR=`"C:\Program Files (x86)\Inno Setup 6`"" -Wait -NoNewWindow
    echo "C:\Program Files (x86)\Inno Setup 6" | Out-File -Append -Encoding utf8 $env:GITHUB_PATH
  shell: pwsh
```

#### GitHub Actions -- Using Chocolatey
```yaml
- name: Install Inno Setup
  run: choco install innosetup -y --no-progress
  shell: cmd
```

#### GitHub Actions -- Using Scoop (no admin)
```yaml
- name: Install Inno Setup via Scoop
  run: |
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
    Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression
    scoop bucket add extras
    scoop install inno-setup
  shell: pwsh
```

#### GitHub Actions -- Using a dedicated action
There are community actions like `Minionguyjpro/Inno-Setup-Action` that wrap the installation:
```yaml
- name: Create Installer
  uses: Minionguyjpro/Inno-Setup-Action@v1.2.4
  with:
    path: installer.iss
```

**Note**: `windows-latest` GitHub Actions runners do NOT have Inno Setup pre-installed. It must be installed as a step.

### Internal Codebase Context

#### Files that handle Inno Setup detection/installation

| File Path | Description |
|---|---|
| `unifypy/platforms/windows/inno_setup.py` | Main InnoSetupPackager class -- `_find_inno_setup_compiler()` (line 173), `_auto_detect_inno_setup()` (line 204), `_check_registry_for_inno_setup()` (line 235) |
| `unifypy/utils/tool_manager.py` | ToolManager class -- `_detect_existing_inno_setup()` (line 421), `_check_registry_for_inno_setup()` (line 455), `ensure_tool()` which currently only prints manual instructions (line 390-419) |
| `unifypy/core/environment.py` | Environment detection -- sets `installer_type: "inno_setup"` (line 438) |
| `unifypy/core/config.py` | Config handling -- `inno_setup_path` config key (line 362) |
| `unifypy/core/validators/tool_validator.py` | Validation for `inno_setup` format type (line 40, 126) |

#### Current behavior (tool_manager.py lines 390-419)
The `ensure_tool()` method currently does NOT auto-install. It:
1. Prints a message telling the user to manually download from `https://jrsoftware.org/download.php/is.exe`
2. Tries `_detect_existing_inno_setup()` to find an already-installed copy
3. Raises `RuntimeError` if not found

The download URL is already configured as `https://jrsoftware.org/download.php/is.exe` in `self.github_tools["inno-setup"]["download_url"]` (line 71).

## Caveats / Not Found

- **No official portable ZIP**: Inno Setup only distributes `.exe` installers. A portable setup requires Scoop or manual extraction with `innounp`.
- **Chocolatey exact version**: Could not confirm the exact latest version on Chocolatey due to API access issues, but the package `innosetup` is well-maintained.
- **Winget exact manifest**: GitHub API rate limits prevented confirming the exact winget manifest structure, but the package `JordanRussell.InnoSetup` is confirmed available.
- **Inno Setup 7 is in preview** (7.0.0-preview-3). It introduces separate x64 and x86 installers, unlike v6 which is a single installer.
- **Admin rights**: The `/VERYSILENT` direct install typically requires admin rights on Windows unless `/CURRENTUSER` is used. Scoop avoids this entirely by extracting to user-space.
