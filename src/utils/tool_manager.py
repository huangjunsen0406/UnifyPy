#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
第三方工具自动下载和管理
支持从GitHub直接获取工具，不依赖系统包管理器
"""

import os
import platform
import shutil
import zipfile
import tarfile
import tempfile
import hashlib
from typing import Dict, Optional, List
from pathlib import Path
import requests
import json


class ToolManager:
    """第三方工具自动下载和管理"""
    
    def __init__(self, tools_dir: Optional[str] = None):
        """
        初始化工具管理器
        
        Args:
            tools_dir: 工具存储目录，默认为当前目录下的tools文件夹
        """
        self.tools_dir = Path(tools_dir or "tools").resolve()
        self.tools_dir.mkdir(exist_ok=True)
        
        # 初始化缓存管理器
        from .parallel_builder import CacheManager
        self.cache_manager = CacheManager()
        
        # 当前平台信息
        self.current_platform = self._detect_platform()
        self.current_arch = self._detect_architecture()
        
        # 本地工具配置（UnifyPy内置工具）
        self.local_tools = {
            'create-dmg': {
                'executable': 'create-dmg',
                'platform': 'macos',
                'path': 'src/tools/create-dmg/create-dmg'
            }
        }
        
        # GitHub工具配置
        self.github_tools = {
            'appimagetool': {
                'repo': 'AppImage/AppImageKit',
                'executable': 'appimagetool',
                'platform': 'linux',
                'type': 'binary',  # 二进制类型
                'asset_pattern': 'appimagetool-{arch}.AppImage',
                'install_method': 'download_binary'
            },
            'linuxdeploy': {
                'repo': 'linuxdeploy/linuxdeploy',
                'executable': 'linuxdeploy',
                'platform': 'linux',
                'type': 'binary',
                'asset_pattern': 'linuxdeploy-{arch}.AppImage',
                'install_method': 'download_binary'
            },
            'inno-setup': {
                'repo': 'jrsoftware/issrc',
                'executable': 'ISCC.exe',
                'platform': 'windows',
                'type': 'installer',  # 安装包类型
                'download_url': 'https://jrsoftware.org/download.php/is.exe',
                'install_method': 'download_installer',
                'description': 'Inno Setup 编译器 - Windows 安装包制作工具'
            }
        }
        
        # 缓存GitHub API响应
        self._api_cache = {}
    
    def _detect_platform(self) -> str:
        """检测当前平台"""
        system = platform.system().lower()
        if system == "darwin":
            return "macos"
        elif system == "windows":
            return "windows"
        elif system == "linux":
            return "linux"
        else:
            return system
    
    def _detect_architecture(self) -> str:
        """检测当前架构"""
        machine = platform.machine().lower()
        if machine in ['x86_64', 'amd64']:
            return 'x86_64'
        elif machine in ['aarch64', 'arm64']:
            return 'arm64'
        elif machine in ['i386', 'i686']:
            return 'i386'
        else:
            return machine
    
    def ensure_tool(self, tool_name: str, version: str = 'latest') -> str:
        """
        确保工具可用，自动下载如果不存在
        
        Args:
            tool_name: 工具名称
            version: 工具版本，默认为latest
            
        Returns:
            str: 工具可执行文件路径
            
        Raises:
            ValueError: 不支持的工具或平台
            RuntimeError: 下载或安装失败
        """
        # 优先检查本地工具
        if tool_name in self.local_tools:
            return self._get_local_tool_path(tool_name)
            
        if tool_name not in self.github_tools:
            raise ValueError(f"不支持的工具: {tool_name}")
        
        tool_config = self.github_tools[tool_name]
        
        # 检查平台兼容性
        if tool_config['platform'] != 'all' and tool_config['platform'] != self.current_platform:
            raise ValueError(f"工具 {tool_name} 不支持当前平台 {self.current_platform}")
        
        # 检查工具是否已存在
        executable_path = self._get_tool_path(tool_name)
        if executable_path and os.path.exists(executable_path):
            return executable_path
        
        # 下载并安装工具
        return self._download_and_install_tool(tool_name, version)
    
    def _get_local_tool_path(self, tool_name: str) -> str:
        """
        获取本地工具路径
        
        Args:
            tool_name: 工具名称
            
        Returns:
            str: 本地工具路径
            
        Raises:
            ValueError: 工具不存在或不支持当前平台
            RuntimeError: 工具文件不存在或无执行权限
        """
        if tool_name not in self.local_tools:
            raise ValueError(f"未知的本地工具: {tool_name}")
            
        tool_config = self.local_tools[tool_name]
        
        # 检查平台兼容性
        if tool_config['platform'] != 'all' and tool_config['platform'] != self.current_platform:
            raise ValueError(f"工具 {tool_name} 不支持当前平台 {self.current_platform}")
            
        # 获取项目根目录
        project_root = Path(__file__).parent.parent.parent  # 从 src/utils/ 回到项目根目录
        tool_path = project_root / tool_config['path']
        
        if not tool_path.exists():
            raise RuntimeError(f"本地工具不存在: {tool_path}")
            
        if not os.access(tool_path, os.X_OK):
            # 尝试设置执行权限
            try:
                os.chmod(tool_path, 0o755)
            except OSError as e:
                raise RuntimeError(f"无法设置工具执行权限: {tool_path}, 错误: {e}")
                
        return str(tool_path)
    
    def _get_tool_path(self, tool_name: str) -> Optional[str]:
        """
        获取工具的本地路径
        
        Args:
            tool_name: 工具名称
            
        Returns:
            Optional[str]: 工具路径，如果不存在则返回None
        """
        tool_config = self.github_tools[tool_name]
        executable_name = tool_config['executable']
        
        # 在tools目录中查找
        tool_dir = self.tools_dir / tool_name
        possible_paths = [
            tool_dir / executable_name,
            tool_dir / f"{executable_name}.exe",  # Windows
            tool_dir / f"{executable_name}.AppImage",  # Linux AppImage
        ]
        
        for path in possible_paths:
            if path.exists() and os.access(path, os.X_OK):
                return str(path)
        
        return None
    
    def _download_and_install_tool(self, tool_name: str, version: str) -> str:
        """
        下载并安装工具
        
        Args:
            tool_name: 工具名称
            version: 版本
            
        Returns:
            str: 安装后的工具路径
        """
        tool_config = self.github_tools[tool_name]
        repo = tool_config['repo']
        install_method = tool_config['install_method']
        
        if install_method == 'copy_executable':
            return self._install_source_tool(tool_name, repo, version)
        elif install_method == 'download_binary':
            return self._install_binary_tool(tool_name, repo, version)
        elif install_method == 'download_installer':
            return self._install_installer_tool(tool_name, tool_config)
        else:
            raise ValueError(f"未知的安装方法: {install_method}")
    
    def _install_source_tool(self, tool_name: str, repo: str, version: str) -> str:
        """
        安装源码类型的工具（如create-dmg）
        
        Args:
            tool_name: 工具名称
            repo: GitHub仓库
            version: 版本
            
        Returns:
            str: 工具路径
        """
        # 下载源码
        download_url = self._get_source_download_url(repo, version)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # 下载并解压
            archive_path = temp_path / "source.zip"
            self._download_file(download_url, archive_path)
            
            extract_dir = temp_path / "extracted"
            extract_dir.mkdir()
            
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # 找到解压后的目录（通常是repo名称）
            extracted_dirs = [d for d in extract_dir.iterdir() if d.is_dir()]
            if not extracted_dirs:
                raise RuntimeError("解压后未找到源码目录")
            
            source_dir = extracted_dirs[0]
            
            # 安装到tools目录
            tool_dir = self.tools_dir / tool_name
            if tool_dir.exists():
                shutil.rmtree(tool_dir)
            
            shutil.copytree(source_dir, tool_dir)
            
            # 设置可执行权限
            executable_path = tool_dir / self.github_tools[tool_name]['executable']
            if executable_path.exists():
                os.chmod(executable_path, 0o755)
                return str(executable_path)
            else:
                raise RuntimeError(f"未找到可执行文件: {executable_path}")
    
    def _install_binary_tool(self, tool_name: str, repo: str, version: str) -> str:
        """
        安装二进制类型的工具（如appimagetool）
        
        Args:
            tool_name: 工具名称
            repo: GitHub仓库
            version: 版本
            
        Returns:
            str: 工具路径
        """
        tool_config = self.github_tools[tool_name]
        
        # 获取下载URL
        download_url = self._get_binary_download_url(repo, tool_config['asset_pattern'], version)
        
        # 确定目标路径
        tool_dir = self.tools_dir / tool_name
        tool_dir.mkdir(exist_ok=True)
        
        executable_name = tool_config['executable']
        if download_url.endswith('.AppImage'):
            executable_name += '.AppImage'
        
        target_path = tool_dir / executable_name
        
        # 下载文件
        self._download_file(download_url, target_path)
        
        # 设置可执行权限
        os.chmod(target_path, 0o755)
        
        return str(target_path)
    
    def _install_installer_tool(self, tool_name: str, tool_config: Dict) -> str:
        """
        安装安装包类型的工具（如Inno Setup）
        
        Args:
            tool_name: 工具名称
            tool_config: 工具配置
            
        Returns:
            str: 工具路径
        """
        download_url = tool_config.get('download_url')
        if not download_url:
            raise ValueError(f"工具 {tool_name} 缺少下载URL配置")
        
        # 提示用户手动安装
        print(f"\n🔧 需要安装 {tool_name}")
        print(f"📝 描述: {tool_config.get('description', '第三方工具')}")
        print(f"🌐 下载地址: {download_url}")
        print(f"\n⚠️  由于 {tool_name} 是完整的安装包软件，需要手动安装：")
        print(f"   1. 访问上述URL下载安装包")
        print(f"   2. 运行安装程序完成安装")
        print(f"   3. 重新运行UnifyPy构建命令")
        print(f"\n💡 或者，您可以在配置文件中指定已安装的路径：")
        print(f'   "inno_setup_path": "C:\\\\Program Files (x86)\\\\Inno Setup 6\\\\ISCC.exe"')
        
        # 检查是否已经安装
        print(f"\n🔍 正在检查系统中是否已安装 {tool_name}...")
        
        # 尝试自动检测
        if tool_name == 'inno-setup':
            # 调用Inno Setup打包器的检测逻辑
            detected_path = self._detect_existing_inno_setup()
            if detected_path:
                print(f"✅ 检测到已安装的 {tool_name}: {detected_path}")
                return detected_path
        
        # 如果没有检测到，抛出异常
        raise RuntimeError(f"未找到 {tool_name}，请按照上述说明手动安装")
    
    def _detect_existing_inno_setup(self) -> Optional[str]:
        """检测已安装的Inno Setup"""
        try:
            # 检查注册表
            registry_path = self._check_registry_for_inno_setup()
            if registry_path and os.path.exists(registry_path):
                return registry_path
            
            # 检查常见路径
            common_paths = [
                r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
                r"C:\Program Files\Inno Setup 6\ISCC.exe",
                r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe", 
                r"C:\Program Files\Inno Setup 5\ISCC.exe",
            ]
            
            for path in common_paths:
                if os.path.exists(path):
                    return path
            
            # 检查PATH
            import shutil
            path_found = shutil.which("ISCC.exe")
            if path_found:
                return path_found
                
        except Exception:
            pass
        
        return None
    
    def _check_registry_for_inno_setup(self) -> Optional[str]:
        """从Windows注册表检查Inno Setup"""
        try:
            import winreg
            
            registry_keys = [
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 6_is1",
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 5_is1",
                r"SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 6_is1",
                r"SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 5_is1",
            ]
            
            for key_path in registry_keys:
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                        install_location, _ = winreg.QueryValueEx(key, "InstallLocation")
                        if install_location:
                            iscc_path = os.path.join(install_location, "ISCC.exe")
                            if os.path.exists(iscc_path):
                                return iscc_path
                except (FileNotFoundError, OSError):
                    continue
                    
        except ImportError:
            # winreg模块不可用（非Windows系统）
            pass
        except Exception:
            pass
        
        return None
    
    def _get_source_download_url(self, repo: str, version: str) -> str:
        """
        获取源码下载URL
        
        Args:
            repo: GitHub仓库
            version: 版本
            
        Returns:
            str: 下载URL
        """
        if version == 'latest':
            # 获取最新版本
            api_url = f"https://api.github.com/repos/{repo}/releases/latest"
            response = self._github_api_request(api_url)
            version = response['tag_name']
        
        return f"https://github.com/{repo}/archive/refs/tags/{version}.zip"
    
    def _get_binary_download_url(self, repo: str, asset_pattern: str, version: str) -> str:
        """
        获取二进制文件下载URL
        
        Args:
            repo: GitHub仓库
            asset_pattern: 资源文件模式
            version: 版本
            
        Returns:
            str: 下载URL
        """
        if version == 'latest':
            api_url = f"https://api.github.com/repos/{repo}/releases/latest"
        else:
            api_url = f"https://api.github.com/repos/{repo}/releases/tags/{version}"
        
        response = self._github_api_request(api_url)
        
        # 格式化资源文件名
        asset_name = asset_pattern.format(arch=self.current_arch)
        
        # 查找匹配的资源
        for asset in response['assets']:
            if asset['name'] == asset_name or asset_name in asset['name']:
                return asset['browser_download_url']
        
        # 如果找不到精确匹配，尝试模糊匹配
        for asset in response['assets']:
            if self.current_arch in asset['name'].lower():
                return asset['browser_download_url']
        
        raise RuntimeError(f"未找到匹配的资源文件: {asset_name}")
    
    def _github_api_request(self, url: str) -> Dict:
        """
        发起GitHub API请求
        
        Args:
            url: API URL
            
        Returns:
            Dict: API响应
        """
        if url in self._api_cache:
            return self._api_cache[url]
        
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'UnifyPy/2.0'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        self._api_cache[url] = data
        
        return data
    
    def _download_file(self, url: str, target_path: Path):
        """
        下载文件
        
        Args:
            url: 下载URL
            target_path: 目标路径
        """
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(target_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
    
    def list_available_tools(self) -> List[str]:
        """
        列出所有可用的工具
        
        Returns:
            List[str]: 工具名称列表
        """
        local_tools = list(self.local_tools.keys())
        github_tools = list(self.github_tools.keys())
        return local_tools + github_tools
    
    def get_tool_info(self, tool_name: str) -> Dict:
        """
        获取工具信息
        
        Args:
            tool_name: 工具名称
            
        Returns:
            Dict: 工具信息
        """
        if tool_name in self.local_tools:
            config = self.local_tools[tool_name].copy()
            config['type'] = 'local'
            try:
                config['local_path'] = self._get_local_tool_path(tool_name)
                config['available'] = True
            except (ValueError, RuntimeError):
                config['local_path'] = None
                config['available'] = False
            return config
            
        if tool_name not in self.github_tools:
            raise ValueError(f"未知工具: {tool_name}")
        
        config = self.github_tools[tool_name].copy()
        config['type'] = 'github'
        config['local_path'] = self._get_tool_path(tool_name)
        config['available'] = config['local_path'] is not None
        
        return config
    
    def remove_tool(self, tool_name: str):
        """
        移除工具
        
        Args:
            tool_name: 工具名称
        """
        tool_dir = self.tools_dir / tool_name
        if tool_dir.exists():
            shutil.rmtree(tool_dir)
    
    def update_tool(self, tool_name: str, version: str = 'latest') -> str:
        """
        更新工具到指定版本
        
        Args:
            tool_name: 工具名称
            version: 版本
            
        Returns:
            str: 更新后的工具路径
        """
        self.remove_tool(tool_name)
        return self.ensure_tool(tool_name, version)