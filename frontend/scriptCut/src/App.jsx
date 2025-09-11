import React, { useState, useRef, useCallback, useEffect } from 'react';
import { Upload, Play, Download, Move, Scissors, FileVideo, Mic, CheckCircle, Loader2, RefreshCw } from 'lucide-react';
import './App.css';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:9002';

const App = () => {
  const [videos, setVideos] = useState([]);
  const [segments, setSegments] = useState([]);
  const [draggedItem, setDraggedItem] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentVideoId, setCurrentVideoId] = useState(null);
  const [processingStatus, setProcessingStatus] = useState(null);
  const [isExporting, setIsExporting] = useState(false);
  const [exportProgress, setExportProgress] = useState(0);
  const [exportOptions, setExportOptions] = useState({
    format: 'mp4',
    quality: 'medium',
    resolution: 'original'
  });
  const fileInputRef = useRef(null);
  const statusIntervalRef = useRef(null);
  const editTimeoutRef = useRef(null);

  // 轮询处理状态
  const pollProcessingStatus = useCallback(async (videoId) => {
    if (!videoId) return;

    try {
      const response = await fetch(`${API_BASE_URL}/videos/${videoId}/status`);
      if (response.ok) {
        const status = await response.json();
        setProcessingStatus(status);
        
        if (status.status === 'completed') {
          // 获取转录文本
          const transcriptResponse = await fetch(`${API_BASE_URL}/videos/${videoId}/transcript`);
          if (transcriptResponse.ok) {
            const transcripts = await transcriptResponse.json();
            setSegments(transcripts.map((seg, index) => ({
              ...seg,
              order: index
            })));
            setIsProcessing(false);
            clearInterval(statusIntervalRef.current);
          }
        } else if (status.status === 'failed') {
          setIsProcessing(false);
          clearInterval(statusIntervalRef.current);
        }
      }
    } catch (error) {
      console.error('获取处理状态失败:', error);
    }
  }, []);

  // 处理文件上传
  const handleFileUpload = useCallback(async (files) => {
    const mediaFiles = Array.from(files).filter(file => 
      file.type.includes('video/') || file.type.includes('audio/')
    );
    
    if (mediaFiles.length === 0) return;

    try {
      const file = mediaFiles[0];
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${API_BASE_URL}/upload`, {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        const result = await response.json();
        
        setVideos([{
          id: result.video_id,
          name: result.filename,
          size: result.size,
          upload_time: result.upload_time
        }]);
        
        setCurrentVideoId(result.video_id);
        setIsProcessing(true);
        setProcessingStatus({ status: 'processing', progress: 0, message: '开始处理...' });
        
        // 开始轮询状态
        statusIntervalRef.current = setInterval(() => {
          pollProcessingStatus(result.video_id);
        }, 2000);
      } else {
        alert('上传失败: ' + await response.text());
      }
    } catch (error) {
      console.error('上传失败:', error);
      alert('上传失败，请检查后端服务是否运行');
    }
  }, [pollProcessingStatus]);

  // 编辑文本片段
  const handleEditSegment = async (segmentId, newText) => {
    try {
      // 验证输入
      if (!segmentId) {
        console.error('片段ID为空');
        return;
      }

      if (newText === null || newText === undefined) {
        console.error('文本内容为空');
        return;
      }

      const response = await fetch(`${API_BASE_URL}/segments/${segmentId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ new_text: newText })
      });

      if (response.ok) {
        const result = await response.json();
        console.log('编辑成功:', result);
        
        // 使用后端返回的清理后的文本
        const updatedText = result.new_text || newText;
        
        setSegments(prev => prev.map(seg => 
          seg.id === segmentId ? { ...seg, text: updatedText } : seg
        ));
      } else {
        const errorText = await response.text();
        console.error('编辑失败:', response.status, errorText);
        
        // 尝试解析错误信息
        try {
          const errorData = JSON.parse(errorText);
          alert(`编辑失败: ${errorData.detail || '未知错误'}`);
        } catch {
          alert(`编辑失败: ${errorText || '服务器错误'}`);
        }
      }
    } catch (error) {
      console.error('编辑失败:', error);
      alert('编辑失败: 网络错误或服务器不可用');
    }
  };

  // 分割文本片段
  const handleSplitSegment = async (segmentId, fullText) => {
    try {
      // 找到要分割的片段
      const segmentToSplit = segments.find(seg => seg.id === segmentId);
      if (!segmentToSplit) return;

      // 按'---'分割文本
      const splitParts = fullText.split('---').map(part => part.trim()).filter(part => part.length > 0);
      
      if (splitParts.length <= 1) {
        // 如果没有'---'或分割后只有一部分，按普通编辑处理
        await handleEditSegment(segmentId, fullText);
        return;
      }

      console.log(`分割片段 ${segmentId} 为 ${splitParts.length} 个部分:`, splitParts);

      // 计算每个部分的时间长度（按字符数比例分配）
      const totalChars = splitParts.join('').length;
      const segmentDuration = segmentToSplit.end_time - segmentToSplit.start_time;
      
      // 准备分割后的新片段数据
      const newSegments = [];
      let currentTime = segmentToSplit.start_time;
      
      splitParts.forEach((part, index) => {
        const partDuration = (part.length / totalChars) * segmentDuration;
        const endTime = currentTime + partDuration;
        
        newSegments.push({
          text: part,
          start_time: currentTime,
          end_time: endTime
        });
        
        currentTime = endTime;
      });

      // 计算分割点（相对于开始时间的时间点）
      const splitPoints = [];
      for (let i = 1; i < newSegments.length; i++) {
        splitPoints.push(newSegments[i].start_time - segmentToSplit.start_time);
      }

      console.log('发送分割点:', splitPoints);

      // 调用后端分割接口
      const response = await fetch(`${API_BASE_URL}/segments/${segmentId}/split`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          split_points: splitPoints,
          new_text: fullText
        })
      });

      if (response.ok) {
        const result = await response.json();
        console.log('分割成功:', result);
        
        // 更新本地状态 - 移除原片段，添加新片段
        setSegments(prev => {
          const otherSegments = prev.filter(seg => seg.id !== segmentId);
          const newSegmentObjects = result.new_segments.map((newSeg, index) => ({
            ...newSeg
            // 使用后端返回的order，不要强制设置
          }));
          
          // 重新排序所有片段
          const allSegments = [...otherSegments, ...newSegmentObjects];
          return allSegments.sort((a, b) => a.order - b.order);
        });
      } else {
        const errorText = await response.text();
        console.error('分割失败:', response.status, errorText);
        
        // 尝试解析错误信息
        try {
          const errorData = JSON.parse(errorText);
          alert(`分割失败: ${errorData.detail || '未知错误'}`);
        } catch {
          alert(`分割失败: ${errorText || '服务器错误'}`);
        }
      }
    } catch (error) {
      console.error('分割失败:', error);
      alert('分割失败: 网络错误');
    }
  };

  // 防抖的文本编辑处理
  const handleSegmentChange = (segmentId, newText) => {
    // 立即更新本地状态以提供即时反馈
    setSegments(prev => prev.map(seg => 
      seg.id === segmentId ? { ...seg, text: newText } : seg
    ));

    // 清除之前的定时器
    if (editTimeoutRef.current) {
      clearTimeout(editTimeoutRef.current);
    }

    // 设置新的定时器，延迟500ms发送API请求
    editTimeoutRef.current = setTimeout(() => {
      // 检查是否包含'---'需要分割
      if (newText.includes('---')) {
        handleSplitSegment(segmentId, newText);
      } else {
        handleEditSegment(segmentId, newText);
      }
    }, 500);
  };

  // 重新排序片段
  const handleReorderSegments = async (newOrder) => {
    if (!currentVideoId) return;

    try {
      const response = await fetch(`${API_BASE_URL}/videos/${currentVideoId}/reorder`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ segment_ids: newOrder })
      });

      if (!response.ok) {
        alert('重新排序失败');
      }
    } catch (error) {
      console.error('重新排序失败:', error);
    }
  };

  // 导出视频
  const handleExport = async (mode) => {
    if (!currentVideoId || segments.length === 0) {
      alert('请先上传并处理视频');
      return;
    }

    setIsExporting(true);
    setExportProgress(0);

    try {
      const segmentOrder = segments
        .sort((a, b) => a.order - b.order)
        .map(seg => seg.id);

      // 模拟进度更新
      const progressInterval = setInterval(() => {
        setExportProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 500);

      const response = await fetch(`${API_BASE_URL}/videos/${currentVideoId}/export`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          mode: mode,
          segment_order: segmentOrder,
          ...exportOptions
        })
      });

      clearInterval(progressInterval);
      setExportProgress(100);

      if (response.ok) {
        const result = await response.json();
        
        // 显示成功消息
        const fileSize = (result.size / (1024 * 1024)).toFixed(2);
        alert(`导出成功！\n文件名: ${result.filename}\n文件大小: ${fileSize} MB\n\n点击确定开始下载`);
        
        // 触发下载
        window.open(`${API_BASE_URL}${result.download_url}`, '_blank');
      } else {
        const error = await response.text();
        alert('导出失败: ' + error);
      }
    } catch (error) {
      console.error('导出失败:', error);
      alert('导出失败，请检查后端服务');
    } finally {
      setIsExporting(false);
      setExportProgress(0);
    }
  };

  // 更新导出选项
  const handleExportOptionChange = (option, value) => {
    setExportOptions(prev => ({
      ...prev,
      [option]: value
    }));
  };

  const handleReprocess = async () => {
    if (!currentVideoId) return;
    
    try {
      const response = await fetch(`${API_BASE_URL}/videos/${currentVideoId}/reprocess`, {
        method: 'POST'
      });
      
      if (response.ok) {
        alert('视频重新处理已开始，请等待处理完成...');
        setIsProcessing(true);
        setSegments([]);
        
        // 开始轮询处理状态
        statusIntervalRef.current = setInterval(async () => {
          const statusResponse = await fetch(`${API_BASE_URL}/videos/${currentVideoId}/status`);
          if (statusResponse.ok) {
            const status = await statusResponse.json();
            
            if (status.status === 'completed') {
              const transcriptResponse = await fetch(`${API_BASE_URL}/videos/${currentVideoId}/transcript`);
              if (transcriptResponse.ok) {
                const transcripts = await transcriptResponse.json();
                setSegments(transcripts.map((seg, index) => ({
                  ...seg,
                  order: index
                })));
                setIsProcessing(false);
                clearInterval(statusIntervalRef.current);
                alert('视频重新处理完成！现在应该显示正确的时间戳了。');
              }
            } else if (status.status === 'failed') {
              setIsProcessing(false);
              clearInterval(statusIntervalRef.current);
              alert('视频处理失败，请重试。');
            }
          }
        }, 2000);
      } else {
        alert('重新处理失败，请重试。');
      }
    } catch (error) {
      console.error('重新处理错误:', error);
      alert('重新处理失败，请重试。');
    }
  };

  // 拖拽处理
  const handleDragStart = (e, index) => {
    setDraggedItem(index);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDrop = (e, targetIndex) => {
    e.preventDefault();
    if (draggedItem === null) return;
    
    const newSegments = [...segments];
    const draggedSegment = newSegments[draggedItem];
    newSegments.splice(draggedItem, 1);
    newSegments.splice(targetIndex, 0, draggedSegment);
    
    // 更新order
    const updatedSegments = newSegments.map((segment, index) => ({
      ...segment,
      order: index
    }));
    
    setSegments(updatedSegments);
    setDraggedItem(null);
    
    // 发送到后端
    const segmentIds = updatedSegments.map(seg => seg.id);
    handleReorderSegments(segmentIds);
  };

  // 清理轮询和定时器
  useEffect(() => {
    return () => {
      if (statusIntervalRef.current) {
        clearInterval(statusIntervalRef.current);
      }
      if (editTimeoutRef.current) {
        clearTimeout(editTimeoutRef.current);
      }
    };
  }, []);

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <div className="header-logo">
            <div className="logo-icon">
              <Scissors size={24} />
            </div>
            <h1 className="header-title">
              Text-Driven Video Editor
            </h1>
          </div>
          <div className="header-actions">
            {/* Export Options Panel */}
            <div className="export-options">
              <select 
                value={exportOptions.format} 
                onChange={(e) => handleExportOptionChange('format', e.target.value)}
                className="export-select"
                disabled={segments.length === 0}
              >
                <option value="mp4">MP4</option>
                <option value="avi">AVI</option>
                <option value="mov">MOV</option>
              </select>
              
              <select 
                value={exportOptions.quality} 
                onChange={(e) => handleExportOptionChange('quality', e.target.value)}
                className="export-select"
                disabled={segments.length === 0}
              >
                <option value="low">Low Quality</option>
                <option value="medium">Medium Quality</option>
                <option value="high">High Quality</option>
              </select>
              
              <select 
                value={exportOptions.resolution} 
                onChange={(e) => handleExportOptionChange('resolution', e.target.value)}
                className="export-select"
                disabled={segments.length === 0}
              >
                <option value="original">Original Resolution</option>
                <option value="720p">720p HD</option>
                <option value="1080p">1080p Full HD</option>
              </select>
            </div>
            
            <button
              onClick={() => handleExport('merge')}
              disabled={segments.length === 0 || isExporting}
              className="btn btn-primary"
            >
              <Download size={18} />
              {isExporting ? 'Exporting...' : 'Export Merged'}
            </button>
            <button
              onClick={() => handleExport('batch')}
              disabled={segments.length === 0 || isExporting}
              className="btn btn-secondary"
            >
              <FileVideo size={18} />
              {isExporting ? 'Exporting...' : 'Export Batch'}
            </button>
          </div>
        </div>
      </header>

      <main className="main">
        <div className="main-grid">
          {/* Left Column - Upload and Video List */}
          <div className="left-column">
            {/* Upload Section */}
            <div className="card upload-card">
              <h2 className="card-title">
                <Upload size={20} />
                Upload Media Files
              </h2>
              
              <div
                className="upload-area"
                onClick={() => fileInputRef.current?.click()}
                onDrop={(e) => {
                  e.preventDefault();
                  handleFileUpload(e.dataTransfer.files);
                }}
                onDragOver={(e) => e.preventDefault()}
              >
                <FileVideo size={40} className="upload-icon" />
                <p className="upload-text">Drop videos or audio files here</p>
                <p className="upload-subtext">or click to browse</p>
                <p className="upload-hint">Supports MP4, MOV, AVI, WAV, MP3</p>
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  accept="video/*,audio/*"
                  className="hidden-input"
                  onChange={(e) => handleFileUpload(e.target.files)}
                />
              </div>
            </div>

            {/* Audio Converter Plugin Section */}
            <div className="card plugin-card">
              <h2 className="card-title">
                <Download size={20} />
                Audio Converter Plugin
              </h2>
              
              <div className="plugin-content">
                <div className="plugin-info">
                  <h3>Convert Videos Locally - Upload 90% Less Data</h3>
                  <p className="plugin-description">
                    Use our local audio converter to transform videos to WAV format before uploading. 
                    This reduces upload time, saves bandwidth, and protects your privacy.
                  </p>
                  
                  <div className="plugin-benefits">
                    <div className="benefit-item">
                      <span className="benefit-icon">🚀</span>
                      <div>
                        <strong>90% Faster Upload</strong>
                        <p>Upload audio instead of full video</p>
                      </div>
                    </div>
                    <div className="benefit-item">
                      <span className="benefit-icon">💰</span>
                      <div>
                        <strong>Reduce Costs</strong>
                        <p>Less bandwidth and storage usage</p>
                      </div>
                    </div>
                    <div className="benefit-item">
                      <span className="benefit-icon">🔒</span>
                      <div>
                        <strong>Privacy First</strong>
                        <p>Video files never leave your computer</p>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="plugin-actions">
                  <button 
                    className="btn btn-primary plugin-download-btn"
                    onClick={() => {
                      // Create download link for the converter
                      const link = document.createElement('a');
                      link.href = '/audio_converter.py';
                      link.download = 'scriptsor_audio_converter.py';
                      link.click();
                    }}
                  >
                    <Download size={16} />
                    Download Converter
                  </button>
                  
                  <a 
                    href="/AUDIO_CONVERTER_README.md" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="btn btn-secondary plugin-docs-btn"
                  >
                    View Instructions
                  </a>
                </div>
              </div>
            </div>

            {/* Video List */}
            {videos.length > 0 && (
              <div className="card video-list-card">
                <h3 className="card-subtitle">
                  <Play size={18} />
                  Uploaded Videos
                </h3>
                <div className="video-list">
                  {videos.map((video) => (
                    <div key={video.id} className="video-item">
                      <div className="video-icon">
                        <FileVideo size={16} />
                      </div>
                      <div className="video-info">
                        <p className="video-name">{video.name}</p>
                        <p className="video-duration">{(video.size / (1024 * 1024)).toFixed(2)} MB</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Processing Status */}
            {isProcessing && processingStatus && (
              <div className="card processing-card">
                <div className="processing-content">
                  <div className="spinner"></div>
                  <div>
                    <h3 className="processing-title">Processing Videos</h3>
                    <p className="processing-text">{processingStatus.message}</p>
                    <div className="progress-bar">
                      <div 
                        className="progress-fill" 
                        style={{ width: `${processingStatus.progress}%` }}
                      ></div>
                    </div>
                    <p className="progress-text">{processingStatus.progress}%</p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Middle Column - Transcript Editing */}
          <div className="middle-column">
            {segments.length > 0 ? (
              <div className="card edit-card">
                <div className="edit-header">
                  <div className="edit-header-main">
                    <h2 className="card-title">
                      <Mic size={20} />
                      Edit Transcripts
                    </h2>
                    <button 
                      onClick={handleReprocess}
                      disabled={isProcessing || !currentVideoId}
                      className="btn btn-secondary"
                      title="重新处理视频以修复时间戳问题"
                    >
                      <RefreshCw size={16} />
                      重新处理
                    </button>
                  </div>
                  <div className="edit-hint">
                    Drag to reorder • Edit text directly • Type "---" to split segment
                  </div>
                </div>
                
                <div className="segments-container">
                  {segments
                    .sort((a, b) => a.order - b.order)
                    .map((segment, index) => (
                      <div
                        key={`${segment.id}-${segment.order}-${index}`}
                        draggable
                        onDragStart={(e) => handleDragStart(e, segment.order)}
                        onDragOver={handleDragOver}
                        onDrop={(e) => handleDrop(e, index)}
                        className="segment-item"
                      >
                        <div className="segment-drag-handle">
                          <Move size={16} />
                        </div>
                        <div className="segment-content">
                          <div className="segment-header">
                            <div className="segment-number">{index + 1}</div>
                            <span className="segment-time">
                              {segment.start_time?.toFixed(1)}s - {segment.end_time?.toFixed(1)}s
                            </span>
                          </div>
                          <textarea
                            value={segment.text}
                            onChange={(e) => {
                              const newText = e.target.value;
                              handleSegmentChange(segment.id, newText);
                            }}
                            className="segment-textarea"
                            rows="3"
                            placeholder="Edit transcript text... (Type --- to split)"
                          />
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            ) : (
              <div className="card welcome-card">
                <div className="welcome-content">
                  <div className="welcome-icon">
                    <FileVideo size={32} />
                  </div>
                  <h3 className="welcome-title">Get Started</h3>
                  <p className="welcome-text">
                    Upload your videos to begin editing with text. 
                    Our AI will automatically transcribe your audio and create editable segments.
                  </p>
                  <div className="welcome-steps">
                    <div className="step-item">
                      <CheckCircle size={16} className="step-icon" />
                      <span className="step-text">Upload video files</span>
                    </div>
                    <div className="step-item">
                      <CheckCircle size={16} className="step-icon" />
                      <span className="step-text">Automatic transcription</span>
                    </div>
                    <div className="step-item">
                      <CheckCircle size={16} className="step-icon" />
                      <span className="step-text">Edit and reorder with text</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Preview Section */}
        {segments.length > 0 && (
          <div className="preview-section">
            <div className="card preview-card">
              <h2 className="card-title">Preview Order</h2>
              
              <div className="preview-grid">
                {segments
                  .sort((a, b) => a.order - b.order)
                  .map((segment, index) => (
                    <div key={`${segment.id}-${segment.order}-${index}`} className="preview-item">
                      <div className="preview-header">
                        <div className="preview-number">{index + 1}</div>
                        <span className="preview-time">
                          {segment.start_time?.toFixed(1)}s - {segment.end_time?.toFixed(1)}s
                        </span>
                      </div>
                      <p className="preview-text">{segment.text}</p>
                    </div>
                  ))}
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Export Progress Modal */}
      {isExporting && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3>Exporting Video</h3>
            </div>
            <div className="modal-body">
              <div className="export-progress">
                <div className="progress-info">
                  <p>Processing your video with the following settings:</p>
                  <div className="export-settings">
                    <span>Format: {exportOptions.format.toUpperCase()}</span>
                    <span>Quality: {exportOptions.quality}</span>
                    <span>Resolution: {exportOptions.resolution}</span>
                  </div>
                </div>
                <div className="progress-bar">
                  <div 
                    className="progress-fill" 
                    style={{ width: `${exportProgress}%` }}
                  ></div>
                </div>
                <p className="progress-text">{exportProgress}% Complete</p>
                <div className="export-steps">
                  <div className={`step ${exportProgress >= 25 ? 'completed' : ''}`}>
                    <div className="step-icon">📝</div>
                    <span>Preparing segments</span>
                  </div>
                  <div className={`step ${exportProgress >= 50 ? 'completed' : ''}`}>
                    <div className="step-icon">🎬</div>
                    <span>Processing video</span>
                  </div>
                  <div className={`step ${exportProgress >= 75 ? 'completed' : ''}`}>
                    <div className="step-icon">🔧</div>
                    <span>Applying settings</span>
                  </div>
                  <div className={`step ${exportProgress >= 100 ? 'completed' : ''}`}>
                    <div className="step-icon">✅</div>
                    <span>Finalizing export</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="footer">
        <div className="footer-content">
          <p>Text-Driven Video Editor • Edit videos through simple text manipulation</p>
        </div>
      </footer>
    </div>
  );
};

export default App;