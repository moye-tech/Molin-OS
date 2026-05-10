"""L4 子公司验收 — 验证真实输出质量（需启动 Docker 服务）"""
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

pytestmark = [
    pytest.mark.skipif(
        not os.getenv("DEEPSEEK_API_KEY") and not os.getenv("DASHSCOPE_API_KEY"),
        reason="No API key configured, skipping acceptance tests",
    ),
    pytest.mark.slow,
]


def _call_ceo(prompt: str, team: str = None) -> str:
    """同步调用 CEO（基于当前 router 配置）"""
    import asyncio
    from core.ceo.model_router import ModelRouter

    async def _run():
        router = ModelRouter()
        result = await router.call_async(prompt=prompt, team=team, task_type="default")
        return result.get("text", "")

    return asyncio.run(_run())


class TestAgencyOutputQuality:
    """5 个核心子公司的输出质量验收"""

    def test_ip_content_creation(self):
        """ip (墨迹内容): 写小红书文案应含标题和正文"""
        text = _call_edu_or_ip(prompt="写一篇小红书爆款文案，主题是AI工具推荐", team="ip")
        if text is None:  # API 不可用时跳过
            pytest.skip("API not available")

        # 质量条件：含"标题""正文"，不含占位文本
        assert any(kw in text for kw in ["标题", "标题：", "#"]), f"No title pattern in: {text[:200]}"
        assert len(text) > 50, f"Text too short: {len(text)} chars"
        assert "任务聚合" not in text, f"Placeholder text found"
        assert "0个成功" not in text, f"Placeholder text found"

    def test_dev_code_generation(self):
        """dev (墨码工坊): 写 Python 函数应含 def 和 return"""
        text = _call_ceo(prompt="写一个Python函数，计算斐波那契数列第n项", team="dev")

        assert "def " in text.lower() or "def(" in text.lower(), \
            f"No function definition in: {text[:200]}"
        assert "return" in text.lower(), f"No return statement in: {text[:200]}"
        assert "待实现" not in text, f"Placeholder found"
        assert len(text) > 30, f"Text too short: {len(text)} chars"

    def test_finance_calculation(self):
        """finance (墨算财务): 计算净利润"""
        text = _call_ceo(
            prompt="一家公司收入800万，成本500万，税率25%，计算净利润",
            team="finance",
        )

        assert len(text) > 30, f"Text too short: {len(text)} chars"
        # 净利应为 (800-500)*0.75 = 225
        assert any(num in text for num in ["225", "225万"]), \
            f"Expected 225 (net profit) in output: {text[:300]}"

    def test_research_analysis(self):
        """research (墨情报局): 竞品分析应包含分析内容"""
        text = _call_ceo(
            prompt="分析一下AIGC行业的主要竞争对手有哪些",
            team="research",
        )

        assert len(text) > 300, f"Research output too short: {len(text)} chars"
        assert any(kw in text for kw in ["竞品", "竞争", "分析", "市场"]), \
            f"Missing analysis keywords in: {text[:200]}"

    def test_cs_response_quality(self):
        """cs (墨声客服): 退款话术应含有礼貌用语"""
        text = _call_ceo(
            prompt="用户说商品有瑕疵要退款，请给出客服回复话术",
            team="cs",
        )

        assert len(text) > 50, f"CS response too short: {len(text)} chars"
        assert any(kw in text for kw in ["您好", "抱歉", "理解", "退款"]), \
            f"Missing CS tone markers in: {text[:200]}"


def _call_edu_or_ip(prompt: str, team: str) -> str | None:
    """调用 ip/edu 子公司，这些保留千问"""
    try:
        return _call_ceo(prompt=prompt, team=team)
    except ValueError as e:
        if "未设置" in str(e) or "API" in str(e):
            return None
        raise
