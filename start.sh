#!/bin/bash

# 股票交易纪律系统 - 智能一键启动脚本
# 自动检测环境、安装依赖、启动服务

set -e  # 遇到错误立即退出

echo "╔════════════════════════════════════════╗"
echo "║  📈 股票交易纪律系统 - 智能启动        ║"
echo "╚════════════════════════════════════════╝"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示进度
show_progress() {
    local current=$1
    local total=$2
    local task=$3
    echo -e "${GREEN}[$current/$total]${NC} $task"
}

# ============================================
# 步骤1: 检查基础环境
# ============================================
log_info "检查基础环境..."

if ! command -v python3 &> /dev/null; then
    log_error "未找到Python3，请先安装Python 3.11+"
    exit 1
fi
log_success "Python3: $(python3 --version)"

if ! command -v node &> /dev/null; then
    log_error "未找到Node.js，请先安装Node.js 18+"
    exit 1
fi
log_success "Node.js: $(node --version)"

echo ""

# ============================================
# 步骤2: 准备后端环境
# ============================================
log_info "准备后端环境..."
cd backend

# 创建虚拟环境
if [ ! -d "venv" ]; then
    log_info "创建虚拟环境..."
    python3 -m venv venv
    log_success "虚拟环境创建完成"
fi

# 激活虚拟环境
source venv/bin/activate

# 临时禁用代理
export http_proxy=""
export https_proxy=""
export HTTP_PROXY=""
export HTTPS_PROXY=""
export all_proxy=""
export ALL_PROXY=""

# 检查并安装后端依赖(检测所有核心依赖)
check_dependencies() {
    python -c "import fastapi, uvicorn, sqlalchemy, pandas, numpy, pytdx, pydantic, loguru" 2>/dev/null
}

if ! check_dependencies; then
    log_warning "检测到依赖缺失，开始自动安装..."
    log_info "使用清华镜像源加速安装"
    echo ""
    
    # 配置pip使用清华镜像
    pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple 2>/dev/null || true
    pip config set global.trusted-host "pypi.tuna.tsinghua.edu.cn" 2>/dev/null || true
    pip config set global.timeout 300 2>/dev/null || true
    
    # 升级pip
    show_progress 1 5 "升级pip..."
    pip install --upgrade pip --quiet
    
    # 分步安装核心依赖(使用兼容版本,不指定小版本提升成功率)
    show_progress 2 5 "安装FastAPI和Uvicorn..."
    pip install "fastapi>=0.109" "uvicorn[standard]>=0.27" --quiet || {
        log_warning "安装失败，尝试使用阿里云镜像..."
        pip install "fastapi>=0.109" "uvicorn[standard]>=0.27" -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com --quiet
    }
    
    show_progress 3 5 "安装数据库和数据处理库..."
    pip install "sqlalchemy>=2.0" "aiosqlite>=0.19" "pandas>=2.2" "numpy>=2.0" --quiet || {
        log_warning "安装失败，尝试使用阿里云镜像..."
        pip install "sqlalchemy>=2.0" "aiosqlite>=0.19" "pandas>=2.2" "numpy>=2.0" -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com --quiet
    }
    
    show_progress 4 5 "安装股票数据API..."
    pip install "pytdx>=1.72" --quiet || {
        log_warning "安装失败，尝试使用阿里云镜像..."
        pip install "pytdx>=1.72" -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com --quiet
    }
    
    show_progress 5 5 "安装其他依赖..."
    pip install "pydantic>=2.6" "pydantic-settings>=2.1" "loguru>=0.7" "python-dotenv>=1.0" "python-multipart>=0.0.9" --quiet || {
        log_warning "安装失败，尝试使用阿里云镜像..."
        pip install "pydantic>=2.6" "pydantic-settings>=2.1" "loguru>=0.7" "python-dotenv>=1.0" "python-multipart>=0.0.9" -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com --quiet
    }
    
    log_success "后端依赖安装完成!"
else
    log_success "后端依赖已安装"
fi

# 创建数据目录
mkdir -p data logs

# 初始化数据库
if [ ! -f "data/stock_discipline.db" ]; then
    log_info "初始化数据库..."
    python init_data.py --quiet 2>/dev/null || python init_data.py
    log_success "数据库初始化完成"
fi

cd ..
echo ""

# ============================================
# 步骤3: 准备前端环境
# ============================================
log_info "准备前端环境..."
cd frontend

# 检查并安装前端依赖
if [ ! -d "node_modules" ]; then
    log_warning "前端依赖未安装，开始自动安装..."
    log_info "使用淘宝镜像源加速安装"
    echo ""
    
    # 配置npm使用淘宝镜像
    npm config set registry https://registry.npmmirror.com
    
    show_progress 1 1 "安装前端依赖..."
    npm install --loglevel=error
    
    if [ $? -ne 0 ]; then
        log_warning "安装失败，尝试使用官方源..."
        npm install --loglevel=error --registry=https://registry.npmjs.org
    fi
    
    log_success "前端依赖安装完成!"
else
    log_success "前端依赖已安装"
fi

cd ..
echo ""

# ============================================
# 步骤4: 启动服务
# ============================================
log_info "启动服务..."
echo ""

# 创建日志目录
mkdir -p logs

# 清理旧进程
pkill -f "uvicorn app.main:app" 2>/dev/null || true
pkill -f "vite.*port=3000" 2>/dev/null || true
sleep 1

# 启动后端服务
log_info "启动后端服务 (端口: 8000)..."
cd backend
source venv/bin/activate
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# 等待后端启动
sleep 3

# 检查后端是否启动成功
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    log_success "后端服务启动成功!"
else
    log_warning "后端服务启动中，请稍候..."
fi

# 启动前端服务
log_info "启动前端服务 (端口: 3000)..."
cd frontend
nohup npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

sleep 2

echo ""
echo "╔════════════════════════════════════════╗"
echo "║        ✅ 服务启动成功！               ║"
echo "╚════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}后端API文档:${NC} http://localhost:8000/docs"
echo -e "${GREEN}前端页面:${NC}    http://localhost:3000"
echo ""
echo -e "${YELLOW}提示:${NC}"
echo "  - 首次启动可能需要等待几秒钟"
echo "  - 按 Ctrl+C 停止所有服务"
echo "  - 日志文件: logs/backend.log, logs/frontend.log"
echo ""

# 保存PID到文件
echo $BACKEND_PID > logs/backend.pid
echo $FRONTEND_PID > logs/frontend.pid

# 等待用户中断
trap "echo ''; log_info '正在停止服务...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; rm -f logs/*.pid; log_success '服务已停止'; exit 0" INT TERM

# 保持脚本运行
wait
