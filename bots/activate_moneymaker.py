#!/usr/bin/env python3
"""
moneymaker-turbo 激活脚本 — 变现策略技能
==========================================
提供业务变现评估、定价生成、收入流分析能力。

核心功能：
  - evaluate_business_idea(idea): 评估一个业务创意的变现潜力
  - generate_pricing(service_type, cost): 为服务或产品生成定价方案
  - assess_revenue_stream(channel): 分析特定收入渠道的变现路径

对应技能：~/.hermes/skills/moneymaker-turbo/SKILL.md
对应子公司：墨商BD（商务拓展、合作洽谈、变现策略）

依赖：纯 Python / subprocess / curl（无额外第三方包）
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional


# ═══════════════════════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════════════════════

def _call_llm(prompt: str, system_prompt: str = None,
              temperature: float = 0.3) -> str:
    """
    调用 LLM 进行分析（通过 OpenRouter API）。

    使用环境变量 OPENROUTER_API_KEY 或 OPENAI_API_KEY。

    Args:
        prompt: 用户提示
        system_prompt: 系统提示（可选）
        temperature: 创造力参数

    Returns:
        LLM 返回的文本
    """
    api_key = (os.environ.get("OPENROUTER_API_KEY")
               or os.environ.get("OPENAI_API_KEY"))
    api_base = os.environ.get("OPENROUTER_BASE_URL",
                               "https://openrouter.ai/api/v1")
    model = os.environ.get("LLM_MODEL", "deepseek/deepseek-chat")

    if not api_key:
        return "[LLM不可用 — 未配置 OPENROUTER_API_KEY。使用内置规则评估。]"

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload = json.dumps({
        "model": model,
        "messages": messages,
        "max_tokens": 2048,
        "temperature": temperature,
    }).encode("utf-8")

    try:
        import urllib.request
        req = urllib.request.Request(
            f"{api_base}/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://hermes-os.local",
                "X-Title": "moneymaker-turbo",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]
            return f"[LLM返回异常: {data}]"
    except ImportError:
        # Fallback: try requests
        try:
            import requests
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://hermes-os.local",
                "X-Title": "moneymaker-turbo",
            }
            resp = requests.post(
                f"{api_base}/chat/completions",
                headers=headers,
                json={"model": model, "messages": messages,
                       "max_tokens": 2048, "temperature": temperature},
                timeout=60,
            )
            if resp.status_code == 200:
                data = resp.json()
                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"]
            return f"[LLM API错误: HTTP {resp.status_code}]"
        except Exception as e:
            return f"[LLM调用失败: {e}]"
    except Exception as e:
        return f"[LLM调用失败: {e}]"


# ═══════════════════════════════════════════════════════════════════
# 核心功能 1: evaluate_business_idea — 评估业务创意的变现潜力
# ═══════════════════════════════════════════════════════════════════

def evaluate_business_idea(idea: str,
                           market: str = "中国",
                           target_audience: str = "") -> dict:
    """
    评估一个业务创意的变现潜力。

    Args:
        idea: 业务创意描述
        market: 目标市场（默认：中国）
        target_audience: 目标用户群体（可选）

    Returns:
        dict: {
            "status": "ok" | "error",
            "idea": str,
            "monetization_score": float,  # 0-100
            "revenue_potential": str,     # 高/中/低
            "time_to_revenue": str,       # 预计变现时间
            "channels": [...],            # 建议变现渠道
            "risks": [...],
            "actionable_steps": [...],
            "llm_analysis": str           # LLM详细分析
        }
    """
    if not idea or not idea.strip():
        return {"status": "error", "idea": idea,
                "message": "业务创意描述不能为空"}

    idea = idea.strip()
    result = {
        "status": "ok",
        "idea": idea,
        "monetization_score": 0,
        "revenue_potential": "",
        "time_to_revenue": "",
        "channels": [],
        "risks": [],
        "actionable_steps": [],
        "llm_analysis": "",
    }

    # ── 尝试 LLM 分析 ──────────────────────────────────────────────
    system_prompt = """你是一位资深商业变现策略分析师，精通一人公司的变现路径设计。
