#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Inno Setup ISS script generation helpers (template + fallback)."""

import hashlib
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional


def process_iss_template(
    template_path: Path,
    app_config: Dict[str, Any],
    format_config: Dict[str, Any],
    source_path: Path,
    output_path: Path,
    chinese_isl_path: Optional[str] = None,
) -> str:
    """Process an ISS template file with placeholders and condition blocks.

    Args:
        template_path: Path to setup.iss.template
        app_config: Top-level app config (name, version, publisher, display_name)
        format_config: inno_setup section config
        source_path: PyInstaller output path
        output_path: Desired installer output path
        chinese_isl_path: Path for ChineseSimplified.isl if Chinese support enabled

    Returns:
        str: Rendered ISS script content
    """
    app_name = app_config.get("name", "MyApp")
    app_version = app_config.get("version", "1.0.0")
    publisher = app_config.get("publisher", "Unknown Publisher")
    app_url = format_config.get("app_url", "")
    display_name = app_config.get("display_name", app_name)

    app_id = format_config.get("app_id", None)
    if not app_id:
        name_hash = hashlib.md5(app_name.encode()).hexdigest()[:8].upper()
        app_id = f"C4D8B3F2-1234-5678-9ABC-{name_hash}12345678"
    elif app_id.startswith("{") and app_id.endswith("}"):
        app_id = app_id.strip("{}")

    source_path_str = str(source_path).replace("/", "\\")

    if source_path.is_file():
        source_files = (
            f'Source: "{source_path_str}"; DestDir: "{{app}}"; Flags: ignoreversion'
        )
        exe_name = source_path.name
    else:
        source_files = (
            f'Source: "{source_path_str}\\*"; DestDir: "{{app}}"; '
            f"Flags: ignoreversion recursesubdirs createallsubdirs"
        )
        exe_name = f"{app_name}.exe"

    with open(template_path, "r", encoding="utf-8") as f:
        template_content = f.read()

    replacements = {
        "{{APP_ID}}": app_id,
        "{{APP_NAME}}": app_name,
        "{{APP_VERSION}}": app_version,
        "{{APP_DISPLAY_NAME}}": display_name,
        "{{APP_PUBLISHER}}": publisher,
        "{{APP_URL}}": app_url,
        "{{OUTPUT_DIR}}": str(output_path.parent).replace("/", "\\"),
        "{{OUTPUT_FILENAME}}": output_path.stem,
        "{{SOURCE_FILES}}": source_files,
        "{{EXE_NAME}}": exe_name,
    }

    conditions = {
        "{{#APP_URL}}": bool(app_url),
        "{{#LICENSE_FILE}}": bool(format_config.get("license_file"))
        and os.path.exists(format_config.get("license_file", "")),
        "{{#SETUP_ICON}}": bool(format_config.get("setup_icon"))
        and os.path.exists(format_config.get("setup_icon", "")),
        "{{#CREATE_DESKTOP_ICON}}": format_config.get("create_desktop_icon", True),
        "{{#CREATE_START_MENU_ICON}}": format_config.get(
            "create_start_menu_icon", False
        ),
        "{{#RUN_AFTER_INSTALL}}": format_config.get("run_after_install", False),
        "{{#CHINESE_SUPPORT}}": "chinesesimplified"
        in format_config.get("languages", [])
        or "chinese" in format_config.get("languages", []),
    }

    result = template_content
    for condition, should_include in conditions.items():
        start_tag = condition
        end_tag = condition.replace("#", "/")

        start_idx = result.find(start_tag)
        while start_idx != -1:
            end_idx = result.find(end_tag, start_idx)
            if end_idx == -1:
                break

            if should_include:
                content = result[start_idx + len(start_tag) : end_idx]
                result = result[:start_idx] + content + result[end_idx + len(end_tag) :]
                start_idx = result.find(start_tag, start_idx + len(content))
            else:
                result = result[:start_idx] + result[end_idx + len(end_tag) :]
                start_idx = result.find(start_tag, start_idx)

    if conditions["{{#LICENSE_FILE}}"]:
        result = result.replace(
            "{{LICENSE_FILE}}",
            str(Path(format_config.get("license_file")).resolve()).replace("/", "\\"),
        )

    if conditions["{{#SETUP_ICON}}"]:
        result = result.replace(
            "{{SETUP_ICON}}",
            str(Path(format_config.get("setup_icon")).resolve()).replace("/", "\\"),
        )

    if conditions["{{#CHINESE_SUPPORT}}"]:
        isl = chinese_isl_path or "compiler:Languages\\ChineseSimplified.isl"
        result = result.replace("{{CHINESE_ISL_PATH}}", isl)

    result = result.replace("{{LICENSE_FILE}}", "")
    result = result.replace("{{SETUP_ICON}}", "")
    result = result.replace("{{CHINESE_ISL_PATH}}", "")

    for placeholder, value in replacements.items():
        result = result.replace(placeholder, value)

    result = re.sub(r"\{\{[#/][^}]+\}\}", "", result)
    result = re.sub(r"\n\s*\n\s*\n", "\n\n", result)

    return result.strip()


