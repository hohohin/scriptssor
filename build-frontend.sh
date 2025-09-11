#!/bin/bash

# 前端构建脚本
# 用于构建生产版本的前端应用

set -e

echo "🚀 开始构建前端应用..."

# 进入前端目录
cd frontend/scriptCut

# 安装依赖
echo "📦 安装依赖..."
npm install

# 设置生产环境API地址
echo "🔧 设置生产环境API地址..."
export VITE_API_BASE_URL="https://scriptssor.onrender.com"

# 构建应用
echo "🏗️  构建应用..."
npm run build

# 创建部署目录
cd ../../
mkdir -p dist

# 复制构建文件
echo "📋 复制构建文件..."
cp -r frontend/scriptCut/dist/* dist/

# 创建 .nojekyll 文件（GitHub Pages 需要）
touch dist/.nojekyll

echo "✅ 前端构建完成！"
echo "📁 构建文件位于: ./dist/"
echo "🌐 可以通过以下方式部署:"
echo "   - GitHub Pages"
echo "   - Netlify"
echo "   - Vercel"
echo "   - 任何静态文件托管服务"