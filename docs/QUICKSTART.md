# 快速启动指南

## 🚀 方式一: 一键启动(推荐)

直接运行启动脚本,会自动检查并安装依赖,**带进度显示**:

```bash
chmod +x start.sh
./start.sh
```

脚本会自动:
- ✅ 检查Python和Node.js环境
- ✅ 创建虚拟环境
- ✅ 使用国内镜像源安装依赖(显示进度)
- ✅ 初始化数据库
- ✅ 启动后端和前端服务

## 🔧 方式二: 分步执行

### 1. 安装依赖(三种方式可选)

#### 方式A: 普通安装(推荐)
```bash
chmod +x install.sh
./install.sh
```
显示详细安装信息,包括每个包的安装状态

#### 方式B: 进度条安装
```bash
chmod +x show_progress.sh
./show_progress.sh
```
显示可视化进度条,更直观

#### 方式C: 快速安装(无输出)
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --quiet

cd ../frontend
npm install --registry=https://registry.npmmirror.com --loglevel=error
```

### 2. 启动服务

```bash
./start.sh
```

## 📊 进度显示说明

### start.sh 启动脚本
- 显示每个包的安装过程
- 实时显示pip安装进度
- 显示npm安装的关键步骤

### install.sh 安装脚本
- 显示总包数和当前进度 `[3/34]`
- 显示每个正在安装的包名
- 显示安装成功/失败状态

### show_progress.sh 进度条脚本
- 可视化进度条 `[████░░░░░░] 50%`
- 实时更新进度
- 显示当前正在安装的包名

## 🌐 访问服务

启动成功后访问:
- **后端API文档**: http://localhost:8000/docs
- **前端页面**: http://localhost:3000

## ⚡ 国内镜像源配置

已自动配置国内镜像源加速:

### Python (清华镜像)
```
https://pypi.tuna.tsinghua.edu.cn/simple
```

### Node.js (淘宝镜像)
```
https://registry.npmmirror.com
```

## ❓ 常见问题

### Q1: 依赖安装很慢怎么办?

A: 脚本已自动配置国内镜像源,如果还是很慢可以:
1. 使用 `show_progress.sh` 查看进度
2. 手动安装关键包:
```bash
# 后端
cd backend
source venv/bin/activate
pip install pandas numpy akshare fastapi -i https://pypi.tuna.tsinghua.edu.cn/simple

# 前端
cd frontend
npm install --registry=https://registry.npmmirror.com
```

### Q2: 看不到安装进度?

A: 使用以下脚本查看进度:
- `./show_progress.sh` - 进度条显示
- `./install.sh` - 详细步骤显示

### Q3: 提示找不到Python或Node.js?

A: 请先安装:
- Python 3.11+: https://www.python.org/downloads/
- Node.js 18+: https://nodejs.org/

### Q4: 端口被占用怎么办?

A: 修改端口:
- 后端: 修改 `start.sh` 中的 `--port 8000`
- 前端: 修改 `frontend/vite.config.js` 中的端口配置

### Q5: 如何停止服务?

A: 按 `Ctrl+C` 即可停止所有服务

## 📁 项目结构

```
stockDiscipline/
├── start.sh          # 一键启动脚本(带进度)
├── install.sh        # 依赖安装脚本(详细)
├── show_progress.sh  # 进度条安装脚本
├── backend/          # 后端FastAPI
│   ├── pip.conf      # pip配置(清华镜像)
│   ├── requirements.txt
│   └── app/
└── frontend/         # 前端Vue3
    ├── .npmrc        # npm配置(淘宝镜像)
    ├── package.json
    └── src/
```

## 💡 使用建议

1. **首次安装**: 推荐使用 `./start.sh`,自动完成所有步骤
2. **重新安装**: 使用 `./show_progress.sh`,查看详细进度
3. **开发调试**: 使用 `./install.sh` 安装依赖后,手动启动服务
