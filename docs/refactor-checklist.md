# Refactor 回归清单（Wave 1 + Sprint 2）

每次 PR 合并前手动执行前 5 项；发版前执行全部。

## 自动化检查

```bash
cd frontend && npx vue-tsc --noEmit && npx vitest run
cd backend && python3 -m pytest tests/ -q
node mcp-server/test.js
```

## 冒烟路径

- [x] 配置图像供应商 → 生成 1024 图成功
- [x] 场景创作 → 电商主图 → 生成
- [x] 场景创作 → AI 智能调优 → 生成
- [x] 切换模型后尺寸选项与后端校验一致
- [x] 视频生成（可灵）提交并轮询完成
- [x] 图片编辑（指令编辑）
- [x] 右侧面板：模板插入、知识检索、作品库
- [x] 全屏预览 / 下载 / 收录案例
- [x] 配置能力弹窗：图像/视频/LLM 可保存

## 知识库（Sprint 2）

- [x] 全新 clone 后仅 `python3 main.py`，`GET /api/knowledge` 返回 >0 条
- [x] `POST /api/knowledge/search` 查询「电商」有结果
- [x] MCP `search_knowledge` 有数据（非空 items）

## P0 遗留修复（已完成）

- [x] `icons.ts` lucide `CheckCircle2` → `CheckCircle`（与 ionicons 一致）
- [x] `stable-diffusion` manifest 标记 `advanced_params`
- [x] `seed_from_json_if_empty` 启动自动灌入知识库

## Wave 1 完成标准

- [x] `GeneratePanel.vue` ≤ 250 行（当前 ~147）
- [x] 无业务代码引用 `data/modelSizeConfig.ts`
- [x] `/api/model-manifest` 含 `name` 字段
- [x] `VideoPanel` 模型列表来自 manifest
- [x] 后端启动自动灌入知识库（`seed_from_json_if_empty`）

## Wave 2（Sprint 2 — 已完成）

- [x] R3 视频 TaskStatus Adapter（`backend/providers/` kling/jimeng/runway + factory）
- [x] R4 知识数据收敛（静态数据 → `dataStore` API；文件仅保留类型/UI 配置）
- [x] R5 `build_payload` 集成测试（43 用例）
- [x] R6 拆分 `ConfigModal.vue`（157 行 + 8 子组件）
- [x] R7 docker-compose（后端 + 前端 + nginx）
- [x] R8 后端 Key 模式（`BACKEND_CONFIGURED_CAPABILITIES` + `useCapabilityReady` 生成链路）
- [x] dataStore 改用 `unified-templates` 单 API（替代 6 路并发）

## Sprint 4（已完成）

- [x] R8 闭环：`generator` / `video` / `editor` 后端 Key 模式可不传 `api_key`
- [x] 删除 `data/modelSizeConfig.ts`、`data/videoTemplates.ts`
- [x] `VideoTemplateWizard` 改读 `dataStore.videoTemplates`
- [x] `TemplateCenter` 子 Tab `defineAsyncComponent` 懒加载
- [x] 知识条目 `lastVerified` 过期标记（术语词典 / 案例库）
- [x] `优化建议.md` 同步终态
