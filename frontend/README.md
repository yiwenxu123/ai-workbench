# 前端（AI绘图工作台）

技术栈：Vue 3 + TypeScript + Vite + Naive UI + Pinia + Dexie

## 开发启动

1. 安装依赖：`pnpm install`
2. 启动开发服务器：`pnpm dev`

默认 API 地址来自 `VITE_API_BASE_URL`：

- 开发：见 `.env.development`（默认 `http://localhost:8000`）
- 生产：见 `.env.production`（默认 `/`，通常配合反向代理或同域部署）

## 常用命令

- 构建：`pnpm build`
- 预览：`pnpm preview`
- 类型检查：`pnpm typecheck`
- 测试：`pnpm test:run`

## 数据存储

本地数据使用 IndexedDB（Dexie）存储，用于提示词、历史、模板等。
