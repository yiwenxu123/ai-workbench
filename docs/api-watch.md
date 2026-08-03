# API 变更巡检记录

自动巡检追加在此（`python scripts/check_apis.py --watch`）。手动记录平台接口变更请按日期追加。

## 手动变更记录模板

```
## YYYY-MM-DD
### 变更: <平台名> <接口名>
- 变更内容: ...
- 影响: 图像生成 / 视频任务查询 / ...
- 适配点: backend/routers/generation.py / backend/providers/xxx_adapter.py
- 处理状态: 待处理 / 已修复(commit xxx)
```

## 2026-08-03

- **豆包/通义图像** (image): ❌ HTTP - — 连接超时（网络波动，复测 200 ✅）
- **可灵** (video): ⚠️ HTTP - — 未配置 (backend/.env 缺少密钥或端点)
- **即梦** (video): ⚠️ HTTP - — 未配置 (backend/.env 缺少密钥或端点)
- **Runway** (video): ⚠️ HTTP - — 未配置 (backend/.env 缺少密钥或端点)
- **阿里万相编辑** (edit): ⚠️ HTTP - — 未配置 (backend/.env 缺少密钥或端点)
- **DashScope向量** (embedding): ✅ HTTP 400 — 端点可达 + 认证通过
