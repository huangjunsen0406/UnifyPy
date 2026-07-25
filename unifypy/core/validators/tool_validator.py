#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
工具验证器
负责检查平台特定的打包器工具是否可用
"""

from typing import List, Dict, Any


class ToolValidator:
    """
    工具验证器，检查打包所需的工具是否可用.
    """

    def __init__(self, tool_manager, progress_manager=None):
        """
        初始化工具验证器.

        Args:
            tool_manager: 工具管理器实例
            progress_manager: 进度管理器实例（可选）
        """
        self.tool_manager = tool_manager
        self.progress = progress_manager

    def check_platform_tools(
        self,
        platform: str,
        verbose: bool = False,
        format_type: str = None,
        config: dict = None
    ) -> List[Dict[str, Any]]:
        """
        检查指定平台的工具是否可用.

        Args:
            platform: 平台名称 (windows/macos/linux)
            verbose: 是否显示详细信息
            format_type: 打包格式 (可选，如 deb/rpm/dmg/appimage/inno_setup)
                        如果指定，则只检查该格式需要的工具
            config: 可选配置字典，传递给工具检测以检查用户配置的路径

        Returns:
            List[Dict]: 缺失的工具列表
        """
        # 获取需要检测的工具
        required_tools = self.tool_manager.get_required_tools_for_platform(
            platform, format_type
        )

        if not required_tools:
            return []

        missing_tools = []

        for tool_info in required_tools:
            tool_name = tool_info["name"]
            tool_display_name = tool_info["display_name"]

            is_available = self.tool_manager.check_tool_available(tool_name, config)

            if not is_available:
                missing_tools.append(tool_info)
                if self.progress and verbose:
                    self.progress.warning(f"⚠️  未找到 {tool_display_name}")

        return missing_tools

    def validate_and_raise(
        self,
        platform: str,
        verbose: bool = False,
        format_type: str = None,
        config: dict = None,
        allow_auto_install: bool = True,
    ):
        """
        检查工具；在 allow_auto_install 时尝试自动安装，否则打印指引并报错.

        Args:
            platform: 平台名称
            verbose: 是否显示详细信息
            format_type: 打包格式 (可选)
            config: 可选配置字典
            allow_auto_install: 是否允许自动安装（默认 True）

        Raises:
            RuntimeError: 如果有工具缺失
        """
        missing_tools = self.check_platform_tools(platform, verbose, format_type, config)

        if not missing_tools:
            return

        # Auto-install when allowed (default on; disable via --no-allow-auto-install)
        still_missing = []
        if allow_auto_install or getattr(self.tool_manager, "allow_auto_install", True):
            # Ensure tool manager flag is set for nested checks
            self.tool_manager.allow_auto_install = True
            for tool_info in missing_tools:
                tool_name = tool_info["name"]
                display_name = tool_info["display_name"]

                # Inno Setup never auto-installs
                if tool_name == "inno-setup":
                    still_missing.append(tool_info)
                    continue

                if self.progress:
                    self.progress.info(f"正在自动安装 {display_name}...")

                try:
                    success = self.tool_manager.auto_install_tool(tool_name)
                except Exception as e:
                    success = False
                    if self.progress:
                        self.progress.warning(f"{display_name} 自动安装失败: {e}")

                if success:
                    if self.progress:
                        self.progress.info(f"{display_name} 安装成功")
                else:
                    still_missing.append(tool_info)
        else:
            still_missing = list(missing_tools)

        if still_missing:
            self._display_missing_tools_error(
                still_missing, allow_auto_install=bool(allow_auto_install)
            )
            raise RuntimeError("请安装缺失的打包工具后重试")

    def _display_missing_tools_error(
        self,
        missing_tools: List[Dict[str, Any]],
        allow_auto_install: bool = True,
    ):
        """
        显示缺失工具的详细错误信息.

        Args:
            missing_tools: 缺失的工具列表
            allow_auto_install: 当前是否已启用自动安装
        """
        from unifypy.core import logutil

        logutil.error("=" * 70)
        logutil.error("缺少必要的打包工具")
        logutil.error("=" * 70)

        auto_installable = {"appimagetool", "dpkg-deb", "rpmbuild"}

        for tool_info in missing_tools:
            logutil.error(f"工具: {tool_info['display_name']}")
            logutil.info(f"   描述: {tool_info['description']}")
            logutil.info(f"   下载地址: {tool_info['download_url']}")

            if "install_instructions" in tool_info:
                logutil.info("   安装说明:")
                for instruction in tool_info["install_instructions"]:
                    logutil.info(f"      {instruction}")

            if "config_example" in tool_info:
                logutil.info("   或在配置文件中指定路径:")
                logutil.info(f"      {tool_info['config_example']}")

            if tool_info.get("name") in auto_installable and not allow_auto_install:
                logutil.info(
                    "   提示: 自动安装默认开启；若被 --no-allow-auto-install 关闭，"
                    "可去掉该参数以尝试自动安装（需 sudo / 网络；appimagetool 将校验 SHA256）"
                )
            if tool_info.get("name") == "inno-setup":
                logutil.info("   注意: Inno Setup 出于安全考虑不会自动下载执行，请手动安装。")

        logutil.error("=" * 70)

    def get_missing_tools_summary(
        self,
        platform: str,
        format_type: str = None
    ) -> Dict[str, Any]:
        """
        获取缺失工具的摘要信息.

        Args:
            platform: 平台名称
            format_type: 打包格式 (可选，如 deb/rpm/dmg/inno_setup)

        Returns:
            Dict: 包含缺失工具数量和列表的字典
        """
        missing_tools = self.check_platform_tools(platform, verbose=False, format_type=format_type)

        return {
            "platform": platform,
            "total_required": len(
                self.tool_manager.get_required_tools_for_platform(platform, format_type)
            ),
            "missing_count": len(missing_tools),
            "missing_tools": [
                {
                    "name": tool["name"],
                    "display_name": tool["display_name"],
                    "description": tool["description"]
                }
                for tool in missing_tools
            ],
            "all_available": len(missing_tools) == 0
        }
