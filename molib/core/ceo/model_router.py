"""
ModelRouter v6.6 — 配置驱动的多模型智能路由
从 config/models.toml 和 config/subsidiaries.toml 加载路由规则，
复用 API 客户端实例，消除硬编码和随机探索。
"""

import os
import time
from pathlib import Path
from typing import Dict, Any, Optional, List

from loguru import logger

# TOML 库兼容
_tomllib = None
_tomllib_is_text = False

try:
    import tomllib  # Python 3.11+，需要二进制模式
    _tomllib = tomllib
    _tomllib_is_text = False
except ImportError:
    try:
        import tomli as _tomllib  # pip install tomli，需要二进制模式
        _tomllib_is_text = False
    except ImportError:
        try:
            import toml as _tomllib  # pip install toml，需要文本模式
            _tomllib_is_text = True
        except ImportError:
            logger.warning("toml/tomllib 不可用，ModelRouter 将使用内置默认配置")

# 配置文件路径
_CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"
_MODELS_TOML = _CONFIG_DIR / "models.toml"
_SUBSIDIARIES_TOML = _CONFIG_DIR / "subsidiaries.toml"


def _load_toml(path: Path) -> Dict[str, Any]:
    """加载 TOML 配置文件"""
    if _tomllib is None or not path.exists():
        return {}
    try:
        if _tomllib_is_text:
            # toml 库需要文本模式
            with open(path, "r", encoding="utf-8") as f:
                return _tomllib.load(f)
        else:
            # tomllib/tomli 需要二进制模式
            with open(path, "rb") as f:
                return _tomllib.load(f)
    except Exception as e:
        logger.error(f"加载 TOML 配置失败 {path}: {e}")
        return {}


# ── 默认配置（当 TOML 不可用时的兜底） ──────────────────

_DEFAULT_ROUTING = {
    "ceo_decision": {"primary": "deepseek-v4-pro", "fallback": ["deepseek-v4-flash"]},
    "code_generation": {"primary": "deepseek-v4-pro", "fallback": ["deepseek-v4-flash"]},
    "code_execution": {"primary": "deepseek-v4-pro", "fallback": ["deepseek-v4-flash"]},
    "data_analysis": {"primary": "deepseek-v4-pro", "fallback": ["deepseek-v4-flash"]},
    "deep_research": {"primary": "deepseek-v4-pro", "fallback": ["deepseek-v4-flash"]},
    "financial_analysis": {"primary": "deepseek-v4-pro", "fallback": ["deepseek-v4-flash"]},
    "compliance_check": {"primary": "deepseek-v4-pro", "fallback": ["deepseek-v4-flash"]},
    "content_creation": {"primary": "qwen3.6-plus", "fallback": ["deepseek-v4-flash"]},
    "customer_service": {"primary": "deepseek-v4-flash", "fallback": ["deepseek-v4-pro"]},
    "batch_content": {"primary": "deepseek-v4-flash", "fallback": ["deepseek-v4-flash"]},
    "routine_tasks": {"primary": "deepseek-v4-flash", "fallback": ["deepseek-v4-pro"]},
    "default": {"primary": "deepseek-v4-flash", "fallback": ["deepseek-v4-pro"]},
}

_DEFAULT_TEAM_MAP = {
    "ip": "qwen3.6-plus", "edu": "qwen3.6-plus",
    "dev": "deepseek-v4-pro", "devops": "deepseek-v4-pro",
    "finance": "deepseek-v4-pro", "legal": "deepseek-v4-pro",
    "research": "deepseek-v4-pro", "ai": "deepseek-v4-pro",
    "data": "deepseek-v4-pro", "secure": "deepseek-v4-pro",
    "ads": "deepseek-v4-flash", "growth": "deepseek-v4-flash",
    "crm": "deepseek-v4-flash", "cs": "deepseek-v4-flash",
    "shop": "deepseek-v4-flash", "product": "deepseek-v4-flash",
    "order": "deepseek-v4-flash", "knowledge": "deepseek-v4-flash",
    "bd": "deepseek-v4-flash", "global_market": "deepseek-v4-flash",
}

