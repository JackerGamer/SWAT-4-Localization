# SWAT 4 简体中文本地化

本仓库用于维护《SWAT 4》及其资料片《The Stetchkov Syndicate》的简体中文本地化资源，并提供游戏字体的生成配置与辅助脚本。

仓库同时保留英文原文和繁体中文文本，便于翻译、校对及术语对照；实际维护目标位于 `Simplified Chinese/`。

## 目录结构

| 路径 | 说明 |
| --- | --- |
| `English/` | 英文本地化原文（`.int`） |
| `Traditional Chinese/` | 繁体中文参考文本（`.tch`） |
| `Simplified Chinese/` | 简体中文本地化文本（`.sch`） |
| `Simplified Chinese/Maps/` | 原版任务和多人地图文本 |
| `Simplified Chinese/MapsExpansion/` | 资料片任务和多人地图文本 |
| `Specifications.md` | 统一的人名、装备、战术指令及界面术语 |
| `Fonts/` | 字体资源及生成后的游戏用字体 |
| `build_pix_fonts.py` | 生成 `Pix`、`PixBd` 和 `Swat` 字体的脚本 |
| `SimplifiedChineseFonts.exec` | 供 Unreal Commandlet 使用的字体包生成宏 |
| `ConvertFonts.bat` | 调用 `ucc execmacro` 生成字体包 |

## 使用说明

1. 备份游戏原始文件。
2. 将 `Simplified Chinese/` 中的 `.sch` 文件复制到游戏对应的本地化目录，并保持原有子目录结构。
3. 准备简体中文字体包 `SwatFonts.sch_utx`，并放入游戏的 `Textures` 目录。
4. 将游戏的语言代码设置为 `sch`。配置文件位置可能因游戏版本和安装方式而异。

本仓库不包含自动安装程序。覆盖文件前请确认目标路径与当前游戏版本相符。

## 生成字体

### 环境要求

- Windows
- Python 3
- [`fonttools`](https://github.com/fonttools/fonttools)
- 当前用户字体目录中可用的 MiSans 字体文件
- 可以运行 `ucc` 的 SWAT 4 工具环境

安装 Python 依赖并生成字体：

```powershell
py -m pip install fonttools
py build_pix_fonts.py
```

脚本默认读取当前用户字体目录中的以下字体：

- `%LOCALAPPDATA%\Microsoft\Windows\Fonts\MiSans-Regular.ttf`
- `%LOCALAPPDATA%\Microsoft\Windows\Fonts\MiSans-Demibold.ttf`
- `%LOCALAPPDATA%\Microsoft\Windows\Fonts\MiSans-Bold.ttf`

生成结果位于 `Fonts/`。随后确保宏中引用的字体名称可被系统识别，并在可调用 `ucc` 的环境中运行：

```powershell
ConvertFonts.bat
```

`SimplifiedChineseFonts.exec` 默认将字体包输出到 `..\Textures\SwatFonts.sch_utx`。请根据实际工具目录调整运行位置。

## 翻译与编辑

本地化风格指南在 [`STYLE_GUIDE.md`](STYLE_GUIDE.md) 中。编辑 `.sch` 文件时还应注意：

- 保持 UTF-16 编码，不要擅自转换格式。
- 修改后检查界面长度、字幕时序以及任务语境。

## 字体与第三方资源

游戏名称、原始文本及相关资源的权利归各自权利人所有。提交或分发字体文件前，请确认相应字体许可证允许该用途。
