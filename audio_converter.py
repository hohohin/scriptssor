#!/usr/bin/env python3
"""
ScriptSor Audio Converter - 本地音频转换插件
将视频文件转换为WAV格式，减少云端处理负载

使用方法:
python audio_converter.py input_video.mp4
"""

import os
import sys
import argparse
import tempfile
import shutil
from pathlib import Path
import subprocess
import json
import platform


class AudioConverter:
    """音频转换器 - 本地将视频转换为WAV"""
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp(prefix="scriptsor_converter_")
        self.supported_formats = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']
        
    def __del__(self):
        """清理临时目录"""
        try:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except:
            pass
    
    def check_dependencies(self):
        """检查依赖项"""
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("错误: 未找到FFmpeg")
            print("请先安装FFmpeg:")
            if platform.system() == "Windows":
                print("  1. 下载FFmpeg: https://ffmpeg.org/download.html")
                print("  2. 添加到系统PATH")
            elif platform.system() == "Darwin":  # macOS
                print("  brew install ffmpeg")
            else:  # Linux
                print("  sudo apt-get install ffmpeg")
            return False
    
    def convert_video_to_wav(self, video_path: str) -> str:
        """将视频文件转换为WAV格式"""
        video_path = Path(video_path)
        
        if not video_path.exists():
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        if video_path.suffix.lower() not in self.supported_formats:
            raise ValueError(f"不支持的视频格式: {video_path.suffix}")
        
        # 生成输出WAV文件路径
        output_path = self.temp_dir / f"{video_path.stem}_converted.wav"
        
        try:
            print(f"正在处理: {video_path.name}")
            print(f"输出文件: {output_path.name}")
            
            # 获取视频信息
            probe_cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format',
                str(video_path)
            ]
            
            try:
                result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
                video_info = json.loads(result.stdout)
                duration = float(video_info['format']['duration'])
                size = int(video_info['format']['size'])
                
                print(f"视频时长: {duration:.1f}秒")
                print(f"视频大小: {size / (1024*1024):.1f}MB")
            except:
                print("无法获取视频信息，继续转换...")
            
            # 转换为WAV (16kHz, 单声道, 16bit)
            cmd = [
                'ffmpeg',
                '-i', str(video_path),
                '-vn',                    # 禁用视频
                '-acodec', 'pcm_s16le',   # 16-bit PCM
                '-ar', '16000',           # 采样率 16kHz
                '-ac', '1',               # 单声道
                '-y',                     # 覆盖输出文件
                str(output_path)
            ]
            
            print("开始转换音频...")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"FFmpeg错误: {result.stderr}")
                raise RuntimeError("音频转换失败")
            
            # 检查输出文件
            if not output_path.exists():
                raise FileNotFoundError("音频文件生成失败")
            
            output_size = output_path.stat().st_size
            print(f"转换完成!")
            print(f"音频文件大小: {output_size / (1024*1024):.1f}MB")
            print(f"压缩率: {output_size / size * 100:.1f}%")
            
            return str(output_path)
            
        except Exception as e:
            print(f"转换失败: {e}")
            raise
    
    def get_file_info(self, file_path: str) -> dict:
        """获取文件信息"""
        path = Path(file_path)
        if not path.exists():
            return {}
        
        stat = path.stat()
        return {
            'name': path.name,
            'size': stat.st_size,
            'size_mb': round(stat.st_size / (1024 * 1024), 2),
            'extension': path.suffix.lower()
        }


def main():
    parser = argparse.ArgumentParser(description='ScriptSor 音频转换器')
    parser.add_argument('input', help='输入视频文件路径')
    parser.add_argument('--info', action='store_true', help='只显示文件信息，不转换')
    parser.add_argument('--output', '-o', help='指定输出路径')
    
    args = parser.parse_args()
    
    # 检查依赖项
    converter = AudioConverter()
    if not converter.check_dependencies():
        sys.exit(1)
    
    input_path = Path(args.input)
    
    # 显示文件信息
    file_info = converter.get_file_info(args.input)
    if not file_info:
        print(f"错误: 无法读取文件 {args.input}")
        sys.exit(1)
    
    print(f"输入文件: {file_info['name']}")
    print(f"文件大小: {file_info['size_mb']:.1f}MB")
    print(f"文件格式: {file_info['extension']}")
    
    if args.info:
        return
    
    try:
        # 转换音频
        wav_path = converter.convert_video_to_wav(args.input)
        
        # 如果指定了输出路径，复制文件
        if args.output:
            output_path = Path(args.output)
            shutil.copy2(wav_path, output_path)
            print(f"文件已保存到: {output_path}")
        else:
            print(f"音频文件位置: {wav_path}")
            print("请将此WAV文件上传到 ScriptSor 网页版进行处理")
        
        # 询问是否打开文件管理器
        if not args.output:
            try:
                if platform.system() == "Windows":
                    os.startfile(converter.temp_dir)
                elif platform.system() == "Darwin":
                    subprocess.run(['open', converter.temp_dir])
                else:
                    subprocess.run(['xdg-open', converter.temp_dir])
                print("已打开文件管理器")
            except:
                print(f"音频文件位于: {converter.temp_dir}")
        
    except KeyboardInterrupt:
        print("\n用户中断操作")
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()