_DEFAULT_MODELS = {
    "deepseek-v4-pro": {
        "provider": "deepseek", "model_name": "deepseek-v4-pro",
        "api_key_env": "DEEPSEEK_API_KEY", "base_url_env": "DEEPSEEK_BASE_URL",
        "max_tokens": 8000, "context_window": 1000000,
        "reasoning_effort": "high",
        "input_cost_cache": 0.000025, "input_cost_miss": 0.003, "output_cost": 0.006,
    },
    "deepseek-v4-flash": {
        "provider": "deepseek", "model_name": "deepseek-v4-flash",
        "api_key_env": "DEEPSEEK_API_KEY", "base_url_env": "DEEPSEEK_BASE_URL",
        "max_tokens": 8000, "context_window": 1000000,
        "reasoning_effort": "low",
        "input_cost_cache": 0.00002, "input_cost_miss": 0.001, "output_cost": 0.002,
    },
    "qwen3.6-plus": {
        "provider": "dashscope", "model_name": "qwen3.6-plus",
        "api_key_env": "DASHSCOPE_API_KEY",
        "max_tokens": 8000, "cost_per_1k_input": 0.0008, "cost_per_1k_output": 0.0032,
    },
    "qwen3.6-flash": {
        "provider": "dashscope", "model_name": "qwen3.6-flash",
        "max_tokens": 4000, "cost_per_1k_input": 0.00015, "cost_per_1k_output": 0.0006,
    },
    "qwen3.6-max-preview": {
        "provider": "dashscope", "model_name": "qwen3.6-max-preview",
        "max_tokens": 8000, "cost_per_1k_input": 0.003, "cost_per_1k_output": 0.012,
        "is_preview": True,
    },
    "glm-5": {
        "provider": "dashscope", "model_name": "glm-5",
        "max_tokens": 4000, "cost_per_1k_input": 0.003, "cost_per_1k_output": 0.003,
    },
}

_DEFAULT_COST_CONTROL = {
    "daily_budget_cny": 50.0,
    "auto_fallback_on_budget": True,
    "budget_fallback_model": "deepseek-v4-flash",
    "prefer_cached": True,
}


