# ScriptSor - Text-Driven Video Editor

A revolutionary video editing tool that allows you to edit videos through simple text manipulation. Upload your videos, get automatic transcription, and edit by rearranging text segments.

## 🌟 Features

- **Automatic Transcription**: AI-powered speech-to-text using Tencent Cloud API
- **Text-Based Editing**: Edit videos by manipulating text segments
- **Drag & Drop Interface**: Intuitive segment reordering
- **Real-time Processing**: Background video processing with progress tracking
- **Multiple Export Options**: Support for various formats and quality settings
- **Batch Processing**: Export individual segments or merged videos
- **Segment Splitting**: Split segments by typing "---" in the text editor

## 🏗️ Architecture

```
├── frontend/              # React + Vite frontend
│   └── scriptCut/         # Main frontend application
├── backend/               # FastAPI backend (Python)
│   ├── main.py           # Main application
│   ├── video_processor.py # Video processing logic
│   ├── models.py         # Data models
│   └── schemas.py        # API schemas
├── Dockerfile            # Backend container configuration
├── render.yaml           # Render deployment configuration
└── requirements.txt      # Python dependencies
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- FFmpeg (installed with Docker)
- Tencent Cloud API credentials

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/hohohin/scriptssor.git
   cd scriptssor
   ```

2. **Backend Setup**
   ```bash
   # Install Python dependencies
   pip install -r requirements.txt
   
   # Configure environment variables
   cp .env.example .env
   # Edit .env with your Tencent Cloud credentials
   
   # Start the backend
   python main.py
   ```

3. **Frontend Setup**
   ```bash
   cd frontend/scriptCut
   
   # Install dependencies
   npm install
   
   # Install missing lucide-react dependency
   npm install lucide-react
   
   # Start development server
   npm run dev
   ```

4. **Access the Application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:9002

## 🌐 Render Deployment

### Step 1: Prepare Your Repository

Ensure your repository contains:
- `Dockerfile` - Backend container configuration
- `render.yaml` - Render Blueprint configuration
- `requirements.txt` - Python dependencies
- `.env.example` - Environment variables template

### Step 2: Create Render Service

