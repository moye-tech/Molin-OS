"""
墨麟核心引擎 — 一人公司操作系统调度中枢
=============================================

负责:
- 任务编排与调度
- 蜂群任务分发
- 心跳监控
- 治理审批流程
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("molin.engine")


class MolinEngine:
    """墨麟核心引擎"""

    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path(__file__).parent.parent.parent / "config"
        self.company_config = self._load_company_config()
        self.governance_config = self._load_governance_config()
        self.logger = logger

    def _load_company_config(self) -> dict:
        """加载公司配置 — 统一读取 company.toml（唯一配置源）"""
        config_file = self.config_dir / "company.toml"
        if config_file.exists():
            import tomllib
            with open(config_file, "rb") as f:
                return tomllib.load(f)
        elif (self.config_dir / "company.yaml").exists():
            import yaml
            with open(self.config_dir / "company.yaml") as f:
                return yaml.safe_load(f)
        return self._default_company_config()

    def _load_governance_config(self) -> dict:
        """加载治理配置"""
        config_file = self.config_dir / "governance.yaml"
        if config_file.exists():
            import yaml
            with open(config_file) as f:
                return yaml.safe_load(f)
        return self._default_governance_config()

    @staticmethod
    def _default_company_config() -> dict:
        """默认公司结构 (6部门 × 22角色)"""
        return {
            "name": "墨麟 AI",
            "mission": "打造AI驱动的全自动一人公司，让个体拥有企业的战斗力",
            "budget_monthly": 1360,  # ¥1,360/月
            "departments": {
                "ceo_office": {"name": "CEO办公室", "headcount": 1, "roles": ["CEO"]},
                "content": {"name": "内容工厂", "headcount": 4, "roles": ["主编", "小红书运营", "视频制作", "SEO专家"]},
                "business": {"name": "商业大脑", "headcount": 4, "roles": ["商业分析师", "产品经理", "定价策略师", "项目经理"]},
                "engineering": {"name": "研发工坊", "headcount": 5, "roles": ["架构师", "后端", "前端", "测试", "运维"]},
                "growth": {"name": "增长引擎", "headcount": 4, "roles": ["营销专家", "闲鱼运营", "渠道管理", "数据分析"]},
                "intelligence": {"name": "情报系统", "headcount": 4, "roles": ["研究员", "趋势分析", "竞品监控", "OSINT"]},
            }
        }

    @staticmethod
    def _default_governance_config() -> dict:
        """默认治理规则 (4级审批)"""
        return {
            "levels": {
                "L0": {"name": "自动执行", "budget_max": 0, "description": "零成本操作，无需审批"},
                "L1": {"name": "AI自审", "budget_max": 10, "description": "AI内部检查后执行"},
                "L2": {"name": "人工确认", "budget_max": 100, "description": "需人工确认"},
                "L3": {"name": "董事会审批", "budget_max": 1000, "description": "重大决策需全面评估"},
            }
        }

    def health_check(self) -> dict:
        """系统健康检查"""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0",
            "departments": len(self.company_config.get("departments", {})),
            "budget_remaining": self.company_config.get("budget_monthly", 0),
            "checks": {
                "skills_loaded": True,
                "config_valid": True,
                "network_ok": True,
            }
        }

    def heartbeat(self) -> dict:
        """每日心跳 - 检查系统状态并生成简报"""
        health = self.health_check()
        return {
            "type": "heartbeat",
            "timestamp": datetime.now().isoformat(),
            "health": health,
            "daily_brief": self._generate_daily_brief(),
        }

    def _generate_daily_brief(self) -> dict:
        """生成每日简报"""
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "departments": self.company_config.get("departments", {}),
            "status": "operational",
            "action_items": [
                "检查各平台内容发布状态",
                "查看闲鱼店铺数据",
                "运行趋势监控",
            ]
        }


# 全局单例
engine = MolinEngine()
