# SmartDispatcher COLLAB_RULES 路由模式

> 2026-05-11 — Open Design 集成时发现的关键路由行为

## 核心机制: 子串匹配

`_match_collab_rule()` 使用 Python 的 `in` 运算符匹配:

```python
def _match_collab_rule(self, task) -> list:
    desc = str(task.payload)  # 整个 payload 转字符串
    for kw, workers in self.COLLAB_RULES.items():
        if kw in desc:         # ← 子串匹配, 不是语义匹配
            return workers
```

## 陷阱: 词序敏感

```
✅ "网页设计" in "需要网页设计..."     → True  → ['designer']
❌ "网页设计" in "帮我设计网页..."     → False → 路由失败
```

**根因:** `"网页设计"` 不是 `"设计网页"` 的子串, 虽然语义相同。

## 修复: 双向关键词注册

```python
# ❌ 单方向 — 遗漏"设计网页"
"网页设计": ["designer"],

# ✅ 双方向 — 覆盖所有词序
"网页设计": ["designer"],
"设计网页": ["designer"],
```

## 最佳实践: COLLAB_RULES 设计原则

1. **双向覆盖**: 中文词序灵活, 常见变体都要加 keyword
2. **中英双语**: 同时注册中文和英文关键词
3. **短关键词优先**: `"PPT"` 比 `"帮我做PPT"` 命中率高
4. **避免过短**: `"设计"` 会误匹配"课程设计"/"Logo设计"等, 用具体词如 `"网页设计"`
5. **测试后部署**: 每次新增规则后用实际句子测试

## 本次新增的 Open Design 路由规则

```python
# ── v2.2 Open Design 集成 ──
"落地页":   ["designer"],
"landing":  ["designer"],
"仪表盘":   ["designer", "data_analyst"],
"dashboard": ["designer", "data_analyst"],
"PPT":      ["designer", "content_writer"],
"pitch":    ["designer", "content_writer"],
"网页设计": ["designer"],
"设计网页": ["designer"],   # ← 关键: 双向注册
"web设计":  ["designer"],
"UI设计":   ["designer"],
"原型":     ["designer"],
"品牌视觉": ["designer", "ip_manager"],
"定价页":   ["designer", "bd"],
"文档页":   ["designer", "knowledge"],
"博客":     ["content_writer", "designer"],
```

## 验证方法

```python
from molib.agencies.smart_dispatcher import SmartDispatcher
from molib.agencies.workers.base import Task

sd = SmartDispatcher()
tests = [
    ("设计网页", ["designer"]),
    ("网页设计", ["designer"]),
    ("落地页", ["designer"]),
]

for desc, expected in tests:
    task = Task(task_id='t', task_type='design', payload={'desc': desc})
    chain = sd._match_collab_rule(task)
    assert chain == expected, f"{desc} → {chain} (expected {expected})"
```
