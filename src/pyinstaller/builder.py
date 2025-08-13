#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PyInstaller构建器
执行PyInstaller打包过程
"""

import os
import sys
from typing import Dict, Any, List, Optional
from pathlib import Path
from .config_builder import PyInstallerConfigBuilder


class PyInstallerBuilder:
    """PyInstaller构建器"""
    
    def __init__(self, project_dir: str, config_builder: Optional[PyInstallerConfigBuilder] = None):
        """
        初始化构建器
        
        Args:
            project_dir: 项目目录
            config_builder: 配置构建器实例
        """
        self.project_dir = Path(project_dir).resolve()
        self.config_builder = config_builder or PyInstallerConfigBuilder()
    
    def build(self, config: Dict[str, Any], entry_script: str) -> bool:
        """
        执行PyInstaller构建
        
        Args:
            config: PyInstaller配置
            entry_script: 入口脚本路径
            
        Returns:
            bool: 构建是否成功
        """
        # 验证配置
        errors = self.config_builder.validate_config(config)
        if errors:
            raise ValueError(f"配置验证失败: {'; '.join(errors)}")
        
        # 构建命令
        command = self.config_builder.build_command(config, entry_script)
        
        # 执行构建
        return self._execute_pyinstaller(command)
    
    def build_with_spec(self, spec_file: str) -> bool:
        """
        使用spec文件构建
        
        Args:
            spec_file: spec文件路径
            
        Returns:
            bool: 构建是否成功
        """
        command = ['pyinstaller', spec_file]
        return self._execute_pyinstaller(command)
    
    def generate_spec_file(self, config: Dict[str, Any], entry_script: str, output_path: str):
        """
        生成spec文件
        
        Args:
            config: PyInstaller配置
            entry_script: 入口脚本路径
            output_path: 输出路径
        """
        spec_content = self.config_builder.build_spec_file_content(config, entry_script)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(spec_content)
    
    def _execute_pyinstaller(self, command: List[str]) -> bool:
        """
        执行PyInstaller命令
        
        Args:
            command: 命令列表
            
        Returns:
            bool: 执行是否成功
        """
        import subprocess
        
        try:
            # 在项目目录中执行
            original_cwd = os.getcwd()
            os.chdir(str(self.project_dir))
            
            # 执行命令
            result = subprocess.run(command, check=False)
            
            return result.returncode == 0
            
        except Exception:
            return False
        finally:
            os.chdir(original_cwd)
    
    def get_output_path(self, config: Dict[str, Any], app_name: str) -> Path:
        """
        获取输出路径
        
        Args:
            config: PyInstaller配置
            app_name: 应用名称
            
        Returns:
            Path: 输出路径
        """
        dist_path = Path(config.get('distpath', self.project_dir / 'dist'))
        
        if config.get('onefile'):
            # 单文件模式
            executable_name = app_name
            if sys.platform == 'win32':
                executable_name += '.exe'
            return dist_path / executable_name
        else:
            # 目录模式
            return dist_path / app_name
    
    def cleanup_build_files(self, config: Dict[str, Any]):
        """
        清理构建文件
        
        Args:
            config: PyInstaller配置
        """
        import shutil
        
        # 清理work目录
        work_path = Path(config.get('workpath', self.project_dir / 'build'))
        if work_path.exists():
            shutil.rmtree(work_path)
        
        # 清理spec文件（如果是自动生成的）
        spec_files = list(self.project_dir.glob('*.spec'))
        for spec_file in spec_files:
            if spec_file.stem in config.get('name', ''):
                spec_file.unlink()