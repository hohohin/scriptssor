"""
数据模型定义 - 用于数据库操作（这里使用内存存储作为演示）
"""

import uuid
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Video:
    """视频文件模型"""
    id: str
    filename: str
    file_path: str
    size: int
    upload_time: datetime
    duration: float = 0.0

@dataclass
class TranscriptSegment:
    """转录片段模型"""
    id: str
    video_id: str
    text: str
    start_time: float
    end_time: float
    order: int

@dataclass
class ProcessingTask:
    """处理任务模型"""
    video_id: str
    status: str  # "processing", "completed", "failed"
    progress: int
    message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

# 内存存储（生产环境应使用数据库）
class Database:
    """简单的内存数据库"""
    videos: Dict[str, Video] = {}
    transcripts: Dict[str, List[TranscriptSegment]] = {}
    processing_tasks: Dict[str, ProcessingTask] = {}

    @classmethod
    def add_video(cls, video: Video):
        cls.videos[video.id] = video

    @classmethod
    def get_video(cls, video_id: str) -> Optional[Video]:
        return cls.videos.get(video_id)

    @classmethod
    def add_transcript(cls, video_id: str, segments: List[TranscriptSegment]):
        cls.transcripts[video_id] = segments

    @classmethod
    def get_transcript(cls, video_id: str) -> List[TranscriptSegment]:
        return cls.transcripts.get(video_id, [])

    @classmethod
    def update_transcript_segment(cls, segment_id: str, new_text: str):
        """
        更新转录片段文本
        """
        if not segment_id:
            print("警告：segment_id为空")
            return False
        
        if new_text is None:
            print("警告：new_text为None")
            return False
        
        # 清理文本
        cleaned_text = str(new_text).strip()
        
        print(f"尝试更新片段 {segment_id}，新文本: {cleaned_text[:50]}...")
        
        for video_id, segments in cls.transcripts.items():
            for segment in segments:
                if segment.id == segment_id:
                    old_text = segment.text
                    segment.text = cleaned_text
                    print(f"片段更新成功: {segment_id}")
                    print(f"旧文本: {old_text[:50]}...")
                    print(f"新文本: {cleaned_text[:50]}...")
                    return True
        
        print(f"未找到片段: {segment_id}")
        print(f"当前数据库中的片段ID: {[seg.id for segs in cls.transcripts.values() for seg in segs]}")
        return False

    @classmethod
    def reorder_segments(cls, video_id: str, segment_ids: List[str]):
        segments = cls.transcripts.get(video_id, [])
        # 创建ID到segment的映射
        segment_map = {seg.id: seg for seg in segments}
        # 按新顺序重新排列
        reordered = []
        for i, seg_id in enumerate(segment_ids):
            if seg_id in segment_map:
                segment_map[seg_id].order = i
                reordered.append(segment_map[seg_id])
        cls.transcripts[video_id] = reordered
        return reordered

    @classmethod
    def add_processing_task(cls, task: ProcessingTask):
        cls.processing_tasks[task.video_id] = task

    @classmethod
    def get_processing_task(cls, video_id: str) -> Optional[ProcessingTask]:
        return cls.processing_tasks.get(video_id)

    @classmethod
    def update_processing_task(cls, video_id: str, **kwargs):
        if video_id in cls.processing_tasks:
            task = cls.processing_tasks[video_id]
            for key, value in kwargs.items():
                if hasattr(task, key):
                    setattr(task, key, value)