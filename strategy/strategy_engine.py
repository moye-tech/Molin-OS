from pathlib import Path
import json
import time
from loguru import logger

from core.ceo.model_router import ModelRouter

PROMPT_PATH = Path(__file__).resolve().parent / 'prompts' / 'strategy.txt'


class StrategyEngine:
    def __init__(self):
        self.router = ModelRouter()
        self.system_prompt = PROMPT_PATH.read_text(encoding='utf-8') if PROMPT_PATH.exists() else ''

    async def generate(self, hermes_decision: dict) -> dict:
        start = time.time()
        full_input = (
            f"Hermes 当前决策：{json.dumps(hermes_decision, ensure_ascii=False, indent=2)}\n"
            "请严格按模板生成量化策略。"
        )
        result = await self.router.call_async(
            prompt=full_input,
            system=self.system_prompt,
            task_type='strategy_generation',
        )
        try:
            text = result['text']
            s, e = text.find('{'), text.rfind('}') + 1
            strategy = json.loads(text[s:e])
            logger.info(f"Strategy generated with model {result.get('model')}")
            return {
                **strategy,
                'model_used': result.get('model'),
                'cost': result.get('cost', 0.0),
                'latency': round(time.time() - start, 2),
            }
        except Exception as exc:
            logger.error(f"Strategy parse failed: {exc}")
            return {'error': 'JSON解析失败', 'raw': result.get('text', '')}