def generate_iss_script(
    app_config: Dict[str, Any],
    format_config: Dict[str, Any],
    source_path: Path,
    output_path: Path,
    project_chinese_file: Optional[str] = None,
) -> str:
    """Built-in ISS script generation (fallback when no template is found).

    Args:
        app_config: Top-level app config
        format_config: inno_setup section config
        source_path: PyInstaller output path
        output_path: Desired installer output path
        project_chinese_file: Optional path to project ChineseSimplified.isl

    Returns:
        str: ISS script content
    """
    app_name = app_config.get("name", "MyApp")
    app_version = app_config.get("version", "1.0.0")
    publisher = app_config.get("publisher", "Unknown Publisher")
    app_url = format_config.get("app_url", "")
    display_name = app_config.get("display_name", app_name)

    source_path_str = str(source_path).replace("/", "\\")

    if source_path.is_file():
        source_files = (
            f'Source: "{source_path_str}"; DestDir: "{{app}}"; Flags: ignoreversion'
        )
        exe_name = source_path.name
    else:
        source_files = (
            f'Source: "{source_path_str}\\*"; DestDir: "{{app}}"; '
            f"Flags: ignoreversion recursesubdirs createallsubdirs"
        )
        exe_name = f"{app_name}.exe"

    app_id = format_config.get("app_id", None)
    if not app_id:
        name_hash = hashlib.md5(app_name.encode()).hexdigest()[:8].upper()
        app_id = f"{{C4D8B3F2-1234-5678-9ABC-{name_hash}12345678}}"
    elif not (app_id.startswith("{") and app_id.endswith("}")):
        app_id = f"{{{app_id}}}"

    output_dir = str(output_path.parent).replace("/", "\\")

    setup_section = f"""[Setup]
AppId={app_id}
AppName={app_name}
AppVersion={app_version}
AppVerName={display_name} {app_version}
AppPublisher={publisher}
DefaultDirName={{autopf}}\\{app_name}
DefaultGroupName={app_name}
AllowNoIcons=yes
OutputDir={output_dir}
OutputBaseFilename={output_path.stem}
Compression=lzma
SolidCompression=yes
WizardStyle=modern"""

    if app_url:
        setup_section += f"\nAppPublisherURL={app_url}"
        setup_section += f"\nAppSupportURL={app_url}"
        setup_section += f"\nAppUpdatesURL={app_url}"

    license_file = format_config.get("license_file", "")
    if license_file and os.path.exists(license_file):
        license_path = str(Path(license_file)).replace("/", "\\")
        setup_section += f"\nLicenseFile={license_path}"

    setup_icon = format_config.get("setup_icon", "")
    if setup_icon and os.path.exists(setup_icon):
        setup_icon_path = str(Path(setup_icon)).replace("/", "\\")
        setup_section += f"\nSetupIconFile={setup_icon_path}"

    languages_section = "[Languages]"
    languages = format_config.get("languages", ["english"])
    if "english" in languages:
        languages_section += (
            '\nName: "english"; MessagesFile: "compiler:Default.isl"'
        )
    if "chinesesimplified" in languages or "chinese" in languages:
        if project_chinese_file:
            chinese_file_path = os.path.abspath(project_chinese_file).replace(
                "\\", "\\\\"
            )
            languages_section += (
                f'\nName: "chinesesimplified"; MessagesFile: "{chinese_file_path}"'
            )
        else:
            languages_section += (
                '\nName: "chinesesimplified"; '
                'MessagesFile: "compiler:Languages\\ChineseSimplified.isl"'
            )

    tasks_section = "[Tasks]"
    if format_config.get("create_desktop_icon", True):
        tasks_section += (
            '\nName: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; '
            'GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked'
        )

    files_section = f"[Files]\n{source_files}"

    icons_section = "[Icons]"
    icons_section += (
        f'\nName: "{{group}}\\{display_name}"; Filename: "{{app}}\\{exe_name}"'
    )

    if format_config.get("create_desktop_icon", True):
        icons_section += (
            f'\nName: "{{autodesktop}}\\{display_name}"; '
            f'Filename: "{{app}}\\{exe_name}"; Tasks: desktopicon'
        )

    icons_section += (
        f'\nName: "{{group}}\\{{cm:UninstallProgram,{display_name}}}"; '
        f'Filename: "{{uninstallexe}}"'
    )

    run_section = "[Run]"
    if format_config.get("run_after_install", False):
        run_section += (
            f'\nFilename: "{{app}}\\{exe_name}"; '
            f'Description: "{{cm:LaunchProgram,{display_name}}}"; '
            f"Flags: nowait postinstall skipifsilent"
        )

    iss_script = f"""; Script generated by UnifyPy 2.0
; Inno Setup Script
; Encoding: UTF-8

{setup_section}

{languages_section}

{tasks_section}

{files_section}

{icons_section}

{run_section}
"""

    return iss_script
