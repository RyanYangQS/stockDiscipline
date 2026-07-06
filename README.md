# 个人股票量能纪律系统

这是一个按《个人股票量能分析系统建设方案》落地的轻量 Web 系统，包含：

- 持仓管理
- 消息面录入
- 量能状态录入
- Vue 单页面前端
- KLineCharts 专业 K 线图
- DeepSeek 每日分析接口
- 交易纪律检查
- 持仓操作建议表
- CSV 导出
- SQLite 数据库

## 启动

```bash
chmod +x start.sh stop.sh
PORT=8080 ./start.sh
```

打开：

```text
http://localhost:8080
```

## 停止

```bash
./stop.sh
```

## 测试

所有功能改动都应先跑单元测试：

```bash
chmod +x scripts/run_tests.sh
scripts/run_tests.sh
```

当前测试覆盖：

- 建议引擎：核心赛道、弱势跟风、高风险退出、主力出货、深度浮亏纪律。
- 数据库仓储：建表、样例数据、持仓增删改查、消息和量能录入。
- 消息/量能联动：消息情景和卖出风险会影响最终操作建议。
- K 线：样例 K 线种子数据、手工日 K 写入、查询。
- AI 日报：未配置 DeepSeek 时本地纪律报告兜底。
- CSV 导出：字段格式与附件式“持仓操作建议表”一致。
- 前端：Vue SPA 结构、Element Plus UI、KLineCharts 依赖、关键页面和构建检查。

## 前端开发

```bash
cd frontend
npm install
npm run dev
```

生产构建：

```bash
cd frontend
npm run build
```

后端会优先托管 `frontend/dist`，没有构建产物时才回退到 `frontend/index.html`。

## API

- `GET /api/summary`
- `GET /api/positions`
- `POST /api/positions`
- `PUT /api/positions/{id}`
- `DELETE /api/positions/{id}`
- `GET /api/news`
- `POST /api/news`
- `GET /api/volume`
- `POST /api/volume`
- `GET /api/advice`
- `POST /api/advice/rebuild`
- `GET /api/advice.csv`

## 说明

系统默认输出类似附件的持仓操作建议表，重点是：

- 分批减仓触发价
- 刚性止损触发价
- 企稳后是否允许加仓
- 当前操作建议

所有建议都只作为纪律辅助，不构成投资建议。
