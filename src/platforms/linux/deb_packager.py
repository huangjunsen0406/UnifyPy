#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Linux DEB 打包器
创建Debian/Ubuntu格式的安装包
"""

import os
import tempfile
import shutil
from typing import Dict, Any, List
from pathlib import Path
from ..base import BasePackager


class DEBPackager(BasePackager):
    """DEB 打包器"""
    
    def get_supported_formats(self) -> List[str]:
        """获取支持的打包格式"""
        return ["deb"]
    
    def can_package_format(self, format_type: str) -> bool:
        """检查是否支持指定格式"""
        return format_type in self.get_supported_formats()
    
    def package(self, format_type: str, source_path: Path, output_path: Path) -> bool:
        """
        执行DEB打包
        
        Args:
            format_type: 打包格式 (deb)
            source_path: PyInstaller生成的应用路径
            output_path: 输出DEB文件路径
            
        Returns:
            bool: 打包是否成功
        """
        if not self.can_package_format(format_type):
            self.progress.on_error(
                Exception(f"不支持的格式: {format_type}"),
                "Linux DEB打包"
            )
            return False
        
        # 获取DEB配置
        deb_config = self.get_format_config("deb")
        
        # 创建临时构建目录
        with tempfile.TemporaryDirectory() as temp_dir:
            build_dir = Path(temp_dir) / "build"
            debian_dir = build_dir / "DEBIAN"
            
            # 创建目录结构
            debian_dir.mkdir(parents=True)
            
            # 安装应用文件
            self._install_application(source_path, build_dir, deb_config)
            
            # 创建控制文件
            self._create_control_file(debian_dir, deb_config)
            
            # 创建脚本文件
            self._create_scripts(debian_dir, deb_config)
            
            # 创建桌面文件
            self._create_desktop_file(build_dir, deb_config)
            
            # 构建DEB包
            success = self._build_deb_package(build_dir, output_path)
            
            return success
    
    def _install_application(self, source_path: Path, build_dir: Path, config: Dict[str, Any]):
        """安装应用文件到构建目录"""
        app_name = self.config.get('name', 'myapp').lower()
        install_dir = build_dir / "opt" / app_name
        
        # 创建安装目录
        install_dir.mkdir(parents=True)
        
        if source_path.is_file():
            # 单个可执行文件
            shutil.copy2(source_path, install_dir / app_name)
            (install_dir / app_name).chmod(0o755)
        else:
            # 目录 - 复制所有内容
            for item in source_path.iterdir():
                if item.is_file():
                    shutil.copy2(item, install_dir)
                else:
                    shutil.copytree(item, install_dir / item.name)
        
        # 创建符号链接到 /usr/local/bin
        bin_dir = build_dir / "usr" / "local" / "bin"
        bin_dir.mkdir(parents=True)
        
        # 创建启动脚本
        launcher_script = bin_dir / app_name
        launcher_content = f"""#!/bin/bash
cd /opt/{app_name}
exec ./{app_name} "$@"
"""
        
        with open(launcher_script, 'w') as f:
            f.write(launcher_content)
        launcher_script.chmod(0o755)
    
    def _create_control_file(self, debian_dir: Path, config: Dict[str, Any]):
        """创建DEBIAN/control文件"""
        app_name = self.config.get('name', 'myapp').lower()
        version = self.config.get('version', '1.0.0')
        
        # 获取架构信息
        import platform
        arch = platform.machine()
        if arch == "x86_64":
            arch = "amd64"
        elif arch.startswith("arm"):
            arch = "arm64" if "64" in arch else "armhf"
        
        control_content = f"""Package: {app_name}
