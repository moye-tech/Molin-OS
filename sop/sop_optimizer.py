"""
SOP 自动优化器（Feature 5）
每日分析各子公司失败率，对失败率 >30% 的子公司触发 SOP 重新生成
"""

import os
import json
import sqlite3
from typing import Dict, Any, List, Optional
from pathlib import Path
from loguru import logger

SOP_DIR = Path(__file__).parent / "definitions"
SOP_DIR.mkdir(exist_ok=True)


class SOPOptimizer:
    """SOP 自动优化器"""

    FAILURE_THRESHOLD = 0.3  # 失败率超过 30% 触发优化

    async def analyze_sop_performance(self) -> Dict[str, Dict[str, Any]]:
        """分析各子公司/任务类型的 SOP 表现"""
        from infra.memory.sqlite_client import DEFAULT_DB_PATH as db_env
        db_path = os.environ.get("SQLITE_DB_PATH", db_env)
        if not os.path.exists(db_path):
            return {}

        try:
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                # 从 evolution_knowledge 表分析各 outcome 的比例
                cur = conn.execute(
                    "SELECT outcome, COUNT(*) as cnt FROM evolution_knowledge GROUP BY outcome"
                )
                outcomes = {r["outcome"]: r["cnt"] for r in cur.fetchall()}

                total = sum(outcomes.values())
                failures = outcomes.get("failure", 0)
                failure_rate = failures / max(1, total)

                return {
                    "total_evaluated": total,
                    "outcomes": outcomes,
                    "failure_rate": round(failure_rate, 3),
                    "needs_optimization": failure_rate > self.FAILURE_THRESHOLD,
                }
        except Exception as e:
            logger.error(f"SOP 性能分析失败: {e}")
            return {}

    async def identify_underperforming_sops(self) -> List[str]:
        """识别需要优化的子公司 SOP"""
        from core.tools.registry import ToolRegistry
        available = list(ToolRegistry.list_all())
        # 从 evolution_knowledge 中找出失败最多的 agency/task_type
        from infra.memory.sqlite_client import DEFAULT_DB_PATH as db_env
        db_path = os.environ.get("SQLITE_DB_PATH", db_env)
        if not os.path.exists(db_path):
            return []

        underperforming = []
        try:
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.execute(
                    "SELECT source_task, outcome, COUNT(*) as cnt "
                    "FROM evolution_knowledge WHERE outcome IN ('failure', 'partial') "
                    "GROUP BY source_task ORDER BY cnt DESC LIMIT 5"
                )
                for r in cur.fetchall():
                    underperforming.append(r["source_task"])
        except Exception as e:
            logger.warning(f"识别低效 SOP 失败: {e}")
        return underperforming

    async def regenerate_sop(self, subsidiary_id: str, failure_patterns: List[str]) -> str:
        """LLM 重新生成 SOP"""
        prompt = f"""你是墨麟AI系统的架构师。请为子公司 "{subsidiary_id}" 生成一份优化后的 SOP（标准操作流程）。

## 当前问题
以下任务模式出现了较高的失败率，请在新 SOP 中增加对应的处理和容错机制：
{chr(10).join(f"- {p}" for p in failure_patterns[:10])}

## 要求
1. 输出 YAML 格式的 SOP 定义
2. 包含: workflow_steps, error_handling, retry_policy, escalation_rules
3. 针对上述失败模式增加专项检查点
4. 保持简洁，步骤不超过 10 个
"""
        try:
            from core.ceo.model_router import ModelRouter
            router = ModelRouter()
            result = await router.call_async(
                prompt=prompt,
                system="你是 SOP 优化专家，输出 YAML 格式的标准操作流程。",
                task_type="ceo_decision",
            )
            sop_content = result.get("text", "")
            return sop_content
        except Exception as e:
            logger.error(f"SOP 重新生成失败: {e}")
            return ""

    async def apply_sop_update(self, subsidiary_id: str, new_sop_content: str) -> bool:
        """将新 SOP 写入文件"""
        try:
            safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in subsidiary_id)
            file_path = SOP_DIR / f"{safe_name}.yaml"
            file_path.write_text(new_sop_content, encoding="utf-8")
            logger.info(f"SOP 已更新: {file_path}")
            return True
        except Exception as e:
            logger.error(f"SOP 写入失败: {e}")
            return False

    async def run_daily_optimization(self) -> Dict[str, Any]:
        """每日 SOP 优化主流程"""
        logger.info("=== 开始每日 SOP 自动优化 ===")
        result = {"status": "started", "actions": []}

        perf = await self.analyze_sop_performance()
        result["performance"] = perf

        if perf.get("needs_optimization"):
            underperforming = await self.identify_underperforming_sops()
            result["underperforming"] = underperforming

            for task in underperforming:
                new_sop = await self.regenerate_sop(task, [f"Failure pattern: {task}"])
                if new_sop:
                    applied = await self.apply_sop_update(task, new_sop)
                    result["actions"].append({"task": task, "applied": applied})
        else:
            logger.info("SOP 性能正常，无需优化")
            result["actions"] = ["no_optimization_needed"]

        return result
