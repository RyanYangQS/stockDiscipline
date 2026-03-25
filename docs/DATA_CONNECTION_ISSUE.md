# 数据连接问题诊断与解决方案

## 🔍 问题描述

前端页面K线图等数据为空，后端日志显示：
```
Connection aborted. RemoteDisconnected('Remote end closed connection without response')
```

## 📊 问题诊断

### 症状
1. ✅ 后端服务正常运行 (端口8000)
2. ✅ 前端服务正常运行 (端口3000)
3. ✅ API接口可以访问
4. ❌ AkShare无法连接东方财富数据源
5. ❌ Python requests库连接被远程断开

### 根本原因

**Python的requests库与东方财富服务器的SSL/TLS握手失败**

可能原因：
1. 系统配置了网络代理，但Python无法正确处理
2. Python的SSL证书验证问题
3. 东方财富服务器限制了某些请求
4. 网络防火墙拦截

## 🔧 解决方案

### 方案1: 修复网络配置 (推荐)

#### 步骤1: 检查并清除系统代理

```bash
# 检查系统代理
networksetup -getwebproxy Wi-Fi
networksetup -getsecurewebproxy Wi-Fi

# 如果显示已启用，尝试关闭
networksetup -setwebproxystate Wi-Fi off
networksetup -setsecurewebproxystate Wi-Fi off
```

#### 步骤2: 检查环境变量

```bash
# 查看代理环境变量
env | grep -i proxy

# 如果有，临时清除
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY
```

#### 步骤3: 重启后端服务

```bash
# 停止服务
pkill -f "python.*app.main"

# 重新启动
cd backend
source venv/bin/activate
python -m app.main
```

### 方案2: 使用备用数据源 (临时方案)

如果网络问题短期无法解决，可以：

1. **使用本地历史数据**
   - 下载历史K线数据到本地
   - 从本地文件读取

2. **使用其他数据源**
   - Tushare (需要注册token)
   - 新浪财经API
   - 腾讯财经API

3. **使用模拟数据**
   - 已创建 `data_fallback.py` 提供模拟数据
   - 可以在无网络时测试功能

### 方案3: 使用VPN或代理

如果是地区网络限制，可以：
1. 使用VPN连接
2. 配置HTTP代理（但需要确保Python正确处理）

## 🧪 测试连接

### 测试脚本

创建 `test_connection.py`:

```python
import requests
import os

# 清除代理
for var in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']:
    os.environ.pop(var, None)

# 测试东方财富API
url = 'https://push2his.eastmoney.com/api/qt/stock/kline/get'
params = {
    'fields1': 'f1,f2,f3,f4,f5,f6',
    'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f116',
    'ut': '7eea3edcaed734bea9cbfc24409ed989',
    'klt': '101',
    'fqt': '1',
    'secid': '0.000001',
    'beg': '20240101',
    'end': '20250331'
}

try:
    resp = requests.get(url, params=params, timeout=10)
    print(f'✅ 连接成功！状态码: {resp.status_code}')
    print(f'数据长度: {len(resp.text)}')
except Exception as e:
    print(f'❌ 连接失败: {e}')
```

### 运行测试

```bash
cd backend
source venv/bin/activate
python test_connection.py
```

## 💡 当前建议

### 短期方案

1. **检查系统网络设置**
   - 系统偏好设置 -> 网络 -> 高级 -> 代理
   - 确保没有启用不必要的代理

2. **重启网络服务**
   ```bash
   # macOS
   sudo ifconfig en0 down
   sudo ifconfig en0 up
   ```

3. **使用移动热点测试**
   - 如果Wi-Fi有问题，尝试用手机热点

### 长期方案

1. **添加多数据源支持**
   - 主数据源: AkShare
   - 备用数据源: Tushare/本地数据

2. **实现数据缓存**
   - 使用Redis缓存历史数据
   - 减少实时请求频率

3. **添加降级策略**
   - AkShare失败时使用缓存数据
   - 缓存miss时使用模拟数据

## 📞 需要帮助？

如果以上方案都无法解决，请提供：

1. 系统版本: `sw_vers`
2. Python版本: `python --version`
3. 网络环境: 公司网络/家庭网络/VPN
4. 代理设置: `env | grep -i proxy`
5. 测试结果: 运行 `test_connection.py` 的输出

---

**当前状态**: 代码功能已完成，但受网络环境限制暂时无法获取实时数据。

**临时建议**: 先用模拟数据测试前端功能，网络恢复后即可正常使用。