Version: {version}
Section: {config.get('section', 'utils')}
Priority: {config.get('priority', 'optional')}
Architecture: {arch}
Maintainer: {config.get('maintainer', self.config.get('publisher', 'Unknown <unknown@example.com>'))}
Description: {config.get('description', self.config.get('display_name', app_name))}
"""
        
        # 添加依赖
        depends = config.get('depends', [])
        if depends:
            if isinstance(depends, list):
                depends_str = ', '.join(depends)
            else:
                depends_str = str(depends)
            control_content += f"Depends: {depends_str}\n"
        
        # 添加冲突
        conflicts = config.get('conflicts', [])
        if conflicts:
            if isinstance(conflicts, list):
                conflicts_str = ', '.join(conflicts)
            else:
                conflicts_str = str(conflicts)
            control_content += f"Conflicts: {conflicts_str}\n"
        
        # 添加推荐和建议
        recommends = config.get('recommends', [])
        if recommends:
            if isinstance(recommends, list):
                recommends_str = ', '.join(recommends)
            else:
                recommends_str = str(recommends)
            control_content += f"Recommends: {recommends_str}\n"
        
        suggests = config.get('suggests', [])
        if suggests:
            if isinstance(suggests, list):
                suggests_str = ', '.join(suggests)
            else:
                suggests_str = str(suggests)
            control_content += f"Suggests: {suggests_str}\n"
        
        # 添加首页
        homepage = config.get('homepage')
        if homepage:
            control_content += f"Homepage: {homepage}\n"
        
        # 写入控制文件
        with open(debian_dir / "control", 'w') as f:
            f.write(control_content)
    
    def _create_scripts(self, debian_dir: Path, config: Dict[str, Any]):
        """创建维护脚本"""
        scripts = ['preinst', 'postinst', 'prerm', 'postrm']
        
        for script in scripts:
            script_content = config.get(f'{script}_script')
            if script_content:
                script_file = debian_dir / script
                with open(script_file, 'w') as f:
                    f.write("#!/bin/bash\n")
                    f.write(script_content)
                script_file.chmod(0o755)
    
    def _create_desktop_file(self, build_dir: Path, config: Dict[str, Any]):
        """创建桌面文件"""
        if not config.get('create_desktop_file', True):
            return
        
        app_name = self.config.get('name', 'myapp')
        display_name = self.config.get('display_name', app_name)
        
        # 创建applications目录
        apps_dir = build_dir / "usr" / "share" / "applications"
        apps_dir.mkdir(parents=True)
        
        # 桌面文件内容
        desktop_content = f"""[Desktop Entry]
Type=Application
Name={display_name}
Exec={app_name.lower()}
Icon={app_name.lower()}
Comment={config.get('description', display_name)}
Categories={config.get('categories', 'Utility;')}
Terminal={str(config.get('terminal', False)).lower()}
"""
        
        # 写入桌面文件
        desktop_file = apps_dir / f"{app_name.lower()}.desktop"
        with open(desktop_file, 'w') as f:
            f.write(desktop_content)
        
        # 复制图标文件
        icon_path = config.get('icon') or self.config.get('icon')
        if icon_path and os.path.exists(icon_path):
            # 创建图标目录
            icon_dir = build_dir / "usr" / "share" / "pixmaps"
            icon_dir.mkdir(parents=True)
            
            # 复制图标
            icon_ext = Path(icon_path).suffix
            icon_dest = icon_dir / f"{app_name.lower()}{icon_ext}"
            shutil.copy2(icon_path, icon_dest)
    
    def _build_deb_package(self, build_dir: Path, output_path: Path) -> bool:
        """构建DEB包"""
        # 确保输出目录存在
        self.ensure_output_dir(output_path)
        
        # 使用dpkg-deb构建包
        command = ['dpkg-deb', '--build', str(build_dir), str(output_path)]
        
        success = self.runner.run_command(
            command,
            "Linux DEB打包",
            "正在构建DEB包...",
            80,
            shell=False
        )
        
        if success and output_path.exists():
            return True
        else:
            self.progress.on_error(
                Exception(f"DEB包生成失败: {output_path}"),
                "Linux DEB打包"
            )
            return False
    
    def validate_config(self, format_type: str) -> List[str]:
        """验证DEB配置"""
        errors = []
        
        config = self.get_format_config("deb")
        
        # 检查必需字段
        required_fields = ['maintainer']
        for field in required_fields:
            if not config.get(field):
                errors.append(f"DEB配置缺少必需字段: {field}")
        
        # 检查图标文件
        icon_path = config.get('icon') or self.config.get('icon')
        if icon_path and not os.path.exists(icon_path):
            errors.append(f"图标文件不存在: {icon_path}")
        
        # 检查dpkg-deb工具
        try:
            import shutil
            if not shutil.which('dpkg-deb'):
                errors.append("dpkg-deb工具未安装，请安装: sudo apt-get install dpkg-dev")
        except:
            errors.append("无法检查dpkg-deb工具")
        
        return errors