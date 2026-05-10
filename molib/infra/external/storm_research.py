"""
墨麟OS — STORM 集成 (⭐22k)
============================
斯坦福STORM：模拟"采访专家"流程自动生成维基百科级别深度文章。

用法:
    from molib.infra.external.storm_research import storm_report
    result = storm_report("量子计算在金融行业的应用前景")

集成点:
  - Research Worker: 深度行业分析报告
  - Education Worker: 课程大纲自动生成
"""

from __future__ import annotations

import os
import json
import asyncio
from typing import Optional


async def storm_report(
    topic: str,
    language: str = "zh",
    max_sections: int = 5,
) -> dict:
    """
    使用STORM生成维基百科级别的深度研究报告。

    Args:
        topic: 研究主题
        language: 语言 (zh/en)
        max_sections: 最大章节数

    Returns:
        {"topic": str, "report": str, "outline": [...], "references": [...]}
    """
    try:
        # STORM 需要 OpenAI API key
        api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("DEEPSEEK_API_KEY", "")
        if not api_key:
            return {"topic": topic, "error": "No API key for LLM", "status": "no_api_key"}

        from knowledge_storm import (
            STORMWikiRunnerArguments,
            STORMWikiRunner,
            STORMWikiLMConfigs,
        )
        from knowledge_storm.lm import OpenAIModel
        from knowledge_storm.rm import YouRM

        # 配置LLM
        engine_lm_configs = STORMWikiLMConfigs()

        # 如果用的是DeepSeek而非OpenAI
        if os.environ.get("DEEPSEEK_API_KEY") and not os.environ.get("OPENAI_API_KEY"):
            lm = OpenAIModel(
                api_key=os.environ["DEEPSEEK_API_KEY"],
                model="deepseek-chat",
                base_url="https://api.deepseek.com/v1",
                max_tokens=4000,
            )
            engine_lm_configs.set_conv_simulator_lm(lm)
            engine_lm_configs.set_question_asker_lm(lm)
            engine_lm_configs.set_outline_gen_lm(lm)
            engine_lm_configs.set_article_gen_lm(lm)
            engine_lm_configs.set_article_polish_lm(lm)

        # 配置检索模块
        rm = YouRM(ydc_api_key=os.environ.get("YDC_API_KEY", ""))

        args = STORMWikiRunnerArguments(
            output_dir="/tmp/storm_output",
            max_conv_turn=3,
            max_perspective=3,
            search_top_k=5,
            max_thread_num=3,
        )

        runner = STORMWikiRunner(engine_lm_configs, args, rm=rm)

        result = await asyncio.wait_for(
            runner.run(
                topic=topic,
                do_research=True,
                do_generate_outline=True,
                do_generate_article=True,
                do_polish_article=True,
            ),
            timeout=600,
        )

        runner.summary()

        return {
            "topic": topic,
            "report": result.get("article", ""),
            "outline": result.get("outline", []),
            "references": result.get("references", []),
            "source": "stanford-storm",
            "status": "success",
        }

    except ImportError:
        return {"topic": topic, "error": "STORM not installed. Run: pip install knowledge-storm", "status": "unavailable"}
    except asyncio.TimeoutError:
        return {"topic": topic, "error": "STORM research timed out (600s)", "status": "timeout"}
    except Exception as e:
        return {"topic": topic, "error": str(e), "status": "error"}
