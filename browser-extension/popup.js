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
            video.muted = true; // Mute video to avoid audio feedback
            
            video.onloadedmetadata = () => {
                this.updateProgress(10, 'Loading video...');
                
                // Create audio element source
                const audioElement = new Audio();
                audioElement.src = video.src;
                audioElement.crossOrigin = 'anonymous';
                
                // Use regular AudioContext for real-time processing
                const source = audioContext.createMediaElementSource(audioElement);
                const destination = audioContext.destination;
                const analyser = audioContext.createAnalyser();
                
                source.connect(analyser);
                analyser.connect(destination);
                
                // Create offline context for final rendering
                const duration = video.duration;
                const sampleRate = 16000;
                const channels = 1;
                const frameCount = Math.floor(duration * sampleRate);
                const offlineContext = new OfflineAudioContext(channels, frameCount, sampleRate);
                
                // Create buffer to capture audio data
                const bufferLength = analyser.frequencyBinCount;
                const dataArray = new Uint8Array(bufferLength);
                const audioData = [];
                
                audioElement.oncanplay = () => {
                    this.updateProgress(20, 'Starting conversion...');
                    
                    // Start playback
                    audioElement.play().then(() => {
                        this.updateProgress(30, 'Processing audio...');
                        
                        // Capture audio data during playback
                        const captureInterval = setInterval(() => {
                            analyser.getByteTimeDomainData(dataArray);
                            audioData.push(new Uint8Array(dataArray));
                            
                            // Update progress based on playback position
                            const progress = Math.min(80, 30 + (audioElement.currentTime / duration) * 50);
                            this.updateProgress(progress, 'Processing audio...');
                            
                        }, 100); // Capture every 100ms
                        
                        audioElement.onended = () => {
                            clearInterval(captureInterval);
                            
                            // Process captured audio data
                            this.processCapturedAudio(audioData, sampleRate, channels, duration)
                                .then((renderedBuffer) => {
                                    this.updateProgress(80, 'Finalizing...');
                                    
                                    // Convert to WAV
                                    const wavBlob = this.audioBufferToWav(renderedBuffer);
                                    
                                    this.updateProgress(100, 'Complete!');
                                    
                                    setTimeout(() => {
                                        URL.revokeObjectURL(video.src);
                                        resolve(wavBlob);
                                    }, 500);
                                })
                                .catch((error) => {
                                    reject(new Error('Audio processing failed: ' + error.message));
                                });
                        };
                        
                    }).catch((error) => {
                        reject(new Error('Audio playback failed: ' + error.message));
                    });
                };
                
                audioElement.onerror = () => {
                    reject(new Error('Audio loading failed'));
                };
            };
            
            video.onerror = () => {
                reject(new Error('Video metadata loading failed'));
            };
        });
    }
    
    async processCapturedAudio(audioData, sampleRate, channels, duration) {
        return new Promise((resolve, reject) => {
            try {
                // Create offline audio context
                const frameCount = Math.floor(duration * sampleRate);
                const offlineContext = new OfflineAudioContext(channels, frameCount, sampleRate);
                
                // Create audio buffer from captured data
                const audioBuffer = offlineContext.createBuffer(channels, frameCount, sampleRate);
                const channelData = audioBuffer.getChannelData(0);
                
                // Process captured audio data
                let sampleIndex = 0;
                const samplesPerCapture = audioData.length > 0 ? audioData[0].length : 0;
                const totalSamples = audioData.length * samplesPerCapture;
                
                for (let i = 0; i < audioData.length && sampleIndex < frameCount; i++) {
                    const captureData = audioData[i];
                    
                    // Convert 8-bit data to float (-1 to 1)
                    for (let j = 0; j < captureData.length && sampleIndex < frameCount; j++) {
                        // Convert 0-255 to -1 to 1
                        const sample = (captureData[j] - 128) / 128;
                        channelData[sampleIndex] = sample;
                        sampleIndex++;
                    }
                }
                
                // If we didn't get enough data, fill with silence
                while (sampleIndex < frameCount) {
                    channelData[sampleIndex] = 0;
                    sampleIndex++;
                }
                
                resolve(audioBuffer);
            } catch (error) {
                reject(error);
            }
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