"""
FastAPI 主应用 - 视频编辑器后端API
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uuid
import os
from typing import List
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from schemas import (
    VideoUploadResponse, TranscriptSegment, SegmentEdit, 
    ReorderRequest, ExportRequest, 
    ExportResponse, ProcessingStatus
)
from models import Video, Database, ProcessingTask
from video_processor import VideoProcessor

# 初始化应用
app = FastAPI(
    title="Text-Driven Video Editor API",
    description="API for text-driven video editing tool",
    version="1.0.0"
)

# 添加CORS中间件 - 允许前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://127.0.0.1:5173", 
        "http://localhost:3000",
        "https://scriptssor-frontend.onrender.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化视频处理器
video_processor = VideoProcessor()

# 创建上传目录
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
async def root():
    """根路径"""
    return {"message": "Text-Driven Video Editor API", "version": "1.0.0"}

@app.post("/upload", response_model=VideoUploadResponse)
async def upload_video(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """
    上传视频文件
    """
    if not file.content_type.startswith('video/'):
        raise HTTPException(status_code=400, detail="文件必须是视频格式")
    
    # 生成唯一ID
    video_id = str(uuid.uuid4())
    
    # 保存文件
    file_path = os.path.join(UPLOAD_DIR, f"{video_id}_{file.filename}")
    
    # 异步保存文件
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # 创建视频对象
    video = Video(
        id=video_id,
        filename=file.filename,
        file_path=file_path,
        size=len(content),
        upload_time=datetime.now()
    )
    
    # 保存到数据库
    Database.add_video(video)
    
    # 创建处理任务
    task = ProcessingTask(
        video_id=video_id,
        status="processing",
        progress=0,
        message="上传完成，开始处理..."
    )
    Database.add_processing_task(task)
    
    # 后台处理视频
    background_tasks.add_task(video_processor.process_video, video_id, file_path)
    
    return VideoUploadResponse(
        video_id=video_id,
        filename=file.filename,
        size=len(content),
        upload_time=video.upload_time
    )

@app.get("/videos/{video_id}/transcript", response_model=List[TranscriptSegment])
async def get_transcript(video_id: str):
    """
    获取视频转录文本
    """
    video = Database.get_video(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="视频未找到")
    
    segments = Database.get_transcript(video_id)
    return segments

@app.get("/videos/{video_id}/status", response_model=ProcessingStatus)
async def get_processing_status(video_id: str):
    """
    获取视频处理状态
    """
    task = Database.get_processing_task(video_id)
    if not task:
        raise HTTPException(status_code=404, detail="处理任务未找到")
    
    return ProcessingStatus(
        video_id=task.video_id,
        status=task.status,
        progress=task.progress,
        message=task.message
    )

@app.put("/segments/{segment_id}")
async def edit_segment(segment_id: str, edit: SegmentEdit):
    """
    编辑转录片段文本
    """
    # 验证输入
    if not edit.new_text:
        raise HTTPException(status_code=400, detail="文本内容不能为空")
    
    if not segment_id:
        raise HTTPException(status_code=400, detail="片段ID不能为空")
    
    # 清理文本内容
    cleaned_text = edit.new_text.strip()
    
    # 更新数据库
    success = Database.update_transcript_segment(segment_id, cleaned_text)
    if not success:
        raise HTTPException(status_code=404, detail="片段未找到")
    
    return {"message": "片段更新成功", "segment_id": segment_id, "new_text": cleaned_text}

@app.post("/videos/{video_id}/reorder")
async def reorder_segments(video_id: str, reorder: ReorderRequest):
    """
    重新排列片段顺序
    """
    video = Database.get_video(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="视频未找到")
    
    reordered_segments = Database.reorder_segments(video_id, reorder.segment_ids)
    
    return {
        "message": "片段顺序更新成功",
        "segment_count": len(reordered_segments)
    }

@app.post("/segments/{segment_id}/split")
async def split_segment(segment_id: str, split_request: dict):
    """
    分割视频片段
    """
    # 验证输入
    if not segment_id:
        raise HTTPException(status_code=400, detail="片段ID不能为空")
    
    # 从请求体中获取参数
    split_points = split_request.get('split_points', [])
    new_text = split_request.get('new_text')
    
    if not split_points:
        raise HTTPException(status_code=400, detail="分割点不能为空")
    
    # 从segment_id中提取video_id (格式: seg_videoId_order 或 seg_videoId_originalIndex_newIndex)
    if segment_id.startswith("seg_") and "_" in segment_id:
        # 移除"seg_"前缀，处理可能的分割片段格式
        parts = segment_id.split("_")
        if len(parts) >= 3:
            # 格式可能是:
            # - 原始片段: seg_videoId_index
            # - 分割后片段: seg_videoId_originalIndex_newIndex
            # 我们需要提取真正的video_id（不包含索引部分）
            
            # 重新组合video_id部分：从第二部分开始，到最后一个数字索引之前
            # UUID格式通常是36个字符（32个字符加上4个连字符）
            video_id_parts = []
            for i in range(1, len(parts)):
                # 如果这部分看起来像数字索引，停止添加
                if parts[i].isdigit() and i > 1:
                    break
                video_id_parts.append(parts[i])
            
            if video_id_parts:
                video_id = "_".join(video_id_parts)
            else:
                # 如果没找到合适的部分，使用第二部分作为video_id
                video_id = parts[1] if len(parts) > 1 else segment_id
        else:
            video_id = segment_id
    else:
        video_id = segment_id
    
    try:
        print(f"分割片段请求: segment_id={segment_id}, video_id={video_id}, split_points={split_points}, new_text={new_text}")
        
        new_segments = await video_processor.split_video_segment(
            video_id, segment_id, split_points, new_text
        )
        
        if not new_segments:
            raise HTTPException(status_code=400, detail="分割失败：未生成新片段")
        
        # 更新数据库中的片段
        segments = Database.get_transcript(video_id)
        # 移除原片段并添加新片段
        segments = [s for s in segments if s.id != segment_id]
        segments.extend(new_segments)
        # 重新排序
        segments.sort(key=lambda x: x.order)
        Database.add_transcript(video_id, segments)
        
        print(f"分割成功，生成了 {len(new_segments)} 个新片段")
        
        return {
            "message": "片段分割成功",
            "new_segments": [s.__dict__ for s in new_segments]
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"分割失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"分割失败: {str(e)}")

@app.post("/videos/{video_id}/export", response_model=ExportResponse)
async def export_video(video_id: str, export_request: ExportRequest):
    """
    导出视频
    """
    video = Database.get_video(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="视频未找到")
    
    try:
        output_path = await video_processor.export_video(
            video_id, 
            export_request.segment_order, 
            export_request.mode,
            export_request.format,
            export_request.quality,
            export_request.resolution
        )
        
        # 获取文件大小
        file_size = os.path.getsize(output_path)
        
        return ExportResponse(
            download_url=f"/download/{os.path.basename(output_path)}",
            filename=os.path.basename(output_path),
            size=file_size
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")

@app.get("/download/{filename}")
async def download_file(filename: str):
    """
    下载文件
    """
    file_path = os.path.join("temp", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件未找到")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/octet-stream'
    )

@app.get("/debug/videos/{video_id}/segments")
async def debug_segments(video_id: str):
    """
    调试端点：查看视频片段的原始数据
    """
    video = Database.get_video(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="视频未找到")
    
    segments = Database.get_transcript(video_id)
    
    return {
        "video_id": video_id,
        "video_filename": video.filename,
        "segments_count": len(segments),
        "segments": [
            {
                "id": seg.id,
                "text": seg.text[:100] + "..." if len(seg.text) > 100 else seg.text,
                "start_time": seg.start_time,
                "end_time": seg.end_time,
                "duration": seg.end_time - seg.start_time,
                "order": seg.order
            }
            for seg in segments
        ]
    }

@app.post("/videos/{video_id}/reprocess")
async def reprocess_video(video_id: str, background_tasks: BackgroundTasks):
    """
    重新处理视频（用于修复时间戳问题）
    """
    video = Database.get_video(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="视频未找到")
    
    # 清理旧的转录数据
    if video_id in Database.transcripts:
        del Database.transcripts[video_id]
    
    # 创建新的处理任务
    task = ProcessingTask(
        video_id=video_id,
        status="processing",
        progress=0,
        message="重新处理视频..."
    )
    Database.add_processing_task(task)
    
    # 后台重新处理视频
    background_tasks.add_task(video_processor.process_video, video_id, video.file_path)
    
    return {"message": "视频重新处理已开始", "video_id": video_id}

# 启动命令示例
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=9002, reload=False)