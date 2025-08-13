#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Linux RPM 打包器
创建RedHat/CentOS/Fedora格式的安装包
"""

import os
import tempfile
import shutil
from typing import Dict, Any, List
from pathlib import Path
from ..base import BasePackager


class RPMPackager(BasePackager):
    """RPM 打包器"""
    
    def get_supported_formats(self) -> List[str]:
        """获取支持的打包格式"""
        return ["rpm"]
    
    def can_package_format(self, format_type: str) -> bool:
        """检查是否支持指定格式"""
        return format_type in self.get_supported_formats()
    
    def package(self, format_type: str, source_path: Path, output_path: Path) -> bool:
        """
        执行RPM打包
        
        Args:
            format_type: 打包格式 (rpm)
            source_path: PyInstaller生成的应用路径
            output_path: 输出RPM文件路径
            
        Returns:
            bool: 打包是否成功
        """
        if not self.can_package_format(format_type):
            self.progress.on_error(
                Exception(f"不支持的格式: {format_type}"),
                "Linux RPM打包"
            )
            return False
        
        # 获取RPM配置
        rpm_config = self.get_format_config("rpm")
        
        # 创建临时构建目录
        with tempfile.TemporaryDirectory() as temp_dir:
            build_root = Path(temp_dir)
            
            # 创建RPM构建目录结构
            rpmbuild_dir = build_root / "rpmbuild"
            for subdir in ["BUILD", "RPMS", "SOURCES", "SPECS", "SRPMS"]:
                (rpmbuild_dir / subdir).mkdir(parents=True)
            
            # 准备源文件
            sources_dir = rpmbuild_dir / "SOURCES"
            self._prepare_sources(source_path, sources_dir, rpm_config)
            
            # 创建spec文件
            spec_file = rpmbuild_dir / "SPECS" / f"{self.config.get('name', 'myapp')}.spec"
            self._create_spec_file(spec_file, rpm_config, sources_dir)
            
            # 构建RPM包
            success = self._build_rpm_package(rpmbuild_dir, spec_file, output_path)
            
            return success
    
    def _prepare_sources(self, source_path: Path, sources_dir: Path, config: Dict[str, Any]):
        """准备源文件"""
        app_name = self.config.get('name', 'myapp')
        version = self.config.get('version', '1.0.0')
        
        # 创建源码目录
        source_tarball = sources_dir / f"{app_name}-{version}.tar.gz"
        
        # 创建临时目录用于打包
        with tempfile.TemporaryDirectory() as temp_source_dir:
            app_source_dir = Path(temp_source_dir) / f"{app_name}-{version}"
            app_source_dir.mkdir()
            
            if source_path.is_file():
                # 单个可执行文件
                shutil.copy2(source_path, app_source_dir / app_name)
            else:
                # 目录 - 复制所有内容
                for item in source_path.iterdir():
                    if item.is_file():
                        shutil.copy2(item, app_source_dir)
                    else:
                        shutil.copytree(item, app_source_dir / item.name)
            
            # 创建tar.gz文件
            import tarfile
            with tarfile.open(source_tarball, "w:gz") as tar:
                tar.add(app_source_dir, arcname=f"{app_name}-{version}")
        
        # 复制其他源文件
        extra_sources = config.get('extra_sources', [])
        for extra_source in extra_sources:
            if os.path.exists(extra_source):
                shutil.copy2(extra_source, sources_dir)
    
    def _create_spec_file(self, spec_file: Path, config: Dict[str, Any], sources_dir: Path):
        """创建RPM spec文件"""
        app_name = self.config.get('name', 'myapp')
        version = self.config.get('version', '1.0.0')
        release = config.get('release', '1')
        
        # 获取架构信息
        import platform
        arch = platform.machine()
        if arch == "x86_64":
            arch = "x86_64"
        elif arch.startswith("arm"):
            arch = "aarch64" if "64" in arch else "armv7hl"
        
        spec_content = f"""Name:           {app_name}
Version:        {version}
Release:        {release}%{{?dist}}
Summary:        {config.get('summary', self.config.get('display_name', app_name))}

License:        {config.get('license', 'Unknown')}
URL:            {config.get('url', '')}
Source0:        %{{name}}-%{{version}}.tar.gz

BuildArch:      {arch}
"""
        
        # 添加依赖
        requires = config.get('requires', [])
        if requires:
            for req in requires:
                spec_content += f"Requires:       {req}\n"
        
        build_requires = config.get('build_requires', [])
        if build_requires:
            for req in build_requires:
                spec_content += f"BuildRequires:  {req}\n"
        
        # 描述部分
        spec_content += f"""
%description
{config.get('description', self.config.get('display_name', app_name))}

%prep
%setup -q

%build
# 不需要编译步骤，因为我们使用的是预编译的二进制文件

