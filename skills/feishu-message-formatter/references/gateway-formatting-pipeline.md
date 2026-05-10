# 飞书网关消息格式化管道诊断

> 2026-05-10 诊断结论：Agent 层遵守 feishu-message-formatter 还不够，
> 网关层 `format_message()` 是空壳，Markdown 原文直通飞书。

## 发送链路

```
Agent 回复（可能含 Markdown）
  │
  ▼
FeishuAdapter.send()                    [feishu.py:1700]
  ├─ format_message()                   [feishu.py:2193]  ← 🐛 只是 str.strip()
  ├─ _build_outbound_payload()          [feishu.py:4177]
  │   ├─ 有 _MARKDOWN_HINT_RE → post 类型 {"tag":"md","text":"原文"}
  │   │   飞书 post 的 md 渲染器不支持表格、部分标题语法
  │   ├─ 有 _MARKDOWN_TABLE_RE → 强制 text 类型，原文直发
  │   │   纯文本消息不解析任何格式，# | ** 全是可见字符
  │   └─ 其他 → text 类型，原文直发
  └─ _strip_markdown_to_plain_text()    [feishu.py:512]
       ⚠️ 仅作 fallback（post 被拒时降级调用），不作为主格式化器
```

## 根因

`format_message()` (line 2193) 执行的是 `return content.strip()`。
没有任何 Markdown→纯文本转换。即使 Agent 严格遵守 feishu-message-formatter，
任何遗漏的 Markdown 也会原样出现在飞书中。

## 关键代码位置

| 位置 | 文件 | 行号 |
|------|------|------|
| format_message | hermes-agent/gateway/platforms/feishu.py | 2193 |
| _build_outbound_payload | 同上 | 4177 |
| _strip_markdown_to_plain_text | 同上 | 512 |
| strip_markdown (公共 helper) | gateway/platforms/helpers.py | 180 |
| _MARKDOWN_HINT_RE | feishu.py | 152-155 |
| _MARKDOWN_TABLE_RE | feishu.py | 158 |

## _MARKDOWN_HINT_RE 匹配范围

```python
_MARKDOWN_HINT_RE = re.compile(
    r"(^#{1,6}\s)|(^\s*[-*]\s)|(^\s*\d+\.\s)|(^\s*---+\s*$)|"
    r"(```)|(`[^`\n]+`)|(\*\*[^*\n].+?\*\*)|(~~[^~\n].+?~~)|"
    r"(<u>.+?</u>)|(\*[^*\n]+\*)|(\[[^\]]+\]\([^)]+\))|(^>\s)",
    re.MULTILINE,
)
```

匹配 Markdown 标记后消息以 `post` 类型发送（`{"tag":"md","text":"..."}`），
但飞书 post 渲染器对 `|表格|`、嵌套格式支持有限。

## _MARKDOWN_TABLE_RE 逻辑

表格消息强制 text 类型发送——因为飞书 post 的 md 元素不渲染表格。
但 text 类型让表格原文（`| col | col |`、`|---|---|`）直接可见。

## 修复方向

1. **网关层**（推荐第一优先）：改造 `format_message()`，
   对 text 类型消息自动调用 `_strip_markdown_to_plain_text()`，
   或实现 Markdown→飞书纯文本的结构化转换（表格→列表、标题→emoji+文字）
2. **Agent 层**：强化 persona 中对飞书格式的约束优先级
3. **Molin-OS 层**：`feishu_card_builder` 已经就绪，可用 Card 替代纯文本，
   但需要 Agent 主动使用

## 已验证的正常组件

- feishu-cli v1.23.0 @ `/usr/local/bin/feishu-cli` ✅
- Molin-OS 飞书模块全部可导入 ✅
- `feishu_card_builder` 11 方法 + 6 预设 ✅
- `feishu_noise_filter` 8 规则 + 13 测试 ✅
- Hermes 飞书网关 lark_oapi WS 连接正常 ✅
- `FEISHU_DRIVE_ARCHIVE_ENABLED=false`（未启用云端归档）⚠️
