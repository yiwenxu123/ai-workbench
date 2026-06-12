# AI绘图工作台（前端 + 后端代理）

本项目包含：

- `frontend/`：Vue 3 + TypeScript + Vite 的工作台 UI
- `backend/`：FastAPI 代理服务（统一对接图像/视频/编辑等不同平台）

## 开发环境启动

### 一键启动（可选）

在项目根目录执行：

- `bash scripts/dev.sh`

说明：该脚本只负责同时拉起前后端；首次运行前仍需要分别安装依赖与配置 `backend/.env`。

### 1) 启动后端（FastAPI）

1. 进入 `backend/`
2. 创建并激活虚拟环境（推荐）
3. 安装依赖：`pip install -r requirements.txt`
4. 配置环境变量：复制 `backend/.env.example` 为 `backend/.env` 并填写
5. 启动服务：`python main.py`

首次启动时，后端会自动将 `backend/data/*.json` 灌入 SQLite 知识库（`knowledge.db` 在 `.gitignore` 中，不会提交到仓库）。一般**无需**手动运行 `migrate_json_to_sqlite.py`；仅在需要强制全量同步 JSON 时使用该脚本。

默认监听：`http://127.0.0.1:8000`

可用接口（核心）：

- `GET /config`
- `POST /generate`
- `POST /generate-video`
- `POST /edit-image`
- `POST /validate-api`

### 2) 启动前端（Vite）

1. 进入 `frontend/`
2. 安装依赖：`pnpm install`
3. 启动开发服务：`pnpm dev`

默认地址一般为：`http://localhost:5345`

前端环境变量：

- 开发：`frontend/.env.development`（默认指向 `http://localhost:8000`）
- 生产：`frontend/.env.production`（`VITE_API_BASE_URL=/`，通常需要反向代理或同域部署）

## 生产构建（前端）

在 `frontend/` 下执行：

- 构建：`pnpm build`
- 预览：`pnpm preview`

## 优化后的使用路径

- 新手优先使用「新手向导」：选择电商主图、社媒海报、PPT 配图、头像、图生视频或图片修改，再用一句中文描述需求。
- 专家功能仍保留在图像生成、视频生成、图片编辑、模板中心、知识库和作品库中。
- 「AI 入库」默认隐藏在维护模式中，用于内容维护，而不是普通用户的首屏功能。

## Agent / MCP 调用

`mcp-server/` 暴露标准 MCP 工具层，默认连接 `http://127.0.0.1:8000`。

- 可通过环境变量 `AI_WORKBENCH_API_BASE` 修改后端地址。
- 工具命名使用 snake_case：`generate_image`、`generate_video`、`check_task_status`、`edit_image`、`list_templates`、`get_template`、`list_cases`、`extract_knowledge`。
- Resources 提供模板库、案例库、模型能力注册表、术语知识库。

## 内容维护机制

- 后端 `/api/model-manifest` 是模型能力注册表，前端和 Agent 均应优先读取它判断模型能力。
- AI 入库保存的内容会补充来源、更新时间、验证时间、审核状态等治理字段。
- 建议每月执行一次内容更新：抓取资料 → AI 提取 → 去重对比 → 人工确认 → 发布到模板中心。

## 仓库约定（重要）

为了可复现与可分发，以下内容不应提交到仓库：

- Python：`backend/.venv/`、`__pycache__/`、`backend/.env`
- Node：`frontend/node_modules/`、`frontend/dist/`

对应忽略规则见：`.gitignore`
