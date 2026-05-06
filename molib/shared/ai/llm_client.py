"""
墨麟AIOS — LLMClient (大语言模型客户端)
参考 CowAgent 模块化 PromptBuilder + Google ADK Agent评估思路。
支持聊天、分析、模板生成、流式响应。
"""

import os
import json
import re
import hashlib
import time
import random
from typing import Optional, Generator
from pathlib import Path

# ───────── 模板仓库 ─────────
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
    支持provider抽象、多轮对话、分析任务、模板生成、流式响应。

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
        """
        self.provider = provider
        self.config = config or {}
        self.templates = {**DEFAULT_TEMPLATES, **(self.config.get("templates", {}))}

        # API配置
        self.api_key = self.config.get("api_key") or os.environ.get(
            f"{provider.upper()}_API_KEY", ""
        )
        self.base_url = self.config.get("base_url") or self._default_base_url()
        self.default_model = self.config.get("model") or self._default_model()
        self.timeout = self.config.get("timeout", 30)
        self.max_retries = self.config.get("max_retries", 3)

        # 对话历史
        self._conversation_history: list[dict] = []
        self._total_tokens_used = 0

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
            "deepseek": "deepseek-chat",
            "qwen": "qwen-plus",
            "openai": "gpt-4o-mini",
            "ollama": "llama3.1",
        }
        return models.get(self.provider, models["deepseek"])

    # ───────── 聊天 ─────────

    def chat(self, messages: list[dict], model: Optional[str] = None) -> str:
        """
        发送聊天消息并获取回复。

        支持消息格式：
        - {"role": "system", "content": "..."}
        - {"role": "user", "content": "..."}
        - {"role": "assistant", "content": "..."}

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

        # 记录对话历史
        self._conversation_history.extend(messages)

        # 模拟API调用（实际项目会使用requests/http调用）
        response = self._simulate_api_call(messages, model)

        # 记录回复
        self._conversation_history.append({"role": "assistant", "content": response})

        return response

    def _simulate_api_call(self, messages: list[dict], model: str) -> str:
        """
        模拟API调用。
        在真实部署中，此处应替换为实际的HTTP请求。
        """
        # 提取system提示
        system_msg = ""
        user_msg = ""
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            elif msg["role"] == "user":
                user_msg = msg["content"]

        # 简易token估算
        total_text = " ".join(m.get("content", "") for m in messages)
        token_estimate = max(1, len(total_text) // 2)
        self._total_tokens_used += token_estimate

        # 模拟不同模型的回复特征
        model_lower = model.lower()
        if "turbo" in model_lower:
            return f"[{model} 快速回复] 收到您的请求。{self._truncate_response(user_msg, 100)}"
        elif "max" in model_lower or "deepseek" in model_lower:
            return f"[{model} 深度分析] 基于您的输入，我进行了全面分析。{self._truncate_response(user_msg, 200)}"
        elif "vl" in model_lower:
            return f"[{model} 视觉分析] 已分析相关视觉内容。"
        else:
            return f"[{model} 回复] {self._truncate_response(user_msg, 150)}"

    def _truncate_response(self, text: str, max_len: int) -> str:
        """截断响应并添加合理回复。"""
        if len(text) > max_len:
            return text[:max_len] + "..."
        return f"已处理您的消息: \"{text}\""

    # ───────── 分析 ─────────

    def analyze(self, text: str, analysis_type: str = "sentiment") -> dict:
        """
        分析文本，返回结构化结果。

        Args:
            text: 待分析文本
            analysis_type: 分析类型
                - sentiment: 情感分析
                - classification: 文本分类
                - extraction: 信息抽取
                - summary: 摘要总结

        Returns:
            dict: 结构化分析结果
        """
        if not text or not text.strip():
            return {"error": "文本内容为空", "analysis_type": analysis_type}

        # 使用模板构建提示
        template = self.templates.get(analysis_type)
        if not template:
            raise ValueError(f"不支持的分析类型: {analysis_type}，支持: {list(self.templates.keys())}")

        if analysis_type == "sentiment":
            prompt = template.format(text=text)
            # 模拟情感分析
            return self._simulate_sentiment(text)
        elif analysis_type == "classification":
            categories = self.config.get("categories", "技术/商业/学术/生活/其他")
            prompt = template.format(text=text, categories=categories)
            return self._simulate_classification(text, categories)
        elif analysis_type == "extraction":
            fields = self.config.get("fields", "关键实体,日期,数量")
            prompt = template.format(text=text, fields=fields)
            return self._simulate_extraction(text, fields)
        elif analysis_type == "summary":
            style = self.config.get("summary_style", "简洁")
            instructions = self.config.get("summary_instructions", "保留关键信息，不超过200字")
            prompt = template.format(content=text, style=style, instructions=instructions)
            return self._simulate_summary(text, style)

        return {"error": f"未知分析类型: {analysis_type}"}

    def _simulate_sentiment(self, text: str) -> dict:
        """模拟情感分析。"""
        positive_words = ["好", "棒", "优秀", "喜欢", "满意", "great", "good", "excellent", "love", "happy"]
        negative_words = ["差", "坏", "糟糕", "讨厌", "失望", "bad", "terrible", "hate", "awful", "poor"]

        pos_count = sum(1 for w in positive_words if w in text.lower())
        neg_count = sum(1 for w in negative_words if w in text.lower())

        if pos_count > neg_count:
            sentiment = "positive"
            score = 0.5 + min(0.5, pos_count * 0.1)
        elif neg_count > pos_count:
            sentiment = "negative"
            score = 0.5 + min(0.5, neg_count * 0.1)
        else:
            sentiment = "neutral"
            score = 0.5

        return {
            "sentiment": sentiment,
            "score": round(score, 2),
            "confidence": round(score, 2),
            "key_points": [
                f"检测到{pos_count}个正面词, {neg_count}个负面词",
                f"文本长度: {len(text)}字",
            ],
            "analysis_type": "sentiment",
        }

    def _simulate_classification(self, text: str, categories: str) -> dict:
        """模拟文本分类。"""
        cat_list = [c.strip() for c in categories.split("/")]
        # 基于关键词简单分类
        text_lower = text.lower()
        for cat in cat_list:
            if cat.lower() in text_lower:
                return {
                    "category": cat,
                    "confidence": round(0.7 + random.random() * 0.25, 2),
                    "reason": f"文本包含分类关键词「{cat}」",
                    "analysis_type": "classification",
                }
        # 默认分类
        return {
            "category": cat_list[0] if cat_list else "未分类",
            "confidence": 0.4,
            "reason": "无明确分类信号，取默认分类",
            "analysis_type": "classification",
        }

    def _simulate_extraction(self, text: str, fields: str) -> dict:
        """模拟信息抽取。"""
        field_list = [f.strip() for f in fields.split(",")]
        result = {"analysis_type": "extraction", "extracted": {}}

        for field in field_list:
            # 简单实体抽取模拟
            if "实体" in field or "entity" in field.lower():
                entities = re.findall(r"[A-Z][a-z]+(?:\s[A-Z][a-z]+)*", text)
                result["extracted"][field] = entities[:5] if entities else ["未发现"]
            elif "日期" in field or "date" in field.lower():
                dates = re.findall(r"\d{4}[-/\.]\d{1,2}[-/\.]\d{1,2}|\d{1,2}月\d{1,2}日", text)
                result["extracted"][field] = dates[:3] if dates else ["未发现"]
            elif "数量" in field or "number" in field.lower():
                nums = re.findall(r"\b\d+[.,]?\d*\b", text)
                result["extracted"][field] = nums[:5] if nums else ["未发现"]
            else:
                result["extracted"][field] = f"已提取{field}信息"

        return result

    def _simulate_summary(self, text: str, style: str) -> dict:
        """模拟摘要生成。"""
        sentences = re.split(r'[。！？\n.!?]', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

        if not sentences:
            summary = "文本过短，无需摘要"
        elif style == "简洁":
            summary = sentences[0] if sentences else text[:50]
        elif style == "详细":
            summary = "；".join(sentences[:3]) if len(sentences) >= 3 else text[:100]
        else:
            summary = sentences[0] if sentences else text[:50]

        return {
            "summary": summary,
            "original_length": len(text),
            "summary_length": len(summary),
            "style": style,
            "analysis_type": "summary",
        }

    # ───────── 模板生成 ─────────

    def generate(self, template_name: str, variables: dict) -> str:
        """
        使用模板和变量生成提示文本。

        Args:
            template_name: 模板名称 (如 summary/sentiment/translate)
            variables: 模板变量字典

        Returns:
            str: 渲染后的提示文本
        """
        template = self.templates.get(template_name)
        if not template:
            raise ValueError(f"未知模板: {template_name}，可用: {list(self.templates.keys())}")

        # 检查变量完整性
        missing_vars = self._find_missing_vars(template, variables)
        if missing_vars:
            raise ValueError(f"模板「{template_name}」缺少变量: {missing_vars}")

        return template.format(**variables)

    def _find_missing_vars(self, template: str, variables: dict) -> list[str]:
        """查找模板中缺失的变量。"""
        required = re.findall(r"\{(\w+)\}", template)
        return [v for v in required if v not in variables]

    # ───────── 流式聊天 ─────────

    def stream_chat(self, messages: list[dict]) -> Generator[str, None, None]:
        """
        流式聊天 — 模拟逐块输出。

        Args:
            messages: 消息列表

        Yields:
            str: 逐块生成的回复片段
        """
        # 获取完整回复
        full_response = self.chat(messages)

        # 按token模拟流式输出
        words = full_response.split()
        chunk_size = max(1, len(words) // 10)

        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i + chunk_size])
            yield chunk
            time.sleep(0.05)  # 模拟网络延迟

        yield "\n[stream_end]"

    # ───────── 工具方法 ─────────

    def clear_history(self) -> None:
        """清空对话历史。"""
        self._conversation_history.clear()

    def get_history(self) -> list[dict]:
        """获取对话历史。"""
        return list(self._conversation_history)

    def get_token_usage(self) -> int:
        """获取累计token使用量。"""
        return self._total_tokens_used

    def register_template(self, name: str, template_text: str) -> None:
        """注册自定义模板。"""
        if not name or not template_text:
            raise ValueError("模板名称和内容不能为空")
        self.templates[name] = template_text

    def __repr__(self) -> str:
        return f"LLMClient(provider={self.provider}, model={self.default_model})"
