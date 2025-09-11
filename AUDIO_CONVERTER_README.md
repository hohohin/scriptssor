# ScriptSor 音频转换插件

## 概述

ScriptSor 音频转换插件是一个本地工具，可以将视频文件转换为WAV格式，显著减少云端处理时间和服务器资源消耗。

## 优势

- 🚀 **减少上传时间** - 只上传音频文件，比完整视频小80-90%
- 💰 **节省成本** - 减少服务器带宽和存储成本
- 🔒 **保护隐私** - 视频文件不离开你的电脑
- ⚡ **快速处理** - 本地转换，云端专注语音识别

## 安装要求

### 系统要求
- Windows 10/11, macOS 10.14+, 或 Linux
- Python 3.7+
- FFmpeg

### 安装 FFmpeg

#### Windows
1. 下载FFmpeg: [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
2. 解压到 `C:\ffmpeg\`
3. 添加到系统PATH:
   - 右键"此电脑" → 属性 → 高级系统设置 → 环境变量
   - 在"系统变量"中找到Path，添加 `C:\ffmpeg\bin`

#### macOS
```bash
brew install ffmpeg
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

## 使用方法

### 基本用法
```bash
python audio_converter.py your_video.mp4
```

### 高级选项
```bash
# 只显示文件信息，不转换
python audio_converter.py your_video.mp4 --info

# 指定输出路径
python audio_converter.py your_video.mp4 -o output.wav

# 显示帮助
python audio_converter.py --help
```

## 工作流程

1. **准备视频** - 选择要处理的视频文件
2. **本地转换** - 运行插件转换为WAV格式
3. **上传音频** - 在ScriptSor网页版上传WAV文件
4. **云端处理** - 语音识别和文本编辑
5. **导出结果** - 下载处理后的视频

## 支持的格式

- **视频格式**: MP4, AVI, MOV, MKV, WMV, FLV, WebM
- **输出格式**: WAV (16kHz, 单声道, 16-bit)

## 文件大小对比

| 视频类型 | 原始大小 | WAV音频大小 | 压缩率 |
|----------|----------|------------|--------|
| 1080p MP4 (5分钟) | ~150MB | ~15MB | 90% |
| 720p MP4 (10分钟) | ~200MB | ~20MB | 90% |
| 4K MP4 (2分钟) | ~300MB | ~30MB | 90% |

## 故障排除

### FFmpeg 未找到
```
错误: 未找到FFmpeg
```
**解决方案**: 确保FFmpeg已正确安装并添加到系统PATH

### 转换失败
```
转换失败: [错误信息]
```
**解决方案**:
- 检查视频文件是否损坏
- 确认视频格式受支持
- 尝试重新安装FFmpeg

### 内存不足
```
ffmpeg: error while decoding
```
**解决方案**:
- 尝试处理较小的视频文件
- 关闭其他占用内存的程序

## 性能优化

### 大文件处理
对于大视频文件（>1GB）：
1. 先分段处理视频
2. 分别转换每段
3. 在ScriptSor中合并处理

### 批量处理
```bash
# 批量转换多个文件
for file in *.mp4; do
    python audio_converter.py "$file"
done
```

## 安全性

- ✅ **本地处理** - 视频文件不上传到云端
- ✅ **无数据收集** - 插件不收集任何用户数据
- ✅ **开源透明** - 代码完全开源，可审计
- ✅ **无网络连接** - 插件完全离线工作

## 技术支持

如果遇到问题：
1. 检查本README的故障排除部分
2. 确认系统满足所有要求
3. 查看控制台输出的错误信息
4. 在GitHub Issues中报告问题

## 更新日志

### v1.0.0
- 初始版本发布
- 支持主流视频格式转换
- 跨平台支持
- 详细的使用说明