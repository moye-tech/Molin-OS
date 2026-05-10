"""
墨麟OS — 飞书互动卡片构建器 (Feishu Card Builder)
==================================================
对标飞书 Card Builder JSON API，替换全部 ASCII 分隔线。
生成飞书原生交互卡片 JSON，支持按钮、多列、分割线、备注等组件。

飞书卡片 JSON 协议: https://open.feishu.cn/document/uAjLw4CM/ukzMukzMukzM/feishu-cards/card-components

用法:
    from molib.infra.gateway.feishu_card_builder import FeishuCardBuilder
    
    card = FeishuCardBuilder()
    card.header("墨麟OS · CEO 简报", template="turquoise")
    card.divider()
    card.section("今日产出", "✅ 3篇内容已发布\n✅ 5条闲鱼消息已回复")
    card.table([
        {"子公司": "墨笔文创", "产出": 3, "状态": "✅"},
        {"子公司": "墨声客服", "产出": 5, "状态": "✅"},
    ])
    card.actions([
        {"text": "查看详情", "url": "https://...", "type": "primary"},
        {"text": "忽略", "type": "default"}
    ])
    
    json_output = card.build()
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Optional

# ═══════════════════════════════════════════════════════════════════
# 卡片颜色模板
# ═══════════════════════════════════════════════════════════════════
TEMPLATE_COLORS = {
    "blue": "blue",
    "wathet": "wathet",          # 浅蓝
    "turquoise": "turquoise",    # 青绿
    "green": "green",
    "yellow": "yellow",
    "orange": "orange",
    "red": "red",
    "carmine": "carmine",        # 胭脂红
    "violet": "violet",
    "purple": "purple",
    "indigo": "indigo",
    "grey": "grey",
    "default": None,             # 默认白色
}

# ═══════════════════════════════════════════════════════════════════
# 飞书卡片标签常量
# ═══════════════════════════════════════════════════════════════════
TAG_PLAIN_TEXT = "plain_text"
TAG_LARK_MD = "lark_md"
TAG_DIV = "div"
TAG_HR = "hr"
TAG_ACTION = "action"
TAG_BUTTON = "button"
TAG_NOTE = "note"
TAG_IMG = "img"
TAG_COLUMN_SET = "column_set"
TAG_COLUMN = "column"

# Lark MD 支持的富文本标签
# 粗体 **text**、斜体 *text*、删除线 ~~text~~、链接 [text](url)
# 颜色 <font color='red'>text</font>（red/green/blue/yellow/purple/grey）


class FeishuCardBuilder:
    """飞书互动卡片构建器。
    
    支持链式调用，最终 build() 返回飞书 Card JSON。
    """

    def __init__(self, wide_screen_mode: bool = True):
        self._config: dict[str, Any] = {
            "wide_screen_mode": wide_screen_mode,
            "enable_forward": True,
        }
        self._header: Optional[dict[str, Any]] = None
        self._elements: list[dict[str, Any]] = []

    # ── 基础组件 ──────────────────────────────────────────────

    def header(self, title: str, template: str = "turquoise") -> "FeishuCardBuilder":
        """设置卡片头部。
        
        Args:
            title: 标题文本，建议不超过 30 字
            template: 颜色模板名，见 TEMPLATE_COLORS
        """
        color = TEMPLATE_COLORS.get(template, TEMPLATE_COLORS["default"])
        header_obj: dict[str, Any] = {
            "title": {"tag": TAG_PLAIN_TEXT, "content": title},
        }
        if color:
            header_obj["template"] = color
        self._header = header_obj
        return self

    def divider(self, text: str = "") -> "FeishuCardBuilder":
        """添加分割线（可选文字）。"""
        elem: dict[str, Any] = {"tag": TAG_HR}
        if text:
            elem["text"] = {"tag": TAG_PLAIN_TEXT, "content": text}
        self._elements.append(elem)
        return self

    def section(self, title: str, content: str, markdown: bool = True) -> "FeishuCardBuilder":
        """添加文本段落。
        
        Args:
            title: 段落标题
            content: 正文内容
            markdown: True 使用 lark_md（支持粗体/链接/颜色），False 使用 plain_text
        """
        tag = TAG_LARK_MD if markdown else TAG_PLAIN_TEXT
        lines = []
        if title:
            lines.append(f"**{title}**")
        lines.append(content)
        self._elements.append({
            "tag": TAG_DIV,
            "text": {"tag": tag, "content": "\n".join(lines)},
        })
        return self

    def note(self, text: str) -> "FeishuCardBuilder":
        """添加备注文字（小号灰色）。"""
        self._elements.append({
            "tag": TAG_NOTE,
            "elements": [{"tag": TAG_PLAIN_TEXT, "content": text}],
        })
        return self

    def markdown(self, text: str) -> "FeishuCardBuilder":
        """添加富文本块（支持 Lark MD 语法）。"""
        self._elements.append({
            "tag": TAG_DIV,
            "text": {"tag": TAG_LARK_MD, "content": text},
        })
        return self

    # ── 复合组件 ──────────────────────────────────────────────

    def table(
        self,
        rows: list[dict[str, Any]],
        cols: Optional[list[str]] = None,
        title: str = "",
    ) -> "FeishuCardBuilder":
        """添加数据表格（多列布局模拟）。
        
        Args:
            rows: 行数据列表，每行为 {列名: 值, ...}
            cols: 列名顺序列表，不传则从第一行推断
            title: 可选的表格标题
        """
        if not rows:
            return self

        if cols is None:
            cols = list(rows[0].keys())

        if title:
            self._elements.append({
                "tag": TAG_DIV,
                "text": {"tag": TAG_LARK_MD, "content": f"**{title}**"},
            })

        # 每行构造一个 lark_md 文本行
        lines = []
        # 表头
        header_cells = [f"**{c}**" for c in cols]
        lines.append(" | ".join(header_cells))
        lines.append(" | ".join(["---"] * len(cols)))

        for row in rows:
            cells = [str(row.get(c, "")) for c in cols]
            lines.append(" | ".join(cells))

        self._elements.append({
            "tag": TAG_DIV,
            "text": {"tag": TAG_LARK_MD, "content": "\n".join(lines)},
        })
        return self

    def columns(self, *column_texts: str) -> "FeishuCardBuilder":
        """添加多列布局。
        
        Args:
            column_texts: 每列的 Lark MD 文本
        """
        col_elements = []
        for text in column_texts:
            col_elements.append({
                "tag": TAG_COLUMN,
                "width_mode": "weight",
                "elements": [{
                    "tag": TAG_DIV,
                    "text": {"tag": TAG_LARK_MD, "content": text},
                }],
            })

        self._elements.append({
            "tag": TAG_COLUMN_SET,
            "flex_mode": "bisect",
            "background_style": "default",
            "columns": col_elements,
        })
        return self

    def field_list(self, fields: list[tuple[str, str]]) -> "FeishuCardBuilder":
        """添加字段列表（key: value 对）。
        
        Args:
            fields: [(label, value), ...]
        """
        lines = []
        for label, value in fields:
            lines.append(f"**{label}:** {value}")
        self._elements.append({
            "tag": TAG_DIV,
            "text": {"tag": TAG_LARK_MD, "content": "\n".join(lines)},
        })
        return self

    def progress_bar(self, label: str, pct: float, color: str = "green") -> "FeishuCardBuilder":
        """添加进度条（文本模拟）。
        
        Args:
            label: 指标名称
            pct: 百分比 0.0-1.0
            color: 进度条颜色 red/green/blue/yellow
        """
        filled = int(pct * 20)
        empty = 20 - filled
        bar = "█" * filled + "░" * empty
        self._elements.append({
            "tag": TAG_DIV,
            "text": {
                "tag": TAG_LARK_MD,
                "content": f"**{label}**\n<font color='{color}'>{bar}</font>  {pct:.0%}",
            },
        })
        return self

    # ── 交互组件 ──────────────────────────────────────────────

    def actions(self, buttons: list[dict[str, str]]) -> "FeishuCardBuilder":
        """添加操作按钮组。
        
        Args:
            buttons: [{"text": "按钮文字", "type": "primary|default|danger", "url": "https://..."}, ...]
        """
        action_elements = []
        for btn in buttons:
            btn_type = btn.get("type", "default")
            btn_elem: dict[str, Any] = {
                "tag": TAG_BUTTON,
                "text": {"tag": TAG_PLAIN_TEXT, "content": btn["text"]},
                "type": btn_type,
            }
            if btn_type == "default":
                btn_elem["type"] = "default"
            if "url" in btn:
                btn_elem["url"] = btn["url"]
                btn_elem["multi_url"] = {"url": btn["url"]}
            if "value" in btn:
                btn_elem["value"] = json.dumps(btn["value"])
            action_elements.append(btn_elem)

        self._elements.append({
            "tag": TAG_ACTION,
            "actions": action_elements,
        })
        return self

    def image(self, img_key: str, alt: str = "", title: str = "") -> "FeishuCardBuilder":
        """添加图片（需先上传到飞书获取 img_key）。
        
        Args:
            img_key: 飞书图片 key
            alt: 替代文本
            title: 图片标题
        """
        img_elem: dict[str, Any] = {
            "tag": TAG_IMG,
            "img_key": img_key,
            "alt": {"tag": TAG_PLAIN_TEXT, "content": alt},
        }
        if title:
            img_elem["title"] = {"tag": TAG_PLAIN_TEXT, "content": title}
        self._elements.append(img_elem)
        return self

    # ── 预设模板 ──────────────────────────────────────────────

    def ceo_brief(
        self,
        date_str: str = "",
        highlights: list[str] = None,
        finance: dict[str, Any] = None,
        risks: list[str] = None,
        tasks: list[str] = None,
    ) -> "FeishuCardBuilder":
        """CEO 简报模板。
        
        Args:
            date_str: 日期（如 "2026-05-10"）
            highlights: 今日亮点列表
            finance: 财务数据 {"收入": ..., "支出": ..., "利润": ...}
            risks: 风险提示列表
            tasks: 待办任务列表
        """
        date_str = date_str or datetime.now().strftime("%Y-%m-%d")
        self.header(f"📊 墨麟OS · CEO 简报", template="turquoise")
        self.markdown(f"📅 {date_str} | 🤖 自动化生成")
        self.divider()

        # 亮点
        if highlights:
            items = "\n".join(f"• {h}" for h in highlights)
            self.section("🌟 今日亮点", items)

        # 财务
        if finance:
            self.divider()
            total_revenue = str(finance.get("revenue", finance.get("收入", "—")))
            total_cost = str(finance.get("cost", finance.get("支出", "—")))
            profit = str(finance.get("profit", finance.get("利润", "—")))
            self.columns(
                f"💰 收入\n**{total_revenue}**",
                f"📤 支出\n**{total_cost}**",
                f"📈 利润\n**{profit}**",
            )

        # 风险
        if risks:
            self.divider()
            items = "\n".join(f"⚠️ {r}" for r in risks)
            self.section("🔴 风险提示", items)

        # 待办
        if tasks:
            self.divider()
            items = "\n".join(f"{i+1}. {t}" for i, t in enumerate(tasks))
            self.section("📋 明日待办", items)

        self.divider()
        self.note(f"墨麟OS · CEO自动化 | 治理级别: L0/L1 自动执行 | {date_str}")
        return self

    def system_alert(self, level: str, title: str, detail: str, fix: str = "") -> "FeishuCardBuilder":
        """系统告警卡片。
        
        Args:
            level: 告警级别 error/warning/info
            title: 告警标题
            detail: 详细信息
            fix: 修复建议
        """
        emoji_map = {"error": "🚨", "warning": "⚠️", "info": "ℹ️"}
        color_map = {"error": "red", "warning": "orange", "info": "blue"}
        emoji = emoji_map.get(level, "📢")
        color = color_map.get(level, "default")

        self.header(f"{emoji} {title}", template=color)
        self.section("详情", detail)
        if fix:
            self.divider()
            self.section("💡 修复建议", fix)
        self.divider()
        self.note(f"墨麟OS · 系统告警 | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        return self

    def content_preview(self, title: str, platform: str, word_count: int, snippet: str) -> "FeishuCardBuilder":
        """内容预览卡片。
        
        Args:
            title: 内容标题
            platform: 发布平台
            word_count: 字数
            snippet: 内容片段
        """
        self.header(f"📝 {title}", template="wathet")
        self.field_list([
            ("平台", platform),
            ("字数", str(word_count)),
        ])
        self.divider()
        self.section("预览", snippet)
        return self

    def finance_report(
        self,
        period: str,
        revenue: float,
        cost: float,
        profit: float,
        top_items: list[dict[str, Any]],
    ) -> "FeishuCardBuilder":
        """财务报告卡片。
        
        Args:
            period: 报告期（如 "2026年5月"）
            revenue: 总收入
            cost: 总支出
            profit: 利润
            top_items: Top N 收支项 [{"name": ..., "amount": ...}, ...]
        """
        profit_rate = profit / revenue if revenue > 0 else 0
        self.header(f"💰 财务报告 · {period}", template="green")
        self.columns(
            f"📥 收入\n**¥{revenue:,.2f}**",
            f"📤 支出\n**¥{cost:,.2f}**",
            f"📊 利润率\n**{profit_rate:.1%}**",
        )
        if top_items:
            self.divider()
            self.table(
                [{"项目": it["name"], "金额": f"¥{it['amount']:,.2f}"} for it in top_items],
                title="Top 收支项",
            )
        self.divider()
        self.note(f"墨麟OS · 墨算财务自动生成 | {period}")
        return self

    def intel_summary(
        self,
        topic: str,
        sources: int,
        key_findings: list[str],
        trend: str = "",
    ) -> "FeishuCardBuilder":
        """情报摘要卡片。
        
        Args:
            topic: 情报主题
            sources: 情报源数量
            key_findings: 关键发现列表
            trend: 趋势判断
        """
        self.header(f"🔍 情报摘要 · {topic}", template="indigo")
        self.field_list([
            ("情报源", f"{sources} 个"),
            ("趋势", trend or "待评估"),
        ])
        self.divider()
        items = "\n".join(f"• {f}" for f in key_findings)
        self.section("关键发现", items)
        self.divider()
        self.note("墨麟OS · 墨研竞情自动采集")
        return self

    # ── 输出 ──────────────────────────────────────────────────

    def build(self) -> dict[str, Any]:
        """构建并返回飞书卡片 JSON。"""
        card: dict[str, Any] = {
            "config": self._config,
            "elements": self._elements,
        }
        if self._header:
            card["header"] = self._header
        return card

    def to_json(self, indent: int = 2) -> str:
        """返回格式化的 JSON 字符串。"""
        return json.dumps(self.build(), ensure_ascii=False, indent=indent)

    def to_message(self, msg_type: str = "interactive") -> dict[str, Any]:
        """返回适合飞书发送 API 的完整消息体。"""
        return {
            "msg_type": msg_type,
            "content": json.dumps(self.build(), ensure_ascii=False),
        }

    # ── 静态工厂 ──────────────────────────────────────────────

    @staticmethod
    def make_text_card(text: str) -> dict[str, Any]:
        """简单文本（纯文本，非卡片）——保留给简单场景。"""
        return {
            "msg_type": "text",
            "content": json.dumps({"text": text}, ensure_ascii=False),
        }


# ═══════════════════════════════════════════════════════════════════
# 便捷函数
# ═══════════════════════════════════════════════════════════════════


def card(*, wide_screen: bool = True) -> FeishuCardBuilder:
    """创建卡片的快捷入口。"""
    return FeishuCardBuilder(wide_screen_mode=wide_screen)


def ceo_brief_card(
    date_str: str = "",
    highlights: list[str] = None,
    finance: dict[str, Any] = None,
    risks: list[str] = None,
    tasks: list[str] = None,
) -> dict[str, Any]:
    """一键生成 CEO 简报卡片。"""
    return (
        FeishuCardBuilder()
        .ceo_brief(date_str, highlights, finance, risks, tasks)
        .build()
    )


def alert_card(level: str, title: str, detail: str, fix: str = "") -> dict[str, Any]:
    """一键生成告警卡片。"""
    return (
        FeishuCardBuilder()
        .system_alert(level, title, detail, fix)
        .build()
    )
