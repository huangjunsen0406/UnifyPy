#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Linux Tarball 打包器
创建tar.gz格式的应用分发包
"""

import os
import tarfile
import shutil
import tempfile
from typing import Dict, Any, List
from pathlib import Path
from ..base import BasePackager


class TarballPackager(BasePackager):
    """Tarball 打包器"""
    
    def get_supported_formats(self) -> List[str]:
        """获取支持的打包格式"""
        return ["tar.gz", "tgz"]
    
    def can_package_format(self, format_type: str) -> bool:
        """检查是否支持指定格式"""
        return format_type in self.get_supported_formats()
    
    def package(self, format_type: str, source_path: Path, output_path: Path) -> bool:
        """
        执行Tarball打包
        
        Args:
            format_type: 打包格式 (tar.gz/tgz)
            source_path: PyInstaller生成的应用路径
            output_path: 输出tar.gz文件路径
            
        Returns:
            bool: 打包是否成功
        """
        if not self.can_package_format(format_type):
            self.progress.on_error(
                Exception(f"不支持的格式: {format_type}"),
                "Linux Tarball打包"
            )
            return False
        
        # 获取Tarball配置
        tarball_config = self.get_format_config("tarball")
        
        try:
            # 确保输出目录存在
            self.ensure_output_dir(output_path)
            
            # 创建临时目录用于准备文件
            with tempfile.TemporaryDirectory() as temp_dir:
                package_dir = Path(temp_dir) / f"{self.config.get('name', 'myapp')}-{self.config.get('version', '1.0.0')}"
                
                # 创建包目录结构
                self._create_package_structure(source_path, package_dir, tarball_config)
                
                # 创建tar.gz文件
                success = self._create_tarball(package_dir, output_path, tarball_config)
                
                return success
                
        except Exception as e:
            self.progress.on_error(
                Exception(f"Tarball打包失败: {e}"),
                "Linux Tarball打包"
            )
            return False
    
    def _create_package_structure(self, source_path: Path, package_dir: Path, config: Dict[str, Any]):
        """创建包目录结构"""
        app_name = self.config.get('name', 'myapp')
        
        # 创建基本目录
        package_dir.mkdir(parents=True)
        bin_dir = package_dir / "bin"
        lib_dir = package_dir / "lib"
        share_dir = package_dir / "share"
        
        bin_dir.mkdir()
        
        self.progress.update_stage("Linux Tarball打包", 10, "复制应用文件")
        
        if source_path.is_file():
            # 单个可执行文件
            shutil.copy2(source_path, bin_dir / app_name)
            (bin_dir / app_name).chmod(0o755)
        else:
            # 目录 - 复制所有内容
            for item in source_path.iterdir():
                if item.is_file():
                    shutil.copy2(item, bin_dir)
                    if os.access(item, os.X_OK):
                        (bin_dir / item.name).chmod(0o755)
                else:
                    lib_dir.mkdir(exist_ok=True)
                    shutil.copytree(item, lib_dir / item.name)
        
        self.progress.update_stage("Linux Tarball打包", 10, "创建安装脚本")
        
        # 创建安装脚本
        self._create_install_script(package_dir, config)
        
        # 创建启动脚本
        self._create_launcher_script(package_dir, config)
        
        # 添加文档文件
        self._add_documentation(package_dir, config)
        
        # 添加额外文件
        self._add_extra_files(package_dir, config)
    
    def _create_install_script(self, package_dir: Path, config: Dict[str, Any]):
        """创建安装脚本"""
        app_name = self.config.get('name', 'myapp')
        install_prefix = config.get('install_prefix', '/usr/local')
        
        install_script_content = f"""#!/bin/bash
# 安装脚本 for {app_name}

set -e

# 默认安装前缀
PREFIX="{install_prefix}"

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --prefix=*)
            PREFIX="${{1#*=}}"
            shift
            ;;
        --prefix)
            PREFIX="$2"
            shift 2
            ;;
        -h|--help)
            echo "使用方法: $0 [--prefix=PREFIX]"
            echo "  --prefix=PREFIX  安装到指定前缀 (默认: {install_prefix})"
            exit 0
            ;;
        *)
            echo "未知选项: $1"
            exit 1
            ;;
    esac
done

echo "安装 {app_name} 到 $PREFIX"

# 创建目录
mkdir -p "$PREFIX/bin"
mkdir -p "$PREFIX/lib/{app_name}"
mkdir -p "$PREFIX/share/applications"
mkdir -p "$PREFIX/share/pixmaps"

