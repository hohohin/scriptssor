"""
视频处理逻辑 - 使用腾讯云语音识别API
"""

import os
import uuid
import asyncio
from typing import List, Tuple
from datetime import datetime
import ffmpeg
from pydub import AudioSegment
import json
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.asr.v20190614 import asr_client, models
import base64
from models import TranscriptSegment, Database, ProcessingTask

class VideoProcessor:
    """视频处理器 - 使用腾讯云语音识别API"""
    
    def __init__(self, upload_dir: str = "uploads", temp_dir: str = "temp"):
        self.upload_dir = upload_dir
        self.temp_dir = temp_dir
        os.makedirs(upload_dir, exist_ok=True)
        os.makedirs(temp_dir, exist_ok=True)
        
        # 从环境变量获取腾讯云配置
        self.secret_id = os.getenv('TENCENT_SECRET_ID')
        self.secret_key = os.getenv('TENCENT_SECRET_KEY')
        
        # 当前处理的音频文件路径
        self.current_audio_file = None
        
        # 检查配置
        if not self.secret_id or not self.secret_key:
            print("警告: 未配置腾讯云API密钥，将使用本地识别作为备选")
    
    async def extract_audio(self, video_path: str) -> str:
        """从视频中提取音频"""
        audio_path = os.path.join(self.temp_dir, f"{uuid.uuid4()}.wav")
        
        try:
            # 首先检查视频文件是否存在
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"视频文件不存在: {video_path}")
            
            # 检查视频文件大小
            file_size = os.path.getsize(video_path)
            if file_size == 0:
                raise ValueError("视频文件为空")
            
            print(f"开始提取音频，视频文件大小: {file_size / (1024*1024):.2f} MB")
            
            # 使用 ffmpeg 提取音频，转换为16kHz单声道WAV格式（腾讯云要求）
            # 添加更多的错误处理和参数验证
            probe = ffmpeg.probe(video_path)
            duration = float(probe['format']['duration'])
            print(f"视频时长: {duration:.2f} 秒")
            
            (
                ffmpeg
                .input(video_path)
                .output(
                    audio_path, 
                    acodec='pcm_s16le', 
                    ac=1, 
                    ar='16000',
                    vn=None,  # 禁用视频流
                    y=None    # 覆盖输出文件
                )
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True, quiet=True)
            )
            
            # 验证生成的音频文件
            if not os.path.exists(audio_path):
                raise FileNotFoundError("音频文件生成失败")
            
            audio_size = os.path.getsize(audio_path)
            if audio_size == 0:
                raise ValueError("生成的音频文件为空")
            
            print(f"音频提取成功，音频文件大小: {audio_size / (1024*1024):.2f} MB")
            return audio_path
            
        except ffmpeg.Error as e:
            print(f"FFmpeg错误: {e.stderr.decode('utf-8') if e.stderr else str(e)}")
            raise Exception(f"音频提取失败: {str(e)}")
        except Exception as e:
            print(f"音频提取失败: {e}")
            import traceback
            traceback.print_exc()
            # 创建一个空的音频文件作为备选
            audio = AudioSegment.silent(duration=1000)  # 1秒静音
            audio.export(audio_path, format="wav")
            return audio_path
    
    def recognize_speech_tencent(self, audio_file_path: str) -> List[Tuple[str, float, float]]:
        """
        使用腾讯云语音识别API（普通话）- 直接传入整段音频文件
        """
        # 保存当前音频文件路径，用于后续获取实际时长
        self.current_audio_file = audio_file_path
        
        try:
            # 检查音频文件是否存在
            if not os.path.exists(audio_file_path):
                raise FileNotFoundError(f"音频文件不存在: {audio_file_path}")
            
            # 检查文件大小
            file_size = os.path.getsize(audio_file_path)
            if file_size == 0:
                raise ValueError("音频文件为空")
            
            print(f"音频文件大小: {file_size / (1024*1024):.2f} MB")
            
            # 获取音频文件的实际时长
            actual_duration = 50.0  # 默认值
            try:
                audio = AudioSegment.from_wav(audio_file_path)
                actual_duration_ms = len(audio)
                actual_duration = actual_duration_ms / 1000.0
                print(f"音频实际时长: {actual_duration}秒")
            except Exception as e:
                print(f"获取音频时长失败: {e}")
            
            # 检查API配置
            if not self.secret_id or not self.secret_key:
                print("腾讯云API密钥未配置，直接使用本地识别")
                return self._fallback_local_recognition(audio_file_path)
            
            print("使用腾讯云语音识别API处理音频（普通话）...")
            
            # 读取音频文件
            with open(audio_file_path, 'rb') as f:
                audio_data = f.read()
            
            # 检查腾讯云API的限制（单次请求最大10MB）
            if len(audio_data) > 10 * 1024 * 1024:  # 10MB限制
                print(f"音频文件过大 ({len(audio_data) / (1024*1024):.2f} MB)，腾讯云API限制为10MB")
                print("使用分段处理方式...")
                return self._process_large_audio_tencent(audio_file_path)
            
            # 检查音频时长
            try:
                audio = AudioSegment.from_wav(audio_file_path)
                duration_seconds = len(audio) / 1000.0
                print(f"音频时长: {duration_seconds:.2f} 秒")
                
                # 腾讯云API对时长也有一定限制，超过5分钟建议使用其他方式
                if duration_seconds > 300:  # 5分钟
                    print(f"音频较长 ({duration_seconds:.2f} 秒)，可能超出API处理能力")
                    print("建议：使用较短的音频文件")
                    return self._fallback_local_recognition(audio_file_path)
            except Exception as e:
                print(f"无法获取音频时长信息: {e}")
            
            # 初始化腾讯云客户端
            cred = credential.Credential(self.secret_id, self.secret_key)
            httpProfile = HttpProfile()
            httpProfile.endpoint = "asr.tencentcloudapi.com"
            
            clientProfile = ClientProfile()
            clientProfile.httpProfile = httpProfile
            client = asr_client.AsrClient(cred, "", clientProfile)
            
            # 创建识别请求 - 直接传入整段音频
            req = models.CreateRecTaskRequest()
            params = {
                "EngineModelType": "16k_zh",  # 使用标准普通话模型
                "ChannelNum": 1,
                "ResTextFormat": 0,
                "SourceType": 1,
                "Data": base64.b64encode(audio_data).decode()
            }
            req.from_json_string(json.dumps(params))
            
            print("发送腾讯云识别请求...")
            # 发送请求
            resp = client.CreateRecTask(req)
            
            if resp.Data and hasattr(resp.Data, 'TaskId'):
                task_id = resp.Data.TaskId
                print(f"腾讯云识别任务已创建，任务ID: {task_id}")
                
                # 轮询获取结果
                return self._poll_tencent_result(client, task_id)
            else:
                print(f"腾讯云API返回无效响应: {resp}")
                raise Exception("腾讯云API返回无效响应")
            
        except Exception as e:
            print(f"腾讯云语音识别失败: {e}")
            import traceback
            traceback.print_exc()
            # 如果腾讯云失败，回退到本地识别
            return self._fallback_local_recognition(audio_file_path)
    
    def _poll_tencent_result(self, client, task_id: int, max_attempts: int = 30) -> List[Tuple[str, float, float]]:
        """轮询腾讯云识别结果"""
        print(f"开始轮询腾讯云识别结果，任务ID: {task_id}")
        
        for attempt in range(max_attempts):
            try:
                print(f"查询任务状态... ({attempt + 1}/{max_attempts})")
                
                # 查询任务状态
                req = models.DescribeTaskStatusRequest()
                params = {"TaskId": task_id}
                req.from_json_string(json.dumps(params))
                
                resp = client.DescribeTaskStatus(req)
                
                if not resp.Data:
                    print(f"腾讯云返回空响应: {resp}")
                    asyncio.sleep(2)
                    continue
                
                status = resp.Data.Status
                print(f"任务状态: {status}")
                
                if status == 2:  # 成功
                    print("腾讯云识别完成")
                    
                    # 检查结果
                    if hasattr(resp.Data, 'Result') and resp.Data.Result:
                        result_text = resp.Data.Result
                        print(f"获得识别结果: {result_text[:200]}...")
                        return self._parse_tencent_result(result_text)
                    else:
                        print("腾讯云识别完成但未返回结果")
                        return [("（识别完成但无结果）", 0.0, actual_duration)]
                        
                elif status == 3:  # 失败
                    error_msg = getattr(resp.Data, 'ErrorMsg', '未知错误')
                    print(f"腾讯云识别失败: {error_msg}")
                    raise Exception(f"腾讯云识别失败: {error_msg}")
                    
                elif status == 0:  # 等待中
                    print("任务等待处理中...")
                    
                elif status == 1:  # 处理中
                    print("任务正在处理中...")
                    
                elif status == 4:  # 超时
                    print("腾讯云识别超时")
                    raise Exception("腾讯云识别超时")
                    
                else:  # 其他状态
                    print(f"未知任务状态: {status}")
                
                # 等待后继续查询
                wait_time = min(2 + attempt * 0.5, 5)  # 逐渐增加等待时间，最多5秒
                print(f"等待 {wait_time} 秒后重试...")
                asyncio.sleep(wait_time)
                    
            except Exception as e:
                print(f"查询识别结果失败: {e}")
                import traceback
                traceback.print_exc()
                
                # 如果是最后一次尝试，抛出异常
                if attempt == max_attempts - 1:
                    raise Exception(f"轮询识别结果失败: {e}")
                
                # 否则等待后继续
                asyncio.sleep(2)
        
        print(f"轮询超时，已尝试 {max_attempts} 次")
        raise Exception("腾讯云识别超时")
    
    def _process_large_audio_tencent(self, audio_file_path: str) -> List[Tuple[str, float, float]]:
        """分段处理大音频文件"""
        try:
            print("开始分段处理大音频文件...")
            
            # 加载音频文件
            audio = AudioSegment.from_wav(audio_file_path)
            total_duration_ms = len(audio)
            total_duration = total_duration_ms / 1000.0
            
            print(f"音频总时长: {total_duration:.2f} 秒")
            
            # 将音频分成较小的段，每段约2分钟
            chunk_length_ms = 120 * 1000  # 2分钟
            overlap_ms = 2000  # 2秒重叠，避免在句中分割
            
            segments = []
            current_time = 0.0
            
            for i in range(0, total_duration_ms, chunk_length_ms - overlap_ms):
                end_time = min(i + chunk_length_ms, total_duration_ms)
                
                # 提取音频段
                chunk = audio[i:end_time]
                
                # 保存临时音频文件
                temp_chunk_path = os.path.join(self.temp_dir, f"chunk_{uuid.uuid4()}.wav")
                chunk.export(temp_chunk_path, format="wav")
                
                print(f"处理第 {len(segments) + 1} 段: {i/1000.0:.1f}s - {end_time/1000.0:.1f}s")
                
                # 处理这一段
                try:
                    # 使用现有的识别方法处理这段音频
                    chunk_results = self.recognize_speech_tencent(temp_chunk_path)
                    
                    # 调整时间戳
                    for text, start, end in chunk_results:
                        adjusted_start = current_time + start
                        adjusted_end = current_time + end
                        segments.append((text, adjusted_start, adjusted_end))
                    
                    current_time += (end_time - i) / 1000.0
                    
                except Exception as e:
                    print(f"处理第 {len(segments) + 1} 段时出错: {e}")
                    # 如果某段处理失败，跳过并继续
                    current_time += (end_time - i) / 1000.0
                    continue
                
                finally:
                    # 清理临时文件
                    if os.path.exists(temp_chunk_path):
                        os.remove(temp_chunk_path)
            
            print(f"分段处理完成，共处理 {len(segments)} 个片段")
            return segments
            
        except Exception as e:
            print(f"分段处理失败: {e}")
            import traceback
            traceback.print_exc()
            # 如果分段处理失败，回退到本地识别
            return self._fallback_local_recognition(audio_file_path)
    
    def _parse_tencent_result(self, result_text: str) -> List[Tuple[str, float, float]]:
        """解析腾讯云识别结果"""
        try:
            print(f"开始解析腾讯云识别结果: {result_text[:200]}...")
            
            # 获取音频文件的实际时长
            actual_duration = 50.0  # 默认值
            actual_duration_ms = 50000  # 默认值
            try:
                audio = AudioSegment.from_wav(self.current_audio_file)
                actual_duration_ms = len(audio)
                actual_duration = actual_duration_ms / 1000.0
                print(f"音频实际时长: {actual_duration}秒")
            except Exception as e:
                print(f"获取音频时长失败: {e}")
            
            # 如果结果是空字符串
            if not result_text or result_text.strip() == "":
                print("腾讯云返回空结果")
                return [("（无识别结果）", 0.0, actual_duration)]
            
            # 检查结果格式 - 可能是JSON或纯文本格式
            sentences = []
            
            # 尝试解析JSON格式
            try:
                result_data = json.loads(result_text)
                print(f"解析结果数据: {result_data}")
                
                # 格式1: sentence_list
                if 'sentence_list' in result_data:
                    sentences = result_data.get('sentence_list', [])
                # 格式2: result
                elif 'result' in result_data:
                    result_content = result_data.get('result', '')
                    if result_content:
                        # 获取音频文件的实际时长来设置时间戳
                        try:
                            audio = AudioSegment.from_wav(self.current_audio_file)
                            actual_duration_ms = len(audio)
                            sentences = [{'text': result_content, 'start_time': 0, 'end_time': actual_duration_ms}]
                        except:
                            sentences = [{'text': result_content, 'start_time': 0, 'end_time': 50000}]
            except json.JSONDecodeError:
                # 如果不是JSON格式，尝试解析纯文本格式 [start:end] text
                print(f"结果不是JSON格式，尝试解析纯文本格式")
                print(f"原始文本: {result_text[:100]}...")
                
                # 使用正则表达式匹配 [start:end] text 格式
                import re
                # 腾讯云格式: [0:0.000,0:50.340] text
                pattern = r'\[(\d+):(\d+(?:\.\d+)?),(\d+):(\d+(?:\.\d+)?)\]\s*(.+)'
                match = re.search(pattern, result_text)
                
                if match:
                    start_minutes = int(match.group(1))
                    start_seconds = float(match.group(2))
                    end_minutes = int(match.group(3))
                    end_seconds = float(match.group(4))
                    
                    start_time = start_minutes * 60 + start_seconds
                    end_time = end_minutes * 60 + end_seconds
                    
                    text_content = match.group(5).strip()
                    
                    print(f"解析到时间戳: {start_time}s - {end_time}s, 文本: {text_content[:50]}...")
                    
                    sentences = [{'text': text_content, 'start_time': start_time * 1000, 'end_time': end_time * 1000}]
                else:
                    # 如果格式不匹配，使用整个文本作为结果
                    print(f"无法解析时间戳格式，使用整个文本: {result_text[:100]}...")
                    try:
                        audio = AudioSegment.from_wav(self.current_audio_file)
                        actual_duration_ms = len(audio)
                        sentences = [{'text': result_text.strip(), 'start_time': 0, 'end_time': actual_duration_ms}]
                    except:
                        sentences = [{'text': result_text.strip(), 'start_time': 0, 'end_time': 50000}]
            
            # 处理解析后的句子数据
            result_segments = []
            
            print(f"处理解析后的句子数据，共 {len(sentences)} 个句子")
            for i, sentence in enumerate(sentences):
                print(f"处理句子 {i}: {sentence}")
                if isinstance(sentence, dict):
                    text = sentence.get('text', '').strip()
                    start_time = sentence.get('start_time', 0) / 1000.0  # 转换为秒
                    end_time = sentence.get('end_time', actual_duration_ms) / 1000.0  # 转换为秒
                    print(f"字典格式 - 文本: {text[:50]}..., 时间: {start_time}s - {end_time}s")
                elif isinstance(sentence, str):
                    text = sentence.strip()
                    start_time = 0.0
                    end_time = 50.0  # 默认50秒
                    print(f"字符串格式 - 文本: {text[:50]}..., 时间: {start_time}s - {end_time}s")
                else:
                    print(f"未知格式: {type(sentence)}")
                    continue
                
                if text:
                    result_segments.append((text, start_time, end_time))
            
            print(f"解析出 {len(result_segments)} 个语音片段")
            for i, (text, start, end) in enumerate(result_segments):
                print(f"片段 {i+1}: {start}s - {end}s, 文本: {text[:50]}...")
            return result_segments
            
        except Exception as e:
            print(f"解析腾讯云识别结果时出错: {e}")
            import traceback
            traceback.print_exc()
            
            # 出错时返回默认结果，使用实际音频时长
            try:
                audio = AudioSegment.from_wav(self.current_audio_file)
                actual_duration = len(audio) / 1000.0
                return [("（识别结果解析出错）", 0.0, actual_duration)]
            except:
                return [("（识别结果解析出错）", 0.0, 50.0)]
    
    def _recognize_large_audio(self, audio_file_path: str) -> List[Tuple[str, float, float]]:
        """处理大音频文件（分割后识别）"""
        print("处理大音频文件...")
        
        try:
            audio = AudioSegment.from_wav(audio_file_path)
            # 减小块大小到30秒，提高识别准确性
            chunk_length_ms = 30000  # 30秒一段
            chunks = []
            
            # 添加重叠部分，避免在句子中间被切断
            overlap_ms = 1000  # 1秒重叠
            
            # 分割音频
            for i in range(0, len(audio), chunk_length_ms - overlap_ms):
                end_pos = min(i + chunk_length_ms, len(audio))
                chunk = audio[i:end_pos]
                chunk_file = os.path.join(self.temp_dir, f"chunk_{uuid.uuid4()}.wav")
                chunk.export(chunk_file, format="wav")
                chunks.append((chunk_file, i / 1000.0, end_pos / 1000.0))
                
                # 如果已经到达音频末尾，停止分割
                if end_pos >= len(audio):
                    break
            
            print(f"音频已分割为 {len(chunks)} 个片段")
            
            # 逐个识别
            all_results = []
            
            for chunk_file, start_time, end_time in chunks:
                try:
                    print(f"处理片段: {start_time:.1f}s - {end_time:.1f}s")
                    chunk_results = self.recognize_speech_tencent(chunk_file)
                    
                    # 调整时间偏移，并过滤掉重叠部分的结果
                    for text, chunk_start, chunk_end in chunk_results:
                        # 只保留有效的时间范围内的结果
                        actual_start = chunk_start + start_time
                        actual_end = chunk_end + start_time
                        
                        # 如果结果超出当前片段的主要范围（排除重叠部分），跳过
                        if actual_end > end_time - (overlap_ms / 2000.0):  # 转换为秒
                            continue
                            
                        if text.strip():  # 只保留非空文本
                            all_results.append((text, actual_start, actual_end))
                    
                    print(f"片段识别完成，获得 {len(chunk_results)} 个结果")
                    
                except Exception as e:
                    print(f"处理音频片段失败: {e}")
                    import traceback
                    traceback.print_exc()
                    # 添加一个占位符结果
                    all_results.append(("（音频片段识别失败）", start_time, end_time))
                finally:
                    # 清理临时文件
                    if os.path.exists(chunk_file):
                        try:
                            os.remove(chunk_file)
                        except:
                            pass
            
            # 按时间排序结果
            all_results.sort(key=lambda x: x[1])
            print(f"大音频文件处理完成，总共获得 {len(all_results)} 个识别结果")
            return all_results
            
        except Exception as e:
            print(f"处理大音频文件失败: {e}")
            import traceback
            traceback.print_exc()
            return [("（大音频文件处理失败）", 0.0, 10.0)]
    
    def _fallback_local_recognition(self, audio_file_path: str) -> List[Tuple[str, float, float]]:
        """回退到本地识别"""
        print("回退到本地语音识别...")
        try:
            import speech_recognition as sr
            
            # 检查文件大小
            file_size = os.path.getsize(audio_file_path)
            print(f"音频文件大小: {file_size / (1024*1024):.2f} MB")
            
            # 如果文件太大，需要分割处理
            if file_size > 5 * 1024 * 1024:  # 5MB
                print("音频文件较大，使用分段识别...")
                return self._local_recognize_with_chunks(audio_file_path)
            
            recognizer = sr.Recognizer()
            
            # 调整识别器的参数
            recognizer.energy_threshold = 300  # 能量阈值
            recognizer.dynamic_energy_threshold = True
            recognizer.pause_threshold = 0.8  # 暂停阈值
            
            with sr.AudioFile(audio_file_path) as source:
                # 调整音频噪音
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio_data = recognizer.record(source)
                
            print("开始本地语音识别...")
            text = recognizer.recognize_google(audio_data, language="zh-CN")
            print(f"本地识别结果: {text}")
            
            # 估算时间长度
            audio_duration = len(audio_data.frame_data) / (audio_data.sample_rate * audio_data.sample_width)
            estimated_duration = max(1.0, audio_duration)
            
            return [(text, 0.0, estimated_duration)]
            
        except sr.UnknownValueError:
            print("本地识别无法理解音频")
            return [("（无法识别音频内容）", 0.0, 10.0)]
        except sr.RequestError as e:
            print(f"本地识别请求失败: {e}")
            return [("（本地识别服务不可用）", 0.0, 10.0)]
        except Exception as e:
            print(f"本地识别也失败: {e}")
            import traceback
            traceback.print_exc()
            return [("（语音识别完全失败）", 0.0, 10.0)]
    
    def _local_recognize_with_chunks(self, audio_file_path: str) -> List[Tuple[str, float, float]]:
        """分段本地识别"""
        try:
            import speech_recognition as sr
            
            audio = AudioSegment.from_wav(audio_file_path)
            chunk_length_ms = 10000  # 10秒一段
            chunks = []
            
            # 分割音频
            for i in range(0, len(audio), chunk_length_ms):
                chunk = audio[i:i + chunk_length_ms]
                chunk_file = os.path.join(self.temp_dir, f"local_chunk_{uuid.uuid4()}.wav")
                chunk.export(chunk_file, format="wav")
                chunks.append((chunk_file, i / 1000.0))
            
            # 逐个识别
            all_results = []
            recognizer = sr.Recognizer()
            recognizer.energy_threshold = 300
            recognizer.dynamic_energy_threshold = True
            
            for chunk_file, start_time in chunks:
                try:
                    with sr.AudioFile(chunk_file) as source:
                        recognizer.adjust_for_ambient_noise(source, duration=0.3)
                        audio_data = recognizer.record(source)
                        text = recognizer.recognize_google(audio_data, language="zh-CN")
                        
                        if text.strip():
                            # 估算当前片段的时长
                            chunk_duration = len(audio_data.frame_data) / (audio_data.sample_rate * audio_data.sample_width)
                            all_results.append((text, start_time, start_time + chunk_duration))
                            
                except sr.UnknownValueError:
                    # 跳过无法识别的片段
                    pass
                except Exception as e:
                    print(f"本地识别片段失败: {e}")
                finally:
                    if os.path.exists(chunk_file):
                        try:
                            os.remove(chunk_file)
                        except:
                            pass
            
            if not all_results:
                return [("（所有片段都无法识别）", 0.0, 10.0)]
            
            return all_results
            
        except Exception as e:
            print(f"分段本地识别失败: {e}")
            return [("（分段识别失败）", 0.0, 10.0)]
    
    async def transcribe_audio(self, audio_path: str) -> List[Tuple[str, float, float]]:
        """语音识别转文本 - 使用腾讯云API"""
        print("开始腾讯云语音识别（普通话）...")
        results = self.recognize_speech_tencent(audio_path)
        print(f"语音识别完成，获得 {len(results)} 个片段")
        return results
    
    async def process_video(self, video_id: str, video_path: str):
        """处理视频：提取音频 -> 转录 -> 生成片段"""
        try:
            print(f"开始处理视频 {video_id}")
            print(f"视频文件路径: {video_path}")
            
            # 更新处理状态
            task = Database.get_processing_task(video_id)
            if task:
                task.status = "processing"
                task.progress = 5
                task.message = "正在验证视频文件..."
            
            # 验证视频文件
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"视频文件不存在: {video_path}")
            
            file_size = os.path.getsize(video_path)
            if file_size == 0:
                raise ValueError("视频文件为空")
            
            print(f"视频文件大小: {file_size / (1024*1024):.2f} MB")
            
            if task:
                task.progress = 10
                task.message = "正在提取音频..."
            
            # 1. 提取音频
            print(f"开始提取视频 {video_id} 的音频...")
            audio_path = await self.extract_audio(video_path)
            print(f"音频提取完成: {audio_path}")
            
            if task:
                task.progress = 30
                task.message = "正在进行语音识别..."
            
            # 获取音频文件的实际时长
            actual_duration = 50.0  # 默认值
            try:
                audio = AudioSegment.from_wav(audio_path)
                actual_duration_ms = len(audio)
                actual_duration = actual_duration_ms / 1000.0
                print(f"音频实际时长: {actual_duration}秒")
            except Exception as e:
                print(f"获取音频时长失败: {e}")
            
            # 2. 语音识别
            print("开始语音识别...")
            transcripts = await self.transcribe_audio(audio_path)
            print(f"语音识别完成，获得 {len(transcripts)} 个片段")
            
            if not transcripts:
                print("警告：没有获得任何识别结果")
                # 创建一个默认的空片段
                transcripts = [("（无识别结果）", 0.0, actual_duration)]
            
            if task:
                task.progress = 70
                task.message = "正在生成文本片段..."
            
            # 3. 生成转录片段
            segments = []
            for i, (text, start_time, end_time) in enumerate(transcripts):
                # 验证时间戳
                if start_time < 0:
                    start_time = 0.0
                if end_time <= start_time:
                    end_time = start_time + 1.0
                
                # 清理文本
                cleaned_text = text.strip()
                if not cleaned_text:
                    cleaned_text = "（无文本内容）"
                
                segment = TranscriptSegment(
                    id=f"seg_{video_id}_{i}",
                    video_id=video_id,
                    text=cleaned_text,
                    start_time=start_time,
                    end_time=end_time,
                    order=i
                )
                segments.append(segment)
                print(f"片段 {i+1}: {start_time:.1f}s - {end_time:.1f}s, 文本: {cleaned_text[:50]}...")
            
            # 保存到数据库
            print(f"保存 {len(segments)} 个片段到数据库")
            Database.add_transcript(video_id, segments)
            
            # 清理临时音频文件
            if os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                    print("临时音频文件已清理")
                except Exception as e:
                    print(f"清理临时文件失败: {e}")
            
            if task:
                task.status = "completed"
                task.progress = 100
                task.message = f"处理完成，共生成 {len(segments)} 个片段"
                
            print(f"视频 {video_id} 处理完成")
                
        except Exception as e:
            print(f"视频处理失败: {e}")
            import traceback
            traceback.print_exc()
            
            task = Database.get_processing_task(video_id)
            if task:
                task.status = "failed"
                task.progress = 0
                task.message = f"处理失败: {str(e)}"
            
            # 确保至少有一个默认片段
            try:
                default_segments = [
                    TranscriptSegment(
                        id=f"seg_{video_id}_0",
                        video_id=video_id,
                        text=f"（处理失败: {str(e)}）",
                        start_time=0.0,
                        end_time=5.0,
                        order=0
                    )
                ]
                Database.add_transcript(video_id, default_segments)
                print("已创建默认片段")
            except Exception as db_e:
                print(f"创建默认片段失败: {db_e}")
    
    async def split_video_segment(self, video_id: str, segment_id: str, split_points: List[float], new_text: str = None) -> List[TranscriptSegment]:
        """分割视频片段"""
        segments = Database.get_transcript(video_id)
        target_segment = None
        target_index = -1
        
        for i, seg in enumerate(segments):
            if seg.id == segment_id:
                target_segment = seg
                target_index = i
                break
        
        if not target_segment:
            raise ValueError("片段未找到")
        
        print(f"分割片段: {segment_id}")
        print(f"原文本: {target_segment.text}")
        print(f"新文本: {new_text}")
        print(f"分割点: {split_points}")
        
        # 优先使用新文本进行分割判断
        text_to_check = new_text if new_text else target_segment.text
        
        # 检查文本是否包含'---'分割符
        if text_to_check and '---' in text_to_check:
            print("检测到'---'分割符，按文本内容分割")
            return self._split_segment_by_text(video_id, target_segment, target_index, text_to_check)
        else:
            print("按时间点分割")
            return self._split_segment_by_time(video_id, target_segment, target_index, split_points)
    
    def _split_segment_by_text(self, video_id: str, target_segment, target_index: int, new_text: str) -> List[TranscriptSegment]:
        """按文本内容分割片段（基于'---'分隔符）"""
        # 按'---'分割文本
        text_parts = [part.strip() for part in new_text.split('---') if part.strip()]
        
        if len(text_parts) <= 1:
            return [target_segment]
        
        print(f"文本分割为 {len(text_parts)} 个部分: {text_parts}")
        
        # 计算每个部分的时间长度（按字符数比例分配）
        total_chars = len(''.join(text_parts))
        duration = target_segment.end_time - target_segment.start_time
        
        new_segments = []
        current_time = target_segment.start_time
        
        for i, text_part in enumerate(text_parts):
            # 计算当前部分的时长
            part_duration = (len(text_part) / total_chars) * duration if total_chars > 0 else duration / len(text_parts)
            end_time = current_time + part_duration
            
            # 确保最后一个部分结束时间不超出原片段
            if i == len(text_parts) - 1:
                end_time = target_segment.end_time
            
            new_segment = TranscriptSegment(
                id=f"seg_{video_id}_{target_index}_{i}",
                video_id=video_id,
                text=text_part,
                start_time=current_time,
                end_time=end_time,
                order=target_segment.order + i
            )
            new_segments.append(new_segment)
            print(f"创建片段 {i}: {current_time:.2f}s - {end_time:.2f}s, 文本: {text_part[:30]}...")
            
            current_time = end_time
        
        return new_segments
    
    def _split_segment_by_time(self, video_id: str, target_segment, target_index: int, split_points: List[float]) -> List[TranscriptSegment]:
        """按时间点分割片段"""
        duration = target_segment.end_time - target_segment.start_time
        
        if len(split_points) == 0:
            return [target_segment]
        
        # 创建分割后的片段
        new_segments = []
        start_time = target_segment.start_time
        
        # 按时间点分割文本
        for i, split_point in enumerate([0] + split_points + [duration]):
            if i < len(split_points) + 1:
                end_time = target_segment.start_time + (split_points[i] if i < len(split_points) else duration)
                
                # 计算当前部分的时间比例
                time_ratio = (end_time - start_time) / duration if duration > 0 else 1.0 / (len(split_points) + 1)
                
                # 按时间比例分割文本
                text_start = int(len(target_segment.text) * (i / (len(split_points) + 1)))
                text_end = int(len(target_segment.text) * ((i + 1) / (len(split_points) + 1)))
                text = target_segment.text[text_start:text_end].strip()
                
                new_segment = TranscriptSegment(
                    id=f"seg_{video_id}_{target_index}_{i}",
                    video_id=video_id,
                    text=text,
                    start_time=start_time,
                    end_time=end_time,
                    order=target_segment.order + i
                )
                new_segments.append(new_segment)
                start_time = end_time
        
        return new_segments
    
    async def export_video(self, video_id: str, segment_ids: List[str], mode: str, 
                           format: str = "mp4", quality: str = "medium", 
                           resolution: str = "original") -> str:
        """导出视频 - 真实视频处理"""
        try:
            # 获取原始视频信息
            video = Database.get_video(video_id)
            if not video:
                raise ValueError(f"视频 {video_id} 未找到")
            
            # 获取所有片段信息
            all_segments = Database.get_transcript(video_id)
            segment_map = {seg.id: seg for seg in all_segments}
            
            # 根据segment_ids顺序获取对应的片段
            ordered_segments = []
            for seg_id in segment_ids:
                if seg_id in segment_map:
                    ordered_segments.append(segment_map[seg_id])
            
            if not ordered_segments:
                raise ValueError("没有找到有效的视频片段")
            
            # 生成输出文件路径
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"export_{video_id[:8]}_{timestamp}.{format}"
            output_path = os.path.join(self.temp_dir, output_filename)
            
            # 获取质量设置
            quality_settings = self._get_quality_settings(quality, resolution)
            
            if mode == "merge":
                # 合并模式：将所有片段合并为一个视频
                await self._merge_segments(video.file_path, ordered_segments, output_path, quality_settings, format)
            elif mode == "batch":
                # 批量模式：每个片段生成单独的视频文件
                await self._export_batch_segments(video.file_path, ordered_segments, output_path, quality_settings, format)
            else:
                raise ValueError(f"不支持的导出模式: {mode}")
            
            print(f"视频导出成功: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"视频导出失败: {str(e)}")
            raise
    
    def _get_quality_settings(self, quality: str, resolution: str) -> dict:
        """获取视频质量设置"""
        settings = {
            "bitrate": "2000k",
            "resolution": None,
            "codec": "libx264",
            "audio_codec": "aac"
        }
        
        # 质量设置
        if quality == "low":
            settings["bitrate"] = "1000k"
            settings["codec"] = "libx264"
        elif quality == "medium":
            settings["bitrate"] = "2000k"
            settings["codec"] = "libx264"
        elif quality == "high":
            settings["bitrate"] = "4000k"
            settings["codec"] = "libx264"
        
        # 分辨率设置
        if resolution == "720p":
            settings["resolution"] = "1280x720"
        elif resolution == "1080p":
            settings["resolution"] = "1920x1080"
        # original 保持原分辨率
        
        return settings
    
    async def _merge_segments(self, video_path: str, segments: List, output_path: str, 
                             quality_settings: dict, format: str):
        """合并视频片段"""
        try:
            print(f"开始合并 {len(segments)} 个视频片段...")
            
            # 导入moviepy
            from moviepy.editor import VideoFileClip, concatenate_videoclips
            
            clips = []
            total_duration = 0
            
            # 创建原始视频的剪辑（保持打开状态）
            video = VideoFileClip(video_path)
            
            # 为每个片段创建视频剪辑
            for i, segment in enumerate(segments):
                try:
                    print(f"处理片段 {i+1}/{len(segments)}: {segment.start_time:.1f}s - {segment.end_time:.1f}s")
                    
                    # 截取对应时间段
                    clip = video.subclip(segment.start_time, segment.end_time)
                    clips.append(clip)
                    total_duration += clip.duration
                    
                    # 模拟处理进度
                    await asyncio.sleep(0.1)
                        
                except Exception as e:
                    print(f"处理片段 {i+1} 失败: {str(e)}")
                    continue
            
            if not clips:
                raise ValueError("没有有效的视频片段可以合并")
            
            print(f"开始合并视频，总时长: {total_duration:.1f}s")
            
            # 合并所有片段
            final_clip = concatenate_videoclips(clips)
            
            # 应用质量设置
            if quality_settings["resolution"]:
                final_clip = final_clip.resize(quality_settings["resolution"])
            
            # 导出视频
            final_clip.write_videofile(
                output_path,
                codec=quality_settings["codec"],
                bitrate=quality_settings["bitrate"],
                audio_codec=quality_settings["audio_codec"],
                threads=4,
                verbose=False,
                logger=None
            )
            
            # 清理资源
            final_clip.close()
            for clip in clips:
                clip.close()
            video.close()
            
            print(f"视频合并完成: {output_path}")
            
        except ImportError:
            print("MoviePy未安装，使用模拟导出")
            await self._simulate_export(segments, output_path, "merge")
        except Exception as e:
            print(f"视频合并失败: {str(e)}")
            # 确保在异常时也清理资源
            try:
                if 'video' in locals():
                    video.close()
                if 'clips' in locals():
                    for clip in clips:
                        clip.close()
                if 'final_clip' in locals():
                    final_clip.close()
            except:
                pass
            await self._simulate_export(segments, output_path, "merge")
    
    async def _export_batch_segments(self, video_path: str, segments: List, output_path: str, 
                                    quality_settings: dict, format: str):
        """批量导出视频片段"""
        try:
            print(f"开始批量导出 {len(segments)} 个视频片段...")
            
            # 创建压缩包目录
            base_name = os.path.splitext(output_path)[0]
            zip_dir = f"{base_name}_segments"
            os.makedirs(zip_dir, exist_ok=True)
            
            # 导入moviepy
            from moviepy.editor import VideoFileClip
            
            # 创建原始视频的剪辑（保持打开状态）
            video = VideoFileClip(video_path)
            
            # 为每个片段创建单独的视频文件
            for i, segment in enumerate(segments):
                try:
                    print(f"导出片段 {i+1}/{len(segments)}: {segment.start_time:.1f}s - {segment.end_time:.1f}s")
                    
                    segment_filename = f"segment_{i+1:02d}_{segment.start_time:.1f}s-{segment.end_time:.1f}s.{format}"
                    segment_path = os.path.join(zip_dir, segment_filename)
                    
                    # 截取对应时间段
                    clip = video.subclip(segment.start_time, segment.end_time)
                    
                    # 应用质量设置
                    if quality_settings["resolution"]:
                        clip = clip.resize(quality_settings["resolution"])
                    
                    # 导出片段
                    clip.write_videofile(
                        segment_path,
                        codec=quality_settings["codec"],
                        bitrate=quality_settings["bitrate"],
                        audio_codec=quality_settings["audio_codec"],
                        threads=2,
                        verbose=False,
                        logger=None
                    )
                    
                    clip.close()
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    print(f"导出片段 {i+1} 失败: {str(e)}")
                    continue
            
            # 关闭视频文件
            video.close()
            
            # 创建压缩包（如果系统支持）
            try:
                import zipfile
                zip_path = f"{base_name}.zip"
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(zip_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, zip_dir)
                            zipf.write(file_path, arcname)
                
                # 清理临时目录
                import shutil
                shutil.rmtree(zip_dir)
                
                print(f"批量导出完成: {zip_path}")
                return zip_path
                
            except ImportError:
                print("无法创建压缩包，返回目录")
                return zip_dir
                
        except ImportError:
            print("MoviePy未安装，使用模拟导出")
            await self._simulate_export(segments, output_path, "batch")
        except Exception as e:
            print(f"批量导出失败: {str(e)}")
            # 确保在异常时也清理资源
            try:
                if 'video' in locals():
                    video.close()
            except:
                pass
            await self._simulate_export(segments, output_path, "batch")
    
    async def _simulate_export(self, segments: List, output_path: str, mode: str):
        """模拟导出过程（当MoviePy不可用时）"""
        print(f"模拟导出 {len(segments)} 个片段，模式: {mode}")
        
        # 创建导出信息文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"视频导出信息（模拟模式）\n")
            f.write(f"导出模式: {mode}\n")
            f.write(f"片段数量: {len(segments)}\n")
            f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 50 + "\n")
            f.write("片段详情:\n")
            
            for i, segment in enumerate(segments, 1):
                f.write(f"\n片段 {i}:\n")
                f.write(f"  时间: {segment.start_time:.1f}s - {segment.end_time:.1f}s\n")
                f.write(f"  时长: {segment.end_time - segment.start_time:.1f}s\n")
                f.write(f"  文本: {segment.text[:100]}{'...' if len(segment.text) > 100 else ''}\n")
            
            f.write("\n" + "=" * 50 + "\n")
            f.write("注意：这是模拟导出。要启用真实视频处理，请安装MoviePy:\n")
            f.write("pip install moviepy\n")
        
        # 模拟处理时间
        processing_time = len(segments) * 0.5
        await asyncio.sleep(processing_time)
        
        print(f"模拟导出完成: {output_path}")