已完成项目分析，结论先说：这个项目的能力底座不错，已经不是“玩具 Demo”，但当前产品形态仍偏“功能堆叠型工作台”。对小白用户来说，最大问题不是功能不够，而是入口、配置、辅助面板和专家参数过早暴露，导致首屏认知负担偏高。你提到的“大面积白色色块”和“模型配置顶部标签没必要”，判断是对的。

**总体判断**
项目目前适合熟悉 API、模型、提示词的人使用；小白用户能用，但需要被“带着走”。现有新手向导是正确方向，见 [BeginnerTaskWizard.vue](/Users/yiwenxu123/Projects/AI绘图/frontend/src/components/BeginnerTaskWizard.vue:3)，但它后续又把用户带回图像生成、视频生成、图片编辑等专家面板，体验还没有闭环。

技术层面整体健康：`npm run typecheck`、`npm run test:run`、`node mcp-server/test.js` 均通过；后端 `/config` 和 `/api/model-manifest` 可正常访问。

**核心问题**
1. 小白入口被专家功能稀释  
主界面同时暴露新手向导、图像生成、视频生成、图片编辑，右侧浮动面板默认打开，还包含模板、知识、分析、作品、笔记、入库。位置在 [App.vue](/Users/yiwenxu123/Projects/AI绘图/frontend/src/App.vue:46) 和 [App.vue](/Users/yiwenxu123/Projects/AI绘图/frontend/src/App.vue:77)。其中“入库”明显是维护/管理员能力，不应出现在普通用户首屏。

2. 右侧浮动面板破坏主流程  
实际打开页面后，右侧面板会遮挡新手向导内容，视觉重心被分裂。默认打开逻辑在 [App.vue](/Users/yiwenxu123/Projects/AI绘图/frontend/src/App.vue:161)。建议默认关闭，改成“素材/知识抽屉”，只在用户需要时打开。

3. 下方白色色块割裂感来自卡片结构  
新手任务区和“三步开始创作”是两个大 `n-card`，见 [BeginnerTaskWizard.vue](/Users/yiwenxu123/Projects/AI绘图/frontend/src/components/BeginnerTaskWizard.vue:3) 和 [BeginnerTaskWizard.vue](/Users/yiwenxu123/Projects/AI绘图/frontend/src/components/BeginnerTaskWizard.vue:25)。在浅灰页面背景上，大面积白卡连续堆叠，确实像两块割裂面板。应改成一个统一工作区：上方任务选择，下方直接展开表单与结果，不再另起一张大白卡。

4. 配置弹窗信息层级过多  
设置弹窗顶部有状态标签，下面又有图像 API、视频 API、编辑 API、视觉模型、大模型、外观六个标签，见 [ConfigModal.vue](/Users/yiwenxu123/Projects/AI绘图/frontend/src/components/ConfigModal.vue:15) 和 [ConfigModal.vue](/Users/yiwenxu123/Projects/AI绘图/frontend/src/components/ConfigModal.vue:28)。对小白来说，“API、Endpoint、供应商、默认模型”都偏技术。应改成“配置创作能力”：生成图片、生成视频、图片编辑、提示词优化。Endpoint 和模型放进高级设置。

5. 有一个视频异步链路风险  
后端在 [main.py](/Users/yiwenxu123/Projects/AI绘图/backend/main.py:252) 提取了 `task_id`，但返回时没有把它写入响应对象，见 [main.py](/Users/yiwenxu123/Projects/AI绘图/backend/main.py:254)。前端视频 store 又依赖 `result.task_id` 做轮询，见 [video.ts](/Users/yiwenxu123/Projects/AI绘图/frontend/src/stores/video.ts:82)。这会导致某些异步视频接口无法正确进入轮询。

6. UI 可访问性和现代感有细节债  
任务卡片用卡片点击而不是语义按钮，见 [BeginnerTaskWizard.vue](/Users/yiwenxu123/Projects/AI绘图/frontend/src/components/BeginnerTaskWizard.vue:10)。全局按钮用了 `transition: all`，见 [style.css](/Users/yiwenxu123/Projects/AI绘图/frontend/src/style.css:95)。一些图标按钮主要靠 `title`，需要补 `aria-label`。这些会影响键盘操作、可访问性和交互质感。

