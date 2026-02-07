#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量处理atlas文件：读取第二行并将sct扩展名替换为png
"""

import os
import glob
import argparse
import json


def process_atlas_file(file_path):
    """
    处理单个atlas文件：读取第二行并将sct扩展名替换为png
    """
    try:
        # 读取文件的所有行
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        if len(lines) < 2:
            print(f"警告: {file_path} 行数少于2行，跳过处理")
            return False

        # 获取第二行内容
        second_line = lines[1]

        # 检查第二行是否包含.sct
        if '.sct' in second_line:
            # 替换.sct为.png
            new_second_line = second_line.replace('.sct', '.png')
            
            # 更新lines列表
            lines[1] = new_second_line
            
            # 写回文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
                
            print(f"已处理: {file_path}, 将 '{second_line.strip()}' 替换为 '{new_second_line.strip()}'")
            return True
        else:
            # 检查是否已经是.png，如果是则跳过
            if '.png' in second_line:
                print(f"跳过: {file_path}, 第二行已是.png扩展名")
            else:
                print(f"跳过: {file_path}, 第二行不含.sct扩展名")
            return False

    except Exception as e:
        print(f"处理文件 {file_path} 时出错: {str(e)}")
        return False


def scan_and_process_atlas_files(folder_path):
    """
    扫描指定文件夹中的所有atlas文件并处理
    """
    # 构建搜索模式，查找所有.atlas文件
    atlas_pattern = os.path.join(folder_path, "*.atlas")
    
    # 获取所有atlas文件
    atlas_files = glob.glob(atlas_pattern)
    
    # 还可能有子目录中的atlas文件，使用递归查找
    recursive_pattern = os.path.join(folder_path, "**", "*.atlas")
    atlas_files.extend(glob.glob(recursive_pattern, recursive=True))
    
    # 去重，防止重复添加
    atlas_files = list(set(atlas_files))
    
    if not atlas_files:
        print(f"在 {folder_path} 中未找到任何.atlas文件")
        return

    print(f"找到 {len(atlas_files)} 个.atlas文件，开始处理...")
    
    processed_count = 0
    for atlas_file in atlas_files:
        if process_atlas_file(atlas_file):
            processed_count += 1
    
    print(f"处理完成！共处理了 {processed_count} 个文件\n")


def mod(folder_path=None):
    """
    主函数，支持传入路径参数，如果未传入则提示用户输入
    """
    if folder_path is None:
        # 获取用户输入的文件夹路径
        folder_path = input("请输入要扫描的文件夹路径: ").strip().strip('"\'')
    else:
        # 如果通过命令行传入，则去除首尾的引号
        folder_path = folder_path.strip().strip('"\'')
    
    # 检查文件夹是否存在
    if not os.path.isdir(folder_path):
        print(f"错误: 文件夹 {folder_path} 不存在!")
        return False
    
    scan_and_process_atlas_files(folder_path)
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='批量处理atlas文件：将第二行的sct扩展名替换为png')
    parser.add_argument('folder_path', nargs='?', help='要扫描的文件夹路径')
    args = parser.parse_args()
    
    mod(args.folder_path)