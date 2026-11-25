# SWAT 4 简体中文本地化

本仓库维护《SWAT 4》及其资料片《The Stetchkov Syndicate》的简体中文本地化文本，并提供生成游戏中文字体包所需的脚本与配置。

仓库同时保留英文原文和繁体中文文本，便于翻译、校对及术语对照；实际维护目标是 `Simplified Chinese/`。

## 目录结构

| 路径 | 说明 |
| --- | --- |
| `English/` | 英文原文（`.int`），翻译依据 |
| `Traditional Chinese/` | 繁体中文参考文本（`.tch`），仅供对照 |
| `Simplified Chinese/` | 简体中文本地化文本（`.sch`） |
| `Simplified Chinese/Maps/` | 原版任务和多人地图文本 |
| `Simplified Chinese/MapsExpansion/` | 资料片任务和多人地图文本 |
| `STYLE_GUIDE.md` | 本地化风格指南：人名、装备、战术指令及界面术语 |
| `build_pix_fonts.py` | 由 MiSans 生成 `Pix`、`PixBd`、`Swat` 字体的脚本 |
| `SimplifiedChineseFonts.exec` | 供 Unreal Commandlet 使用的字体包生成宏 |
| `ConvertFonts.bat` | 调用 `ucc execmacro` 生成字体包 |

## 安装

1. 备份游戏原始文件。
2. 将 `Simplified Chinese/` 中的 `.sch` 文件复制到游戏对应的本地化目录，保持原有子目录结构（`Maps/`、`MapsExpansion/`）。
3. 按下文「生成字体」制作简体中文字体包 `SwatFonts.sch_utx`，放入游戏的 `Textures` 目录。
4. 将游戏的语言代码设置为 `sch`。配置文件位置可能因游戏版本和安装方式而异。

本仓库不包含自动安装程序，也不提供字体文件。覆盖文件前请确认目标路径与当前游戏版本相符。

## 生成字体

出于许可原因，仓库不包含任何字体文件。生成的字体及第三方字体均放在本地的 `Fonts/` 目录中，该目录已被 Git 忽略。

### 环境要求

- Windows
- Python 3 与 [`fonttools`](https://github.com/fonttools/fonttools)
- [MiSans](https://hyperos.mi.com/font/) 字体（`MiSans-Regular`、`MiSans-Demibold`、`MiSans-Bold`）
- `DS-Digital` 字体（用于 LCD 数字显示，需自行获取并安装）
- 可以运行 `ucc` 的 SWAT 4 工具环境

### 步骤

```powershell
py -m pip install fonttools
py build_pix_fonts.py
```

脚本默认从当前用户字体目录 `%LOCALAPPDATA%\Microsoft\Windows\Fonts\` 读取 MiSans。若字体在其他位置，可通过环境变量指定：

```powershell
$env:MISANS_DIR = "D:\Fonts\MiSans"; py build_pix_fonts.py
```

脚本会统计 `Simplified Chinese/` 中实际用到的字符，据此调整字形度量，并输出 `Fonts/Pix.ttf`、`Fonts/PixBd.ttf`、`Fonts/Swat.ttf`。

安装生成的字体和 `DS-Digital`，使系统能按名称识别它们，然后在可调用 `ucc` 的目录中运行：

```powershell
.\ConvertFonts.bat
```

`SimplifiedChineseFonts.exec` 默认将字体包输出到 `..\Textures\SwatFonts.sch_utx`，请根据实际工具目录调整运行位置。

## 参与翻译

请先阅读 [`STYLE_GUIDE.md`](STYLE_GUIDE.md)。编辑 `.sch` 文件时请注意：

- 以英文原文为准，繁体中文仅作参考，不要直接转换。
- 保持 UTF-16 LE（带 BOM）编码和 CRLF 换行，不要擅自转换格式。
- 保留标记、占位符、资源路径和配置语法。
- 修改后检查界面长度、字幕时序以及任务语境。
- 新增字符后需重新生成字体，否则游戏中可能显示为空白。

欢迎通过 Issue 报告错译、漏译或显示问题，或直接提交 Pull Request。

## 许可

- 脚本与工具（`build_pix_fonts.py`、`ConvertFonts.bat`、`SimplifiedChineseFonts.exec`）采用 [MIT 许可证](LICENSE)。
- 简体中文译文（`Simplified Chinese/`）与 `STYLE_GUIDE.md` 采用 [CC BY-NC-SA 4.0](LICENSE-TRANSLATIONS)。
- `English/` 与 `Traditional Chinese/` 中的文本来自原版游戏，不适用以上许可，权利归原权利人所有。

《SWAT 4》及《The Stetchkov Syndicate》的名称、商标及原始内容归各自权利人所有。本项目为非官方的玩家社区作品，与相关权利人无关联。
