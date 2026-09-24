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

### 发现: DashScope 账户欠费
- 现象: 图像生成与 LLM 调用均返回 Arrearage，旧代码误报为"请求参数有误"
- 处理: 已修复错误映射（humanize_provider_error），提示"账户欠费"；**需充值后复测**
- 另: multimodal-generation 端点 default 模型映射修正为 qwen-image-2.0-pro（原误映射 wanx-v1）

## 2026-08-03 (巡检)

- **豆包/通义图像** (image): ✅ HTTP 200 — 端点可达 + 认证通过（实际生成受账户欠费限制）
- **可灵** (video): ⚠️ HTTP - — 未配置 (backend/.env 缺少密钥或端点)
- **即梦** (video): ⚠️ HTTP - — 未配置 (backend/.env 缺少密钥或端点)
- **Runway** (video): ⚠️ HTTP - — 未配置 (backend/.env 缺少密钥或端点)
- **阿里万相编辑** (edit): ⚠️ HTTP - — 未配置 (backend/.env 缺少密钥或端点)
- **DashScope向量** (embedding): ✅ HTTP 400 — 端点可达 + 认证通过

## 2026-09-23

- **豆包/通义图像** (image): ❌ HTTP 401 — API密钥无效或已过期
- **可灵** (video): ⚠️ HTTP - — 未配置 (backend/.env 缺少密钥或端点)
- **即梦** (video): ⚠️ HTTP - — 未配置 (backend/.env 缺少密钥或端点)
- **Runway** (video): ⚠️ HTTP - — 未配置 (backend/.env 缺少密钥或端点)
- **阿里万相编辑** (edit): ⚠️ HTTP - — 未配置 (backend/.env 缺少密钥或端点)
- **DashScope向量** (embedding): ✅ HTTP 400 — 端点可达 + 认证通过
- **网关 stepfun** (gateway): ✅ HTTP 200 — 认证通过，在售模型 36 个
- **网关 newapi** (gateway): ⚠️ HTTP - — base_url 未配置（model_catalog.json gateways）
- **网关 siliconflow** (gateway): ✅ HTTP 200 — 认证通过，在售模型 98 个
- **stepfun/step-tts-mini** (tts): ✅ HTTP 200 — 在网关在售清单中
- **stepfun/step-tts-2** (tts): ✅ HTTP 200 — 在网关在售清单中
- **placeholder/本地占位图（¥0）** (image): ⚠️ HTTP - — 无模型名（本地/免费通道，不发请求）
- **stepfun/step-image-edit-2** (image): ✅ HTTP 200 — 在网关在售清单中
- **stepfun/step-2x-large** (image): ✅ HTTP 200 — 在网关在售清单中
- **ark_plan/doubao-seedream-5.0-lite** (image): ✅ HTTP 400 — 认证通过（参数被拒＝探针未真正生成，零消耗）（越界 size 探针，未出图）
- **siliconflow/Kwai-Kolors/Kolors** (image): ✅ HTTP 200 — 在网关在售清单中
- **siliconflow/Tongyi-MAI/Z-Image-Turbo** (image): ✅ HTTP 200 — 在网关在售清单中
- **none/不生成 B-roll（静轨 Ken Burns）** (video): ⚠️ HTTP - — 无模型名（本地/免费通道，不发请求）
- **dashscope（账号级探针 qwen3-tts-flash）** (gateway): ❌ HTTP 400 — 账号级失效（arrearage）——去控制台查余额/资格：{"code":"Arrearage","message":"Access denied, please make sure your account is in good standing. For details, see: https://help.aliyun.com/zh/model-st
- **dashscope/qwen3-tts-flash** (tts): ❌ HTTP - — 随账号判定：不可用
- **dashscope/cosyvoice-v3.5-flash** (tts): ❌ HTTP - — 随账号判定：不可用
- **dashscope/wanx2.1-t2i-turbo** (image): ❌ HTTP - — 随账号判定：不可用
- **dashscope/wanx-v1** (image): ❌ HTTP - — 随账号判定：不可用
- **dashscope/wanx2.1-i2v-turbo** (video): ❌ HTTP - — 随账号判定：不可用
- **edge/无模型** (tts): ⚠️ HTTP - — 当前解释器无 edge-tts（/Users/yiwenxu123/Projects/content-ops/AI绘图/backend/.venv/bin/python）——用管线的 venv 跑本脚本才能验到这条兜底
