class AudioConverter {
    constructor() {
        this.originalFile = null;
        this.wavBlob = null;
        this.isProcessing = false;
        
        this.initElements();
        this.bindEvents();
    }
    
    initElements() {
        this.uploadArea = document.getElementById('uploadArea');
        this.fileInput = document.getElementById('fileInput');
        this.processing = document.getElementById('processing');
        this.result = document.getElementById('result');
        this.error = document.getElementById('error');
        this.progressFill = document.getElementById('progressFill');
        this.statusText = document.getElementById('statusText');
        this.uploadBtn = document.getElementById('uploadBtn');
        this.newFileBtn = document.getElementById('newFileBtn');
        
        // Result elements
        this.originalSize = document.getElementById('originalSize');
        this.wavSize = document.getElementById('wavSize');
        this.compression = document.getElementById('compression');
    }
    
    bindEvents() {
        // File upload events
        this.uploadArea.addEventListener('click', () => this.fileInput.click());
        this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        
        // Drag and drop events
        this.uploadArea.addEventListener('dragover', (e) => this.handleDragOver(e));
        this.uploadArea.addEventListener('dragleave', (e) => this.handleDragLeave(e));
        this.uploadArea.addEventListener('drop', (e) => this.handleDrop(e));
        
        // Button events
        this.uploadBtn.addEventListener('click', () => this.uploadToScriptSor());
        this.newFileBtn.addEventListener('click', () => this.reset());
    }
    
    handleDragOver(e) {
        e.preventDefault();
        this.uploadArea.classList.add('dragover');
    }
    
    handleDragLeave(e) {
        e.preventDefault();
        this.uploadArea.classList.remove('dragover');
    }
    
