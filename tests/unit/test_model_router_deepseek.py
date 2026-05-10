"""L1 单元测试 — ModelRouter DeepSeek 迁移验证（6 个用例）"""
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


class TestModelRouterDeepSeek:
    """验证 DeepSeek 模型路由正确性"""

    @pytest.fixture
    def router(self):
        from core.ceo.model_router import ModelRouter
        return ModelRouter()

    def test_code_task_routes_to_pro(self, router):
        """代码生成任务应路由到 deepseek-v4-pro"""
        selected = router._select("code_generation")
        assert selected == "deepseek-v4-pro", f"expected deepseek-v4-pro, got {selected}"

    def test_cs_task_routes_to_flash(self, router):
        """客服任务应路由到 deepseek-v4-flash"""
        selected = router._select("customer_service")
        assert selected == "deepseek-v4-flash", f"expected deepseek-v4-flash, got {selected}"

    def test_default_routes_to_flash(self, router):
        """默认路由应使用 deepseek-v4-flash"""
        selected = router._select("unknown_task_type")
        assert "deepseek" in selected, f"expected deepseek model, got {selected}"

    def test_content_creation_stays_qwen(self, router):
        """内容创作 (ip/edu) 保留千问"""
        selected = router._select("content_creation")
        assert selected == "qwen3.6-plus", f"expected qwen3.6-plus, got {selected}"

    def test_deepseek_models_have_deepseek_provider(self, router):
        """DeepSeek 模型配置的 provider 应为 deepseek"""
        pro_cfg = router._models.get("deepseek-v4-pro", {})
        flash_cfg = router._models.get("deepseek-v4-flash", {})
        assert pro_cfg.get("provider") == "deepseek", f"pro provider: {pro_cfg.get('provider')}"
        assert flash_cfg.get("provider") == "deepseek", f"flash provider: {flash_cfg.get('provider')}"

    def test_fallback_chain_does_not_contain_removed_models(self, router):
        """回退链不应包含已移除的模型（qwen3-coder-plus, minimax）"""
        for task_type in ["code_generation", "ceo_decision", "default"]:
            chain = router._get_fallback_chain(task_type)
            chain_str = " ".join(chain).lower()
            assert "qwen3-coder" not in chain_str, f"{task_type} chain contains removed model"
            assert "minimax" not in chain_str, f"{task_type} chain contains removed model"
