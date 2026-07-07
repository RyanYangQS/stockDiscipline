# 项目长期记忆

## 工作流程偏好

**部署要求**: 用户明确要求，所有代码改动必须先在本地验证，经过用户同意后才能部署到服务器。部署流程：
1. 本地验证功能正常（127.0.0.1:5173）
2. **告知用户验证结果，等待用户确认同意**
3. 用户同意后，提交代码到GitHub（git push origin main）
4. SSH登录服务器拉取最新代码（git reset --hard origin/main）
5. 前端重新构建（cd frontend && npm run build）
6. 后端服务重启（sudo systemctl restart stock-backend）
7. 验证线上系统：curl http://43.163.87.9/api/health + 前端页面检查

**⚠️ 重要**: 未经用户同意，禁止直接部署到服务器。必须先本地验证，用户确认后才能部署。

**本地调试**: 用户优先在本地调试（127.0.0.1:5173），确认功能正常后再部署到线上。

---

## 技术栈规范

**前端框架**: Vue 3 + Vite + KlineCharts（专业K线图表库）
**后端框架**: Python 3.10 + FastAPI + SQLite
**数据源**: Baostock（主源）、东方财富、腾讯、新浪财经（备用）
**缓存策略**: IndexedDB持久化缓存 + localStorage短期缓存

---

## 核心组件说明

**KlineChart.vue**: 统一的K线图表组件，支持日K蜡烛图和分时价格曲线（LineType）
- mode='daily': 使用CandleType.CandleUpStroke绘制蜡烛图
- mode='minute': 使用CandleType.Line绘制红色价格曲线
- 避免引入额外图表库（如ECharts）

---

## 服务器信息

- **IP**: 43.163.87.9
- **用户**: ubuntu
- **项目目录**: /var/www/stock-discipline
- **后端服务**: systemd stock-backend.service（端口8080）
- **Nginx配置**: /etc/nginx/sites-available/stock-discipline

---

## 重要约定

1. **部署前必须用户同意**: 所有代码改动先本地验证，用户确认后才能部署服务器
2. **分时图使用KlineChart原生能力**: 禁止引入ECharts或其他图表库
3. **买卖信号标记**: 使用简化算法，避免复杂计算影响性能
4. **缓存策略**: K线数据缓存到次日收盘时间，避免页面空白
5. **分时图要求**: 正常股票分时线样式，横向填满容器
