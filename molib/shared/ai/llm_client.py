"""
墨麟AIOS — LLMClient (大语言模型客户端)
真实 DeepSeek API 调用 + BudgetGuard 成本熔断。

从 Hermes ~/.hermes/config.yaml 读取 API Key 和配置，
支持 provider 抽象：deepseek, qwen, openai, ollama。
"""

import os
import json
import re
import time
import yaml
from typing import Optional, Generator
from pathlib import Path
from datetime import datetime, date
from openai import OpenAI

# ── BudgetGuard 预算守护 ──────────────────────────────────────────
BUDGET_LOG_DIR = Path.home() / ".hermes" / "budget"
BUDGET_LOG_DIR.mkdir(parents=True, exist_ok=True)
BUDGET_LOG = BUDGET_LOG_DIR / "daily_cost.jsonl"


class BudgetGuard:
    """
    成本熔断器 — 每次 LLM 调用前预检当日预算。
    逼近阈值时自动降级模型。
    """

    def __init__(self, config_path: Path = None):
        if config_path is None:
            config_path = Path.home() / ".hermes" / "config.yaml"
        self.config_path = config_path
        self.monthly_cap = 1360.0  # ¥1360/月 默认
        self.alert_threshold = 0.8
        self._load_config()

    def _load_config(self):
        """从 governance.yaml 读取预算配置"""
        # 尝试从 molin 的 governance.yaml 读取
        paths = [
            Path(os.getcwd()) / "config" / "governance.yaml",
            Path.home() / ".hermes" / "governance.yaml",
        ]
        for p in paths:
            if p.exists():
                with open(p, encoding="utf-8") as f:
                    cfg = yaml.safe_load(f)
                    if cfg and "budget" in cfg:
                        cap = cfg["budget"].get("monthly_cap")
                        if cap:
                            self.monthly_cap = float(cap)
                        thr = cfg["budget"].get("alert_threshold")
                        if thr:
                            self.alert_threshold = float(thr)
                        return

    def _get_today_cost(self) -> float:
        """获取当日累计花费"""
        today_str = date.today().isoformat()
        total = 0.0
        if BUDGET_LOG.exists():
            with open(BUDGET_LOG, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        if entry.get("date") == today_str:
                            total += entry.get("cost", 0)
                    except json.JSONDecodeError:
                        continue
        return total

    def _get_month_cost(self) -> float:
        """获取当月累计花费"""
        month_prefix = date.today().isoformat()[:7]  # "2026-05"
        total = 0.0
        if BUDGET_LOG.exists():
            with open(BUDGET_LOG, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        if entry.get("date", "").startswith(month_prefix):
                            total += entry.get("cost", 0)
                    except json.JSONDecodeError:
                        continue
        return total

    def check(self, model_tag: str = "default") -> str:
        """
        预检：返回可用模型标签。
        - 正常 → 返回请求的模型
        - 逼近阈值 → 降级为 flash
        - 超额 → 强制降级
        """
        month_cost = self._get_month_cost()
        usage_ratio = month_cost / self.monthly_cap if self.monthly_cap > 0 else 0

        if usage_ratio >= 0.9:
            # 超额 90% — 强制降级到最便宜的
            return "force_flash"
        elif usage_ratio >= self.alert_threshold and model_tag != "flash":
            # 逼近阈值 — 自动降级
            return "auto_flash"
        return model_tag

    def log_cost(self, model: str, cost: float, prompt_tokens: int, completion_tokens: int):
        """记录一笔花费"""
        entry = {
            "date": date.today().isoformat(),
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "cost": round(cost, 6),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
        }
        with open(BUDGET_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ── 全局 BudgetGuard 实例 ─────────────────────────────────────────
_GUARD = BudgetGuard()

# ── 模板仓库 ──────────────────────────────────────────────────────
DEFAULT_TEMPLATES = {
    "summary": (
        "请对以下内容进行{style}总结：\n"
        "---\n{content}\n---\n"
        "要求：{instructions}"
    ),
    "sentiment": (
        "分析以下文本的情感倾向。\n"
        "输出JSON格式：{{\"sentiment\": \"positive|negative|neutral\", "
        "\"score\": 0.0-1.0, \"key_points\": []}}\n"
        "文本：{text}"
    ),
    "classification": (
        "将以下文本分类到以下类别之一：{categories}\n"
        "输出JSON格式：{{\"category\": \"...\", \"confidence\": 0.0-1.0, \"reason\": \"...\"}}\n"
        "文本：{text}"
    ),
    "extraction": (
        "从以下文本中提取{fields}信息。\n"
        "输出JSON格式。\n"
        "文本：{text}"
    ),
    "translate": (
        "将以下{source_lang}翻译成{target_lang}：\n"
        "---\n{text}\n---\n"
        "只输出翻译结果。"
    ),
    "rewrite": (
        "改写以下内容，风格：{style}，语气：{tone}：\n"
        "---\n{text}\n---"
    ),
}


class LLMClient:
    """
    大语言模型客户端 — 统一接口调用LLM。
    真实 API 调用（通过 OpenAI 兼容库），支持 BudgetGuard 成本熔断。

    Provider: deepseek (默认), qwen, openai, ollama
    """

    def __init__(self, provider: str = "deepseek", config: Optional[dict] = None):
        """
        Args:
            provider: 模型供应商 (deepseek/qwen/openai/ollama)
            config: 配置字典，支持:
                - api_key: API密钥
                - base_url: API地址
                - model: 默认模型名
                - timeout: 超时秒数
                - max_retries: 重试次数
                - templates: 自定义模板字典
                - guard_enabled: 是否启用 BudgetGuard (默认True)
        """
        self.provider = provider
        self.config = config or {}
        self.templates = {**DEFAULT_TEMPLATES, **(self.config.get("templates", {}))}

        # 优先从 config.yaml 读取
        self._load_from_hermes_config()

        # API配置（config 覆盖 > config.yaml > 环境变量）
        self.api_key = (
            self.config.get("api_key")
            or getattr(self, "_hermes_api_key", "")
            or os.environ.get(f"{provider.upper()}_API_KEY", "")
        )
        self.base_url = (
            self.config.get("base_url")
            or getattr(self, "_hermes_base_url", "")
            or self._default_base_url()
        )
        self.default_model = (
            self.config.get("model")
            or getattr(self, "_hermes_model", "")
            or self._default_model()
        )
        self.timeout = self.config.get("timeout", 60)
        self.max_retries = self.config.get("max_retries", 3)
        self.guard_enabled = self.config.get("guard_enabled", True)

        # 初始化 OpenAI 兼容客户端
        self._client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout,
            max_retries=self.max_retries,
        )

        # 对话历史
        self._conversation_history: list[dict] = []
        self._total_cost = 0.0
        self._total_tokens = 0

    def _load_from_hermes_config(self):
        """从 ~/.hermes/config.yaml 取默认 API 配置"""
        config_paths = [
            Path.home() / ".hermes" / "config.yaml",
            Path.home() / ".hermes" / "config.yml",
        ]
        for cp in config_paths:
            if cp.exists():
                try:
                    with open(cp, encoding="utf-8") as f:
                        cfg = yaml.safe_load(f) or {}
                    # 读 providers.deepseek
                    ds = (cfg.get("providers") or {}).get("deepseek") or {}
                    if ds.get("api_key"):
                        self._hermes_api_key = ds["api_key"]
                    if ds.get("base_url"):
                        self._hermes_base_url = ds["base_url"]
                    if ds.get("model"):
                        self._hermes_model = ds["model"]
                    # 也尝试 model.default
                    mdl = cfg.get("model") or {}
                    if not self._hermes_model and mdl.get("default"):
                        self._hermes_model = mdl["default"]
                    return
                except Exception:
                    continue

    def _default_base_url(self) -> str:
        urls = {
            "deepseek": "https://api.deepseek.com/v1",
            "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "openai": "https://api.openai.com/v1",
            "ollama": "http://localhost:11434/v1",
        }
        return urls.get(self.provider, urls["deepseek"])

    def _default_model(self) -> str:
        models = {
            "deepseek": "deepseek-v4-pro",
            "qwen": "qwen-plus",
            "openai": "gpt-4o-mini",
            "ollama": "llama3.1",
        }
        return models.get(self.provider, models["deepseek"])

    def _estimate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """估算调用的花费（¥）"""
        # 模型单价表（¥/1K tokens）
        pricing = {
            "deepseek-v4-pro": {"input": 0.0004, "output": 0.0014},
            "deepseek-v4-flash": {"input": 0.00014, "output": 0.00028},
            "deepseek-chat": {"input": 0.00014, "output": 0.00028},
            "deepseek-reasoner": {"input": 0.00055, "output": 0.00219},
            "qwen-turbo": {"input": 0.0003, "output": 0.0006},
            "qwen-plus": {"input": 0.0008, "output": 0.002},
            "qwen-max": {"input": 0.002, "output": 0.008},
        }
        model_key = model.lower()
        # 模糊匹配
        p = pricing.get(model_key, {"input": 0.0004, "output": 0.0014})
        for key, val in pricing.items():
            if key in model_key:
                p = val
                break

        cost_input = (prompt_tokens / 1000) * p["input"]
        cost_output = (completion_tokens / 1000) * p["output"]
        return cost_input + cost_output

    # ───────── 聊天（真实 API） ──────────────────────────────────────

    def chat(self, messages: list[dict], model: Optional[str] = None) -> str:
        """
        发送聊天消息并获取回复 — 真实 DeepSeek API 调用。

        Args:
            messages: 消息列表
            model: 指定模型 (默认使用self.default_model)

        Returns:
            str: 模型回复内容
        """
        model = model or self.default_model

        # 验证消息格式
        valid_roles = {"system", "user", "assistant"}
        for msg in messages:
            if msg.get("role") not in valid_roles:
                raise ValueError(f"无效消息角色: {msg.get('role')}，允许: {valid_roles}")
            if not msg.get("content"):
                raise ValueError("消息内容不能为空")

        # ── BudgetGuard 预检 ──
        if self.guard_enabled:
            guard_result = _GUARD.check(model)
            if guard_result == "force_flash":
                # 强制降级到最便宜的
                model = "deepseek-v4-flash"
            elif guard_result == "auto_flash" and "flash" not in model.lower():
                model = "deepseek-v4-flash"

        # 记录对话历史
        self._conversation_history.extend(messages)

        # ── 真实 API 调用 ──
        try:
            resp = self._client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=4096,
            )
        except Exception as e:
            # 降级重试：如果用的是 Pro 失败，用 Flash 再试
            if "flash" not in model.lower() and "turbo" not in model.lower():
                try:
                    fallback_model = "deepseek-v4-flash"
                    # 启用前缀缓存
                    resp = self._client.chat.completions.create(
                        model=fallback_model,
                        messages=messages,
                        temperature=0.7,
                        max_tokens=4096,
                        extra_body={"enable_prefix_cache": True},
                    )
                    model = fallback_model
                except Exception as e2:
                    error_msg = f"[LLM 调用失败] {e2}"
                    self._conversation_history.append(
                        {"role": "assistant", "content": error_msg}
                    )
                    return error_msg
            else:
                error_msg = f"[LLM 调用失败] {e}"
                self._conversation_history.append(
                    {"role": "assistant", "content": error_msg}
                )
                return error_msg

        content = resp.choices[0].message.content or ""
        usage = resp.usage

        # 记录花费
        if usage:
            pt = usage.prompt_tokens or 0
            ct = usage.completion_tokens or 0
            cost = self._estimate_cost(model, pt, ct)
            self._total_cost += cost
            self._total_tokens += pt + ct
            _GUARD.log_cost(model, cost, pt, ct)

        # 记录回复
        self._conversation_history.append({"role": "assistant", "content": content})

        return content

    def chat_with_fallback(self, messages: list[dict], preferred_model: str = None) -> str:
        """
        带逐级降级的聊天：Pro → Flash → 告知失败
        """
        models_to_try = []
        if preferred_model:
            models_to_try.append(preferred_model)
        models_to_try.extend(["deepseek-v4-pro", "deepseek-v4-flash"])

        last_error = None
        for model in models_to_try:
            try:
                return self.chat(messages, model=model)
            except Exception as e:
                last_error = e
                continue

        return f"[LLM 调用失败：全部模型不可用] {last_error}"

    # ───────── 分析 ──────────────────────────────────────────────────

    def analyze(self, text: str, analysis_type: str = "sentiment") -> dict:
        """
        分析文本，通过真实 LLM 返回结构化结果。
        """
        if not text or not text.strip():
            return {"error": "文本内容为空", "analysis_type": analysis_type}

        template = self.templates.get(analysis_type)
        if not template:
            raise ValueError(f"不支持的分析类型: {analysis_type}，支持: {list(self.templates.keys())}")

        # 构建提示
        if analysis_type == "sentiment":
            prompt = template.format(text=text)
        elif analysis_type == "classification":
            categories = self.config.get("categories", "技术/商业/学术/生活/其他")
            prompt = template.format(text=text, categories=categories)
        elif analysis_type == "extraction":
            fields = self.config.get("fields", "关键实体,日期,数量")
            prompt = template.format(text=text, fields=fields)
        elif analysis_type == "summary":
            style = self.config.get("summary_style", "简洁")
            instructions = self.config.get("summary_instructions", "保留关键信息，不超过200字")
            prompt = template.format(content=text, style=style, instructions=instructions)
        else:
            return {"error": f"未知分析类型: {analysis_type}"}

        # 调真实 LLM
        response = self.chat([
            {"role": "system", "content": "你是一个文本分析专家。始终输出严格的JSON格式。"},
            {"role": "user", "content": prompt},
        ], model="deepseek-v4-flash")

        # 尝试解析 JSON
        try:
            # 从回复中提取 JSON
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            # 直接解析
            return json.loads(response)
        except (json.JSONDecodeError, AttributeError):
            # LLM 返回了非 JSON，作为原始文本返回
            return {
                "raw_response": response,
                "analysis_type": analysis_type,
                "note": "LLM 返回非JSON格式，返回原始文本",
            }

    # ───────── 模板生成 ──────────────────────────────────────────────

    def generate(self, template_name: str, variables: dict) -> str:
        """使用模板和变量生成提示文本。"""
        template = self.templates.get(template_name)
        if not template:
            raise ValueError(f"未知模板: {template_name}，可用: {list(self.templates.keys())}")

        missing_vars = self._find_missing_vars(template, variables)
        if missing_vars:
            raise ValueError(f"模板「{template_name}」缺少变量: {missing_vars}")

        return template.format(**variables)

    def _find_missing_vars(self, template: str, variables: dict) -> list[str]:
        required = re.findall(r"\{(\w+)\}", template)
        return [v for v in required if v not in variables]

    # ───────── 流式聊天 ──────────────────────────────────────────────

    def stream_chat(self, messages: list[dict]) -> Generator[str, None, None]:
        """流式聊天 — 真实 API 流式调用"""
        model = self.default_model

        try:
            stream = self._client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=4096,
                stream=True,
            )
        except Exception as e:
            yield f"[流式调用失败] {e}"
            return

        full_response = ""
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                token = chunk.choices[0].delta.content
                full_response += token
                yield token

        yield "\n[stream_end]"

    # ───────── 工具方法 ──────────────────────────────────────────────

    def clear_history(self) -> None:
        self._conversation_history.clear()

    def get_history(self) -> list[dict]:
        return list(self._conversation_history)

    def get_cost(self) -> float:
        return self._total_cost

    def get_token_usage(self) -> int:
        return self._total_tokens

    def register_template(self, name: str, template_text: str) -> None:
        if not name or not template_text:
            raise ValueError("模板名称和内容不能为空")
        self.templates[name] = template_text

    def __repr__(self) -> str:
        return f"LLMClient(provider={self.provider}, model={self.default_model}, api_key={'*' * 8 + self.api_key[-4:] if self.api_key else '未配置'})"
