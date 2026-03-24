# 个人股票交易纪律系统

一个智能股票交易纪律辅助系统，帮助投资者严格执行交易规则，克服人性弱点。

## 系统定位

**本系统仅做辅助决策，不进行实际交易**

- ✅ AI选股 - 根据规则筛选符合条件的股票标的
- ✅ K线图展示 - 专业K线图+技术指标+买卖点标注
- ✅ 买卖点建议 - 基于规则的买入/卖出信号提示
- ✅ 纪律执行提醒 - 止损止盈/风控规则触发提醒
- ❌ 实际交易 - 不对接券商下单接口

## 技术栈

### 后端
- **框架**: FastAPI (Python 3.11+)
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **ORM**: SQLAlchemy 2.0
- **股票数据**: AKShare + Tushare
- **数据处理**: Pandas + NumPy

### 前端
- **框架**: Vue 3 + TypeScript
- **构建工具**: Vite 5
- **UI组件**: Element Plus
- **图表库**: klinecharts
- **状态管理**: Pinia
- **HTTP客户端**: Axios

## 项目结构

```
stockDiscipline/
├── backend/                    # 后端服务
│   ├── app/
│   │   ├── api/               # API路由
│   │   ├── core/              # 核心配置
│   │   ├── models/            # 数据库模型
│   │   ├── schemas/           # Pydantic模型
│   │   ├── services/          # 业务服务
│   │   └── main.py            # 应用入口
│   ├── tests/                 # 测试文件
│   ├── requirements.txt       # Python依赖
│   └── init_data.py           # 初始化脚本
├── frontend/                   # 前端应用
│   ├── src/
│   │   ├── api/               # API服务
│   │   ├── assets/            # 静态资源
│   │   ├── components/        # 组件
│   │   ├── router/            # 路由
│   │   ├── stores/            # 状态管理
│   │   ├── views/             # 页面视图
│   │   └── main.js            # 入口文件
│   ├── package.json           # npm依赖
│   └── vite.config.js         # Vite配置
├── PRD-股票交易纪律系统.md      # 产品需求文档
└── README.md                   # 项目说明
```

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- npm 或 pnpm

### 后端启动

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 复制配置文件
cp .env.example .env

# 初始化数据库和默认数据
python init_data.py

# 启动服务
uvicorn app.main:app --reload --port 8000
```

后端API文档: http://localhost:8000/docs

### 前端启动

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端地址: http://localhost:3000

## 核心功能

### 1. AI选股模块

- 系统默认规则（ST股排除、市值过滤、利空排除等）
- 核心标的识别（放量长上影、一进二接力、抗跌强势）
- 自定义规则配置
- 实时股票数据对接（AKShare）

### 2. K线图展示模块

- 专业K线图表（klinecharts）
- 技术指标叠加（MA/MACD/RSI）
- 买卖点标注
- 日K/周K/分时切换

### 3. 买卖提示引擎

- 缩量企稳买入
- 弱转强买入
- 尾盘确定性买入
- 止损止盈提醒

### 4. 风控规则引擎

- 8%硬止损
- 阶梯止盈（3%/5%/10%）
- 连续亏损限仓
- 单日最大回撤预警

## API接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/stock/screening` | POST | 执行选股 |
| `/api/stock/kline/{code}` | GET | 获取K线数据 |
| `/api/stock/realtime/{code}` | GET | 获取实时行情 |
| `/api/stock/market/overview` | GET | 市场概览 |
| `/api/position/list` | GET | 持仓列表 |
| `/api/position/create` | POST | 创建持仓 |
| `/api/rule/system` | GET | 系统规则 |
| `/api/rule/custom` | GET | 自定义规则 |

## 开发进度

- [x] Phase 1: 需求分析与PRD设计
- [x] Phase 2: 技术架构设计
- [ ] Phase 3: 核心功能开发
- [ ] Phase 4: 测试与优化

## 许可证

MIT License

## 免责声明

本系统仅供学习研究使用，不构成任何投资建议。股市有风险，投资需谨慎。
