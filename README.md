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
├── docs/                       # 📚 项目文档
│   ├── README.md              # 文档索引
│   ├── PRD-股票交易纪律系统.md  # 产品需求文档
│   ├── QUICKSTART.md          # 快速启动指南
│   └── ...                    # 更多文档
├── demo/                       # 📺 演示版本
│   ├── index.html             # 单文件演示
│   ├── server.js              # 演示服务器
│   └── README.md              # 演示说明
├── start.sh                    # 🚀 一键启动脚本
├── install.sh                  # 依赖安装脚本
└── README.md                   # 项目说明
```

## 快速开始

### 🚀 一键启动

```bash
# 添加执行权限(首次运行)
chmod +x start.sh

# 启动所有服务
./start.sh
```

**就这么简单!** 脚本会自动:
- ✅ 检查环境(Python、Node.js)
- ✅ 创建虚拟环境
- ✅ 自动安装所有依赖(智能处理网络问题)
- ✅ 初始化数据库
- ✅ 启动后端和前端服务

### 🌐 访问服务

启动成功后访问:
- **后端API文档**: http://localhost:8000/docs
- **前端页面**: http://localhost:3000

### 🛑 停止服务

```bash
# 方式1: 按 Ctrl+C (如果在运行start.sh)
# 方式2: 运行停止脚本
./stop.sh
```

### 环境要求

- Python 3.11+
- Node.js 18+
- npm 或 pnpm

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

- [x] Phase 1: 需求分析与PRD设计 ✅
- [x] Phase 2: 技术架构设计 ✅
- [x] Phase 3: 核心功能开发 ✅
  - [x] AI选股模块
  - [x] K线图展示
  - [x] 买卖信号引擎
  - [x] 风控规则引擎
  - [x] AkShare数据接口集成
- [ ] Phase 4: 测试与优化

## 📝 更多文档

- [文档中心](./docs/README.md) - 完整文档索引
- [AkShare接口文档](./docs/AKSHARE_INTEGRATION.md) - 数据接口使用说明
- [klinecharts使用指南](./docs/KLINECHARTS_GUIDE.md) - 图表库开发文档
- [交易规则说明](./docs/个人股票交易纪律系统规则.md) - 业务规则详解

## 📺 演示版本

- [demo/](./demo/README.md) - 单文件演示版本(无需安装，仅供快速预览)

**注意**: 演示版本功能有限，推荐使用完整版本。完整版本启动命令: `./start.sh`

## 💡 特色功能

### 智能一键启动
- 🤖 自动检测环境和依赖
- 🔧 自动处理网络和代理问题
- 📦 自动安装所有必需组件
- 🚀 真正实现一键启动,零手动配置

## 许可证

MIT License

## 免责声明

本系统仅供学习研究使用，不构成任何投资建议。股市有风险，投资需谨慎。
