#!/bin/bash

# GitHub Pages 部署脚本
# 用于将构建后的前端部署到 GitHub Pages

set -e

echo "🚀 开始部署到 GitHub Pages..."

# 检查是否在正确的分支
current_branch=$(git branch --show-current)
if [ "$current_branch" != "main" ]; then
    echo "❌ 请在 main 分支上执行此脚本"
    exit 1
fi

# 构建前端
echo "🏗️  构建前端应用..."
./build-frontend.sh

# 创建临时目录
mkdir -p gh-pages

# 复制构建文件
echo "📋 复制构建文件..."
cp -r dist/* gh-pages/

# 创建或切换到 gh-pages 分支
if git show-ref --verify --quiet refs/heads/gh-pages; then
    git checkout gh-pages
    git pull origin gh-pages
else
    git checkout --orphan gh-pages
    git rm -rf .
    touch .nojekyll
    echo "# Scriptssor Frontend" > README.md
    echo "静态前端页面，部署在 GitHub Pages" >> README.md
fi

# 复制构建文件
cp -r gh-pages/* .
rm -rf gh-pages

# 添加并提交
git add .
git commit -m "Deploy frontend to GitHub Pages

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# 推送到 GitHub
echo "📤 推送到 GitHub..."
git push origin gh-pages

# 切换回 main 分支
git checkout main

echo "✅ 部署完成！"
echo "🌐 前端将在几分钟后通过以下地址访问:"
echo "   https://hohohin.github.io/scriptssor/"

echo ""
echo "⚠️  注意事项:"
echo "   1. 确保在 GitHub 仓库设置中启用了 GitHub Pages"
echo "   2. 选择 gh-pages 分支作为源"
echo "   3. 首次部署可能需要等待 5-10 分钟生效"