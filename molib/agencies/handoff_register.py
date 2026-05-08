"""
Handoff 注册中心 — 为所有16家注册了Worker的子公司注册handoff

每个注册包含：
- tool_name: LLM可调用的工具名（如 "transfer_to_content_writer"）
- tool_description: 描述（LLM自动匹配用）
- target_worker: WorkerRegistry中的ID
- is_enabled: 运行时启用/禁用控制

使用方式：
    from molib.agencies.handoff_register import register_all_handoffs
    register_all_handoffs()
    
然后：
    from molib.agencies.handoff import HandoffManager
    result = HandoffManager.route("内容创作", input_data)
"""

from molib.agencies.handoff import create_handoff


def register_all_handoffs():
    """注册所有子公司的 handoff，清空已有的重注册"""
    from molib.agencies.handoff import HandoffManager
    
    # 清空已有注册（允许重新注册，但create_handoff会去重）
    # 不改私有属性，依赖去重逻辑
    
    # ═══════════════════════════════════════════
    # VP营销（5家）
    # ═══════════════════════════════════════════

    create_handoff(
        target_worker="content_writer",
        target_worker_name="墨笔文创",
        tool_name_override="transfer_to_content_writer",
        tool_description_override="内容创作：文字创作、文案、公众号文章、博客、小红书笔记写作"
    )

    create_handoff(
        target_worker="ip_manager",
        target_worker_name="墨韵IP",
        tool_name_override="transfer_to_ip_manager",
        tool_description_override="IP管理：品牌视觉规范、IP衍生设计、商标保护、版权管理"
    )

    create_handoff(
        target_worker="designer",
        target_worker_name="墨图设计",
        tool_name_override="transfer_to_designer",
        tool_description_override="视觉设计：图片生成、封面设计、UI设计、生图提示词、品牌视觉"
    )

    create_handoff(
        target_worker="short_video",
        target_worker_name="墨播短视频",
        tool_name_override="transfer_to_short_video",
        tool_description_override="短视频：脚本生成、视频内容创作、抖音/视频号脚本"
    )

    create_handoff(
        target_worker="voice_actor",
        target_worker_name="墨声配音",
        tool_name_override="transfer_to_voice_actor",
        tool_description_override="音频制作：TTS语音合成、播客制作、配音、音频编辑"
    )

    # ═══════════════════════════════════════════
    # VP运营（4家）
    # ═══════════════════════════════════════════

    create_handoff(
        target_worker="crm",
        target_worker_name="墨域私域",
        tool_name_override="transfer_to_crm",
        tool_description_override="私域运营：CRM管理、用户分层、社群运营、触达序列、复购体系"
    )

    create_handoff(
        target_worker="customer_service",
        target_worker_name="墨声客服",
        tool_name_override="transfer_to_customer_service",
        tool_description_override="智能客服：闲鱼消息自动回复、客服QA、工单处理、满意度追踪"
    )

    create_handoff(
        target_worker="ecommerce",
        target_worker_name="墨链电商",
        tool_name_override="transfer_to_ecommerce",
        tool_description_override="电商管理：订单处理、交易管理、电商平台上架、物流追踪"
    )

    create_handoff(
        target_worker="education",
        target_worker_name="墨学教育",
        tool_name_override="transfer_to_education",
        tool_description_override="教育与学习：课程设计、学习路径规划、辅导系统、教程制作"
    )

    # ═══════════════════════════════════════════
    # VP技术（4家）
    # ═══════════════════════════════════════════

    create_handoff(
        target_worker="developer",
        target_worker_name="墨码开发",
        tool_name_override="transfer_to_developer",
        tool_description_override="软件开发：代码编写、技术实现、CLI工具开发、API开发"
    )

    create_handoff(
        target_worker="ops",
        target_worker_name="墨维运维",
        tool_name_override="transfer_to_ops",
        tool_description_override="系统运维：服务器部署、DevOps、环境配置、监控维护"
    )

    create_handoff(
        target_worker="security",
        target_worker_name="墨安安全",
        tool_name_override="transfer_to_security",
        tool_description_override="安全审计：代码审计、安全评估、合规检查、漏洞扫描"
    )

    create_handoff(
        target_worker="auto_dream",
        target_worker_name="墨梦AutoDream",
        tool_name_override="transfer_to_auto_dream",
        tool_description_override="AI自动化实验：快速原型开发、记忆蒸馏、自学习闭环、自动化实验"
    )

    # ═══════════════════════════════════════════
    # VP财务（1家，交易已作为独立Worker）
    # ═══════════════════════════════════════════

    create_handoff(
        target_worker="finance",
        target_worker_name="墨算财务",
        tool_name_override="transfer_to_finance",
        tool_description_override="财务管理：记账、预算控制、成本分析、财务报表"
    )

    # ═══════════════════════════════════════════
    # VP战略（3家）
    # ═══════════════════════════════════════════

    create_handoff(
        target_worker="bd",
        target_worker_name="墨商BD",
        tool_name_override="transfer_to_bd",
        tool_description_override="商务拓展：商务合作、变现策略评估、合作洽谈、渠道拓展"
    )

    create_handoff(
        target_worker="global_marketing",
        target_worker_name="墨海出海",
        tool_name_override="transfer_to_global_marketing",
        tool_description_override="出海运营：多语言本地化、繁体转换、海外社媒、跨境合规"
    )

    create_handoff(
        target_worker="research",
        target_worker_name="墨研竞情",
        tool_name_override="transfer_to_research",
        tool_description_override="情报研究：趋势分析、竞品研究、情报扫描、行业研究"
    )

    # ═══════════════════════════════════════════
    # 共同服务（3家）
    # ═══════════════════════════════════════════

    create_handoff(
        target_worker="legal",
        target_worker_name="墨律法务",
        tool_name_override="transfer_to_legal",
        tool_description_override="法务合规：合同审查、风险评估、隐私合规、NDA生成"
    )

    create_handoff(
        target_worker="knowledge",
        target_worker_name="墨脑知识",
        tool_name_override="transfer_to_knowledge",
        tool_description_override="知识管理：RAG检索、长期记忆、知识图谱、文档管理"
    )

    create_handoff(
        target_worker="data_analyst",
        target_worker_name="墨测数据",
        tool_name_override="transfer_to_data_analyst",
        tool_description_override="数据分析：数据统计、BI报表、测试质量、效果追踪"
    )

    # ═══════════════════════════════════════════
    # 交易（新增）
    # ═══════════════════════════════════════════

    create_handoff(
        target_worker="trading",
        target_worker_name="墨投交易",
        tool_name_override="transfer_to_trading",
        tool_description_override="量化交易：市场分析、策略回测、交易信号生成、研究报告"
    )

    print(f"[Handoff] 已注册 {len(HandoffManager._handoffs)} 个 Worker 的 handoff")


if __name__ == "__main__":
    register_all_handoffs()
    from molib.agencies.handoff import HandoffManager
    manifest = HandoffManager.get_manifest()
    print(f"\n注册清单 ({len(manifest)} 个 handoff):")
    for m in manifest:
        print(f"  🔄 {m['tool_name']:<35s} → {m['target_worker_name']:<10s} [{'✅' if m['enabled'] else '❌'}]")
