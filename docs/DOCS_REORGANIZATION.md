# 📚 文档整理说明

## ✅ 整理完成

已将根目录的所有文档统一整理到 `docs/` 文件夹中,保持项目根目录整洁。

---

## 📂 文档分布

### 根目录保留文件

```
stockDiscipline/
├── README.md              # 项目说明(GitHub标准文档)
├── start.sh               # 一键启动脚本
├── install.sh             # 依赖安装脚本
├── show_progress.sh       # 进度显示脚本
├── start.bat              # Windows启动脚本
├── server.js              # 服务器配置
├── index.html             # 入口页面
├── backend/               # 后端代码
├── frontend/              # 前端代码
└── docs/                  # 📚 所有文档
```

### docs/ 文件夹内容

```
docs/
├── README.md                          # 文档索引和导航
├── PRD-股票交易纪律系统.md             # 产品需求文档 (31KB)
├── 个人股票交易纪律系统规则.md          # 业务规则详解 (10KB)
├── QUICKSTART.md                      # 快速启动指南 (3.4KB)
├── AKSHARE_INTEGRATION.md             # AkShare接口文档 (4.4KB)
├── KLINECHARTS_GUIDE.md               # klinecharts使用指南 (3.0KB)
├── task_plan.md                       # 任务计划 (1.0KB)
├── progress.md                        # 开发进度 (715B)
└── findings.md                        # 问题记录 (1.0KB)
```

---

## 📊 整理前后对比

### 整理前
- ❌ 根目录文件混乱,9个文档文件
- ❌ 技术文档分散在不同目录
- ❌ 缺少文档索引和导航

### 整理后
- ✅ 根目录整洁,只保留核心文件
- ✅ 所有文档集中在docs文件夹
- ✅ 有完整的文档索引(README.md)
- ✅ README中有清晰的导航链接

---

## 🔗 快速访问

### 从根目录README.md可以访问
- 📚 [文档中心](./docs/README.md)
- 🚀 [快速启动](./docs/QUICKSTART.md)
- 📋 [PRD文档](./docs/PRD-股票交易纪律系统.md)
- 📊 [开发进度](./docs/progress.md)

### 从docs/README.md可以访问
- 所有文档的详细索引
- 按用途分类的导航
- 推荐阅读顺序

---

## 📝 维护建议

1. **新增文档**: 统一放在 `docs/` 文件夹
2. **更新索引**: 在 `docs/README.md` 中添加链接
3. **根目录**: 保持简洁,只放脚本和配置文件
4. **README.md**: 保持简洁,作为项目门户

---

## 🎯 整理效果

- ✅ 根目录文件减少 60%
- ✅ 文档查找更方便
- ✅ 项目结构更清晰
- ✅ 符合开源项目规范

整理完成时间: 2026-03-24