%install
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/opt/{app_name}
mkdir -p $RPM_BUILD_ROOT/usr/local/bin
"""
        
        # 安装文件
        spec_content += f"""
# 复制应用文件
cp -r * $RPM_BUILD_ROOT/opt/{app_name}/

# 创建启动脚本
cat > $RPM_BUILD_ROOT/usr/local/bin/{app_name} << 'EOF'
#!/bin/bash
cd /opt/{app_name}
exec ./{app_name} "$@"
EOF
chmod +x $RPM_BUILD_ROOT/usr/local/bin/{app_name}
"""
        
        # 桌面文件
        if config.get('create_desktop_file', True):
            spec_content += f"""
# 创建桌面文件
mkdir -p $RPM_BUILD_ROOT/usr/share/applications
cat > $RPM_BUILD_ROOT/usr/share/applications/{app_name}.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name={self.config.get('display_name', app_name)}
Exec={app_name}
Icon={app_name}
Comment={config.get('description', self.config.get('display_name', app_name))}
Categories={config.get('categories', 'Utility;')}
Terminal={str(config.get('terminal', False)).lower()}
EOF
"""
        
        # 图标文件
        icon_path = config.get('icon') or self.config.get('icon')
        if icon_path and os.path.exists(icon_path):
            icon_ext = Path(icon_path).suffix
            spec_content += f"""
# 复制图标文件
mkdir -p $RPM_BUILD_ROOT/usr/share/pixmaps
cp {sources_dir / Path(icon_path).name} $RPM_BUILD_ROOT/usr/share/pixmaps/{app_name}{icon_ext}
"""
        
        # 文件列表
        spec_content += f"""
%files
%defattr(-,root,root,-)
/opt/{app_name}/*
/usr/local/bin/{app_name}
"""
        
        if config.get('create_desktop_file', True):
            spec_content += f"/usr/share/applications/{app_name}.desktop\n"
        
        if icon_path and os.path.exists(icon_path):
            icon_ext = Path(icon_path).suffix
            spec_content += f"/usr/share/pixmaps/{app_name}{icon_ext}\n"
        
        # 脚本部分
        scripts = ['pre', 'post', 'preun', 'postun']
        for script in scripts:
            script_content = config.get(f'{script}_script')
            if script_content:
                spec_content += f"""
%{script}
{script_content}
"""
        
        # 变更日志
        spec_content += f"""
%changelog
* {self._get_current_date()} {config.get('packager', 'Unknown <unknown@example.com>')} - {version}-{release}
- Initial package
"""
        
        # 写入spec文件
        with open(spec_file, 'w') as f:
            f.write(spec_content)
    
    def _get_current_date(self) -> str:
        """获取当前日期（RPM格式）"""
        import datetime
        import locale
        
        try:
            # 设置为英文locale以确保日期格式正确
            locale.setlocale(locale.LC_TIME, 'C')
        except:
            pass
        
        return datetime.datetime.now().strftime("%a %b %d %Y")
    
    def _build_rpm_package(self, rpmbuild_dir: Path, spec_file: Path, output_path: Path) -> bool:
        """构建RPM包"""
        # 设置环境变量
        env = os.environ.copy()
        env['HOME'] = str(rpmbuild_dir.parent)
        
        # 构建命令
        command = [
            'rpmbuild',
            '--define', f'_topdir {rpmbuild_dir}',
            '-bb',
            str(spec_file)
        ]
        
        success = self.runner.run_command(
            command,
            "Linux RPM打包",
            "正在构建RPM包...",
            80,
            shell=False
        )
        
        if success:
            # 查找生成的RPM文件
            rpms_dir = rpmbuild_dir / "RPMS"
            rpm_files = list(rpms_dir.rglob("*.rpm"))
            
            if rpm_files:
                # 复制到输出位置
                shutil.copy2(rpm_files[0], output_path)
                return True
            else:
                self.progress.on_error(
                    Exception("未找到生成的RPM文件"),
                    "Linux RPM打包"
                )
                return False
        else:
            return False
    
    def validate_config(self, format_type: str) -> List[str]:
        """验证RPM配置"""
        errors = []
        
        config = self.get_format_config("rpm")
        
        # 检查必需字段
        required_fields = ['summary', 'license']
        for field in required_fields:
            if not config.get(field):
                errors.append(f"RPM配置缺少必需字段: {field}")
        
        # 检查图标文件
        icon_path = config.get('icon') or self.config.get('icon')
        if icon_path and not os.path.exists(icon_path):
            errors.append(f"图标文件不存在: {icon_path}")
        
        # 检查rpmbuild工具
        try:
            import shutil
            if not shutil.which('rpmbuild'):
                errors.append("rpmbuild工具未安装，请安装: sudo yum install rpm-build 或 sudo dnf install rpm-build")
        except:
            errors.append("无法检查rpmbuild工具")
        
        return errors