#!/bin/bash

# 创建必要的目录
mkdir -p uploads temp

# 设置环境变量
export PYTHONPATH=/app
export PYTHONUNBUFFERED=1

# 等待数据库/其他服务就绪
echo "Starting application..."

# 启动应用
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}