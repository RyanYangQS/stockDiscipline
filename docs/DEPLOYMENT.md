# 部署说明

当前系统不依赖第三方 Python 包，服务器有 Python 3 即可运行。

## 本地启动

部署前先跑测试：

```bash
chmod +x scripts/run_tests.sh
scripts/run_tests.sh
```

```bash
chmod +x start.sh stop.sh
PORT=8080 ./start.sh
```

访问：

```text
http://localhost:8080
```

停止：

```bash
./stop.sh
```

## 部署到服务器

服务器信息：

```text
Host: 43.163.87.9
User: ubuntu
```

执行：

```bash
chmod +x scripts/deploy.sh
HOST=43.163.87.9 SSH_USER=ubuntu PORT=8080 scripts/deploy.sh
```

脚本不会保存密码。若没有 SSH Key，会提示输入 SSH 密码。

## 先查看已有小程序服务

```bash
chmod +x scripts/stop_remote_service.sh
HOST=43.163.87.9 SSH_USER=ubuntu scripts/stop_remote_service.sh
```

登录服务器后也可以手动查看：

```bash
sudo ss -lntp
ps -ef | grep -E "node|python|pm2|nginx" | grep -v grep
```

如果小程序是 PM2 管理：

```bash
pm2 list
pm2 stop <name-or-id>
```

如果占用 8080 端口：

```bash
sudo lsof -i :8080
sudo kill <pid>
```

## 数据库位置

```text
backend/data/stock_discipline.db
```

首次启动会自动建表，并写入附件里的 5 条样例持仓。