class ModelRouter:
    """配置驱动的多模型智能路由器"""

    def __init__(self, config_path: Optional[Path] = None):
        # 加载配置
        models_toml = _load_toml(config_path or _MODELS_TOML)
        subsidiaries_toml = _load_toml(_SUBSIDIARIES_TOML)

        # 解析模型定义
        self._models: Dict[str, Dict[str, Any]] = (
            models_toml.get("models", {}) or _DEFAULT_MODELS
        )

        # 解析路由规则
        self._routing: Dict[str, Dict[str, Any]] = (
            models_toml.get("routing", {}) or _DEFAULT_ROUTING
        )

        # 解析成本控制
        self._cost_control: Dict[str, Any] = (
            models_toml.get("cost_control", {}) or _DEFAULT_COST_CONTROL
        )

        # 解析 provider 配置
        self._providers: Dict[str, Dict[str, Any]] = models_toml.get("providers", {})

        # 从 subsidiaries.toml 构建 team→model 映射
        self._team_model_map: Dict[str, str] = self._build_team_model_map(subsidiaries_toml)

        # v6.6: 预览版模型调用计数
        self._preview_call_count: Dict[str, int] = {}

        logger.info(
            f"ModelRouter 初始化: {len(self._models)} 个模型, "
            f"{len(self._routing)} 条路由规则, "
            f"{len(self._team_model_map)} 个 team 映射"
        )

    # ── 配置构建 ──────────────────────────────────────

    def _build_team_model_map(self, subsidiaries_toml: Dict[str, Any]) -> Dict[str, str]:
        """从 subsidiaries.toml 构建 team → model 映射"""
        team_map = {}
        if "agencies" in subsidiaries_toml and isinstance(subsidiaries_toml["agencies"], list):
            for config in subsidiaries_toml["agencies"]:
                if not config.get("enabled", True):
                    continue
                team_id = config.get("id")
                if not team_id:
                    continue
                model_pref = config.get("default_model") or config.get("model_preference")
                if model_pref:
                    model_config = self._models.get(model_pref, {})
                    actual_model = model_config.get("model_name", model_pref)
                    team_map[team_id] = actual_model
        return team_map or _DEFAULT_TEAM_MAP

    # ── 模型选择 ──────────────────────────────────────

    def _select(self, task_type: str, team: Optional[str] = None) -> str:
        """确定性模型选择：team 映射优先 → task 路由规则 → 默认"""
        # 1. Team 级映射优先
        if team and team in self._team_model_map:
            return self._team_model_map[team]

        # 2. Task 类型路由：TOML → _DEFAULT_ROUTING → 兜底 qwen3.6-plus
        route = self._routing.get(task_type) or _DEFAULT_ROUTING.get(task_type, {})
        if not route:
            route = _DEFAULT_ROUTING.get("default", {"primary": "qwen3.6-plus"})
        primary = route.get("primary", "qwen3.6-plus")

        model_config = self._models.get(primary, {})
        return model_config.get("model_name", primary)

    def _get_fallback_chain(self, task_type: str) -> List[str]:
        """获取任务类型对应的回退链"""
        route = self._routing.get(task_type) or _DEFAULT_ROUTING.get(task_type, {})
        if not route:
            route = _DEFAULT_ROUTING.get("default", {"fallback": ["qwen3.6-flash"]})
        fallback_names = route.get("fallback", ["qwen3.6-flash"])
        chain = []
        for name in fallback_names:
            model_config = self._models.get(name, {})
            chain.append(model_config.get("model_name", name))
        return chain

    def _check_preview_quota(self, model_name: str) -> bool:
        """检查预览版模型是否超过每日调用上限"""
        if not self._models.get(model_name, {}).get("is_preview", False):
            return True  # 非预览版不限制
        max_calls = self._cost_control.get("max_preview_daily_calls", 50)
        return self._preview_call_count.get(model_name, 0) < max_calls

    def _increment_preview_count(self, model_name: str):
        """增加预览版模型调用计数"""
        if self._models.get(model_name, {}).get("is_preview", False):
            self._preview_call_count[model_name] = self._preview_call_count.get(model_name, 0) + 1

    # ── 核心调用 ──────────────────────────────────────

    async def call_async(
        self,
        prompt: str,
        system: str = "",
        task_type: str = "default",
        team: Optional[str] = None,
        model: Optional[str] = None,
        enable_search: bool = False,
        reasoning_effort: Optional[str] = None,  # CEO 根据意图动态覆盖
        max_tokens: Optional[int] = None,        # CEO 根据意图动态覆盖
    ) -> Dict[str, Any]:
        """调用模型，失败时沿回退链尝试。reasoning_effort/max_tokens 可动态覆盖。"""
        if model:
            selected = model
        else:
            selected = self._select(task_type, team)

        # BudgetGuard 预检
        from molib.core.budget_guard import get_budget_guard
        guard = get_budget_guard()
        selected = guard.check_and_select(selected, 0.05)

        fallback_chain = self._get_fallback_chain(task_type)
        start = time.time()

        # 尝试主模型
        try:
            text, provider = await self._call_model(
                prompt, system, selected, enable_search=enable_search,
                reasoning_effort=reasoning_effort, max_tokens=max_tokens,
            )
            cost = self._cost(selected, len(prompt), len(text))
            guard.record_cost(cost)
            return {
                "text": text, "model": selected, "provider": provider,
                "cost": cost, "latency": round(time.time() - start, 2),
                "fallback": False,
            }
        except Exception as e:
            logger.warning(f"[{selected}] 调用失败: {e}, 尝试回退链 {fallback_chain}")

        # 沿回退链尝试
        for fb_model in fallback_chain:
            try:
                text, provider = await self._call_model(prompt, system, fb_model)
                cost = self._cost(fb_model, len(prompt), len(text))
                guard.record_cost(cost)
                return {
                    "text": text, "model": fb_model, "provider": provider,
                    "cost": cost, "latency": round(time.time() - start, 2),
                    "fallback": True,
                }
            except Exception as fb_e:
                logger.warning(f"[{fb_model}] 回退也失败: {fb_e}")

        # 最终兜底：从配置读取 fallback_model，不再硬编码
        final_fallback = self._cost_control.get("budget_fallback_model", "deepseek-v4-flash")
        logger.error(f"所有模型失败，使用最终兜底: {final_fallback}")
        text, provider = await self._call_model(prompt, system, final_fallback)
        cost = self._cost(final_fallback, len(prompt), len(text))
        return {
            "text": text, "model": final_fallback, "provider": provider,
            "cost": cost, "latency": round(time.time() - start, 2),
            "fallback": True,
        }

    async def _call_model(self, prompt: str, system: str, model: str, enable_search: bool = False,
                         reasoning_effort: Optional[str] = None,
                         max_tokens: Optional[int] = None) -> tuple:
        """根据模型 provider 字段自动路由到对应 API 方法"""
        # 1. 从配置查找 provider
        provider = "dashscope"  # 默认兜底
        for m_name, m_cfg in self._models.items():
            if m_cfg.get("model_name") == model or m_name == model:
                provider = m_cfg.get("provider", "dashscope")
                break

        # 2. 按模型名前缀自动识别 DeepSeek
        if model.startswith("deepseek-"):
            provider = "deepseek"

        # 3. 路由分发
        if provider == "deepseek":
            return await self._deepseek(prompt, system, model,
                                       reasoning_effort=reasoning_effort,
                                       max_tokens=max_tokens)
        elif provider == "dashscope":
            return await self._dashscope(prompt, system, model, enable_search=enable_search)
        else:
            return await self._dashscope(prompt, system, model, enable_search=enable_search)

    async def _deepseek(self, prompt: str, system: str, model: str,
                        reasoning_effort: Optional[str] = None,
                        max_tokens: Optional[int] = None) -> tuple[str, str]:
        """DeepSeek API 直连 — 前缀缓存 + 思考模式（CE0 可动态覆盖推理深度）"""
        import httpx
        cfg = self._models.get(model, {})
        api_key = os.getenv(cfg.get("api_key_env", "DEEPSEEK_API_KEY"))
        base_url = os.getenv(cfg.get("base_url_env", "DEEPSEEK_BASE_URL"),
                             "https://api.deepseek.com")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY 未设置")

        # CE0 意图动态覆盖 > 模型配置默认值
        max_tokens_val = max_tokens or cfg.get("max_tokens", 8000)
        reasoning = reasoning_effort or cfg.get("reasoning_effort")
        enable_cache = os.getenv("DEEPSEEK_CACHE_ENABLED", "true").lower() == "true"

        messages = []
        if system:
            sys_msg = {"role": "system", "content": system}
            if enable_cache and len(system) > 500:
                sys_msg["prefix"] = True
            messages.append(sys_msg)
        messages.append({"role": "user", "content": prompt})

        payload: dict = {"model": model, "messages": messages, "max_tokens": max_tokens_val}
        if reasoning and os.getenv("DEEPSEEK_REASONING_ENABLED", "true").lower() == "true":
            payload["reasoning_effort"] = reasoning

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{base_url.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        usage = data.get("usage", {})
        cache_hit = usage.get("prompt_cache_hit_tokens", 0)
        if cache_hit:
            logger.debug(f"[DeepSeek] 缓存命中 {cache_hit} tokens")
        return data["choices"][0]["message"]["content"], "deepseek"

    async def _dashscope(self, prompt: str, system: str, model: str, enable_search: bool = False) -> str:
        """直连阿里云百炼 DashScope OpenAI 兼容端点"""
        import httpx

        # 优先模型级配置，回退 provider 配置
        model_cfg = self._models.get(model, {})
        prov_cfg = self._providers.get("dashscope", {})
        api_key_env = model_cfg.get("api_key_env") or prov_cfg.get("api_key_env", "DASHSCOPE_API_KEY")
        api_key = os.getenv(api_key_env)
        if not api_key:
            raise ValueError(f"{api_key_env} 未设置")

        base_url_env = model_cfg.get("base_url_env", "")
        base_url = (os.getenv(base_url_env) or prov_cfg.get("base_url", "")) if base_url_env else ""
        if not base_url:
            base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"

        max_tokens = model_cfg.get("max_tokens", 8000)
        enable_cache = prov_cfg.get("enable_cache", True)

        msgs = []
        if system:
            msg = {"role": "system", "content": system}
            if enable_cache and len(system) > 1024:
                msg["cache_control"] = {"type": "ephemeral"}
            msgs.append(msg)
        msgs.append({"role": "user", "content": prompt})

        payload: dict = {
            "model": model,
            "messages": msgs,
            "max_tokens": max_tokens,
        }
        if enable_search:
            payload["enable_search"] = True
            payload["search_options"] = {"forced_search": False}

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{base_url.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "X-DashScope-Client": "molin-ai-v8",
                },
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        usage = data.get("usage", {})
        cache_hit = usage.get("cache_hit_tokens", 0)
        if cache_hit > 0:
            logger.debug(f"[{model}] 缓存命中 {cache_hit} tokens")

        return data["choices"][0]["message"]["content"], model

    # ── 成本计算 ──────────────────────────────────────

    def _cost(self, model: str, in_chars: int, out_chars: int) -> float:
        """基于配置计算成本，兼容新旧定价格式"""
        for m_name, m_cfg in self._models.items():
            actual_name = m_cfg.get("model_name", m_name)
            if actual_name == model or m_name == model:
                # 新定价格式（input_cost_miss + output_cost per 1M token）
                if "input_cost_miss" in m_cfg:
                    cost_in_m = m_cfg.get("input_cost_miss", 0.001)
                    cost_out_m = m_cfg.get("output_cost", 0.002)
                    return round(
                        (in_chars / 1_000_000 * cost_in_m) +
                        (out_chars / 1_000_000 * cost_out_m), 5
                    )
                # 旧定价格式（cost_per_1k）
                cost_in = m_cfg.get("cost_per_1k_input", 0.01)
                cost_out = m_cfg.get("cost_per_1k_output", 0.01)
                return round(
                    (in_chars / 1000 * cost_in) + (out_chars / 1000 * cost_out), 5
                )
        return 0.01

    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """获取模型配置信息"""
        for m_name, m_cfg in self._models.items():
            if m_cfg.get("model_name") == model_name or m_name == model_name:
                return {"id": m_name, **m_cfg}
        return None

    def list_available_models(self) -> List[Dict[str, Any]]:
        """列出所有可用模型"""
        return [
            {"id": m_name, "model_name": m_cfg.get("model_name", m_name),
             "provider": m_cfg.get("provider", "unknown")}
            for m_name, m_cfg in self._models.items()
        ]

    # ── Feature 7: 模型路由自优化 ──────────────────────────

    async def auto_optimize(self) -> Dict[str, Any]:
        """
        月度模型路由自优化：分析 model_logs 统计，自动调整路由策略。
        每月 1 日触发。
        """
        from molib.infra.memory.sqlite_client import DEFAULT_DB_PATH as db_env
        import sqlite3
        db_path = os.environ.get("SQLITE_DB_PATH", db_env)
        if not os.path.exists(db_path):
            return {"status": "skipped", "reason": "SQLite db not found"}

        result = {"status": "completed", "changes": [], "report": ""}
        try:
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                # 按 (provider, model, task_type) 分组统计
                cur = conn.execute(
                    "SELECT provider, model, task_type, "
                    "COUNT(*) as total, SUM(success) as success_count, "
                    "SUM(cost) as total_cost, AVG(latency) as avg_latency "
                    "FROM model_logs GROUP BY provider, model, task_type"
                )
                stats = [dict(r) for r in cur.fetchall()]

            # 按 task_type 分组分析
            by_task: Dict[str, List[dict]] = {}
            for s in stats:
                tt = s.get("task_type", "default")
                by_task.setdefault(tt, []).append(s)

            for task_type, entries in by_task.items():
                if len(entries) < 2:
                    continue
                # 排序: 成功率优先，成本其次
                for e in entries:
                    e["success_rate"] = round(e["success_count"] / max(1, e["total"]) * 100, 1)
                    e["avg_cost"] = round(e["total_cost"] / max(1, e["total"]), 4)

                entries.sort(key=lambda x: (-x["success_rate"], x["avg_cost"]))
                best = entries[0]

                # 检查当前路由配置
                route = self._routing.get(task_type)
                if route:
                    primary = route.get("primary", "")
                    best_model = f"{best['provider']}/{best['model']}"
                    if best["success_rate"] >= 90 and primary and primary not in best_model:
                        result["changes"].append({
                            "task_type": task_type,
                            "recommendation": f"建议将 {task_type} 的主模型调整为 {best_model} "
                            f"(成功率 {best['success_rate']}%, 成本 ¥{best['avg_cost']})",
                            "best_model": best_model,
                            "current_primary": primary,
                        })

            # 标记低效模型
            for s in stats:
                sr = s["success_count"] / max(1, s["total"]) * 100
                if sr < 50 and s["total"] >= 5:
                    result["changes"].append({
                        "task_type": s.get("task_type", "unknown"),
                        "warning": f"模型 {s['provider']}/{s['model']} 成功率仅 {sr:.1f}% ({s['total']} 次调用)",
                        "success_rate": round(sr, 1),
                        "total_calls": s["total"],
                    })

            # 生成报告
            report_lines = ["# 模型路由月度优化报告\n"]
            for c in result["changes"]:
                if "recommendation" in c:
                    report_lines.append(f"## {c['task_type']}: 建议切换主模型")
                    report_lines.append(f"- 当前: {c['current_primary']}")
                    report_lines.append(f"- 推荐: {c['best_model']}")
                elif "warning" in c:
                    report_lines.append(f"## ⚠️ {c['warning']}")

            result["report"] = "\n".join(report_lines)
            logger.info(f"模型路由优化完成: {len(result['changes'])} 条变更/建议")

            # 推送到飞书
            if result["report"]:
                try:
                    from molib.infra.reports.daily_weekly_report import send_report_to_feishu
                    await send_report_to_feishu({
                        "status": "success", "type": "模型优化报告", "report": result["report"],
                    })
                except Exception:
                    pass

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            logger.error(f"模型路由优化失败: {e}")

        return result
