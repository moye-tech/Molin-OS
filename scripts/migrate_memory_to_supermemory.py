"""
批量迁移 Hermes memory 中的静态信息到 Supermemory 云存储
"""
import sys
sys.path.insert(0, "/home/ubuntu/hermes-os")

from molib.infra.supermemory import save_memory

# ===== 分类保存 =====

# 1. 系统架构
arch_id = save_memory(
    title="墨麟OS系统架构",
    content="""
墨麟OS v1.0 架构概览：

【6层架构】
L0 控制台 → L1 CEO引擎(IntentRouter+风险+SOP) → L2 5VP管理层 → L3 20家子公司 → L4 基础设施 → L5 存储

【L1 CEO引擎核心组件】
- IntentRouter: 语义判断用户意图
- 风险评估: 三层决策(GO/NO_GO/NEED_INFO)
- SOP引擎: YAML定义自动流程(engine.py+sop_feedback+sop_optimizer)
- 记忆集成: 多后端记忆系统

【L2 5VP管理层】
- 营销VP: 墨笔/墨韵/墨图/墨播/墨声配
- 运营VP: 墨域/墨声客/墨链/墨学
- 技术VP: 墨码/墨维/墨安/墨梦
- 财务VP: 墨算
- 战略VP: 墨商/墨海/墨研

【统一入口】python3 -m molib.cli
【FastAPI入口】molib/ceo/main.py

【技能系统】336个SKILL.md, 已标准化molin_owner标记
【子公司技能】36个(business/molin下24个目录+sub/5个子公司)
【吸收项目】27个项目(~520K⭐)已吸收设计模式
【CI入口】CLI: python3 -m molib
""",
    tags=["系统架构", "墨麟OS", "v1.0"],
)
print(f"✅ 架构: {arch_id}")

# 2. 20家子公司详情
subs_id = save_memory(
    title="墨麟AI集团20家子公司",
    content="""
墨麟AI集团 — 20家垂直子公司 + 3家共同服务 + 3家专项预置

【VP营销 5家】
1. 墨笔文创 — 文字内容创作、文案、公众号、博客
2. 墨韵IP — IP衍生、商标、版权、品牌管理
3. 墨图设计 — 图片/UI/封面/视觉设计
4. 墨播短视频 — 短视频脚本+生成
5. 墨声配音 — AI语音合成、播客制作

【VP运营 4家】
6. 墨域私域 — CRM、用户分层、社群运营
7. 墨声客服 — 自动化客服（闲鱼消息检测→回复）
8. 墨链电商 — 订单管理、交易、电商平台
9. 墨学教育 — 课程设计、学习路径、辅导

【VP技术 4家】
10. 墨码开发 — 软件开发、代码编写
11. 墨维运维 — 服务器、部署、DevOps
12. 墨安安全 — 代码审计、安全评估
13. 墨梦AutoDream — AI自动化实验、快速原型

【VP财务 1家】
14. 墨算财务 — 记账、预算、成本控制

【VP战略 3家】
15. 墨商BD — 商务拓展、合作洽谈
16. 墨海出海 — 多语言、全球化、出海运营
17. 墨研竞情 — 竞争分析、趋势研究

【共同服务 3家】
18. 墨律法务 — 合同审查、合规、风险评估
19. 墨脑知识 — 知识管理、RAG、长期记忆
20. 墨测数据 — 数据分析、测试、质量

【专项预置】
- trading.py — 量化交易策略·信号·回测
- scrapling_worker.py — 网页抓取·数据采集(来自Scrapling)
- router9.py — 网络流量·多路路由(来自9router)
""",
    tags=["子公司", "墨麟OS", "组织架构"],
)
print(f"✅ 子公司: {subs_id}")

