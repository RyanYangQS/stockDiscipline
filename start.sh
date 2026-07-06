#!/bin/bash

# Stock Discipline - 统一启动脚本

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

echo "=== Stock Discipline 启动 ==="

# 检查依赖
check_dependencies() {
    echo "检查 Python 依赖..."
    if ! python3 -c "import akshare" 2>/dev/null; then
        echo "  [可选] AKShare 未安装: pip3 install akshare"
    fi
    if ! python3 -c "import requests, bs4" 2>/dev/null; then
        echo "  [可选] requests/beautifulsoup4 未安装: pip3 install requests beautifulsoup4"
    fi

    echo "检查前端依赖..."
    if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
        echo "  安装前端依赖..."
        cd "$FRONTEND_DIR" && npm install
    fi
}

# 停止旧进程
stop_old_processes() {
    echo "停止旧进程..."
    lsof -i :8080-8089 -i :5173-5179 | grep LISTEN | awk '{print $2}' | xargs -I {} kill -9 {} 2>/dev/null
    sleep 1
}

# 启动后端
start_backend() {
    echo "启动后端服务器..."
    cd "$BACKEND_DIR"
    python3 run.py &
    BACKEND_PID=$!
    sleep 2
    echo "后端 PID: $BACKEND_PID"
}

# 启动前端
start_frontend() {
    echo "启动前端开发服务器..."
    cd "$FRONTEND_DIR"
    npm run dev &
    FRONTEND_PID=$!
    sleep 2
    echo "前端 PID: $FRONTEND_PID"
}

# 主流程
check_dependencies
stop_old_processes
start_backend
start_frontend

echo ""
echo "=== 启动完成 ==="
echo "后端: http://127.0.0.1:8080 (或更高端口)"
echo "前端: http://127.0.0.1:5173 (或更高端口)"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 等待子进程
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM
wait
