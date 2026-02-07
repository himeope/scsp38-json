# Project Description
[Chinese](README.md) | [English](README.en.md)
- Supports conversion of SCSP files with version 3.8.xx.scsp to JSON files
- Supported game: Chaos Zero Nightmare (lz4 compressed)
- In theory, other games with SCSP version 3.8.xx.scsp are also supported, but the encryption and compression methods may vary between games. You may need to handle decryption and decompression of SCSP files yourself.
- The conversion process typically completes without errors and produces valid results, though issues may still occur.


# Instructions for Use

## Install Dependencies
```bash
pip install -r requirements.txt
```

## Script Commands

| Option | Description | Default |
|------|------|--------|
| `--skip-atlas` | Skip Atlas file processing | Process Atlas files |
| `--lz4` | Enable LZ4 decompression feature | Not processed |
| `--ext` | Specify file extension to convert | scsp |

## Script Examples
- Basic run:
  ```bash
  python main.py <folder path of SCSP files to be processed>
  ```
- Processing Chaos Zero Nightmare (lz4 compressed):
  ```bash
  python main.py <folder path of SCSP files to be processed> --lz4 --ext decompressed
  ```

## Script Description
- **lz4_processor.py**: Decompresses SCSP files compressed with lz4.
- **scsp_dec_to_json.py**: Converts decompressed scsp.decompressed files to JSON format.
- **replace_sct_with_png.py**: Changes the file extension of Atlas texture files from SCT to PNG.

## Disclaimer
Do not use the converted files for any commercial or illegal purposes, only for educational and exchange purposes.

## Acknowledgments
Thanks to the following projects or posts for providing references:
- Live2DHub user [d-miracle](https://live2dhub.com/u/d-miracle/summary)'s post: [Decompressing SCSP Files Approach](https://live2dhub.com/t/topic/4283/2)
- Live2DHub user [evildebugger](https://live2dhub.com/t/topic/4283/17)'s code: [SCSP Parsing Approach (String Constant Pool, skeleton, bones, slots)](https://live2dhub.com/t/topic/4283/17)
- Reference from existing JSON file authors' conversion results
- [wang606/SpineSkeletonDataConverter](https://github.com/wang606/SpineSkeletonDataConverter): Reference for Spine Skel reader.
- [Spine Official Documentation](http://zh.esotericsoftware.com/spine-json-format): Spine Binary Format
- [CeciliaBot/EpicSevenAssetRipper](https://github.com/CeciliaBot/EpicSevenAssetRipper): Game unpacking tool
- [ww-rm/SpineViewer](https://github.com/ww-rm/SpineViewer): Spine file viewer