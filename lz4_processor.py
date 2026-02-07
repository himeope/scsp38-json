import argparse
import struct
import sys
import os
import lz4.block



def process_file(in_path, out_path, endian='<'):
	written = 0
	with open(in_path, 'rb') as f_in, open(out_path, 'wb') as f_out:
		block_index = 0
		while True:
			hdr = f_in.read(8)
			if not hdr:
				break
			if len(hdr) < 8:
				raise EOFError(f'文件在读取第 {block_index} 个块时遇到不完整的头（长度 {len(hdr)}）')

			decomp_size, comp_len = struct.unpack(endian + 'II', hdr)

			if comp_len == 0:
				# 空块，写入对应长度的空字节
				if decomp_size:
					f_out.write(b'\x00' * decomp_size)
					written += decomp_size
				block_index += 1
				continue

			comp = f_in.read(comp_len)
			if len(comp) < comp_len:
				raise EOFError(f'文件在读取第 {block_index} 个块的数据时不完整（期望 {comp_len}，得到 {len(comp)}）')

			data = lz4.block.decompress(comp, uncompressed_size=decomp_size)

			if len(data) != decomp_size:
				# 仅警告，不立即失败
				sys.stderr.write(f'警告：第 {block_index} 个块解压后的大小为 {len(data)} ，期望 {decomp_size}\n')

			f_out.write(data)
			written += len(data)
			block_index += 1

	return written

def decompress_single_file(file_path, output_dir=None, endian='<'):
	"""解压单个文件"""
	if not os.path.isfile(file_path):
		sys.stderr.write(f'输入文件不存在: {file_path}\n')
		return False

	if output_dir:
		out_path = os.path.join(output_dir, os.path.basename(file_path) + '.decompressed')
	else:
		out_path = file_path + '.decompressed'

	try:
		written = process_file(file_path, out_path, endian=endian)
		print(f'完成，写入 {written} 字节 到: {out_path}\n')
		return True
	except Exception as e:
		sys.stderr.write(f'处理失败: {str(e)}\n')
		return False

def process_folder(folder_path, output_dir=None, endian='<'):
	"""处理文件夹中的所有.scsp文件"""
	scsp_files = []
	for root, dirs, files in os.walk(folder_path):
		for file in files:
			if file.lower().endswith('.scsp'):
				scsp_files.append(os.path.join(root, file))
	
	if not scsp_files:
		print(f'在 {folder_path} 及其子目录中没有找到 .scsp 文件')
		return
	
	print(f'找到 {len(scsp_files)} 个 .scsp 文件，开始解压...')
	
	for file_path in scsp_files:
		print(f'正在处理: {file_path}')
		decompress_single_file(file_path, output_dir, endian)

def handle_path(input_path, output_dir=None, endian='<'):
	"""
	处理输入路径的主要函数，支持文件或文件夹
	可以被其他模块直接调用
	"""
	if os.path.isdir(input_path):
		# 如果输入是文件夹，则处理其中的所有.scsp文件
		process_folder(input_path, output_dir, endian)
	elif os.path.isfile(input_path):
		# 如果输入是文件，则处理单个文件
		decompress_single_file(input_path, output_dir, endian)
	else:
		sys.stderr.write('输入路径不存在: ' + input_path + '\n')
		return False

	return True

def main():
	p = argparse.ArgumentParser(description='处理自定义 8 字节头 + lz4.block 压缩流（前4字节解压大小，次4字节为数据长度）')
	p.add_argument('input', help='输入文件路径或输入文件夹路径')
	p.add_argument('-o', '--output', help='输出文件夹路径（可选），默认在原位置添加 .decompressed 后缀')
	p.add_argument('--big-endian', action='store_true', help='如果头使用大端字节序，请使用此选项（默认小端）')
	args = p.parse_args()

	input_path = args.input
	output_dir = args.output
	endian = '>' if args.big_endian else '<'
	
	handle_path(input_path, output_dir, endian)


if __name__ == '__main__':
	main()