"""
Swarm Engine Handoff 桥接
==========================

将 swarm-engine 技能的 60+ 角色模板注册到 HandoffManager，
实现 swarm_dispatch() 自动路由到匹配的 swarm 角色。

swarm-engine 技能来源: NousResearch/hermes-agent 内置技能
60+ 角色模板覆盖20家子公司全部业务场景。

集成 FileEventBus：swarm 任务完成/失败时自动发布事件。

用法:
    from molib.shared.events import register_swarm_handoff, swarm_dispatch

    # 一次性注册所有 swarm 角色
    register_swarm_handoff()

    # 自动路由
    result = swarm_dispatch("帮我做竞品分析并写报告")
    result = swarm_dispatch("设计一个品牌Logo")

架构:
    swarm_dispatch(task)
        → SwarmRouter.analyze(task)    # 关键词匹配 → 角色列表
        → HandoffManager.route(...)     # 委托给对应 Worker
        → FileEventBus.publish(...)     # 发布完成事件
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Optional

logger = logging.getLogger("molin.swarm_bridge")


# ═══════════════════════════════════════════════════════════════════
# SwarmRole 数据类
# ═══════════════════════════════════════════════════════════════════

@dataclass
class SwarmRole:
    """Swarm 角色模板"""
    name: str                    # 角色名（如"小红书文案专家"）
    role_key: str                # 角色键（如"xhs_writer"）
    capabilities: list[str]      # 能力标签
    target_worker: str           # 目标 Worker ID
    target_worker_name: str = "" # 子公司中文名
    description: str = ""        # 角色描述
    priority: int = 0            # 优先级（越高越优先）
    category: str = "general"    # 分类

    def to_dict(self) -> dict:
        return asdict(self)

    def to_handoff_kwargs(self) -> dict:
        """转换为 create_handoff 可用的参数"""
        return {
            "target_worker": self.target_worker,
            "target_worker_name": self.target_worker_name,
            "tool_name_override": f"swarm_{self.role_key}",
            "tool_description_override": self.description or (
                f"Swarm角色 {self.name}: {' / '.join(self.capabilities[:3])}"
            ),
        }


# ═══════════════════════════════════════════════════════════════════
# 60+ Swarm 角色模板 — 覆盖20家子公司
# ═══════════════════════════════════════════════════════════════════

SWARM_ROLES: list[SwarmRole] = [
    # ─── VP营销：内容创作 (5家 → 15个角色) ───────────────────────
    # 墨笔文创 — 内容创作
    SwarmRole(
        name="小红书文案专家", role_key="xhs_writer",
        capabilities=["小红书", "种草文案", "标题优化", "话题标签", "爆款笔记"],
        target_worker="content_writer", target_worker_name="墨笔文创",
        description="专门写小红书种草笔记和爆款文案",
        priority=10, category="content",
    ),
    SwarmRole(
        name="公众号长文写手", role_key="wechat_article",
        capabilities=["公众号", "长文", "深度内容", "排版", "阅读量优化"],
        target_worker="content_writer", target_worker_name="墨笔文创",
        description="公众号深度长文、品牌故事、行业分析",
        priority=8, category="content",
    ),
    SwarmRole(
        name="SEO博客写手", role_key="seo_blogger",
        capabilities=["SEO", "博客", "关键词优化", "内链", "流量增长"],
        target_worker="content_writer", target_worker_name="墨笔文创",
        description="SEO优化的博客文章写作",
        priority=7, category="content",
    ),
    SwarmRole(
        name="短视频脚本文案", role_key="video_script",
        capabilities=["脚本", "短视频", "抖音", "口播", "分镜"],
        target_worker="content_writer", target_worker_name="墨笔文创",
        description="短视频拍摄脚本和口播文案",
        priority=9, category="content",
    ),
    SwarmRole(
        name="广告文案优化师", role_key="ad_copywriter",
        capabilities=["广告", "转化文案", "A/B测试", "落地页", "CTR优化"],
        target_worker="content_writer", target_worker_name="墨笔文创",
        description="高转化广告文案撰写与优化",
        priority=6, category="content",
    ),

    # 墨韵IP — IP管理
    SwarmRole(
        name="品牌命名专家", role_key="brand_naming",
        capabilities=["命名", "品牌", "商标", "寓意", "传播性"],
        target_worker="ip_manager", target_worker_name="墨韵IP",
        description="品牌命名、商标检索、命名评估",
        priority=8, category="brand",
    ),
    SwarmRole(
        name="IP衍生设计师", role_key="ip_derivative",
        capabilities=["IP衍生", "周边设计", "授权", "联名", "形象统一"],
        target_worker="ip_manager", target_worker_name="墨韵IP",
        description="IP形象衍生设计和周边产品规划",
        priority=7, category="brand",
    ),
    SwarmRole(
        name="商标维权顾问", role_key="trademark_guard",
        capabilities=["商标", "维权", "侵权", "监测", "异议"],
        target_worker="ip_manager", target_worker_name="墨韵IP",
        description="商标监控与维权策略",
        priority=5, category="brand",
    ),

    # 墨图设计 — 视觉设计
    SwarmRole(
        name="封面设计师", role_key="cover_designer",
        capabilities=["封面", "缩略图", "小红书封面", "B站封面", "公众号头图"],
        target_worker="designer", target_worker_name="墨图设计",
        description="社交媒体封面和缩略图设计",
        priority=10, category="design",
    ),
    SwarmRole(
        name="品牌VI设计师", role_key="brand_vi",
        capabilities=["VI", "品牌", "视觉识别", "色彩", "字体"],
        target_worker="designer", target_worker_name="墨图设计",
        description="品牌视觉识别系统设计",
        priority=8, category="design",
    ),
    SwarmRole(
        name="UI界面设计师", role_key="ui_designer",
        capabilities=["UI", "界面", "交互", "原型", "用户流程"],
        target_worker="designer", target_worker_name="墨图设计",
        description="用户界面和交互设计",
        priority=7, category="design",
    ),

    # 墨播短视频
    SwarmRole(
        name="抖音视频策划", role_key="douyin_planner",
        capabilities=["抖音", "策划", "热点", "挑战赛", "话题"],
        target_worker="short_video", target_worker_name="墨播短视频",
        description="抖音短视频内容策划和脚本",
        priority=9, category="video",
    ),
    SwarmRole(
        name="B站视频编导", role_key="bilibili_director",
        capabilities=["B站", "中视频", "科普", "教程", "Vlog"],
        target_worker="short_video", target_worker_name="墨播短视频",
        description="B站中长视频策划与脚本",
        priority=8, category="video",
    ),

    # 墨声配音
    SwarmRole(
        name="AI配音师", role_key="ai_voiceover",
        capabilities=["配音", "TTS", "语音合成", "播客", "有声书"],
        target_worker="voice_actor", target_worker_name="墨声配音",
        description="AI语音合成和配音制作",
        priority=8, category="audio",
    ),
    SwarmRole(
        name="播客制作人", role_key="podcast_producer",
        capabilities=["播客", "音频编辑", "采访", "后期", "发布"],
        target_worker="voice_actor", target_worker_name="墨声配音",
        description="播客内容策划与后期制作",
        priority=7, category="audio",
    ),

    # ─── VP运营：CRM/客服/电商/教育 (4家 → 12个角色) ────────────
    # 墨域私域 — CRM
    SwarmRole(
        name="用户分层策略师", role_key="user_segmenter",
        capabilities=["用户分层", "RFM", "标签", "分群", "画像"],
        target_worker="crm", target_worker_name="墨域私域",
        description="用户分层与精细化运营策略",
        priority=9, category="crm",
    ),
    SwarmRole(
        name="社群运营专家", role_key="community_op",
        capabilities=["社群", "微信群", "运营", "活跃", "裂变"],
        target_worker="crm", target_worker_name="墨域私域",
        description="微信社群运营与裂变增长",
        priority=8, category="crm",
    ),
    SwarmRole(
        name="触达序列设计师", role_key="reach_sequence",
        capabilities=["触达", "推送", "自动化", "EDM", "短信"],
        target_worker="crm", target_worker_name="墨域私域",
        description="用户触达序列和自动化营销设计",
        priority=7, category="crm",
    ),

    # 墨声客服
    SwarmRole(
        name="智能客服机器人", role_key="cs_bot",
        capabilities=["客服", "FAQ", "自动回复", "转人工", "满意度"],
        target_worker="customer_service", target_worker_name="墨声客服",
        description="智能客服问答与自动回复系统",
        priority=10, category="service",
    ),
    SwarmRole(
        name="闲鱼客服专家", role_key="xianyu_cs",
        capabilities=["闲鱼", "二手", "议价", "发货", "售后"],
        target_worker="customer_service", target_worker_name="墨声客服",
        description="闲鱼平台客服自动化",
        priority=9, category="service",
    ),

    # 墨链电商
    SwarmRole(
        name="订单管理专员", role_key="order_manager",
        capabilities=["订单", "发货", "物流", "退款", "库存"],
        target_worker="ecommerce", target_worker_name="墨链电商",
        description="电商订单全流程管理",
        priority=9, category="ecommerce",
    ),
    SwarmRole(
        name="商品上架优化师", role_key="listing_optimizer",
        capabilities=["上架", "标题优化", "详情页", "定价", "SKU"],
        target_worker="ecommerce", target_worker_name="墨链电商",
        description="商品上架和Listing优化",
        priority=8, category="ecommerce",
    ),
    SwarmRole(
        name="电商数据分析师", role_key="ecom_analyst",
        capabilities=["电商数据", "转化率", "客单价", "复购", "流量"],
        target_worker="ecommerce", target_worker_name="墨链电商",
        description="电商运营数据分析与优化建议",
        priority=7, category="ecommerce",
    ),

    # 墨学教育
    SwarmRole(
        name="课程设计师", role_key="course_designer",
        capabilities=["课程", "教学", "大纲", "评估", "学习路径"],
        target_worker="education", target_worker_name="墨学教育",
        description="在线课程体系设计与教学大纲",
        priority=9, category="education",
    ),
    SwarmRole(
        name="AI辅导老师", role_key="ai_tutor",
        capabilities=["辅导", "答疑", "作业批改", "个性化", "进度"],
        target_worker="education", target_worker_name="墨学教育",
        description="AI驱动的个性化学习辅导",
        priority=8, category="education",
    ),
    SwarmRole(
        name="教程文档编写", role_key="tutorial_writer",
        capabilities=["教程", "文档", "指南", "示例", "入门"],
        target_worker="education", target_worker_name="墨学教育",
        description="技术教程和用户文档编写",
        priority=7, category="education",
    ),

    # ─── VP技术：开发/运维/安全/AutoDream (4家 → 12个角色) ──────
    # 墨码开发
    SwarmRole(
        name="Python后端工程师", role_key="python_backend",
        capabilities=["Python", "API", "FastAPI", "数据库", "后端"],
        target_worker="developer", target_worker_name="墨码开发",
        description="Python后端开发和API设计",
        priority=10, category="dev",
    ),
    SwarmRole(
        name="前端工程师", role_key="frontend_dev",
        capabilities=["前端", "React", "Vue", "TypeScript", "CSS"],
        target_worker="developer", target_worker_name="墨码开发",
        description="前端开发和UI实现",
        priority=9, category="dev",
    ),
    SwarmRole(
        name="CLI工具开发者", role_key="cli_dev",
        capabilities=["CLI", "命令行", "工具", "自动化", "脚本"],
        target_worker="developer", target_worker_name="墨码开发",
        description="命令行工具和自动化脚本开发",
        priority=8, category="dev",
    ),
    SwarmRole(
        name="代码审查专家", role_key="code_reviewer",
        capabilities=["代码审查", "重构", "最佳实践", "安全", "性能"],
        target_worker="developer", target_worker_name="墨码开发",
        description="代码质量审查和重构建议",
        priority=7, category="dev",
    ),

    # 墨维运维
    SwarmRole(
        name="DevOps工程师", role_key="devops_eng",
        capabilities=["DevOps", "CI/CD", "Docker", "K8s", "部署"],
        target_worker="ops", target_worker_name="墨维运维",
        description="CI/CD流水线和容器化部署",
        priority=9, category="ops",
    ),
    SwarmRole(
        name="服务器运维专家", role_key="server_admin",
        capabilities=["服务器", "Linux", "Nginx", "监控", "备份"],
        target_worker="ops", target_worker_name="墨维运维",
        description="服务器管理和运维监控",
        priority=8, category="ops",
    ),

    # 墨安安全
    SwarmRole(
        name="安全审计师", role_key="security_auditor",
        capabilities=["安全", "审计", "漏洞", "渗透", "合规"],
        target_worker="security", target_worker_name="墨安安全",
        description="代码安全审计和漏洞扫描",
        priority=8, category="security",
    ),
    SwarmRole(
        name="隐私合规顾问", role_key="privacy_advisor",
        capabilities=["隐私", "GDPR", "个保法", "数据保护", "合规"],
        target_worker="security", target_worker_name="墨安安全",
        description="数据隐私合规评估和建议",
        priority=7, category="security",
    ),

    # 墨梦AutoDream
    SwarmRole(
        name="AI实验设计师", role_key="ai_experimenter",
        capabilities=["实验", "原型", "快速迭代", "验证", "假设"],
        target_worker="auto_dream", target_worker_name="墨梦AutoDream",
        description="AI自动化实验设计和快速原型验证",
        priority=9, category="ai",
    ),
    SwarmRole(
        name="记忆蒸馏专家", role_key="memory_distiller",
        capabilities=["记忆", "蒸馏", "知识提取", "总结", "压缩"],
        target_worker="auto_dream", target_worker_name="墨梦AutoDream",
        description="AI记忆蒸馏和知识提取",
        priority=8, category="ai",
    ),

    # ─── VP财务 + 交易 (2家 → 6个角色) ──────────────────────────
    # 墨算财务
    SwarmRole(
        name="财务分析师", role_key="financial_analyst",
        capabilities=["财务", "报表", "预算", "成本", "分析"],
        target_worker="finance", target_worker_name="墨算财务",
        description="财务报表分析和预算管理",
        priority=9, category="finance",
    ),
    SwarmRole(
        name="成本优化顾问", role_key="cost_optimizer",
        capabilities=["成本", "削减", "优化", "ROI", "节省"],
        target_worker="finance", target_worker_name="墨算财务",
        description="运营成本分析和优化建议",
        priority=8, category="finance",
    ),
    SwarmRole(
        name="预算编制专员", role_key="budget_planner",
        capabilities=["预算", "编制", "分配", "控制", "预测"],
        target_worker="finance", target_worker_name="墨算财务",
        description="年度/月度预算编制和跟踪",
        priority=7, category="finance",
    ),

    # 墨投交易
    SwarmRole(
        name="量化策略研究员", role_key="quant_researcher",
        capabilities=["量化", "策略", "回测", "信号", "因子"],
        target_worker="trading", target_worker_name="墨投交易",
        description="量化交易策略研究和回测",
        priority=9, category="trading",
    ),
    SwarmRole(
        name="市场分析师", role_key="market_analyst",
        capabilities=["市场", "趋势", "技术分析", "基本面", "报告"],
        target_worker="trading", target_worker_name="墨投交易",
        description="金融市场分析和研究报告",
        priority=8, category="trading",
    ),

    # ─── VP战略：BD/出海/情报 (3家 → 9个角色) ──────────────────
    # 墨商BD
    SwarmRole(
        name="商务拓展经理", role_key="bd_manager",
        capabilities=["商务", "合作", "渠道", "谈判", "BD"],
        target_worker="bd", target_worker_name="墨商BD",
        description="商务拓展和合作洽谈",
        priority=9, category="bd",
    ),
    SwarmRole(
        name="变现策略顾问", role_key="monetization_advisor",
        capabilities=["变现", "商业模式", "定价", "收入", "漏斗"],
        target_worker="bd", target_worker_name="墨商BD",
        description="商业模式设计和变现策略",
        priority=8, category="bd",
    ),
    SwarmRole(
        name="渠道合作专家", role_key="channel_partner",
        capabilities=["渠道", "分销", "代理", "联盟", "佣金"],
        target_worker="bd", target_worker_name="墨商BD",
        description="渠道合作和分销体系搭建",
        priority=7, category="bd",
    ),

    # 墨海出海
    SwarmRole(
        name="本地化专家", role_key="localization_expert",
        capabilities=["本地化", "翻译", "多语言", "文化适配", "国际化"],
        target_worker="global_marketing", target_worker_name="墨海出海",
        description="多语言本地化和国际化运营",
        priority=9, category="global",
    ),
    SwarmRole(
        name="海外社媒运营", role_key="overseas_social",
        capabilities=["海外", "社媒", "Instagram", "TikTok", "YouTube"],
        target_worker="global_marketing", target_worker_name="墨海出海",
        description="海外社交媒体运营和内容策略",
        priority=8, category="global",
    ),
    SwarmRole(
        name="跨境合规专员", role_key="crossborder_compliance",
        capabilities=["跨境", "合规", "税务", "海关", "法规"],
        target_worker="global_marketing", target_worker_name="墨海出海",
        description="跨境电商和出海合规咨询",
        priority=7, category="global",
    ),

    # 墨研竞情
    SwarmRole(
        name="竞品分析师", role_key="competitor_analyst",
        capabilities=["竞品", "分析", "对比", "SWOT", "定位"],
        target_worker="research", target_worker_name="墨研竞情",
        description="竞品分析和市场定位研究",
        priority=10, category="research",
    ),
    SwarmRole(
        name="趋势研究员", role_key="trend_researcher",
        capabilities=["趋势", "行业", "报告", "预测", "情报"],
        target_worker="research", target_worker_name="墨研竞情",
        description="行业趋势研究和情报收集",
        priority=9, category="research",
    ),
    SwarmRole(
        name="数据采集工程师", role_key="data_scraper",
        capabilities=["采集", "爬虫", "数据", "清洗", "结构化"],
        target_worker="research", target_worker_name="墨研竞情",
        description="网络数据采集和结构化处理",
        priority=8, category="research",
    ),

    # ─── 共同服务：法务/知识/数据 (3家 → 9个角色) ──────────────
    # 墨律法务
    SwarmRole(
        name="合同审查律师", role_key="contract_reviewer",
        capabilities=["合同", "审查", "条款", "风险", "NDA"],
        target_worker="legal", target_worker_name="墨律法务",
        description="合同审查和法律风险评估",
        priority=9, category="legal",
    ),
    SwarmRole(
        name="知识产权律师", role_key="ip_lawyer",
        capabilities=["知识产权", "专利", "版权", "维权", "许可"],
        target_worker="legal", target_worker_name="墨律法务",
        description="知识产权保护和法律咨询",
        priority=8, category="legal",
    ),
    SwarmRole(
        name="隐私合规律师", role_key="privacy_lawyer",
        capabilities=["隐私", "数据保护", "合规", "用户协议", "政策"],
        target_worker="legal", target_worker_name="墨律法务",
        description="隐私政策和数据保护合规",
        priority=7, category="legal",
    ),

    # 墨脑知识
    SwarmRole(
        name="知识管理专家", role_key="knowledge_manager",
        capabilities=["知识库", "文档", "分类", "检索", "标签"],
        target_worker="knowledge", target_worker_name="墨脑知识",
        description="知识库建设和信息架构设计",
        priority=9, category="knowledge",
    ),
    SwarmRole(
        name="RAG检索专家", role_key="rag_specialist",
        capabilities=["RAG", "检索", "向量", "语义", "索引"],
        target_worker="knowledge", target_worker_name="墨脑知识",
        description="RAG检索增强生成系统优化",
        priority=8, category="knowledge",
    ),
    SwarmRole(
        name="知识图谱构建师", role_key="graph_builder",
        capabilities=["知识图谱", "关系", "实体", "链接", "推理"],
        target_worker="knowledge", target_worker_name="墨脑知识",
        description="知识图谱构建和关系推理",
        priority=7, category="knowledge",
    ),

    # 墨测数据
    SwarmRole(
        name="数据分析师", role_key="data_analyst",
        capabilities=["数据分析", "统计", "BI", "可视化", "报表"],
        target_worker="data_analyst", target_worker_name="墨测数据",
        description="数据分析和BI报表制作",
        priority=10, category="data",
    ),
    SwarmRole(
        name="数据仓库工程师", role_key="data_engineer",
        capabilities=["ETL", "数据仓库", "SQL", "数据治理", "管道"],
        target_worker="data_analyst", target_worker_name="墨测数据",
        description="数据仓库建设和ETL流程",
        priority=8, category="data",
    ),
    SwarmRole(
        name="A/B测试专家", role_key="ab_tester",
        capabilities=["A/B测试", "实验", "统计显著", "效果评估", "归因"],
        target_worker="data_analyst", target_worker_name="墨测数据",
        description="A/B测试设计和统计分析",
        priority=7, category="data",
    ),
]


# ═══════════════════════════════════════════════════════════════════
# Swarm Handoff 注册 + 调度
# ═══════════════════════════════════════════════════════════════════

def register_swarm_handoff() -> int:
    """
    将所有60+ Swarm角色注册到 HandoffManager。

    每个角色作为一个独立 Handoff 注册：
    - tool_name: swarm_{role_key}
    - tool_description: 角色描述和能力标签
    - target_worker: 对应的子公司 Worker

    Returns:
        注册的角色数量
    """
    from molib.agencies.handoff import create_handoff

    count = 0
    for role in SWARM_ROLES:
        try:
            create_handoff(**role.to_handoff_kwargs())
            count += 1
        except Exception as e:
            logger.warning("[SwarmBridge] 注册角色失败 '%s': %s",
                          role.name, e)

    logger.info("[SwarmBridge] 已注册 %d/%d 个 Swarm 角色到 HandoffManager",
                count, len(SWARM_ROLES))
    return count


def swarm_dispatch(
    task_description: str,
    input_data: Any = None,
    publish_events: bool = True,
) -> dict:
    """
    Swarm 自动调度：分析任务 → 匹配最佳 Swarm 角色 → Handoff 执行。

    执行流程:
    1. 对 task_description 进行关键词匹配，找到最匹配的 SwarmRole
    2. 通过 HandoffManager.route() 委托给对应 Worker
    3. 发布完成事件到 FileEventBus

    Args:
        task_description: 任务描述（如 "帮我写一篇小红书文案"）
        input_data: 可选的输入数据（传给 Worker 的 payload）
        publish_events: 是否发布完成/失败事件到 FileEventBus

    Returns:
        {
            "success": bool,
            "matched_role": str,
            "target_worker": str,
            "match_score": float,
            "result": Any,
            "error": str | None,
            "duration_ms": float,
            "alternatives": [...]  # 备选角色
        }
    """
    start = time.time()

    # Step 1: 匹配最佳 SwarmRole
    matches = _match_swarm_roles(task_description)
    if not matches:
        error_msg = f"未找到匹配的Swarm角色: {task_description[:80]}"
        logger.warning("[SwarmBridge] %s", error_msg)
        if publish_events:
            _publish_swarm_event("swarm_dispatch_failed", {
                "task": task_description[:200],
                "error": error_msg,
            })
        return {
            "success": False,
            "matched_role": "",
            "target_worker": "",
            "match_score": 0.0,
            "result": None,
            "error": error_msg,
            "duration_ms": (time.time() - start) * 1000,
            "alternatives": [],
        }

    best_match, score = matches[0]
    alternatives = [{"name": m.name, "role_key": m.role_key, "score": s}
                    for m, s in matches[1:4]]

    logger.info("[SwarmBridge] 匹配角色: %s (score=%.2f) → %s",
                best_match.name, score, best_match.target_worker)

    # Step 2: Handoff 路由
    from molib.agencies.handoff import HandoffManager, HandoffInputData

    hd_input = HandoffInputData(
        input_history=task_description,
        task_payload=input_data or {"task": task_description},
    )

    try:
        result, record = HandoffManager.route(
            task_type=best_match.role_key,
            input_data=hd_input,
            source_worker="swarm_bridge",
        )

        duration = (time.time() - start) * 1000
        success = not (hasattr(result, 'code') and hasattr(result, 'message'))

        if success and publish_events:
            _publish_swarm_event("swarm_task_completed", {
                "task": task_description[:200],
                "role": best_match.name,
                "role_key": best_match.role_key,
                "target_worker": best_match.target_worker,
                "match_score": round(score, 2),
                "duration_ms": round(duration, 1),
            })

        if not success and publish_events:
            _publish_swarm_event("swarm_task_failed", {
                "task": task_description[:200],
                "role": best_match.name,
                "error": str(getattr(result, 'message', str(result)))[:500],
                "match_score": round(score, 2),
            })

        return {
            "success": success,
            "matched_role": best_match.name,
            "target_worker": best_match.target_worker,
            "match_score": round(score, 2),
            "result": _safe_result(result),
            "error": None if success else str(getattr(result, 'message', str(result))),
            "duration_ms": round(duration, 1),
            "alternatives": alternatives,
        }

    except Exception as e:
        duration = (time.time() - start) * 1000
        logger.error("[SwarmBridge] 调度异常: %s", e)
        if publish_events:
            _publish_swarm_event("swarm_dispatch_error", {
                "task": task_description[:200],
                "role": best_match.name,
                "error": str(e),
            })
        return {
            "success": False,
            "matched_role": best_match.name,
            "target_worker": best_match.target_worker,
            "match_score": round(score, 2),
            "result": None,
            "error": str(e),
            "duration_ms": round(duration, 1),
            "alternatives": alternatives,
        }


def _match_swarm_roles(task: str) -> list[tuple[SwarmRole, float]]:
    """关键词匹配：找到最匹配的 SwarmRole 列表"""
    task_lower = task.lower()
    scored: list[tuple[SwarmRole, float]] = []

    for role in SWARM_ROLES:
        score = 0.0
        weights = 0.0

        # 能力标签匹配
        for cap in role.capabilities:
            cap_lower = cap.lower()
            if cap_lower in task_lower:
                score += 1.5  # 精确匹配
            else:
                # 部分词匹配
                for word in cap_lower.split():
                    if len(word) > 1 and word in task_lower:
                        score += 0.6
                        break
            weights += 1.0

        # 角色名匹配
        if role.name in task_lower:
            score += 2.0
        weights += 1.0

        # 子公司名匹配
        if role.target_worker_name and role.target_worker_name in task_lower:
            score += 1.5
        weights += 1.0

        # 角色键匹配
        if role.role_key.replace('_', ' ') in task_lower:
            score += 1.0
        weights += 0.5

        # 分类匹配
        if role.category in task_lower:
            score += 0.5
        weights += 0.5

        # 优先级加成
        score += role.priority * 0.05
        weights += 0.5

        normalized = score / max(weights, 1.0)
        if normalized > 0.1:
            scored.append((role, normalized))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:5]


def _publish_swarm_event(event_type: str, payload: dict) -> None:
    """发布 Swarm 事件到 FileEventBus"""
    try:
        from .event_bus import FileEventBus
        bus = FileEventBus()
        bus.set_source("swarm_bridge")
        bus.publish(event_type, source="swarm_bridge", payload=payload)
    except Exception as e:
        logger.debug("[SwarmBridge] 事件发布失败: %s", e)


def _safe_result(result: Any) -> Any:
    """安全提取结果内容"""
    try:
        if hasattr(result, 'to_dict'):
            return result.to_dict()
        if hasattr(result, 'output'):
            return str(result.output)[:500]
        return str(result)[:500] if result is not None else None
    except Exception:
        return str(result)[:500] if result else None


# ═══════════════════════════════════════════════════════════════════
# 辅助查询
# ═══════════════════════════════════════════════════════════════════

def list_swarm_roles(category: str | None = None) -> list[dict]:
    """列出所有 Swarm 角色（可按分类过滤）"""
    roles = SWARM_ROLES
    if category:
        roles = [r for r in roles if r.category == category]
    return [r.to_dict() for r in sorted(roles, key=lambda r: r.priority, reverse=True)]


def get_swarm_roles_by_worker(worker_id: str) -> list[dict]:
    """获取指定 Worker 的所有 Swarm 角色"""
    roles = [r for r in SWARM_ROLES if r.target_worker == worker_id]
    return [r.to_dict() for r in sorted(roles, key=lambda r: r.priority, reverse=True)]


def get_swarm_categories() -> list[str]:
    """获取所有 Swarm 角色分类"""
    return sorted(set(r.category for r in SWARM_ROLES))


__all__ = [
    "SWARM_ROLES",
    "SwarmRole",
    "register_swarm_handoff",
    "swarm_dispatch",
    "list_swarm_roles",
    "get_swarm_roles_by_worker",
    "get_swarm_categories",
]
