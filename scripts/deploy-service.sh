#!/bin/bash
# 服务器部署脚本 - 配置systemd服务和Nginx

# 创建日志目录
mkdir -p /var/www/stock-discipline/backend/logs

# 后端systemd服务配置
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

# 重载systemd
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start stock-backend

# 设置开机自启
sudo systemctl enable stock-backend

# 查看状态
sudo systemctl status stock-backend --no-pager