**优化方案**
P0：先修可用性和首屏体验  
隐藏右侧浮动面板，移除普通用户首屏的“入库”。把配置入口改成首次使用向导：选择要做什么，推荐一个供应商，只填 API Key；Endpoint、模型作为高级项。修复视频 `task_id` 返回问题。把 MCP 测试从硬编码 8 个工具改为校验真实 server，因为当前 [test.js](/Users/yiwenxu123/Projects/AI绘图/mcp-server/test.js:4) 仍写着 8 个工具，而实际 [index.js](/Users/yiwenxu123/Projects/AI绘图/mcp-server/index.js:34) 已有 10 个工具。

P1：重构小白主路径  
首页只保留“我想做什么”的任务入口。用户选任务、写一句中文、看到提示词解释、直接生成、查看结果、继续编辑或转视频，全程不离开向导。图像生成面板里的模型、尺寸、负面词、高级参数保留给专家模式，普通模式只显示“用途、风格、比例、生成”。

P2：重做视觉结构  
把页面从“多个白色卡片堆叠”改成统一工作台布局：浅灰背景、单一主工作区、局部内容分区，不要卡片套卡片。右侧模板/知识改成抽屉或底部推荐区。减少 emoji 标签，换成统一图标体系。配置弹窗顶部状态标签去掉或改成左侧步骤导航。

P3：增强长期可维护性  
统一供应商预设来源，避免 `ConfigModal` 和 `types/provider` 重复维护。知识库搜索里未使用的 `model_type` 要清理或真正参与模型适配。API Key 当前明文存在 `localStorage`，本地个人版可以接受，若要公开部署，需要改成后端加密保存或只走服务端环境变量。

**建议执行顺序**
先做 P0：默认关闭浮动面板、隐藏入库、重做配置弹窗第一屏、修复视频 `task_id`。这几项投入小，但会立刻改善“小白能不能开始用”的问题。

然后做 P1/P2：把新手向导变成真正的主流程闭环，同时重构大白卡布局。这个阶段会明显提升现代感和产品完成度。


已完成第一轮优化，重点先处理“小白首屏”和“配置过载”。

本轮改动：
- 首屏辅助面板默认关闭，不再遮挡新手向导；“AI 入库”改为维护模式才显示：[App.vue](/Users/yiwenxu123/Projects/AI绘图/frontend/src/App.vue)
- 顶部按钮从“配置 API”改为“配置能力”，减少技术感。
- 新手向导从两块割裂白卡改成统一工作区，任务卡改为真实按钮，键盘可访问性更好：[BeginnerTaskWizard.vue](/Users/yiwenxu123/Projects/AI绘图/frontend/src/components/BeginnerTaskWizard.vue)
- 配置弹窗去掉顶部那排状态标签，改为“生成图片 / 生成视频 / 图片编辑 / 提示词优化 / 图片分析”能力卡片：[ConfigModal.vue](/Users/yiwenxu123/Projects/AI绘图/frontend/src/components/ConfigModal.vue)
- 文案从“配置 API 密钥”调整为更面向用户的“配置生成图片/视频/编辑能力”。
- 修复视频任务 `task_id` 没返回给前端的问题：[main.py](/Users/yiwenxu123/Projects/AI绘图/backend/main.py)
- MCP 测试从 8 个工具更新为当前真实的 10 个工具：[test.js](/Users/yiwenxu123/Projects/AI绘图/mcp-server/test.js)
- 去掉全局 `transition: all`，改为明确过渡属性：[style.css](/Users/yiwenxu123/Projects/AI绘图/frontend/src/style.css)

验证结果：
- `npm run typecheck` 通过
- `npm run test:run` 通过，24 个测试通过
- `npm run build` 通过，仅有包体积提示
- `node mcp-server/test.js` 通过
- Python 编译检查通过
- 本地页面已打开验证：首屏显示“展开面板”，配置弹窗显示新的能力卡片结构

下一步建议继续做第二轮：把“去生成图片”后的流程也留在新手向导内，减少跳转到专家生成面板带来的割裂感。