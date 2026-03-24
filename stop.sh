#!/bin/bash

# 停止所有服务

echo "正在停止服务..."

# 读取PID并停止
if [ -f "logs/backend.pid" ]; then
    BACKEND_PID=$(cat logs/backend.pid)
    kill $BACKEND_PID 2>/dev/null && echo "✅ 后端服务已停止"
    rm -f logs/backend.pid
fi

if [ -f "logs/frontend.pid" ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    kill $FRONTEND_PID 2>/dev/null && echo "✅ 前端服务已停止"
    rm -f logs/frontend.pid
fi

# 强制清理残留进程
pkill -f "uvicorn app.main:app" 2>/dev/null
pkill -f "vite.*port=3000" 2>/dev/null

echo ""
echo "✅ 所有服务已停止"
