#!/bin/bash
# 股票量能分析系统完整部署脚本
# 自动化部署流程：拉取代码 + 安装依赖 + 构建前端 + 重启服务

set -e  # 遇到错误立即退出

PROJECT_DIR="/var/www/stock-discipline"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
LOG_DIR="$BACKEND_DIR/logs"

echo "======================================"
echo "股票量能分析系统自动化部署"
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "======================================"

# 1. 拉取最新代码
echo ""
echo ">>> [1/6] 拉取最新代码..."
cd $PROJECT_DIR
git fetch origin main
git reset --hard origin/main
echo "✓ 代码已更新到最新版本"

# 2. 安装后端Python依赖
echo ""
echo ">>> [2/6] 安装后端依赖..."
cd $BACKEND_DIR
if [ -f "requirements.txt" ]; then
    echo "安装Python依赖包..."
    pip3 install -r requirements.txt --quiet || {
        echo "部分依赖安装失败，尝试逐个安装..."
        pip3 install baostock --quiet || echo "baostock安装失败（可选依赖）"
        pip3 install requests --quiet || echo "❌ requests安装失败（必需依赖）"
        pip3 install beautifulsoup4 --quiet || echo "❌ beautifulsoup4安装失败（必需依赖）"
        pip3 install lxml --quiet || echo "lxml安装失败（可选依赖）"
    }
    echo "✓ 后端依赖安装完成"
else
    echo "⚠ requirements.txt不存在，跳过依赖安装"
fi

# 3. 创建必要目录
echo ""
echo ">>> [3/6] 创建必要目录..."
mkdir -p $LOG_DIR
mkdir -p $BACKEND_DIR/data
mkdir -p $PROJECT_DIR/logs
echo "✓ 目录结构已创建"

# 4. 安装前端依赖并构建
echo ""
echo ">>> [4/6] 构建前端..."
cd $FRONTEND_DIR
if [ -f "package.json" ]; then
    echo "检查并安装前端依赖..."
    npm install --quiet || {
        echo "npm install失败，尝试安装必需依赖..."
        npm install marked --quiet || echo "❌ marked安装失败"
        npm install klinecharts --quiet || echo "❌ klinecharts安装失败"
    }
    
    echo "构建前端应用..."
    npm run build || {
        echo "❌ 前端构建失败"
        exit 1
    }
    echo "✓ 前端构建完成"
else
    echo "⚠ package.json不存在，跳过前端构建"
fi

# 5. 配置并重启后端服务
echo ""
echo ">>> [5/6] 配置并重启后端服务..."
cd $PROJECT_DIR

# 创建systemd服务配置
sudo tee /etc/systemd/system/stock-backend.service > /dev/null <<'EOF'
[Unit]
Description=Stock Discipline Backend API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/var/www/stock-discipline/backend
ExecStart=/usr/bin/python3 /var/www/stock-discipline/backend/run.py --host 127.0.0.1 --port 8080
Restart=on-failure
RestartSec=5
StandardOutput=append:/var/www/stock-discipline/backend/logs/server.log
StandardError=append:/var/www/stock-discipline/backend/logs/error.log

[Install]
WantedBy=multi-user.target
EOF

# 重载systemd配置
sudo systemctl daemon-reload

# 重启服务（先停止再启动，避免端口占用）
sudo systemctl stop stock-backend || true
sleep 2
sudo systemctl start stock-backend
sudo systemctl enable stock-backend

# 等待服务启动
sleep 3

# 检查服务状态
if sudo systemctl is-active --quiet stock-backend; then
    echo "✓ 后端服务启动成功"
else
    echo "❌ 后端服务启动失败"
    sudo systemctl status stock-backend --no-pager
    exit 1
fi

# 6. 验证部署结果
echo ""
echo ">>> [6/6] 验证部署结果..."

# 检查后端API
API_HEALTH=$(curl -s http://127.0.0.1:8080/api/health)
if echo "$API_HEALTH" | grep -q "ok"; then
    echo "✓ 后端API正常: $API_HEALTH"
else
    echo "❌ 后端API异常"
    echo "$API_HEALTH"
    exit 1
fi

# 检查前端文件
if [ -f "$FRONTEND_DIR/dist/index.html" ]; then
    echo "✓ 前端文件已构建"
else
    echo "❌ 前端文件缺失"
    exit 1
fi

# 检查Nginx（如果已配置）
NGINX_STATUS=$(sudo systemctl is-active nginx)
if [ "$NGINX_STATUS" = "active" ]; then
    echo "✓ Nginx服务正常运行"
    
    # 测试公网访问
    PUBLIC_API=$(curl -s http://43.163.87.9/api/health)
    if echo "$PUBLIC_API" | grep -q "ok"; then
        echo "✓ 公网API正常访问"
    else
        echo "⚠ 公网API访问异常（可能需要检查防火墙）"
    fi
else
    echo "⚠ Nginx未运行或未安装"
fi

# 检查Python依赖是否安装成功
echo ""
echo ">>> 依赖检查:"
python3 -c "import baostock; print('✓ baostock已安装')" || echo "⚠ baostock未安装（可选）"
python3 -c "import requests; print('✓ requests已安装')" || echo "❌ requests未安装"
python3 -c "import bs4; print('✓ beautifulsoup4已安装')" || echo "❌ beautifulsoup4未安装"

echo ""
echo "======================================"
echo "✅ 部署完成！"
echo "访问地址: http://43.163.87.9"
echo "本地API: http://127.0.0.1:8080/api/health"
echo "======================================"
echo ""
echo "💡 提示:"
echo "- 前端缓存已更新，建议浏览器强制刷新（Ctrl+F5）"
echo "- 日志位置: $LOG_DIR/"
echo "- 重启命令: sudo systemctl restart stock-backend"
echo "- 查看状态: sudo systemctl status stock-backend"
echo "======================================"