你的分析需要：
1. 务实 — 给出可操作的真实建议
2. 数据驱动 — 基于真实市场情况
3. 关注现金流 — 什么能最快变现
4. 结构化输出

请用中文回复，输出格式为JSON：
{
    "monetization_score": 0-100的整数评分,
    "revenue_potential": "高/中/低",
    "time_to_revenue": "1周内/1个月内/3个月内/6个月内/1年以上",
    "channels": ["渠道1", "渠道2"],
    "risks": ["风险1", "风险2"],
    "actionable_steps": ["步骤1", "步骤2"]
}"""

    prompt = f"""业务创意：{idea}
目标市场：{market}
目标用户：{target_audience if target_audience else '尚未明确'}

请评估该创意的变现潜力。"""

    llm_output = _call_llm(prompt, system_prompt, temperature=0.4)

    if llm_output.startswith("["):
        # LLM不可用，使用内置规则评估
        result["llm_analysis"] = llm_output
        result["monetization_score"] = _rule_based_evaluation(idea)
        result["revenue_potential"] = "待评估"
        result["time_to_revenue"] = "需进一步分析"
        result["channels"] = _suggest_channels(idea)
        result["risks"] = ["LLM不可用，建议配置API Key获取详细分析"]
        result["actionable_steps"] = [
            "1. 验证市场需求",
            "2. 分析竞争对手",
            "3. 设计最小可行产品",
            "4. 测试变现渠道",
        ]
    else:
        result["llm_analysis"] = llm_output
        # 尝试从LLM输出中解析JSON
        try:
            # Find JSON in response
            start = llm_output.find("{")
            end = llm_output.rfind("}") + 1
            if start >= 0 and end > start:
                parsed = json.loads(llm_output[start:end])
                result.update(parsed)
        except (json.JSONDecodeError, ValueError):
            # 无法解析，保留原始输出
            pass

    return result


def _rule_based_evaluation(idea: str) -> int:
    """基于规则的关键词评分（LLM不可用时的备用方案）。"""
    score = 50  # baseline
    idea_lower = idea.lower()

    # 加分项
    boosters = {
        "ai": 10, "saas": 15, "订阅": 15, "订阅制": 15,
        "课程": 10, "培训": 10, "咨询": 8, "付费": 10,
        "电商": 10, "自媒体": 8, "内容": 8, "工具": 10,
        "变现": 15, "转化": 10, "自动化": 8,
        "知识付费": 12, "会员": 10, "佣金": 10,
    }
    # 减分项
    penalties = {
        "硬件": -10, "实体": -8, "线下": -5,
        "开店": -10, "库存": -8, "加盟": -10,
    }

    for word, points in boosters.items():
        if word in idea:
            score += points

    for word, points in penalties.items():
        if word in idea:
            score += points

    return max(0, min(100, score))


def _suggest_channels(idea: str) -> list:
    """基于关键词建议变现渠道。"""
    channels = []
    idea_lower = idea.lower()

    if any(w in idea for w in ["课程", "培训", "教育", "知识"]):
        channels.append("知识付费平台（小鹅通/知识星球）")
    if any(w in idea for w in ["内容", "自媒体", "公众号", "小红书"]):
        channels.append("内容变现（广告/带货/付费内容）")
    if any(w in idea for w in ["工具", "saas", "软件", "app"]):
        channels.append("SaaS订阅/工具付费")
    if any(w in idea for w in ["咨询", "顾问", "服务"]):
        channels.append("咨询服务/项目制收费")
    if any(w in idea for w in ["电商", "带货", "商品"]):
        channels.append("电商平台/直播带货")
    if any(w in idea for w in ["ai", "人工智能", "llm"]):
        channels.append("AI API服务/AI Agent解决方案")

    if not channels:
        channels = [
            "内容变现（公众号/小红书/抖音）",
            "咨询服务",
            "知识付费产品",
            "SaaS工具订阅",
        ]

    return channels


# ═══════════════════════════════════════════════════════════════════
# 核心功能 2: generate_pricing — 定价方案生成
# ═══════════════════════════════════════════════════════════════════

def generate_pricing(service_type: str, cost: float = 0.0,
                     competitors: list = None) -> dict:
    """
    为服务或产品生成定价方案。

    Args:
        service_type: 服务类型
            - "consulting": 咨询服务
            - "course": 课程/知识付费
            - "saas": SaaS订阅
            - "content": 内容创作
            - "custom": 定制服务
        cost: 成本（人民币元），用于基于成本的定价
        competitors: 竞争对手定价列表（可选）

    Returns:
        dict: {
            "status": "ok" | "error",
            "service_type": str,
            "pricing_tiers": [...],       # 定价档位
            "recommended_price": float,   # 推荐价格
            "profit_margin": float,       # 利润率
            "break_even_units": int,      # 盈亏平衡点
            "strategies": [...]           # 定价策略建议
        }
    """
    valid_types = ["consulting", "course", "saas", "content", "custom"]
    if service_type not in valid_types:
        return {"status": "error", "service_type": service_type,
                "message": f"无效的服务类型。可选: {', '.join(valid_types)}"}

    if competitors is None:
        competitors = []

    result = {
        "status": "ok",
        "service_type": service_type,
        "pricing_tiers": [],
        "recommended_price": 0.0,
        "profit_margin": 0.0,
        "break_even_units": 0,
        "strategies": [],
    }

    # ── 定价模板 ────────────────────────────────────────────────────
    pricing_templates = {
        "consulting": {
            "tiers": [
                {"name": "基础咨询", "price": 299, "description": "1小时线上咨询"},
                {"name": "深度咨询", "price": 999, "description": "3小时深度分析+方案"},
                {"name": "VIP陪跑", "price": 4999, "description": "月度顾问服务"},
            ],
            "strategies": [
                "按小时定价 → 按价值定价",
                "首次咨询优惠以建立信任",
                "套餐制提高客单价",
            ],
        },
        "course": {
            "tiers": [
                {"name": "单课", "price": 99, "description": "单个课程"},
                {"name": "系列课", "price": 399, "description": "全系列课程"},
                {"name": "训练营", "price": 1999, "description": "带辅导的训练营"},
            ],
            "strategies": [
                "阶梯定价：基础免费/高级付费",
                "早鸟价 + 正常价 + 涨价",
                "捆绑销售提高感知价值",
            ],
        },
        "saas": {
            "tiers": [
                {"name": "免费版", "price": 0, "description": "基础功能免费"},
                {"name": "专业版", "price": 99, "description": "月付，高级功能"},
                {"name": "企业版", "price": 499, "description": "月付，企业定制"},
            ],
            "strategies": [
                "Freemium转化漏斗",
                "按用量/按席位定价",
                "年付折扣（年付=月付×10）",
            ],
        },
        "content": {
            "tiers": [
                {"name": "单篇", "price": 50, "description": "单篇内容创作"},
                {"name": "月套餐", "price": 500, "description": "月更10篇"},
                {"name": "全案", "price": 2999, "description": "月度全案运营"},
            ],
            "strategies": [
                "按篇定价 → 套餐制",
                "内容+分发打包服务",
                "效果分成模式",
            ],
        },
        "custom": {
            "tiers": [
                {"name": "基础定制", "price": 999, "description": "标准定制服务"},
                {"name": "高级定制", "price": 4999, "description": "深度定制服务"},
                {"name": "企业定制", "price": 19999, "description": "企业级解决方案"},
            ],
            "strategies": [
                "项目制报价 + 里程碑付款",
                "基于ROI的价值定价",
                "可分阶段交付降低门槛",
            ],
        },
    }

    template = pricing_templates[service_type]
    result["pricing_tiers"] = template["tiers"]
    result["strategies"] = template["strategies"]

    # ── 基于成本计算推荐价格和利润 ──────────────────────────────────
    if cost > 0:
        # 基础定价：成本 × 3（标准服务业利润率）
        base_price = cost * 3
        # 调整到最近的档次
        tiers = template["tiers"]
        if tiers:
            # 找第一个价格超过 base_price 的档位
            recommended = tiers[0]
            for t in tiers:
                if t["price"] >= base_price:
                    recommended = t
                    break
            # 如果没有超过的，使用最高档
            result["recommended_price"] = recommended["price"]
        else:
            result["recommended_price"] = round(base_price, -1)

        result["profit_margin"] = round(
            (result["recommended_price"] - cost) / result["recommended_price"] * 100, 1
        )
        if result["recommended_price"] > 0:
            result["break_even_units"] = max(1, int(cost / (result["recommended_price"] - cost)) + 1)
    else:
        # 无成本数据，直接推荐中间档
        tiers = template["tiers"]
        if tiers:
            mid = len(tiers) // 2
            result["recommended_price"] = tiers[mid]["price"]

    # ── 竞争对手感知 ───────────────────────────────────────────────
    if competitors:
        avg_comp = sum(competitors) / len(competitors)
        result["competitor_avg"] = avg_comp
        if result["recommended_price"] < avg_comp:
            result["strategies"].append("渗透定价：低于竞品均价的差异化策略")
        elif result["recommended_price"] > avg_comp:
            result["strategies"].append("溢价定价：高于竞品，强调差异化价值")

    return result


# ═══════════════════════════════════════════════════════════════════
# 核心功能 3: assess_revenue_stream — 收入渠道评估
# ═══════════════════════════════════════════════════════════════════

def assess_revenue_stream(channel: str) -> dict:
    """
    分析特定收入渠道的变现路径和潜力。

    Args:
        channel: 收入渠道名称
            - "content": 内容变现（公众号/小红书/抖音）
            - "consulting": 咨询服务
            - "saas": SaaS/工具订阅
            - "course": 课程/知识付费
            - "ecommerce": 电商/带货
            - "affiliate": 联盟营销/佣金
            - "agency": 代运营/服务
            - "custom": 其他

    Returns:
        dict: {
            "status": "ok" | "error",
            "channel": str,
            "upside": str,              # 天花板
            "time_investment": str,     # 时间投入
            "difficulty": str,          # 难度
            "monthly_potential": str,   # 月收入潜力
            "entry_barrier": str,       # 入行门槛
            "scalability": str,         # 可扩展性
            "pathway": [...],           # 变现路径步骤
            "tips": [...]               # 实操建议
        }
    """
    valid_channels = ["content", "consulting", "saas", "course",
                      "ecommerce", "affiliate", "agency", "custom"]

    if channel not in valid_channels:
        return {"status": "error", "channel": channel,
                "message": f"无效的渠道。可选: {', '.join(valid_channels)}"}

    # ── 渠道评估数据库 ──────────────────────────────────────────────
    channel_data = {
        "content": {
            "name": "内容变现",
            "upside": "高（头部博主月入10万+）",
            "time_investment": "高（每日4-6小时）",
            "difficulty": "中",
            "monthly_potential": "¥1,000 - ¥100,000+",
            "entry_barrier": "低（只需一部手机）",
            "scalability": "中（受限于个人精力）",
            "pathway": [
                "选择平台（公众号/小红书/抖音/B站）",
                "垂直领域定位",
                "持续输出优质内容（至少3个月）",
                "积累粉丝到1万+启动变现",
                "广告/带货/付费内容/咨询服务",
            ],
            "tips": [
                "先做内容后想变现，粉丝信任是基础",
                "垂直比泛流量更值钱",
                "注意平台规则，避免违规限流",
                "多平台分发降低风险",
                "尽快建立私域（微信社群/朋友圈）",
            ],
        },
        "consulting": {
            "name": "咨询服务",
            "upside": "中（时薪制天花板）",
            "time_investment": "中（按项目执行）",
            "difficulty": "中",
            "monthly_potential": "¥5,000 - ¥50,000",
            "entry_barrier": "中（需要专业能力背书）",
            "scalability": "低（个人时间有限）",
            "pathway": [
                "梳理个人专业能力和案例",
                "明确服务范围和定价",
                "建立获客渠道（内容/圈子/平台）",
                "提供首次优惠咨询积累案例",
                "沉淀方法论→可复制的产品",
            ],
            "tips": [
                "从免费咨询开始积累案例",
                "客户见证是最好的销售素材",
                "按价值定价而非按时间定价",
                "把咨询经验沉淀为课程/产品",
            ],
        },
        "saas": {
            "name": "SaaS/工具订阅",
            "upside": "极高（互联网规模效应）",
            "time_investment": "极高（产品开发迭代）",
            "difficulty": "高",
            "monthly_potential": "¥0 - ¥1,000,000+",
            "entry_barrier": "高（开发能力+运营能力）",
            "scalability": "极高（边际成本趋零）",
            "pathway": [
                "发现细分市场痛点",
                "开发MVP最小可行产品",
                "找种子用户免费试用",
                "根据反馈迭代产品",
                "制定定价策略，启动付费",
            ],
            "tips": [
                "先验证需求再做产品",
                "从工具切入积累用户",
                "注意获客成本（CAC）与用户生命周期价值（LTV）",
                "尽早收费验证付费意愿",
            ],
        },
        "course": {
            "name": "课程/知识付费",
            "upside": "中高（可规模化复制）",
            "time_investment": "高（前期课程开发）",
            "difficulty": "中",
            "monthly_potential": "¥3,000 - ¥50,000",
            "entry_barrier": "低（有知识即可）",
            "scalability": "高（一次录制多次销售）",
            "pathway": [
                "确定课程主题和目标学员",
                "设计课程大纲和学习路径",
                "录制/制作课程内容",
                "上架平台（小鹅通/知识星球/腾讯课堂）",
                "持续运营和迭代",
            ],
            "tips": [
                "先通过免费内容建立信任",
                "课程+社群+答疑组合提高客单价",
                "热点话题是快速起量的捷径",
                "关注完课率而非仅销量",
            ],
        },
        "ecommerce": {
            "name": "电商/带货",
            "upside": "高",
            "time_investment": "高",
            "difficulty": "中高",
            "monthly_potential": "¥2,000 - ¥100,000+",
            "entry_barrier": "中（供应链/流量）",
            "scalability": "中",
            "pathway": [
                "选择品类并搭建供应链",
                "选择平台（淘宝/拼多多/抖音电商）",
                "准备货源（一件代发/自营/代理）",
                "获取流量（内容/投流/直播）",
                "优化转化率和复购率",
            ],
            "tips": [
                "轻资产起步，避免囤货",
                "选品比运营更重要",
                "私域复购是利润核心",
            ],
        },
        "affiliate": {
            "name": "联盟营销/佣金",
            "upside": "中",
            "time_investment": "低（被动收入）",
            "difficulty": "低",
            "monthly_potential": "¥500 - ¥20,000",
            "entry_barrier": "极低（注册即可）",
            "scalability": "高",
            "pathway": [
                "加入联盟平台（淘宝客/京东联盟/好省）",
                "选择高佣金产品",
                "建立推广渠道（社群/内容/网站）",
                "生成推广链接",
                "持续优化转化率",
            ],
            "tips": [
                "选择与自己受众匹配的产品",
                "内容推荐而非硬广",
                "跟紧平台活动获得额外佣金",
            ],
        },
        "agency": {
            "name": "代运营/服务",
            "upside": "中高",
            "time_investment": "高",
            "difficulty": "中",
            "monthly_potential": "¥5,000 - ¥50,000",
            "entry_barrier": "中（需要案例）",
            "scalability": "中",
            "pathway": [
                "确定代运营领域（社媒/电商/内容）",
                "打造标杆案例",
                "制定服务套餐",
                "通过内容获客",
                "组建团队实现规模化",
            ],
            "tips": [
                "先免费帮一个客户做起来",
                "标准化SOP降低交付成本",
                "从代运营转型为培训/课程",
            ],
        },
        "custom": {
            "name": "其他变现渠道",
            "upside": "视具体情况",
            "time_investment": "视具体情况",
            "difficulty": "视具体情况",
            "monthly_potential": "视具体情况",
            "entry_barrier": "视具体情况",
            "scalability": "视具体情况",
            "pathway": [
                "明确你的核心能力和资源",
                "找到愿意付费的目标用户",
                "设计最小可行服务/产品",
                "测试变现",
                "放大成功模式",
            ],
            "tips": [
                "优先选择ROI最高的路径",
                "主动测试多个渠道",
                "跟踪数据，淘汰低效渠道",
            ],
        },
    }

    data = channel_data[channel]
    result = {
        "status": "ok",
        "channel": data["name"],
        "upside": data["upside"],
        "time_investment": data["time_investment"],
        "difficulty": data["difficulty"],
        "monthly_potential": data["monthly_potential"],
        "entry_barrier": data["entry_barrier"],
        "scalability": data["scalability"],
        "pathway": data["pathway"],
        "tips": data["tips"],
    }

    return result


# ═══════════════════════════════════════════════════════════════════
# 自检
# ═══════════════════════════════════════════════════════════════════

def self_check() -> dict:
    """
    运行环境自检，报告 moneymaker-turbo 功能可用性。

    Returns:
        dict: 各功能检查结果
    """
    result = {
        "environment": {},
        "core_functions": {},
    }

    # 检查依赖
    for tool in ["curl", "python3"]:
        try:
            subprocess.run(["which", tool], capture_output=True, timeout=3, check=True)
            result["environment"][tool] = True
        except Exception:
            result["environment"][tool] = False

    # 检查API Key
    api_key = (os.environ.get("OPENROUTER_API_KEY")
               or os.environ.get("OPENAI_API_KEY"))
    result["environment"]["llm_api_key"] = bool(api_key)

    # 测试 evaluate_business_idea
    eval_result = evaluate_business_idea("AI写作工具SaaS订阅", market="中国")
    result["core_functions"]["evaluate_business_idea"] = eval_result["status"] == "ok"

    # 测试 generate_pricing
    pricing_result = generate_pricing("saas", cost=500)
    result["core_functions"]["generate_pricing"] = pricing_result["status"] == "ok"

    # 测试 assess_revenue_stream
    stream_result = assess_revenue_stream("content")
    result["core_functions"]["assess_revenue_stream"] = stream_result["status"] == "ok"

    return result


# ═══════════════════════════════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("moneymaker-turbo 激活脚本 · 自检报告")
    print("=" * 60)

    check = self_check()

    print("\n  📊 环境:")
    print(f"    ✓ curl: {check['environment'].get('curl', False)}")
    print(f"    ✓ python3: {check['environment'].get('python3', False)}")
    print(f"    {'✓' if check['environment']['llm_api_key'] else '✗'} LLM API Key: "
          f"{'已配置' if check['environment']['llm_api_key'] else '未配置（使用规则评估）'}")

    print("\n  🔧 核心功能:")
    for func, ok in check["core_functions"].items():
        icon = "✓" if ok else "✗"
        print(f"    {icon} {func}")

    print()
    print("-" * 60)
    print("测试: evaluate_business_idea()")
    idea = "AI写作工具SaaS订阅"
    eval_result = evaluate_business_idea(idea)
    print(f"  创意: {idea}")
    print(f"  评分: {eval_result.get('monetization_score', 'N/A')}/100")
    print(f"  推荐渠道: {eval_result.get('channels', [])}")
    print(f"  风险: {eval_result.get('risks', [])}")

    print()
    print("-" * 60)
    print("测试: generate_pricing()")
    pricing = generate_pricing("saas", cost=500)
    print(f"  推荐价格: ¥{pricing['recommended_price']}")
    print(f"  利润率: {pricing.get('profit_margin', 'N/A')}%")
    print(f"  盈亏平衡: {pricing.get('break_even_units', 'N/A')} 单")

    print()
    print("-" * 60)
    print("测试: assess_revenue_stream()")
    stream = assess_revenue_stream("content")
    print(f"  渠道: {stream['channel']}")
    print(f"  难度: {stream['difficulty']}")
    print(f"  月收入潜力: {stream['monthly_potential']}")
    print(f"  可扩展性: {stream['scalability']}")

    print()
    print("=" * 60)
    print("moneymaker-turbo 激活完成 ✓")
    print("每次新业务规划时自动加载moneymaker-turbo评估变现路径")
    print("=" * 60)
