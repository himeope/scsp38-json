import argparse
import sys
import os
import lz4_processor
import scsp_dec_to_json
import replace_sct_with_png


def main_process(dir_path, skip_atlas=False, lz4=False, extension='scsp'):
    """
    主要处理流程函数
    
    Args:
        dir_path (str): 处理目录路径
        skip_atlas (bool): 是否跳过atlas文件处理，默认为False
        lz4_only (bool): 是否仅处理LZ4解压，默认为False
        extension (str): 要转换的文件扩展名，默认为.scsp
    """
    print(f"开始处理目录: {dir_path}")
    
    if not skip_atlas:
        print("正在处理 Atlas 文件...")
        replace_sct_with_png.scan_and_process_atlas_files(dir_path)
    else:
        print("跳过 Atlas 文件处理")
        
    # 检查目录是否存在
    if not os.path.isdir(dir_path):
        raise ValueError(f"指定的目录不存在: {dir_path}")
    
    # 执行处理步骤
    
    if lz4:
        print("正在处理 LZ4 压缩文件...")
        lz4_processor.process_folder(dir_path)
        extension = 'decompressed'  # LZ4处理后文件扩展名

    
    print("正在批量转换解压文件...")
    scsp_dec_to_json.batch_convert_decompressed_files(dir_path, extension)
    
    print("处理完成！")


def main():
    parser = argparse.ArgumentParser(
        description='处理 Scsp 文件的工具集',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        'directory',
        nargs='?',
        default=os.getcwd(),
        help='要处理的目录路径 (默认为当前工作目录)'
    )
    parser.add_argument(
        '--skip-atlas',
        action='store_true',
        help='跳过 Atlas 文件处理 (默认为处理Atlas文件)'
    )
    parser.add_argument(
        '--lz4',
        action='store_true',
        help='LZ4 解压缩 (默认为不处理流程)'
    )
    parser.add_argument(
        '--ext',
        type=str,
        default='scsp',
        dest='extension',
        help='要转换的文件扩展名 (默认为 scsp)'
    )
    # parser.add_argument(
    #     '-v', '--verbose',
    #     action='store_true',
    #     help='显示详细处理信息'
    # )
    
    args = parser.parse_args()
    
    try:
        main_process(args.directory, skip_atlas=args.skip_atlas, lz4=args.lz4, extension=args.extension)
    except Exception as e:
        print(f"处理过程中发生错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()