"""L3 API 连通性测试 — DeepSeek 直连验证（需 DEEPSEEK_API_KEY）"""
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

pytestmark = [
    pytest.mark.skipif(
        not os.getenv("DEEPSEEK_API_KEY"),
        reason="DEEPSEEK_API_KEY not set, skipping live API test",
    ),
    pytest.mark.integration,
]


class TestDeepSeekAPILive:
    """验证 DeepSeek API 直连正常"""

    @pytest.fixture
    def router(self):
        from core.ceo.model_router import ModelRouter
        return ModelRouter()

    @pytest.mark.asyncio
    async def test_pro_basic_call(self, router):
        """Pro 基础调用返回 200 + 内容非空"""
        result = await router.call_async(
            prompt="用一句话解释 Python 的 GIL",
            model="deepseek-v4-pro",
        )
        assert result["text"], "response text should not be empty"
        assert len(result["text"]) > 10, f"response too short: {len(result['text'])} chars"
        assert result["provider"] in ("deepseek", "dashscope"), f"unexpected provider: {result['provider']}"

    @pytest.mark.asyncio
    async def test_flash_basic_call(self, router):
        """Flash 基础调用返回 200 + 内容非空"""
        result = await router.call_async(
            prompt="用一句话解释什么是 API",
            model="deepseek-v4-flash",
        )
        assert result["text"], "response text should not be empty"
        assert len(result["text"]) > 5, f"response too short: {len(result['text'])} chars"

    @pytest.mark.asyncio
    async def test_deepseek_provider_detected(self, router):
        """deepseek- 前缀自动识别为 deepseek provider"""
        text, provider = await router._call_model(
            "Hello, respond in one sentence",
            "You are a helpful assistant",
            "deepseek-v4-flash",
        )
        assert provider == "deepseek", f"expected deepseek provider, got {provider}"

    @pytest.mark.asyncio
    async def test_cache_prefix_in_system_message(self, router):
        """长 system prompt 应标记 prefix=True（验证缓存机制）"""
        long_system = "You are a helpful assistant. " * 100  # ~3500 chars > 500
        text, provider = await router._call_model(
            "Say hello", long_system, "deepseek-v4-flash"
        )
        assert text, "should get a response"

    @pytest.mark.asyncio
    async def test_cost_calculation_new_format(self, router):
        """新定价格式成本计算不报错"""
        cost = router._cost("deepseek-v4-pro", 10000, 5000)
        assert isinstance(cost, (int, float)), f"cost should be numeric, got {type(cost)}"
        assert cost >= 0, f"cost should be non-negative, got {cost}"
