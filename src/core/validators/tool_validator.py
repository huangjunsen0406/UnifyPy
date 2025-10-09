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
        verbose: bool = False
    ) -> List[Dict[str, Any]]:
        """
        检查指定平台的工具是否可用.

        Args:
            platform: 平台名称 (windows/macos/linux)
            verbose: 是否显示详细信息

        Returns:
            List[Dict]: 缺失的工具列表

        Raises:
            RuntimeError: 如果有工具缺失且强制检查
        """
        # 获取需要检测的工具
        required_tools = self.tool_manager.get_required_tools_for_platform(
            platform
        )

        if not required_tools:
            # 没有需要检测的工具
            return []

        missing_tools = []

        for tool_info in required_tools:
            tool_name = tool_info["name"]
            tool_display_name = tool_info["display_name"]

            # 检查工具是否可用
            is_available = self.tool_manager.check_tool_available(tool_name)

            if not is_available:
                missing_tools.append(tool_info)
                if self.progress and verbose:
                    self.progress.warning(f"⚠️  未找到 {tool_display_name}")

        return missing_tools

    def validate_and_raise(self, platform: str, verbose: bool = False):
        """
        检查工具并在缺失时抛出异常.

        Args:
            platform: 平台名称
            verbose: 是否显示详细信息

        Raises:
            RuntimeError: 如果有工具缺失
        """
        missing_tools = self.check_platform_tools(platform, verbose)

        if missing_tools:
            self._display_missing_tools_error(missing_tools)
            raise RuntimeError("请安装缺失的打包工具后重试")

    def _display_missing_tools_error(self, missing_tools: List[Dict[str, Any]]):
        """
        显示缺失工具的详细错误信息.

        Args:
            missing_tools: 缺失的工具列表
        """
        print("\n" + "=" * 70)
        print("❌ 缺少必要的打包工具")
        print("=" * 70)

        for tool_info in missing_tools:
            print(f"\n📦 工具: {tool_info['display_name']}")
            print(f"   描述: {tool_info['description']}")
            print(f"   下载地址: {tool_info['download_url']}")

            if "install_instructions" in tool_info:
                print("   安装说明:")
                for instruction in tool_info["install_instructions"]:
                    print(f"      {instruction}")

            if "config_example" in tool_info:
                print("   或在配置文件中指定路径:")
                print(f"      {tool_info['config_example']}")

        print("\n" + "=" * 70)

    def get_missing_tools_summary(
        self,
        platform: str
    ) -> Dict[str, Any]:
        """
        获取缺失工具的摘要信息.

        Args:
            platform: 平台名称

        Returns:
            Dict: 包含缺失工具数量和列表的字典
        """
        missing_tools = self.check_platform_tools(platform, verbose=False)

        return {
            "platform": platform,
            "total_required": len(
                self.tool_manager.get_required_tools_for_platform(platform)
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
