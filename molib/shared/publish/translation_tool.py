"""
墨麟AIOS 翻译工具 — TranslationTool
=====================================
提供多语言翻译、语言检测、术语表管理和翻译记忆检索能力。

参考项目：
- weblate (5.8K⭐): 多语言发布 + 翻译记忆库 + VCS 集成
  核心设计：组件化 MT 引擎抽象、翻译记忆模糊匹配、术语表管理
"""

import uuid
import hashlib
import re
from datetime import datetime
from typing import Any


class TranslationTool:
    """翻译与本地化工具。

    功能：
    - translate:      多语言翻译（zh → en/ja/ko/zh-TW）
    - detect_language: 语言检测
    - manage_glossary: 自定义术语表管理
    - tm_suggest:     翻译记忆检索（模糊匹配）
    """

    # ── 语言映射 ──────────────────────────────────────────────
    LANGUAGES = {
        "zh": "中文（简体）",
        "zh-TW": "中文（繁体）",
        "en": "English",
        "ja": "日本語",
        "ko": "한국어",
        "fr": "Français",
        "de": "Deutsch",
        "es": "Español",
        "pt": "Português",
        "ru": "Русский",
        "ar": "العربية",
        "th": "ไทย",
        "vi": "Tiếng Việt",
    }

    SUPPORTED_SOURCE = ["zh", "en", "ja", "ko"]
    SUPPORTED_TARGET = {
        "zh": ["en", "ja", "ko", "zh-TW", "fr", "de", "es"],
        "en": ["zh", "zh-TW", "ja", "ko", "fr", "de", "es", "pt", "ru"],
        "ja": ["zh", "en", "ko", "zh-TW"],
        "ko": ["zh", "en", "ja", "zh-TW"],
    }

    # ── 语言检测特征 ──────────────────────────────────────────
    LANG_PATTERNS = {
        "zh": {
            "chars": r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]",
            "threshold": 0.6,
        },
        "zh-TW": {
            "chars": r"[\u4e00-\u9fff]",
            "traditional_markers": r"[誌爲著裏戶匯與從]"  # 繁体特有字
        },
        "ja": {
            "chars": r"[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]",
            "hiragana": r"[\u3040-\u309f]",
            "katakana": r"[\u30a0-\u30ff]",
        },
        "ko": {
            "chars": r"[\uac00-\ud7af\u1100-\u11ff]",
        },
        "en": {
            "chars": r"[a-zA-Z]",
        },
    }

    def __init__(self, api_key: str | None = None):
        """
        Args:
            api_key: 可选的翻译服务 API 密钥
        """
        self.api_key = api_key or f"molib_tr_{hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:12]}"
        self._glossary: dict[str, dict] = {}          # 术语表: {term: {"translation": str, "lang": str, ...}}
        self._translation_memory: list[dict] = []     # 翻译记忆库
        self._history: list[dict] = []                # 翻译历史

    # ═══════════════════════════════════════════════════════════
    #  1. 多语言翻译
    # ═══════════════════════════════════════════════════════════

    def translate(
        self,
        text: str,
        source_lang: str = "zh",
        target_langs: str | list[str] = "en",
    ) -> dict:
        """多语言翻译。

        支持链式翻译和批量目标语言。
        内置模拟翻译引擎（含术语表优先匹配和翻译记忆检索）。

        Args:
            text: 待翻译文本
            source_lang: 源语言代码 (zh / en / ja / ko)
            target_langs: 目标语言代码或列表 (如 "en" 或 ["en", "ja", "ko"])

        Returns:
            dict: 包含 translations, source_info, usage 的结构化结果
        """
        translation_id = f"tr_{uuid.uuid4().hex[:12]}"
        now = datetime.now()

        # 校验语言
        if source_lang not in self.SUPPORTED_SOURCE:
            return {
                "id": translation_id,
                "status": "failed",
                "error": f"不支持的源语言: {source_lang}。支持: {self.SUPPORTED_SOURCE}",
                "timestamps": {"created": now.isoformat()},
            }

        if isinstance(target_langs, str):
            target_langs = [target_langs]

        # 校验目标语言
        valid_targets = self.SUPPORTED_TARGET.get(source_lang, [])
        invalid = [t for t in target_langs if t not in valid_targets]
        if invalid:
            return {
                "id": translation_id,
                "status": "failed",
                "error": f"不支持的翻译方向 {source_lang}→{invalid}。支持: {valid_targets}",
                "timestamps": {"created": now.isoformat()},
            }

        # 如果源语言为 zh，先进行繁简检测（zh ↔ zh-TW 特殊处理）
        if source_lang == "zh" and "zh-TW" in target_langs:
            target_langs = [l for l in target_langs if l != "zh-TW"]
            # zh-TW 会放在最后一起处理

        # 逐语言翻译
        translations = {}
        for target_lang in target_langs:
            result = self._translate_single(text, source_lang, target_lang)
            translations[target_lang] = result

        # 特殊处理 zh → zh-TW
        if "zh-TW" in target_langs or (source_lang in ("zh",) and any(
            t == "zh-TW" for t in target_langs
        )):
            translations["zh-TW"] = self._zh_to_traditional(
                text if source_lang == "zh" else translations.get("zh", {}).get("translated_text", text)
            )
        # 修正：如果传入了 zh-TW 但不在 target_langs 检查中
        if isinstance(target_langs, list) and "zh-TW" in target_langs:
            pass  # 已处理

        # 检测到的源语言（有可能用户标错）
        detected = self.detect_language(text)

        result = {
            "id": translation_id,
            "status": "completed",
            "source_text": text,
            "source_lang": source_lang,
            "detected_lang": detected,
            "target_langs": target_langs,
            "translations": translations,
            "word_count": len(text),
            "char_count": len(text),
            "meta": {
                "glossary_matches": self._count_glossary_matches(text),
                "tm_hits": self._count_tm_hits(text),
            },
            "timestamps": {
                "created": now.isoformat(),
                "completed": now.isoformat(),
            },
        }
        self._history.append(result)
        return result

    def _translate_single(self, text: str, source_lang: str, target_lang: str) -> dict:
        """单语言翻译引擎（模拟实现）。

        实际使用时可接入外部 MT 引擎（Google Translate / DeepL / OpenAI）。
        weblate 设计思路：通过统一的 MT 抽象层调用不同后端。
        """
        # Step 1: 术语表优先匹配
        glossary_applied = self._apply_glossary(text, source_lang, target_lang)

        # Step 2: 翻译记忆检索（模糊匹配，提升一致性）
        tm_matches = self.tm_suggest(text)
        best_match = tm_matches[0] if tm_matches else None

        # Step 3: 模拟翻译（实际项目中替换为真实引擎调用）
        translated = self._mock_translate(
            glossary_applied.get("text", text),
            source_lang,
            target_lang,
            best_match,
        )

        return {
            "translated_text": translated,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "confidence": self._calc_confidence(text, translated, best_match),
            "glossary_applied": glossary_applied["matches"],
            "tm_used": best_match is not None,
        }

    def _apply_glossary(self, text: str, source_lang: str, target_lang: str) -> dict:
        """应用术语表到文本"""
        matches = []
        result = text

        for term, entry in self._glossary.items():
            if entry.get("source_lang") == source_lang and entry.get("target_lang") == target_lang:
                if term.lower() in result.lower():
                    replacement = entry["translation"]
                    # 保留原大小写风格
                    idx = result.lower().find(term.lower())
                    if idx >= 0:
                        result = result[:idx] + replacement + result[idx + len(term):]
                        matches.append({
                            "term": term,
                            "replacement": replacement,
                            "position": idx,
                        })

        return {"text": result, "matches": matches}

    def _mock_translate(self, text: str, source: str, target: str, tm_match: dict | None = None) -> str:
        """模拟翻译引擎。

        当有翻译记忆命中且相似度足够高时，直接复用。
        否则使用基于规则的模拟翻译（仅用于原型/测试）。
        """
        # 如果有高质量翻译记忆匹配，直接复用
        if tm_match and tm_match.get("similarity", 0) >= 0.85:
            return tm_match["target_text"]

        # 模拟翻译字典（演示用）
        mock_dict = {
            ("zh", "en"): {
                "你好": "Hello",
                "谢谢": "Thank you",
                "发布": "Publish",
                "内容": "Content",
                "平台": "Platform",
                "翻译": "Translation",
                "记忆": "Memory",
                "工具": "Tool",
                "欢迎": "Welcome",
                "墨麟AIOS": "Molin AIOS",
            },
            ("zh", "ja"): {
                "你好": "こんにちは",
                "谢谢": "ありがとう",
                "发布": "公開",
                "内容": "コンテンツ",
                "平台": "プラットフォーム",
                "翻译": "翻訳",
                "记忆": "記憶",
                "工具": "ツール",
                "欢迎": "ようこそ",
                "墨麟AIOS": "墨麟AIOS",
            },
            ("zh", "ko"): {
                "你好": "안녕하세요",
                "谢谢": "감사합니다",
                "发布": "발행",
                "内容": "내용",
                "平台": "플랫폼",
                "翻译": "번역",
                "记忆": "기억",
                "工具": "도구",
                "欢迎": "환영합니다",
                "墨麟AIOS": "모린AIOS",
            },
            ("en", "zh"): {
                "Hello": "你好",
                "Thank you": "谢谢",
                "Publish": "发布",
                "Content": "内容",
                "Platform": "平台",
                "Translation": "翻译",
                "Memory": "记忆",
                "Tool": "工具",
                "Welcome": "欢迎",
                "Molin AIOS": "墨麟AIOS",
            },
        }

        key = (source, target)
        dictionary = mock_dict.get(key, {})

        result = text
        for src_word, tgt_word in dictionary.items():
            result = result.replace(src_word, tgt_word)

        # 如果没有匹配到任何词，返回原文 + 标注
        if result == text:
            result = f"[{target}] {text}"

        return result

    def _calc_confidence(self, source: str, translated: str, tm_match: dict | None = None) -> float:
        """计算翻译置信度"""
        if tm_match and tm_match.get("similarity", 0) >= 0.85:
            return min(1.0, tm_match["similarity"] + 0.1)

        # 基于翻译前后变化的词数比估算
        if translated.startswith("[") and "]" in translated:
            return 0.3  # 未命中任何词，低置信度

        # 简单估算：替换的词越多，置信度越高
        source_words = set(source.lower().split())
        target_words = set(translated.lower().split())
        if not source_words:
            return 0.5
        overlap = len(source_words & target_words)
        ratio = 1.0 - (overlap / max(len(source_words), 1))
        return min(0.95, max(0.3, ratio))

    def _count_glossary_matches(self, text: str) -> int:
        """统计术语匹配数"""
        count = 0
        for term in self._glossary:
            if term.lower() in text.lower():
                count += 1
        return count

    def _count_tm_hits(self, text: str) -> int:
        """统计翻译记忆命中数"""
        hits = 0
        for entry in self._translation_memory:
            sim = self._text_similarity(text, entry.get("source_text", ""))
            if sim >= 0.6:
                hits += 1
        return hits

    # ═══════════════════════════════════════════════════════════
    #  2. 语言检测
    # ═══════════════════════════════════════════════════════════

    def detect_language(self, text: str) -> str:
        """检测文本语言。

        基于字符特征 + 关键词匹配的多策略检测。

        Args:
            text: 待检测文本

        Returns:
            str: 语言代码 (zh / en / ja / ko / zh-TW / unknown)
        """
        if not text or not text.strip():
            return "unknown"

        text_clean = text.strip()

        # ── 策略1: 字符特征检测 ──
        scores = {}
        total_chars = len([c for c in text_clean if not c.isspace()])

        for lang_code, patterns in self.LANG_PATTERNS.items():
            if "chars" in patterns:
                matches = len(re.findall(patterns["chars"], text_clean))
                scores[lang_code] = matches / max(total_chars, 1)

        # ── 策略2: 区分 zh 和 zh-TW ──
        if scores.get("zh", 0) > 0.3:
            # 检查繁体字特征
            tw_markers = re.findall(
                self.LANG_PATTERNS["zh-TW"]["traditional_markers"],
                text_clean,
            )
            if len(tw_markers) >= 2:
                scores["zh-TW"] = scores.get("zh", 0) + 0.2

        # ── 策略3: 区分 ja 和 zh（日文包含汉字但含假名） ──
        if scores.get("ja", 0) > 0.3 and scores.get("zh", 0) > 0.3:
            hiragana = len(re.findall(self.LANG_PATTERNS["ja"]["hiragana"], text_clean))
            katakana = len(re.findall(self.LANG_PATTERNS["ja"]["katakana"], text_clean))
            kana_ratio = (hiragana + katakana) / max(total_chars, 1)
            if kana_ratio > 0.15:
                scores["ja"] += kana_ratio
            else:
                scores["zh"] += 0.1

        # ── 取最高分 ──
        if not scores:
            # 兜底：检查是否纯 ASCII
            if all(ord(c) < 128 for c in text_clean if not c.isspace()):
                return "en"
            return "unknown"

        best_lang = max(scores, key=scores.get)
        best_score = scores[best_lang]

        if best_score < 0.2:
            # 无明显特征，检查是否英文
            en_chars = len(re.findall(r"[a-zA-Z]", text_clean))
            en_ratio = en_chars / max(total_chars, 1)
            if en_ratio > 0.5:
                return "en"
            return "unknown"

        return best_lang

    # ═══════════════════════════════════════════════════════════
    #  3. 术语表管理
    # ═══════════════════════════════════════════════════════════

    def manage_glossary(
        self,
        term: str,
        translation: str,
        action: str = "add",
        source_lang: str = "zh",
        target_lang: str = "en",
        category: str = "general",
    ) -> dict:
        """自定义术语表管理。

        参考 weblate 术语表管理设计：
        - 支持增/删/改/查操作
        - 按语言对分组
        - 可分类管理

        Args:
            term: 源语言术语
            translation: 目标语言翻译
            action: 操作类型 (add / update / delete / get)
            source_lang: 源语言
            target_lang: 目标语言
            category: 分类标签

        Returns:
            dict: 操作结果与当前术语表状态
        """
        action = action.lower().strip()
        glossary_id = f"gl_{hashlib.md5(f'{term}:{source_lang}:{target_lang}'.encode()).hexdigest()[:12]}"
        now = datetime.now()

        if action == "add":
            if glossary_id in self._glossary:
                return {
                    "id": glossary_id,
                    "status": "exists",
                    "message": f"术语 '{term}'  (ID: {glossary_id}) 已存在，使用 update 更新",
                    "term": term,
                    "existing_entry": self._glossary[glossary_id],
                }

            self._glossary[glossary_id] = {
                "id": glossary_id,
                "term": term,
                "translation": translation,
                "source_lang": source_lang,
                "target_lang": target_lang,
                "category": category,
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
                "usage_count": 0,
            }
            return {
                "id": glossary_id,
                "status": "added",
                "message": f"术语 '{term}' → '{translation}' 已添加 ({source_lang}→{target_lang})",
                "entry": self._glossary[glossary_id],
                "glossary_size": len(self._glossary),
            }

        elif action == "update":
            if glossary_id not in self._glossary:
                return {
                    "id": glossary_id,
                    "status": "not_found",
                    "message": f"术语 '{term}' 不存在，请先 add",
                }
            self._glossary[glossary_id].update({
                "translation": translation,
                "category": category,
                "updated_at": now.isoformat(),
            })
            return {
                "id": glossary_id,
                "status": "updated",
                "message": f"术语 '{term}' 已更新为 '{translation}'",
                "entry": self._glossary[glossary_id],
            }

        elif action == "delete":
            if glossary_id not in self._glossary:
                return {
                    "id": glossary_id,
                    "status": "not_found",
                    "message": f"术语 '{term}' 不存在",
                }
            removed = self._glossary.pop(glossary_id)
            return {
                "id": glossary_id,
                "status": "deleted",
                "message": f"术语 '{term}' 已删除",
                "removed_entry": removed,
                "glossary_size": len(self._glossary),
            }

        elif action == "get":
            if glossary_id in self._glossary:
                return {
                    "id": glossary_id,
                    "status": "found",
                    "entry": self._glossary[glossary_id],
                }
            # 模糊搜索
            matches = []
            for gid, entry in self._glossary.items():
                if term.lower() in entry["term"].lower() or translation.lower() in entry["translation"].lower():
                    matches.append(entry)
            return {
                "id": glossary_id,
                "status": "search_results",
                "query": {"term": term, "translation": translation, "source_lang": source_lang, "target_lang": target_lang},
                "matches": matches,
                "total_matches": len(matches),
            }

        else:
            return {
                "status": "failed",
                "error": f"不支持的操作: {action}。支持: add / update / delete / get",
            }

    def get_glossary(
        self,
        source_lang: str | None = None,
        target_lang: str | None = None,
        category: str | None = None,
    ) -> dict:
        """查询术语表。

        Args:
            source_lang: 按源语言筛选
            target_lang: 按目标语言筛选
            category: 按分类筛选

        Returns:
            dict: 符合条件的术语列表和统计
        """
        entries = list(self._glossary.values())

        if source_lang:
            entries = [e for e in entries if e["source_lang"] == source_lang]
        if target_lang:
            entries = [e for e in entries if e["target_lang"] == target_lang]
        if category:
            entries = [e for e in entries if e["category"] == category]

        return {
            "total": len(entries),
            "entries": entries,
            "filters": {
                "source_lang": source_lang,
                "target_lang": target_lang,
                "category": category,
            },
        }

    # ═══════════════════════════════════════════════════════════
    #  4. 翻译记忆检索
    # ═══════════════════════════════════════════════════════════

    def tm_suggest(self, text: str, top_k: int = 5) -> list[dict]:
        """翻译记忆检索。

        参考 weblate 翻译记忆库设计：
        - 基于文本相似度模糊匹配
        - 返回按相似度排序的候选项
        - 匹配度低于 0.3 的不返回

        Args:
            text: 源文本
            top_k: 最多返回结果数 (默认 5)

        Returns:
            list[dict]: 按相似度降序排列的记忆条目，每项包含:
                - source_text: 源文本
                - target_text: 目标文本
                - source_lang: 源语言
                - target_lang: 目标语言
                - similarity: 相似度 (0-1)
                - context: 上下文标签
        """
        if not text or not self._translation_memory:
            return []

        scored: list[tuple[float, dict]] = []

        for entry in self._translation_memory:
            sim = self._text_similarity(text, entry.get("source_text", ""))
            if sim >= 0.3:  # 最低匹配阈值
                scored.append((sim, {
                    "source_text": entry.get("source_text", ""),
                    "target_text": entry.get("target_text", ""),
                    "source_lang": entry.get("source_lang", "zh"),
                    "target_lang": entry.get("target_lang", "en"),
                    "similarity": round(sim, 4),
                    "context": entry.get("context", ""),
                    "entry_id": entry.get("id", ""),
                }))

        # 降序排列
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[:top_k]]

    def add_to_tm(
        self,
        source_text: str,
        target_text: str,
        source_lang: str = "zh",
        target_lang: str = "en",
        context: str = "",
    ) -> dict:
        """向翻译记忆库添加条目。

        Args:
            source_text: 源文本
            target_text: 目标文本
            source_lang: 源语言
            target_lang: 目标语言
            context: 上下文标签

        Returns:
            dict: 添加结果
        """
        entry_id = f"tm_{uuid.uuid4().hex[:12]}"
        now = datetime.now()

        entry = {
            "id": entry_id,
            "source_text": source_text,
            "target_text": target_text,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "context": context,
            "created_at": now.isoformat(),
            "usage_count": 0,
        }
        self._translation_memory.append(entry)
        return {
            "status": "added",
            "entry": entry,
            "tm_size": len(self._translation_memory),
        }

    def _text_similarity(self, text_a: str, text_b: str) -> float:
        """计算两段文本的相似度。

        使用以下策略综合评分：
        1. 精确匹配（完全相同）
        2. 子串匹配
        3. 词袋 Jaccard 相似度
        4. 字符 n-gram 重叠

        Args:
            text_a, text_b: 待比较的文本

        Returns:
            float: 0-1 的相似度
        """
        if not text_a or not text_b:
            return 0.0

        a = text_a.lower().strip()
        b = text_b.lower().strip()

        # 精确匹配
        if a == b:
            return 1.0

        # 子串匹配
        if a in b or b in a:
            short_len = min(len(a), len(b))
            long_len = max(len(a), len(b))
            if long_len > 0:
                return round(short_len / long_len, 4)

        # Jaccard 相似度（词袋）
        words_a = set(a.split())
        words_b = set(b.split())
        if not words_a or not words_b:
            # 单字词，用字符 Jaccard
            chars_a, chars_b = set(a), set(b)
            intersection = chars_a & chars_b
            union = chars_a | chars_b
            return len(intersection) / max(len(union), 1)

        intersection = words_a & words_b
        union = words_a | words_b
        jaccard = len(intersection) / max(len(union), 1)

        # 字符 bigram 重叠
        bigram_a = set(a[i:i + 2] for i in range(len(a) - 1))
        bigram_b = set(b[i:i + 2] for i in range(len(b) - 1))
        if bigram_a and bigram_b:
            bigram_overlap = len(bigram_a & bigram_b) / max(len(bigram_a | bigram_b), 1)
        else:
            bigram_overlap = 0

        # 综合评分（权重可调）
        combined = 0.6 * jaccard + 0.4 * bigram_overlap
        return round(min(1.0, combined), 4)

    def get_tm_stats(self) -> dict:
        """获取翻译记忆库统计信息。

        Returns:
            dict: 条目数、语言对覆盖等统计
        """
        if not self._translation_memory:
            return {"total_entries": 0, "language_pairs": {}, "recent_entries": []}

        lang_pairs: dict[str, int] = {}
        for entry in self._translation_memory:
            pair = f"{entry.get('source_lang', '?')}→{entry.get('target_lang', '?')}"
            lang_pairs[pair] = lang_pairs.get(pair, 0) + 1

        recent = sorted(
            self._translation_memory,
            key=lambda e: e.get("created_at", ""),
            reverse=True,
        )[:10]

        return {
            "total_entries": len(self._translation_memory),
            "language_pairs": lang_pairs,
            "recent_entries": [
                {
                    "id": e["id"],
                    "source_text": e["source_text"][:50],
                    "target_text": e["target_text"][:50],
                    "lang_pair": f"{e['source_lang']}→{e['target_lang']}",
                    "created_at": e["created_at"],
                }
                for e in recent
            ],
        }

    # ═══════════════════════════════════════════════════════════
    #  内部工具
    # ═══════════════════════════════════════════════════════════

    def _zh_to_traditional(self, text: str) -> str:
        """简体中文 → 繁体中文（模拟转换）。

        真实环境应使用 OpenCC 或类似库。
        """
        # 常用简繁对照表（演示用）
        simple_to_traditional = {
            "发": "發",
            "布": "佈",
            "内": "內",
            "容": "容",
            "翻": "翻",
            "译": "譯",
            "记": "記",
            "忆": "憶",
            "工": "工",
            "具": "具",
            "欢": "歡",
            "迎": "迎",
            "墨": "墨",
            "麟": "麟",
            "对": "對",
            "应": "應",
            "转": "轉",
            "换": "換",
            "用": "用",
            "户": "戶",
            "设": "設",
            "置": "置",
            "管": "管",
            "理": "理",
            "数": "數",
            "据": "據",
            "统": "統",
            "计": "計",
            "语": "語",
            "言": "言",
            "检": "檢",
            "测": "測",
            "术": "術",
            "语": "語",
            "表": "表",
            "搜": "搜",
            "索": "索",
            "实": "實",
            "验": "驗",
            "区": "區",
            "别": "別",
            "应": "應",
            "该": "該",
            "这": "這",
            "那": "那",
            "的": "的",
            "了": "了",
            "和": "和",
            "是": "是",
            "不": "不",
            "在": "在",
            "有": "有",
            "人": "人",
            "大": "大",
            "小": "小",
            "上": "上",
            "下": "下",
            "为": "為",
            "与": "與",
            "及": "及",
            "以": "以",
            "可": "可",
            "以": "以",
            "能": "能",
            "会": "會",
            "还": "還",
            "被": "被",
            "把": "把",
            "从": "從",
            "到": "到",
            "让": "讓",
            "给": "給",
            "看": "看",
            "说": "說",
            "叫": "叫",
            "问": "問",
            "答": "答",
            "写": "寫",
            "读": "讀",
            "学": "學",
            "习": "習",
            "时": "時",
            "间": "間",
            "日": "日",
            "期": "期",
            "年": "年",
            "月": "月",
            "星": "星",
            "期": "期",
            "现": "現",
            "在": "在",
            "开": "開",
            "关": "關",
            "启": "啟",
            "用": "用",
            "帮": "幫",
            "助": "助",
            "支": "支",
            "持": "持",
            "版": "版",
            "本": "本",
            "号": "號",
            "码": "碼",
            "件": "件",
            "文": "文",
            "件": "件",
            "目": "目",
            "录": "錄",
            "路": "路",
            "径": "徑",
            "源": "源",
            "代": "代",
            "码": "碼",
            "网": "網",
            "页": "頁",
            "链": "鏈",
            "接": "接",
            "图": "圖",
            "片": "片",
            "视": "視",
            "频": "頻",
            "音": "音",
            "频": "頻",
            "文": "文",
            "本": "本",
            "格": "格",
            "式": "式",
            "字": "字",
            "体": "體",
            "颜": "顏",
            "色": "色",
            "大": "大",
            "小": "小",
            "位": "位",
            "置": "置",
            "坐": "座",
            "标": "標",
            "线": "線",
            "面": "面",
            "点": "點",
            "击": "擊",
            "选": "選",
            "择": "擇",
            "输": "輸",
            "入": "入",
            "输": "輸",
            "出": "出",
            "打": "打",
            "印": "印",
            "显": "顯",
            "示": "示",
            "隐": "隱",
            "藏": "藏",
            "保": "保",
            "存": "存",
            "删": "刪",
            "除": "除",
            "修": "修",
            "改": "改",
            "复": "複",
            "制": "制",
            "粘": "黏",
            "贴": "貼",
            "拖": "拖",
            "动": "動",
            "放": "放",
            "大": "大",
            "缩": "縮",
            "小": "小",
        }

        result = []
        for char in text:
            result.append(simple_to_traditional.get(char, char))
        return "".join(result)

    def get_translation_history(
        self,
        limit: int = 20,
        source_lang: str | None = None,
    ) -> list[dict]:
        """获取翻译历史。

        Args:
            limit: 最大返回条数
            source_lang: 按源语言筛选

        Returns:
            list[dict]: 翻译历史记录
        """
        history = self._history
        if source_lang:
            history = [h for h in history if h.get("source_lang") == source_lang]
        return history[-limit:]
