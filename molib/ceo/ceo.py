"""
Hermes OS — CEO 决策核心
"""
import os
import yaml
from pathlib import Path

HERMES_ROOT = Path(os.path.expanduser("~/.hermes"))

class CEO:
    def __init__(self):
        self.company_config = self._load_config()
    
    def _load_config(self):
        config_path = Path(os.getcwd()) / "config" / "company.yaml"
        if config_path.exists():
            with open(config_path) as f:
                return yaml.safe_load(f)
        return {}
    
    def _get_subsidiary_by_intent(self, user_input: str) -> list:
        """基于意图匹配子公司"""
        intent_map = {
            "写": "墨迹内容",
            "开发": "墨码开发",
            "设计": "墨工设计",
            "客服": "墨声客服",
            "增长": "墨增增长",
            "交易": "墨投交易",
        }
        matches = []
        for keyword, sub in intent_map.items():
            if keyword in user_input:
                matches.append(sub)
        return matches if matches else ["L0-中枢"]
    
    async def run_async(self, user_input: str, budget=None, timeline=None, context=None):
        """CEO决策入口"""
        subsidiaries = self._get_subsidiary_by_intent(user_input)
        return {
            "input": user_input,
            "decision": "dispatching",
            "subsidiaries": subsidiaries,
            "confidence": 0.85,
            "note": "由意图关键词匹配路由"
        }