# 3. 项目吸收记录
absorb_id = save_memory(
    title="已吸收开源项目清单(~520K⭐)",
    content="""
墨麟OS已吸收27个开源项目(~520K⭐)的设计模式：

【吸收顺序】
1. CowAgent(44K) — Deep Dream记忆蒸馏
2. MetaGPT(67K) — 角色-Action-消息循环
3. nanobot(41K) — 轻量Agent架构
4. Agent-Reach(18.7K) — 多Agent协作
5. ADK(19K) — Google Agent开发套件
6. E2B(12K) — 沙箱执行保护
7. omi(12K) — 全平台OAuth
8. GenericAgent(9.1K) — 自进化SOP
9. Vibe-Trading(4K) — 量化交易Agent
10. min-SWE(4K) — 极简Agent循环
11. A2A(23.5K) — Agent通信协议(Google)
12. refact(3.9K) — Session-Stream架构
13. beeai(3.8K) — Workflow引擎(IBM)
14. Pixelle-Video(10.7K) — 短视频引擎
15. opensre(4.4K) — SRE Agent
16. cocoindex(7.8K) — 增量计算引擎
17. Parlant(18.1K) — Context Engineering(客服)
18. Ranedeer(29.6K) — AI导师DSL
19. Onlook(25.6K) — 设计工具(视觉↔代码同步)
20. Weblate(5.8K) — 本地化平台
21. Stagehand(22.4K) — Browser Agent SDK
22. UI-TARS(29.6K) — 多模态Agent(Bytedance)
23. CUA(15.6K) — Computer-Use Agent
24. DeepTutor(23.3K) — 深度辅导
25. CozeStudio(20.7K) — 扣子工作室
26. InvokeAI(27.1K) — AI图像生成
27. MiroFish(35K) — 趋势预测

【后续跳过】
- Skyvern(21.5K) — 浏览器自动化
- Crawlee(8.8K) — 爬虫框架
- PyMuPDF(9.6K) — PDF处理
""",
    tags=["项目吸收", "开源", "设计模式"],
)
print(f"✅ 项目吸收: {absorb_id}")

# 4. 基建踩坑经验
lessons_id = save_memory(
    title="基建踩坑经验集锦",
    content="""
【Hermes Agent使用经验】

1. xhs-cli小红书自动化
- --qrcode在无头服务器报错,需调_http_qrcode_login()绕过
- 飞书发二维码需FeishuAdapter.send_image_file()直调API
- 扫码后guest=true表示未实名,需实名账号才可发布
- Cookie保存在~/.xiaohongshu-cli/cookies.json

2. GPT Image 2
- api.openai.com被墙不可达(168.143.x.x)
- 千问百炼qwen-image-2.0-pro已验证可用

3. 闲鱼API
- 旧session过期必须重新扫码(Playwright)
- _m_h5_tk+旧unb仍返回FAIL_SYS_SESSION_EXPIRED
- 依赖: pip install websockets==13.1 Pillow blackboxprotobuf PyExecJS
- 统一入口: python3.12 xianyu_helper.py [verify|cover|publish|monitor]
- 中文字体: /usr/share/fonts/truetype/wqy/wqy-zenhei.ttc

4. 模型等级路由
- flash=DeepSeek v4 flash(简单任务/低成本)
- pro=DeepSeek v4 pro(复杂分析/决策/长文)
- vision=qwen3-vl-plus via 千问百炼
- video=HappyHorse-1.0-T2V via 千问百炼
- 生图=qwen-image-2.0-pro

5. CEO引擎排障
- vp_results=[]→asyncio.gather并行
- risk_engine.assess()同步勿await
- auto_dream去"ai"关键词避错路由
- 控制台群: oc_94c87f141e118b68c2da9852bf2f3bda

6. 网络诊断
- 仅Cogent直连IP(chatgpt.com 128.121.x.x)被墙
- CF CDN域名(sentinel.openai.com 172.64.x.x)可达
- 分段测:DNS→TCP→TLS→HTTP
""",
    tags=["踩坑", "基建", "排障", "经验"],
)
print(f"✅ 踩坑: {lessons_id}")

# 5. 模型&API配置
model_id = save_memory(
    title="模型配置与API密钥信息",
    content="""
【模型配置】
当前主模型: DeepSeek via OpenRouter
- flash: DeepSeek v4 flash（简单任务/低成本）
- pro: DeepSeek v4 pro（复杂分析/决策/长文）
- vision: qwen3-vl-plus via 千问百炼API
- video: HappyHorse-1.0-T2V via 千问百炼API
- 生图: qwen-image-2.0-pro via 千问百炼API
- GPT-4o生图: 通过ChatGPT免费额度(codex CLI/auth.json)

【API Key来源】
- OpenRouter API Key: 配置在 Hermes Agent
- 千问百炼: 已充值可用
- 阿里百炼: 已充值可用千问全家桶
- GPT/Claude: 免费额度,通过浏览器操作使用

【预算】
- 每月API预算: ¥1,360
- 所有LLM调用复用Hermes的模型配置
- 各发布平台API Key通过Hermes Agent能力间接实现
""",
    tags=["模型配置", "API", "DeepSeek", "千问"],
)
print(f"✅ 模型配置: {model_id}")