# 复制文件
echo "复制可执行文件..."
cp -r bin/* "$PREFIX/bin/"

if [ -d "lib" ]; then
    echo "复制库文件..."
    cp -r lib/* "$PREFIX/lib/{app_name}/"
fi

if [ -d "share" ]; then
    echo "复制共享文件..."
    cp -r share/* "$PREFIX/share/"
fi

# 设置权限
chmod +x "$PREFIX/bin/{app_name}"

echo "安装完成!"
echo "运行 '{app_name}' 启动应用程序"
"""
        
        install_script = package_dir / "install.sh"
        with open(install_script, 'w') as f:
            f.write(install_script_content)
        install_script.chmod(0o755)
    
    def _create_launcher_script(self, package_dir: Path, config: Dict[str, Any]):
        """创建启动脚本（用于便携式运行）"""
        app_name = self.config.get('name', 'myapp')
        
        launcher_content = f"""#!/bin/bash
# 启动脚本 for {app_name}

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"

# 设置环境变量
export LD_LIBRARY_PATH="$SCRIPT_DIR/lib:$LD_LIBRARY_PATH"
export PATH="$SCRIPT_DIR/bin:$PATH"

# 运行应用程序
exec "$SCRIPT_DIR/bin/{app_name}" "$@"
"""
        
        launcher_script = package_dir / f"run-{app_name}.sh"
        with open(launcher_script, 'w') as f:
            f.write(launcher_content)
        launcher_script.chmod(0o755)
    
    def _add_documentation(self, package_dir: Path, config: Dict[str, Any]):
        """添加文档文件"""
        self.progress.update_stage("Linux Tarball打包", 5, "添加文档文件")
        
        # 创建README文件
        readme_content = config.get('readme_content')
        if not readme_content:
            app_name = self.config.get('name', 'myapp')
            display_name = self.config.get('display_name', app_name)
            version = self.config.get('version', '1.0.0')
            
            readme_content = f"""{display_name} v{version}
{'=' * (len(display_name) + len(version) + 3)}

这是 {display_name} 的便携式分发包。

安装:
------
运行 ./install.sh 安装到系统目录
或者使用 ./install.sh --prefix=/path/to/install/dir 安装到自定义目录

便携式运行:
----------
运行 ./run-{app_name}.sh 直接启动应用程序（无需安装）

系统要求:
--------
- Linux x86_64 或 ARM64
- 依赖库需要预先安装

{config.get('description', '')}
"""
        
        readme_file = package_dir / "README.txt"
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        # 复制许可证文件
        license_file = config.get('license_file') or self.config.get('license')
        if license_file and os.path.exists(license_file):
            shutil.copy2(license_file, package_dir / "LICENSE.txt")
        
        # 复制变更日志
        changelog_file = config.get('changelog_file')
        if changelog_file and os.path.exists(changelog_file):
            shutil.copy2(changelog_file, package_dir / "CHANGELOG.txt")
    
    def _add_extra_files(self, package_dir: Path, config: Dict[str, Any]):
        """添加额外文件"""
        extra_files = config.get('extra_files', [])
        
        for extra_file in extra_files:
            if isinstance(extra_file, str):
                # 简单的文件路径
                if os.path.exists(extra_file):
                    if os.path.isfile(extra_file):
                        shutil.copy2(extra_file, package_dir)
                    else:
                        shutil.copytree(extra_file, package_dir / os.path.basename(extra_file))
            elif isinstance(extra_file, dict):
                # 带有映射的文件
                source = extra_file.get('source')
                target = extra_file.get('target')
                
                if source and target and os.path.exists(source):
                    target_path = package_dir / target
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    if os.path.isfile(source):
                        shutil.copy2(source, target_path)
                    else:
                        shutil.copytree(source, target_path)
    
    def _create_tarball(self, package_dir: Path, output_path: Path, config: Dict[str, Any]) -> bool:
        """创建tar.gz文件"""
        self.progress.update_stage("Linux Tarball打包", 30, "创建tar.gz文件")
        
        try:
            compression_level = config.get('compression_level', 6)
            
            with tarfile.open(output_path, "w:gz", compresslevel=compression_level) as tar:
                # 获取包目录名
                package_name = package_dir.name
                parent_dir = package_dir.parent
                
                # 添加整个包目录
                tar.add(package_dir, arcname=package_name)
            
            self.progress.update_stage("Linux Tarball打包", 15, "验证tar.gz文件")
            
            # 验证生成的文件
            if output_path.exists() and output_path.stat().st_size > 0:
                # 测试tar文件完整性
                with tarfile.open(output_path, "r:gz") as tar:
                    # 简单的完整性检查
                    members = tar.getnames()
                    if not members:
                        raise Exception("tar文件为空")
                
                return True
            else:
                self.progress.on_error(
                    Exception(f"tar.gz文件生成失败: {output_path}"),
                    "Linux Tarball打包"
                )
                return False
                
        except Exception as e:
            self.progress.on_error(
                Exception(f"创建tar.gz文件失败: {e}"),
                "Linux Tarball打包"
            )
            return False
    
    def validate_config(self, format_type: str) -> List[str]:
        """验证Tarball配置"""
        errors = []
        
        config = self.get_format_config("tarball")
        
        # 检查许可证文件
        license_file = config.get('license_file') or self.config.get('license')
        if license_file and not os.path.exists(license_file):
            errors.append(f"许可证文件不存在: {license_file}")
        
        # 检查变更日志文件
        changelog_file = config.get('changelog_file')
        if changelog_file and not os.path.exists(changelog_file):
            errors.append(f"变更日志文件不存在: {changelog_file}")
        
        # 检查额外文件
        extra_files = config.get('extra_files', [])
        for extra_file in extra_files:
            if isinstance(extra_file, str):
                if not os.path.exists(extra_file):
                    errors.append(f"额外文件不存在: {extra_file}")
            elif isinstance(extra_file, dict):
                source = extra_file.get('source')
                if source and not os.path.exists(source):
                    errors.append(f"额外文件不存在: {source}")
        
        return errors