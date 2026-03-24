# 🚨 快速故障排除

## 问题: http://localhost:8000/docs 访问不了

**原因**: 后端服务未启动或依赖安装失败

---

## ⚡ 快速修复

### 方式1: 使用智能启动脚本(推荐)

```bash
./start.sh
```

脚本会自动:
- ✅ 检测并安装缺失的依赖
- ✅ 使用版本范围(不指定具体版本),提高成功率
- ✅ 自动处理网络和代理问题
- ✅ 自动重试备用镜像源

### 方式2: 手动安装

```bash
cd backend
source venv/bin/activate

# 使用版本范围,提高成功率
pip install "fastapi>=0.109,<0.110" -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn

pip install "uvicorn[standard]>=0.27,<0.28" -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn

pip install "sqlalchemy>=2.0,<2.1" "aiosqlite>=0.19,<0.20" "pydantic>=2.6,<2.7" "loguru>=0.7,<0.8" -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn

pip install "pandas>=2.2,<2.3" "numpy>=1.26,<1.27" "akshare>=1.12,<1.13" -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn

# 启动服务
python -m app.main
```

---

## 🎯 版本策略说明

### 为什么使用版本范围?

**旧方式(具体版本)**:
```bash
pip install fastapi==0.109.2  # ❌ 如果镜像源没有0.109.2会失败
```

**新方式(版本范围)**:
```bash
pip install "fastapi>=0.109,<0.110"  # ✅ 会安装0.109.x的最新版本
```

### 优势

| 特性 | 具体版本 | 版本范围 |
|------|----------|----------|
| 安装成功率 | ❌ 低 | ✅ 高 |
| 镜像源兼容 | ❌ 差 | ✅ 好 |
| 版本锁定 | ✅ 精确 | ⚠️ 范围 |
| 稳定性 | ⚠️ 一般 | ✅ 更好 |

### 版本范围说明

- `>=0.109,<0.110` - 安装0.109.x系列的任意版本
- `>=2.2,<2.3` - 安装2.2.x系列的任意版本
- 允许镜像源返回最接近的可用版本

---

## 🐛 常见错误

### 错误1: 找不到指定版本

```
ERROR: Could not find a version that satisfies the requirement fastapi==0.109.2
```

**解决**: 使用版本范围而不是具体版本号
```bash
pip install "fastapi>=0.109,<0.110"
```

### 错误2: 代理连接失败

```
ProxyError: Cannot connect to proxy
```

**解决**: start.sh会自动禁用代理,手动安装时:
```bash
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY
pip install ...
```

### 错误3: SSL证书问题

**解决**: 添加 `--trusted-host` 参数(start.sh已自动添加)

---

## 📚 相关文档

- [一键启动说明](../ONEKEY_START.md) - 智能启动脚本详解
- [手动安装指南](./MANUAL_INSTALL.md) - 详细安装步骤

---

**创建时间**: 2026-03-24  
**核心策略**: 使用版本范围代替具体版本,大幅提升安装成功率
