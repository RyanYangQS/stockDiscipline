#!/bin/bash

# 股票交易纪律系统启动脚本

echo "========================================"
echo "  股票交易纪律系统 - 启动脚本"
echo "========================================"

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python3.11+"
    exit 1
fi

# 检查Node.js
if ! command -v node &> /dev/null; then
    echo "错误: 未找到Node.js，请先安装Node.js 18+"
    exit 1
fi

echo ""
echo "正在启动后端服务..."

# 启动后端
cd backend

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 检查依赖
if [ ! -f "venv/lib/python*/site-packages/fastapi/__init__.py" ]; then
    echo "安装后端依赖..."
    pip install -r requirements.txt
fi

# 创建数据目录
mkdir -p data logs

# 初始化数据
if [ ! -f "data/stock_discipline.db" ]; then
    echo "初始化数据库..."
    python init_data.py
fi

# 启动后端服务（后台运行）
echo "启动FastAPI服务..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

cd ..

echo ""
echo "正在启动前端服务..."

# 启动前端
cd frontend

# 检查依赖
if [ ! -d "node_modules" ]; then
    echo "安装前端依赖..."
    npm install
fi

# 启动前端服务（后台运行）
echo "启动Vite开发服务器..."
npm run dev &
FRONTEND_PID=$!

cd ..

echo ""
echo "========================================"
echo "  服务启动完成！"
echo "========================================"
echo ""
echo "后端API文档: http://localhost:8000/docs"
echo "前端页面:    http://localhost:3000"
echo ""
echo "按 Ctrl+C 停止所有服务"
echo ""

# 等待用户中断
trap "echo '正在停止服务...'; kill $BACKEND_PID $FRONTEND_PID; exit 0" INT TERM

# 保持脚本运行
wait
