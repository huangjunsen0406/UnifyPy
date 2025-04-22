#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
创建一个简单的图标文件
此脚本创建一个最小的有效.ico文件供打包工具使用
"""

import os
import argparse


def create_minimal_ico(output_path="app.ico"):
    """
    创建一个最小的有效.ico文件
    
    Args:
        output_path: 输出图标文件路径，默认为当前目录下的app.ico
    """
    # 最小的有效.ico文件数据
    # 包含一个16x16像素，1色深度的图标
    ico_data = bytes([
        0x00, 0x00,           # 保留，必须为0
        0x01, 0x00,           # 图像类型，1=图标(.ICO)，2=光标(.CUR)
        0x01, 0x00,           # 图像数量（1个）
        0x10, 0x10,           # 宽度高度（16x16像素）
        0x01, 0x00,           # 色彩平面数（1）
        0x01, 0x00,           # 每像素位数（1位 = 黑白）
        0x22, 0x00, 0x00, 0x00,  # 图像数据大小（34字节）
        0x16, 0x00, 0x00, 0x00,  # 图像数据偏移量
        
        # BITMAPINFOHEADER （14字节）
        0x28, 0x00, 0x00, 0x00,  # 头大小（40字节）
        0x10, 0x00, 0x00, 0x00,  # 宽度（16像素）
        0x20, 0x00, 0x00, 0x00,  # 高度（32像素）
        0x01, 0x00,           # 色彩平面数
        0x01, 0x00,           # 每像素位数
        0x00, 0x00, 0x00, 0x00,  # 压缩方式
        0x00, 0x00, 0x00, 0x00,  # 图像大小
        0x00, 0x00, 0x00, 0x00,  # 水平分辨率
        0x00, 0x00, 0x00, 0x00,  # 垂直分辨率
        0x02, 0x00, 0x00, 0x00,  # 颜色数（黑白=2）
        0x00, 0x00, 0x00, 0x00,  # 重要颜色数
        
        # 颜色表（8字节）
        0x00, 0x00, 0x00, 0x00,  # 黑色
        0xFF, 0xFF, 0xFF, 0x00,  # 白色
        
        # 图像数据（8字节）
        0xFF, 0xFF, 0x00, 0x00,  # XOR图像
        0xFF, 0xFF, 0x00, 0x00,  # AND图像
    ])
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    # 写入文件
    with open(output_path, "wb") as f:
        f.write(ico_data)
    
    print(f"已创建最小有效图标文件: {os.path.abspath(output_path)}")
    return os.path.abspath(output_path)


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="创建一个简单的图标文件")
    parser.add_argument("--output", default="app.ico", 
                        help="输出文件路径，默认为当前目录下的app.ico")
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_arguments()
    create_minimal_ico(args.output)
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main()) 