"""墨麟OS — 飞书卡片基础构建模块

提供 CardBuilder 类和颜色常量、内部辅助函数。
"""
import json
import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger("molin.ceo.cards.builder")

# ── 颜色模板常量 ──
BLUE = "blue"
WATARI = "watari"
INDIGO = "indigo"
PURPLE = "purple"
RED = "red"
ORANGE = "orange"
YELLOW = "yellow"
GREEN = "green"
TURQUOISE = "turquoise"
GREY = "grey"


def _timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def _header(title: str, color: str = BLUE) -> dict:
    return {"title": {"tag": "plain_text", "content": title}, "template": color}


def _md(content: str) -> dict:
    return {"tag": "lark_md", "content": content}


def _div(content: str) -> dict:
    return {"tag": "div", "text": _md(content)}


def _row(fields: list[dict]) -> dict:
    return {"tag": "column_set", "flex_mode": "none", "background_style": "default", "columns": fields}


def _field(key: str, value: str, width: str = "weighted", weight: int = 1) -> dict:
    return {
        "tag": "column",
        "width": width,
        "weight": weight,
        "vertical_align": "top",
        "elements": [
            {"tag": "div", "text": {"tag": "lark_md", "content": f"**{key}**"}},
            {"tag": "div", "text": {"tag": "lark_md", "content": value}},
        ],
    }


def _hr() -> dict:
    return {"tag": "hr"}


def _note(text: str) -> dict:
    return {"tag": "note", "text": {"tag": "plain_text", "content": text}}


class CardBuilder:
    """飞书卡片构建器基类"""

    def __init__(self, title: str, color: str = BLUE):
        self.title = title
        self.color = color
        self.elements: list[dict] = []

    def add_div(self, content: str) -> "CardBuilder":
        self.elements.append(_div(content))
        return self

    def add_hr(self) -> "CardBuilder":
        self.elements.append(_hr())
        return self

    def add_field(self, key: str, value: str) -> "CardBuilder":
        self.elements.append({"tag": "div", "text": {"tag": "lark_md", "content": f"**{key}**  {value}"}})
        return self

    def add_fields_row(self, fields: list[tuple[str, str]]) -> "CardBuilder":
        """添加行内多列字段（最多4列）"""
        columns = [_field(k, v) for k, v in fields]
        self.elements.append(_row(columns))
        return self

    def add_section(self, title: str, items: list[str]) -> "CardBuilder":
        self.elements.append(_div(f"**{title}**"))
        for item in items:
            self.elements.append(_div(f"· {item}"))
        return self

    def add_button(self, text: str, url: str = "", type_: str = "default") -> "CardBuilder":
        btn: dict[str, Any] = {"tag": "action", "actions": [{"tag": "button", "text": {"tag": "plain_text", "content": text}, "type": type_}]}
        if url:
            btn["actions"][0]["url"] = url
        self.elements.append(btn)
        return self

    def add_note(self, text: str) -> "CardBuilder":
        self.elements.append(_note(text))
        return self

    def add_table(self, data: list[dict], max_rows: int = 20) -> "CardBuilder":
        """
        添加数据表格（缺口② — 表格→CardBuilder 转换）。

        将 [{\"col1\": \"val1\", \"col2\": \"val2\"}, ...] 渲染为
        飞书原生友好的结构化表格。

        Args:
            data: 表格数据，每行为一个 dict
            max_rows: 最大行数，超出截断并标注
        """
        if not data:
            return self

        # 提取表头（从第一行 dict 的 keys）
        headers = list(data[0].keys())
        header_text = " | ".join(f"**{h}**" for h in headers)
        self.elements.append(_div(header_text))
        self.elements.append(_hr())

        # 渲染数据行
        for i, row in enumerate(data[:max_rows]):
            cells = [str(row.get(h, "")) for h in headers]
            row_text = " | ".join(cells)
            self.elements.append(_div(row_text))

        if len(data) > max_rows:
            self.elements.append(_div(f"… 等共 {len(data)} 行（已截断显示前 {max_rows} 行）"))

        return self

    def build(self) -> dict:
        return {"config": {"wide_screen_mode": True}, "header": _header(self.title, self.color), "elements": self.elements}

    def build_json(self) -> str:
        return json.dumps(self.build(), ensure_ascii=False)


__all__ = [
    "CardBuilder",
    "BLUE", "WATARI", "INDIGO", "PURPLE", "RED", "ORANGE",
    "YELLOW", "GREEN", "TURQUOISE", "GREY",
    "_timestamp", "_header", "_md", "_div", "_row", "_field", "_hr", "_note",
]
