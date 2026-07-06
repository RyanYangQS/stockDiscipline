#!/bin/bash

# Stock Discipline - 停止脚本

echo "停止 Stock Discipline 服务..."
lsof -i :8080-8089 -i :5173-5179 | grep LISTEN | awk '{print $2}' | xargs -I {} kill -9 {} 2>/dev/null
echo "已停止所有服务"
