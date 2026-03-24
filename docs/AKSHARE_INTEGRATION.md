# AkShare 数据接口集成说明

## 📋 功能概览

本次开发完成了后端对接AkShare库,实现全市场实时报价、盘口、分时、分钟K数据的获取。

### ✅ 已实现功能

| 功能模块 | API接口 | 说明 |
|---------|--------|------|
| 全市场实时报价 | `GET /api/stock/list` | 获取A股市场所有股票实时行情 |
| 实时行情 | `GET /api/stock/realtime/{code}` | 获取单个股票实时行情 |
| **盘口数据** | `GET /api/stock/bid-ask/{code}` | 获取买卖五档数据 |
| **分时数据** | `GET /api/stock/intraday/{code}` | 获取当日分时走势数据 |
| 日K线 | `GET /api/stock/kline/{code}` | 获取日/周K线数据 |
| **分钟K线** | `GET /api/stock/minute-kline/{code}` | 获取分钟K线(1/5/15/30/60分钟) |
| 市场概览 | `GET /api/stock/market/overview` | 获取涨跌家数等统计 |
| 股票信息 | `GET /api/stock/info/{code}` | 获取股票详细信息 |

---

## 🚀 快速开始

### 1. 安装依赖

```bash
cd backend
source venv/bin/activate  # Windows使用: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 启动后端服务

```bash
cd backend
source venv/bin/activate
python -m app.main
```

或者使用uvicorn:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 访问API文档

启动服务后访问: http://localhost:8000/docs

---

## 📖 API 使用示例

### 1. 获取盘口数据(买卖五档)

**请求:**
```http
GET /api/stock/bid-ask/000001
```

**响应:**
```json
{
  "code": "000001",
  "bid1": 12.50,
  "bid1_volume": 5000,
  "bid2": 12.49,
  "bid2_volume": 3200,
  ...
  "ask1": 12.51,
  "ask1_volume": 4800,
  "updated_at": "2026-03-24T14:30:00"
}
```

### 2. 获取分时数据

**请求:**
```http
GET /api/stock/intraday/000001
```

**响应:**
```json
{
  "code": "000001",
  "name": "平安银行",
  "data": [
    {
      "timestamp": "2026-03-24T09:30:00",
      "price": 12.45,
      "volume": 150000,
      "avg_price": 12.46
    },
    ...
  ]
}
```

### 3. 获取分钟K线

**请求:**
```http
GET /api/stock/minute-kline/000001?period=5&count=48
```

**参数说明:**
- `period`: 周期 (1/5/15/30/60分钟)
- `count`: 数据条数 (1-240)

**响应:**
```json
{
  "code": "000001",
  "name": "平安银行",
  "period": "5",
  "data": [
    {
      "timestamp": "2026-03-24T09:30:00",
      "open": 12.45,
      "high": 12.48,
      "low": 12.43,
      "close": 12.46,
      "volume": 150000,
      "turnover": 1869000
    },
    ...
  ]
}
```

---

## 🧪 测试接口

### 方式一: 运行测试脚本

```bash
cd backend
source venv/bin/activate
python test_akshare.py
```

### 方式二: 使用curl测试

```bash
# 测试盘口数据
curl http://localhost:8000/api/stock/bid-ask/000001

# 测试分时数据
curl http://localhost:8000/api/stock/intraday/000001

# 测试分钟K线
curl http://localhost:8000/api/stock/minute-kline/000001?period=5&count=10
```

### 方式三: 使用FastAPI自动文档

访问 http://localhost:8000/docs,可以直接在浏览器中测试所有API接口。

---

## 📂 代码结构

```
backend/
├── app/
│   ├── api/
│   │   └── stocks.py          # 股票API路由(新增3个接口)
│   ├── schemas/
│   │   └── schemas.py         # 数据模型(新增4个模型)
│   ├── services/
│   │   └── stock_service.py   # 股票服务(新增3个方法)
│   └── main.py
├── test_akshare.py            # 测试脚本
└── requirements.txt
```

---

## ⚠️ 注意事项

1. **数据获取时间**
   - 分时数据: 仅交易时间有数据
   - 分钟K线: 仅交易时间有数据
   - 盘口数据: 仅交易时间有数据

2. **缓存策略**
   - 当前实现简单的内存缓存(5分钟)
   - 生产环境建议使用Redis

3. **错误处理**
   - 所有接口都有异常捕获
   - 非交易时间或无效代码会返回404

4. **性能优化建议**
   - 使用Redis缓存高频访问的数据
   - 批量查询使用异步并发
   - 定时预加载热门股票数据

---

## 🔧 后续优化建议

1. **数据源容错**: 增加Tushare备用数据源
2. **WebSocket推送**: 实现实时数据推送
3. **数据存储**: 定时存储历史数据到数据库
4. **性能监控**: 添加接口响应时间统计

---

## 📞 技术支持

如有问题,请查看:
- AkShare文档: https://akshare.akfamily.xyz/
- FastAPI文档: https://fastapi.tiangolo.com/
