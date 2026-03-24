# 🔧 依赖安装问题解决方案

## ❌ 问题描述

后端服务无法启动,提示 `ModuleNotFoundError: No module named 'fastapi'`

**错误原因**: 依赖安装失败,可能由于代理配置或网络问题

---

## ✅ 解决方案

### 方案1: 手动安装核心依赖(推荐)

```bash
# 1. 进入后端目录
cd backend

# 2. 激活虚拟环境
source venv/bin/activate

# 3. 安装核心依赖(使用版本范围,提高成功率)
pip install "fastapi>=0.109,<0.110" -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn

pip install "uvicorn[standard]>=0.27,<0.28" -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn

pip install "sqlalchemy>=2.0,<2.1" "aiosqlite>=0.19,<0.20" -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn

pip install "pandas>=2.2,<2.3" "numpy>=1.26,<1.27" -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn

pip install "akshare>=1.12,<1.13" -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn

pip install "pydantic>=2.6,<2.7" "pydantic-settings>=2.1,<2.2" "loguru>=0.7,<0.8" -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
```

### 方案2: 使用阿里云镜像

如果清华镜像不可用,尝试阿里云镜像:

```bash
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com
```

### 方案3: 关闭代理后安装

```bash
# 临时关闭所有代理
unset http_proxy
unset https_proxy
unset HTTP_PROXY
unset HTTPS_PROXY
unset all_proxy
unset ALL_PROXY

# 然后安装
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 方案4: 使用pip配置文件

在 `backend/` 目录创建 `pip.conf`:

```ini
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn
timeout = 300
```

然后安装:
```bash
export PIP_CONFIG_FILE="$(pwd)/pip.conf"
pip install -r requirements.txt
```

---

## 🚀 验证安装

安装完成后验证:

```bash
# 在backend目录下
source venv/bin/activate

# 测试导入
python -c "import fastapi; import akshare; import pandas; print('✅ 依赖安装成功')"
```

如果输出 `✅ 依赖安装成功`,则可以启动服务:

```bash
python -m app.main
```

或使用uvicorn:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 📝 常见错误

### 错误1: 代理连接超时
```
ProxyError: Cannot connect to proxy
```
**解决**: 取消代理配置,或使用 `--trusted-host` 参数

### 错误2: SSL证书问题
```
SSLError: CERTIFICATE_VERIFY_FAILED
```
**解决**: 添加 `--trusted-host` 参数

### 错误3: 找不到模块
```
ModuleNotFoundError: No module named 'xxx'
```
**解决**: 检查虚拟环境是否激活,重新安装对应模块

---

## 💡 最佳实践

1. **分步安装**: 核心包先安装,避免一次性安装超时
2. **使用国内镜像**: 清华/阿里云镜像速度快
3. **添加信任主机**: `--trusted-host` 避免SSL问题
4. **检查虚拟环境**: 确保在正确的虚拟环境中安装

---

## 🆘 仍然无法解决?

### 最小化安装

只安装最核心的包,让服务先跑起来:

```bash
pip install fastapi uvicorn sqlalchemy aiosqlite pydantic loguru pandas -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
```

### 检查网络

```bash
# 测试网络连接
curl -I https://pypi.tuna.tsinghua.edu.cn/simple/

# 检查DNS
nslookup pypi.tuna.tsinghua.edu.cn
```

### 完全重装

```bash
# 删除虚拟环境
rm -rf venv

# 重新创建
python3 -m venv venv
source venv/bin/activate

# 重新安装
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
```

---

**创建时间**: 2026-03-24
**适用场景**: 后端依赖安装失败,网络/代理问题