1. **Sign in to Render Dashboard**
   - Go to [dashboard.render.com](https://dashboard.render.com)
   - Sign in with your GitHub account

2. **Create New Web Service**
   - Click "New +" button
   - Select "Web Service"
   - Connect your GitHub repository
   - Select the `scriptssor` repository

3. **Configure Build Script**
   In the Render service configuration, set the following build script:

   ```bash
   #!/bin/bash
   
   # Set environment variables
   export PORT=10000
   export PYTHONUNBUFFERED=1
   
   # Install system dependencies
   apt-get update && apt-get install -y \
       ffmpeg \
       libsndfile1 \
       gcc \
       && rm -rf /var/lib/apt/lists/*
   
   # Install Python dependencies
   pip install --no-cache-dir -r requirements.txt
   
   # Create necessary directories
   mkdir -p uploads temp
   
   # Start the application
   python main.py
   ```

4. **Environment Variables**
   Add these environment variables in Render dashboard:

   ```bash
   # Application Configuration
   PORT=10000
   ENVIRONMENT=production
   
   # Tencent Cloud API (Required)
   TENCENT_SECRET_ID=your_actual_secret_id
   TENCENT_SECRET_KEY=your_actual_secret_key
   
   # CORS Configuration
   ALLOWED_ORIGINS=https://your-frontend-domain.com
   
   # File Storage
   UPLOAD_DIR=uploads
   TEMP_DIR=temp
   MAX_FILE_SIZE=500000000
   ```

5. **Service Configuration**
   - **Name**: `scriptssor-backend`
   - **Environment**: `Docker`
   - **Build Command**: Leave empty (using Dockerfile)
   - **Start Command**: `/app/start.sh`
   - **Port**: `10000`

6. **Persistent Storage**
   - Add a disk with 10GB mounted to `/app/temp`
   - This ensures temporary files persist during processing

### Step 3: Frontend Deployment

#### Option 1: GitHub Pages (Recommended)

1. **Build Frontend**
   ```bash
   cd frontend/scriptCut
   
   # Install dependencies
   npm install
   npm install lucide-react
   
   # Build with production API URL
   export VITE_API_BASE_URL=https://your-backend.onrender.com
   npm run build
   ```

2. **Deploy to GitHub Pages**
   - Copy the contents of `dist/` to your `gh-pages` branch
   - Enable GitHub Pages in repository settings
   - Set source to `gh-pages` branch

#### Option 2: Netlify/Vercel

1. **Connect your repository** to Netlify or Vercel
2. **Set build command**: `cd frontend/scriptCut && npm install && npm install lucide-react && npm run build`
3. **Set publish directory**: `frontend/scriptCut/dist`
4. **Add environment variable**: `VITE_API_BASE_URL=https://your-backend.onrender.com`

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TENCENT_SECRET_ID` | Tencent Cloud API Secret ID | Yes |
| `TENCENT_SECRET_KEY` | Tencent Cloud API Secret Key | Yes |
| `PORT` | Application port | No (default: 10000) |
| `ENVIRONMENT` | Runtime environment | No (default: production) |
| `ALLOWED_ORIGINS` | CORS allowed origins | No |
| `MAX_FILE_SIZE` | Maximum upload file size | No (default: 500MB) |

### Tencent Cloud API Setup

1. **Create Tencent Cloud Account**
   - Sign up at [Tencent Cloud](https://cloud.tencent.com/)
   - Complete identity verification

2. **Enable Speech Recognition Service**
   - Go to Console > AI > Speech Recognition
   - Enable the service
   - Create API credentials

3. **Get Credentials**
   - Access Key Management
   - Create sub-user with speech recognition permissions
   - Note down SecretId and SecretKey

## 📚 API Documentation

### Core Endpoints

#### Upload Video
```http
POST /upload
Content-Type: multipart/form-data
```

#### Get Transcript
```http
GET /videos/{video_id}/transcript
```

#### Edit Segment
```http
PUT /segments/{segment_id}
Content-Type: application/json

{
  "new_text": "Updated transcript text"
}
```

#### Reorder Segments
```http
POST /videos/{video_id}/reorder
Content-Type: application/json

{
  "segment_ids": ["id1", "id2", "id3"]
}
```

#### Export Video
```http
POST /videos/{video_id}/export
Content-Type: application/json

{
  "mode": "merge",
  "segment_order": ["id1", "id2", "id3"],
  "format": "mp4",
  "quality": "medium",
  "resolution": "original"
}
```

### Response Formats

All API responses follow JSON format with appropriate HTTP status codes:

```json
{
  "video_id": "uuid",
  "filename": "video.mp4",
  "size": 1024000,
  "upload_time": "2025-01-01T00:00:00Z"
}
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Frontend Build Fails
```bash
# Missing lucide-react dependency
cd frontend/scriptCut
npm install lucide-react
npm run build
```

#### 2. Backend Processing Errors
- Check Tencent Cloud API credentials
- Verify FFmpeg is installed
- Ensure sufficient disk space
- Check file size limits

#### 3. CORS Issues
- Verify `ALLOWED_ORIGINS` environment variable
- Check frontend API base URL configuration
- Ensure proper CORS middleware configuration

#### 4. Render Deployment Issues
- Check build logs for dependency installation errors
- Verify environment variables are correctly set
- Ensure disk storage is properly configured

### Performance Optimization

1. **Video Processing**
   - Use appropriate video formats (MP4 recommended)
   - Limit video file size to 500MB
   - Optimize FFmpeg parameters

2. **Frontend Performance**
   - Use production builds for deployment
   - Implement proper caching strategies
   - Optimize bundle size

3. **Backend Performance**
   - Monitor memory usage during video processing
   - Implement proper cleanup of temporary files
   - Use background tasks for long-running operations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the ISC License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
- Create an issue on GitHub
- Check the troubleshooting section above
- Verify your configuration matches the requirements

## 🎯 Roadmap

- [ ] Enhanced video editing features
- [ ] Multi-language support
- [ ] Advanced AI-powered editing
- [ ] Real-time collaboration
- [ ] Mobile app development
- [ ] Additional export formats

---

**Built with ❤️ using React, FastAPI, and Tencent Cloud AI**