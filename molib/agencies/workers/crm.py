"""墨域私域 + Twenty CRM Worker

双模式集成：
1. **Twenty CRM 模式** — 通过 REST API 操作联系人、公司、商机
2. **墨域私域模式** — 用户分层与触达序列（当 Twenty 未部署时）

用法（Hermes terminal）：
    # Twenty API 调用
    from molib.agencies.workers.crm import create_contact, list_contacts, create_opportunity
    
    # 墨域私域（离线）
    from molib.agencies.workers.crm import segment_users, build_touch_sequence
"""

import json
import os
import logging
from typing import Optional
from dataclasses import dataclass

import httpx

logger = logging.getLogger("molin.crm")

# ═══ Twenty CRM 配置 ═══

TWENTY_BASE_URL = os.environ.get("TWENTY_BASE_URL", "https://api.twenty.com")
TWENTY_API_KEY = os.environ.get("TWENTY_API_KEY", "")


@dataclass
class TwentyClient:
    """Twenty CRM REST API 客户端"""
    base_url: str = TWENTY_BASE_URL
    api_key: str = TWENTY_API_KEY

    @property
    def headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def is_ready(self) -> bool:
        """检查 Twenty API 是否可访问"""
        return bool(self.api_key)

    # ── 联系人 ──

    def create_contact(self, name: str, email: str = "",
                       phone: str = "", company_id: str = "",
                       **extra) -> dict:
        """创建联系人"""
        payload = {
            "name": name,
            "email": email,
            "phone": phone,
            "companyId": company_id,
            **extra,
        }
        resp = httpx.post(
            f"{self.base_url}/rest/people",
            headers=self.headers,
            json=payload,
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()

    def list_contacts(self, limit: int = 50, offset: int = 0,
                      filter_str: str = "") -> list[dict]:
        """获取联系人列表"""
        params = {"limit": limit, "offset": offset}
        if filter_str:
            params["filter"] = filter_str
        resp = httpx.get(
            f"{self.base_url}/rest/people",
            headers=self.headers,
            params=params,
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json().get("data", resp.json())

    def get_contact(self, contact_id: str) -> dict:
        """获取单个联系人"""
        resp = httpx.get(
            f"{self.base_url}/rest/people/{contact_id}",
            headers=self.headers,
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()

    def update_contact(self, contact_id: str, **fields) -> dict:
        """更新联系人"""
        resp = httpx.patch(
            f"{self.base_url}/rest/people/{contact_id}",
            headers=self.headers,
            json=fields,
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()

    def delete_contact(self, contact_id: str) -> bool:
        """删除联系人"""
        resp = httpx.delete(
            f"{self.base_url}/rest/people/{contact_id}",
            headers=self.headers,
            timeout=15,
        )
        return resp.status_code == 200

    # ── 公司 ──

    def create_company(self, name: str, domain: str = "",
                       address: str = "", **extra) -> dict:
        """创建公司"""
        payload = {"name": name, "domain": domain,
                   "address": address, **extra}
        resp = httpx.post(
            f"{self.base_url}/rest/companies",
            headers=self.headers,
            json=payload,
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()

    def list_companies(self, limit: int = 50) -> list[dict]:
        """获取公司列表"""
        resp = httpx.get(
            f"{self.base_url}/rest/companies",
            headers=self.headers,
            params={"limit": limit},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json().get("data", resp.json())

    # ── 商机 ──

    def create_opportunity(self, name: str, amount: float = 0.0,
                           stage: str = "NEW", person_id: str = "",
                           company_id: str = "", **extra) -> dict:
        """创建商机"""
        payload = {
            "name": name,
            "amount": amount,
            "stage": stage,
            "pointOfContactId": person_id,
            "companyId": company_id,
            **extra,
        }
        resp = httpx.post(
            f"{self.base_url}/rest/opportunities",
            headers=self.headers,
            json=payload,
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()

    def list_opportunities(self, limit: int = 50,
                           stage: str = "") -> list[dict]:
        """获取商机列表，可按阶段过滤"""
        params = {"limit": limit}
        if stage:
            params["filter"] = json.dumps({"stage": {"eq": stage}})
        resp = httpx.get(
            f"{self.base_url}/rest/opportunities",
            headers=self.headers,
            params=params,
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json().get("data", resp.json())

    def update_opportunity_stage(self, opportunity_id: str,
                                  stage: str) -> dict:
        """更新商机阶段"""
        return self.update_opportunity(opportunity_id, stage=stage)

    def update_opportunity(self, opportunity_id: str, **fields) -> dict:
        """更新商机"""
        resp = httpx.patch(
            f"{self.base_url}/rest/opportunities/{opportunity_id}",
            headers=self.headers,
            json=fields,
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()

    # ── 邮件/日历 (通过Twenty的API) ──

    def get_emails(self, person_id: str, limit: int = 20) -> list[dict]:
        """获取联系人的邮件记录"""
        resp = httpx.get(
            f"{self.base_url}/rest/people/{person_id}/emails",
            headers=self.headers,
            params={"limit": limit},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json().get("data", resp.json())


# ═══ 墨域私域（离线模式） ═══

# 用户分层标准
SEGMENT_LEVELS = [
    {"level": "S级（高价值）", "criteria": "消费>1000 或 高频互动",
     "action": "一对一专属服务，节日礼品"},
    {"level": "A级（活跃）", "criteria": "消费100-1000 或 周互动>3",
     "action": "定期推送，新品优先体验"},
    {"level": "B级（普通）", "criteria": "有互动记录但消费<100",
     "action": "兴趣内容推送，限时活动引导"},
    {"level": "C级（沉默）", "criteria": "30天未互动",
     "action": "召回推送，生日/节日唤醒"},
    {"level": "D级（流失）", "criteria": "90天无互动 或 明确拒绝",
     "action": "静默处理，仅重大活动通知"},
]

# 标准触达序列
TOUCH_SEQUENCES = {
    "new_lead": [
        {"day": 0, "channel": "自动欢迎", "template": "欢迎加入！送你一份新手礼包"},
        {"day": 1, "channel": "私信", "template": "了解你的需求，帮你推荐最合适的内容"},
        {"day": 3, "channel": "推送", "template": "这是我们最受欢迎的{N}篇内容"},
        {"day": 7, "channel": "私信", "template": "有遇到什么问题吗？随时问我"},
    ],
    "inactive": [
        {"day": 0, "channel": "推送", "template": "好久不见，最近有{N}个新内容"},
        {"day": 3, "channel": "私信", "template": "想你了，送你一个专属福利"},
        {"day": 7, "channel": "推送", "template": "最后一次提醒，不然就把你藏起来了 😢"},
    ],
    "high_value": [
        {"day": 0, "channel": "专属私信", "template": "你是我们的重要用户，邀请你内测新产品"},
        {"day": 3, "channel": "客服", "template": "专属客服已就位，任何问题直接找我"},
        {"day": 7, "channel": "推送", "template": "VIP专属活动预告，请查收"},
    ],
}


def segment_users(interaction_data: list[dict]) -> dict:
    """根据互动数据对用户分层"""
    segments = {l["level"]: [] for l in SEGMENT_LEVELS}
    segments["未分类"] = []
    for user in interaction_data:
        score = user.get("score", 0)
        days_since_last = user.get("days_since_last_interaction", 999)
        if score > 1000:
            segments["S级（高价值）"].append(user)
        elif score > 100:
            segments["A级（活跃）"].append(user)
        elif days_since_last < 30:
            segments["B级（普通）"].append(user)
        elif days_since_last < 90:
            segments["C级（沉默）"].append(user)
        else:
            segments["D级（流失）"].append(user)
    return {
        "segments": {k: len(v) for k, v in segments.items()},
        "total": len(interaction_data),
        "segment_details": segments,
    }


def build_touch_sequence(segment_level: str, campaign_name: str = "") -> list[dict]:
    """根据用户分层生成触达序列"""
    if "S" in segment_level:
        seq_key = "high_value"
    elif "C" in segment_level or "D" in segment_level:
        seq_key = "inactive"
    else:
        seq_key = "new_lead"
    sequence = []
    for step in TOUCH_SEQUENCES[seq_key]:
        entry = dict(step)
        if campaign_name:
            entry["template"] = entry["template"].replace(
                "{campaign}", campaign_name
            )
        sequence.append(entry)
    return sequence


# ═══ 辅助：获取 Twenty API 的健康状态 ═══

def get_twenty_status() -> dict:
    """返回 Twenty CRM 连接状态（供系统监控用）"""
    client = TwentyClient()
    if not client.is_ready():
        return {
            "status": "unconfigured",
            "message": "未配置 TWENTY_API_KEY / TWENTY_BASE_URL",
            "actions": [
                "1. 注册/登录 https://twenty.com",
                "2. Settings → API & Webhooks → 创建 Key",
                "3. 设置环境变量 TWENTY_API_KEY 和 TWENTY_BASE_URL",
            ],
        }
    try:
        companies = client.list_companies(limit=1)
        return {
            "status": "connected",
            "message": "Twenty CRM API 连接正常",
            "base_url": client.base_url,
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"连接失败: {e}",
        }