    handleDrop(e) {
        e.preventDefault();
        this.uploadArea.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            this.processFile(files[0]);
        }
    }
    
    handleFileSelect(e) {
        const file = e.target.files[0];
        if (file) {
            this.processFile(file);
        }
    }
    
    async processFile(file) {
        if (!file.type.startsWith('video/')) {
            this.showError('Please select a video file');
            return;
        }
        
        if (file.size > 500 * 1024 * 1024) { // 500MB limit
            this.showError('File size must be less than 500MB');
            return;
        }
        
        this.originalFile = file;
        this.hideError();
        this.showProcessing();
        
        try {
            this.wavBlob = await this.convertVideoToWav(file);
            this.showResult();
        } catch (error) {
            this.showError('Conversion failed: ' + error.message);
            this.reset();
        }
    }
    
    async convertVideoToWav(videoFile) {
        return new Promise((resolve, reject) => {
            const video = document.createElement('video');
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            
            video.src = URL.createObjectURL(videoFile);
            video.crossOrigin = 'anonymous';
            
            video.onloadedmetadata = () => {
                this.updateProgress(10, 'Loading video...');
                
                const duration = video.duration;
                const sampleRate = 16000;
                const channels = 1;
                const frameCount = Math.floor(duration * sampleRate);
                
                // Create offline audio context for rendering
                const offlineContext = new OfflineAudioContext(channels, frameCount, sampleRate);
                const source = offlineContext.createMediaElementSource(video);
                const destination = offlineContext.destination;
                
                source.connect(destination);
                
                video.oncanplay = () => {
                    this.updateProgress(20, 'Starting conversion...');
                    
                    // Start video playback
                    video.play().then(() => {
                        this.updateProgress(30, 'Processing audio...');
                        
                        // Start offline rendering
                        offlineContext.startRendering().then((renderedBuffer) => {
                            this.updateProgress(80, 'Finalizing...');
                            
                            // Convert to WAV
                            const wavBlob = this.audioBufferToWav(renderedBuffer);
                            
                            this.updateProgress(100, 'Complete!');
                            
                            setTimeout(() => {
                                URL.revokeObjectURL(video.src);
                                resolve(wavBlob);
                            }, 500);
                            
                        }).catch((error) => {
                            reject(new Error('Audio rendering failed: ' + error.message));
                        });
                        
                    }).catch((error) => {
                        reject(new Error('Video playback failed: ' + error.message));
                    });
                };
                
                video.onerror = () => {
                    reject(new Error('Video loading failed'));
                };
            };
            
            video.onerror = () => {
                reject(new Error('Video metadata loading failed'));
            };
        });
    }
    
    audioBufferToWav(buffer) {
        const length = buffer.length;
        const numberOfChannels = buffer.numberOfChannels;
        const sampleRate = buffer.sampleRate;
        const arrayBuffer = new ArrayBuffer(44 + length * numberOfChannels * 2);
        const view = new DataView(arrayBuffer);
        
        // WAV header
        const writeString = (offset, string) => {
            for (let i = 0; i < string.length; i++) {
                view.setUint8(offset + i, string.charCodeAt(i));
            }
        };
        
        writeString(0, 'RIFF');
        view.setUint32(4, 36 + length * numberOfChannels * 2, true);
        writeString(8, 'WAVE');
        writeString(12, 'fmt ');
        view.setUint32(16, 16, true);
        view.setUint16(20, 1, true);
        view.setUint16(22, numberOfChannels, true);
        view.setUint32(24, sampleRate, true);
        view.setUint32(28, sampleRate * numberOfChannels * 2, true);
        view.setUint16(32, numberOfChannels * 2, true);
        view.setUint16(34, 16, true);
        writeString(36, 'data');
        view.setUint32(40, length * numberOfChannels * 2, true);
        
        // Convert float samples to 16-bit PCM
        let offset = 44;
        for (let i = 0; i < length; i++) {
            for (let channel = 0; channel < numberOfChannels; channel++) {
                const sample = Math.max(-1, Math.min(1, buffer.getChannelData(channel)[i]));
                view.setInt16(offset, sample * 0x7FFF, true);
                offset += 2;
            }
        }
        
        return new Blob([arrayBuffer], { type: 'audio/wav' });
    }
    
    updateProgress(percent, status) {
        this.progressFill.style.width = percent + '%';
        this.statusText.textContent = status;
    }
    
    showProcessing() {
        this.uploadArea.style.display = 'none';
        this.result.style.display = 'none';
        this.processing.style.display = 'block';
        this.error.style.display = 'none';
    }
    
    showResult() {
        this.uploadArea.style.display = 'none';
        this.processing.style.display = 'none';
        this.result.style.display = 'block';
        this.error.style.display = 'none';
        
        // Update file info
        this.originalSize.textContent = this.formatFileSize(this.originalFile.size);
        this.wavSize.textContent = this.formatFileSize(this.wavBlob.size);
        
        const compressionRatio = ((this.originalFile.size - this.wavBlob.size) / this.originalFile.size * 100).toFixed(1);
        this.compression.textContent = compressionRatio + '% smaller';
    }
    
    showError(message) {
        this.error.textContent = message;
        this.error.style.display = 'block';
    }
    
    hideError() {
        this.error.style.display = 'none';
    }
    
    reset() {
        this.uploadArea.style.display = 'block';
        this.processing.style.display = 'none';
        this.result.style.display = 'none';
        this.error.style.display = 'none';
        
        this.fileInput.value = '';
        this.originalFile = null;
        this.wavBlob = null;
        this.isProcessing = false;
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    async uploadToScriptSor() {
        if (!this.wavBlob) return;
        
        try {
            // Create form data
            const formData = new FormData();
            const wavFile = new File([this.wavBlob], this.originalFile.name.replace(/\.[^/.]+$/, '.wav'), {
                type: 'audio/wav'
            });
            formData.append('file', wavFile);
            
            // Send to backend
            const response = await fetch('https://scriptssor.onrender.com/upload', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                const result = await response.json();
                
                // Open ScriptSor in new tab with the video ID
                chrome.tabs.create({
                    url: `https://scriptssor-frontend.onrender.com/?video_id=${result.video_id}`
                });
                
                // Close popup
                window.close();
            } else {
                throw new Error('Upload failed');
            }
        } catch (error) {
            this.showError('Upload failed: ' + error.message);
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new AudioConverter();
});