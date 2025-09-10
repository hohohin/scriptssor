"""
Pydantic 模式定义 - 用于数据验证和序列化
"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class VideoUploadResponse(BaseModel):
    """视频上传响应"""
    video_id: str
    filename: str
    size: int
    upload_time: datetime

class TranscriptSegment(BaseModel):
    """转录片段"""
    id: str
    video_id: str
    text: str
    start_time: float
    end_time: float
    order: int

class SegmentEdit(BaseModel):
    """片段编辑请求"""
    new_text: str

class ReorderRequest(BaseModel):
    """重新排序请求"""
    segment_ids: List[str]

class SplitSegmentRequest(BaseModel):
    """分割片段请求"""
    split_points: List[float]  # 时间点列表
    new_text: Optional[str] = None  # 新的文本内容（用于按文本分割）

class ExportRequest(BaseModel):
    """导出请求"""
    mode: str  # "merge" 或 "batch"
    segment_order: List[str]
    format: str = "mp4"  # "mp4", "avi", "mov"
    quality: str = "medium"  # "low", "medium", "high"
    resolution: str = "original"  # "original", "720p", "1080p"

class ExportResponse(BaseModel):
    """导出响应"""
    download_url: str
    filename: str
    size: int

class ProcessingStatus(BaseModel):
    """处理状态"""
    video_id: str
    status: str  # "processing", "completed", "failed"
    progress: int  # 0-100
    message: Optional[str] = None