# 6. cronjob与飞轮管线
cron_id = save_memory(
    title="Cronjob与飞轮管线配置",
    content="""
【系统原则】零空转费用，有任务时才手动跑。

【Cronjob总览】11个cronjob
暂停10个，仅保留闲鱼消息检测(赚钱入口)的排期。
大盘已关闭，运营大盘已关闭。
系统干净待命，用户主动给任务才消耗token。

【飞轮管线】(全部暂停,需要时手动触发)
08:00 墨思情报银行 — 扫描博客/arXiv/MiroFish→情报日报
09:00 墨迹内容工厂 — 情报→AI生成3篇内容
09:00 CEO每日简报 — 汇总状态推送
10:00 墨增增长引擎 — SEO优化·增长分析
10:00 每日治理合规 — 审计+合规检查
12:00 系统状态快照 — 汇总产出+运营快照
15/45分 闲鱼消息检测 — 新消息AI自动回复(唯一活跃)
周五10:00 自学习进化 — GitHub扫描+技能更新

【飞轮接力文件格式】
relay/intelligence_morning.json → relay/content_flywheel.json → relay/distribution_plan.json
""",
    tags=["cronjob", "飞轮", "系统配置"],
)
print(f"✅ cron: {cron_id}")

# 7. 文件系统与记忆路径
fs_id = save_memory(
    title="系统关键文件位置与记忆路径",
    content="""
【工作目录】~/hermes-os/
【系统文件】~/.hermes/os/ (Hermes Agent系统)
【Python包】~/hermes-os/molib/ (执行层)
【机器人脚本】~/hermes-os/bots/
【商业化方案】~/hermes-os/business/
【飞轮数据】~/hermes-os/relay/
【系统文档】~/hermes-os/docs/

【记忆系统】
向量记忆: ~/.hermes/memory/chroma_db/
结构化记忆: ~/.hermes/memory/vector_memory.db
记忆蒸馏: ~/.hermes/dream/
日报存档: ~/.hermes/daily_reports/
长期记忆: ~/.hermes/memory/long_term/ (claude-mem)
事件总线: ~/.hermes/events/
事件文件: ~/.hermes/events/ (FileEventBus)
Supermemory: 云服务(app.supermemory.ai)
凭证保险柜: ~/.hermes/vault/

【GitHub】
主仓库: moye-tech/Molin-OS (原Hermes-OS)
README/AGENTS/SOUL/setup.py已标准化
""",
    tags=["文件路径", "系统文件", "GitHub"],
)
print(f"✅ 文件系统: {fs_id}")

# 8. 用户铁律与偏好
rules_id = save_memory(
    title="用户核心铁律与偏好",
    content="""
【底层铁律】
1. 现金隔离: 绝不碰任何与现金/余额/转账相关的操作。支付、提现、改价等需用户手动确认。
2. 数据驱动: 所有策略和建议必须有真实依据(API返回数据/官方文档/GitHub数据)。禁止模拟、编造或假设。
3. 自主进化: 每周扫描GitHub高星(>500⭐)相关项目,发现可集成的能力直接尝试部署并汇报结果。

【用户偏好】
- 零空转费用,有任务才跑
- 报告类内容用飞书CLI发富文本/FeishuCardSender
- 飞书控制台群: oc_94c87f141e118b68c2da9852bf2f3bda
- CEO引擎build_summary_card只留做任务执行追踪
- 支持report_url参数卡片末尾挂"查看完整报告"按钮

【用户账号】
- 有GPT/Claude免费额度(强生图/长文)
- 阿里百炼已充值可用千问全家桶

【交付习惯】
- 优先选择零依赖方案
- 喜欢看量化对比(效率和效果的评估)
- 偏好简洁直接的输出
""",
    tags=["用户", "铁律", "偏好", "规则"],
)
print(f"✅ 用户铁律: {rules_id}")

print()
print("=== ✅ 全部8条静态记忆已迁移到 Supermemory ===")
