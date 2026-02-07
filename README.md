# 项目说明
[中文](README.md) | [English](README.en.md)
- 支持版本号为 3.8.xx.scsp 的 SCSP 文件转换为 JSON 文件
- 支持游戏：《卡厄思梦境》 (lz4压缩)
- 理论上其他游戏的 SCSP 3.8.xx.scsp 版本，但是游戏的加密和压缩方式可能不太一样，这里需要先自行处理解密和解压 SCSP 文件
- 转换过程无报错，结果通常是有效的，但仍可能存在问题。


# 使用说明

## 安装依赖
```bash
pip install -r requirements.txt
```

## 脚本命令

| 选项 | 描述 | 默认值 |
|------|------|--------|
| `--skip-atlas` | 	跳过 Atlas 文件处理 | 	处理 Atlas 文件 |
| `--lz4` | 启用 LZ4 解压缩功能 | 不处理 |
| `--ext` |	指定要转换的文件扩展名 |scsp |

## 脚本示例
- 基本运行：
  ```bash
  python main.py <需要处理 SCSP 的文件夹路径>
  ```
- 处理 《卡厄思梦境》(lz4压缩)
  ```bash
  python main.py <需要处理 SCSP 的文件夹路径> --lz4 --ext decompressed
  ```

## 脚本说明
- **lz4_processor.py**：解压使用lz4压缩的 SCSP 文件。
- **scsp_dec_to_json.py**：将解压后的 scsp.decompressed 文件转换成 JSON。
- **replace_sct_with_png.py**：将 Atlas 纹理文件的扩展名从 SCT 改为 PNG。

## 免责声明
请不要将转换的文件用于任何商业或非法用途，仅供交流学习使用。

## 感谢
感谢以下项目或帖子提供的参考：
- Live2DHub 网友 [d-miracle](https://live2dhub.com/u/d-miracle/summary) 的帖子：[解压 SCSP 文件思路](https://live2dhub.com/t/topic/4283/2)
- Live2DHub 网友 [evildebugger](https://live2dhub.com/t/topic/4283/17) 的代码：[SCSP 解析思路（字串常量池、skeleton、bones、slots）](https://live2dhub.com/t/topic/4283/17)
- 现有 JSON 文件作者的转换结果参考
- [wang606/SpineSkeletonDataConverter](https://github.com/wang606/SpineSkeletonDataConverter)：Spine Skel读取参考。
- [Spine 官方说明](http://zh.esotericsoftware.com/spine-json-format)：Spine 二进制 格式
- [CeciliaBot/EpicSevenAssetRipper](https://github.com/CeciliaBot/EpicSevenAssetRipper)：游戏解包工具
- [ww-rm/SpineViewer](https://github.com/ww-rm/SpineViewer)：Spine 文件查看器
