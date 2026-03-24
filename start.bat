@echo off
REM 股票交易纪律系统启动脚本 (Windows)

echo ========================================
echo   股票交易纪律系统 - 启动脚本
echo ========================================

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python3.11+
    exit /b 1
)

REM 检查Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Node.js，请先安装Node.js 18+
    exit /b 1
)

echo.
echo 正在启动后端服务...

cd backend

REM 检查虚拟环境
if not exist "venv" (
    echo 创建虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
call venv\Scripts\activate

REM 安装依赖
pip install -r requirements.txt

REM 创建数据目录
if not exist "data" mkdir data
if not exist "logs" mkdir logs

REM 初始化数据
if not exist "data\stock_discipline.db" (
    echo 初始化数据库...
    python init_data.py
)

REM 启动后端服务
echo 启动FastAPI服务...
start "Backend" cmd /c uvicorn app.main:app --host 0.0.0.0 --port 8000

cd ..

echo.
echo 正在启动前端服务...

cd frontend

REM 安装依赖
if not exist "node_modules" (
    echo 安装前端依赖...
    call npm install
)

REM 启动前端服务
echo 启动Vite开发服务器...
start "Frontend" cmd /c npm run dev

cd ..

echo.
echo ========================================
echo   服务启动完成！
echo ========================================
echo.
echo 后端API文档: http://localhost:8000/docs
echo 前端页面:    http://localhost:3000
echo.
echo 按任意键退出此窗口（服务将继续运行）
pause >nul
