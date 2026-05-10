# Worker v2.0 Migration Pattern — 批量升级 + 协作注入

> 来源: 2026-05-10 整改报告执行会话
> 触发: Molin-OS v2.0 六大模块落地，24个Worker需批量迁移

## 迁移模式

### Step 1: 修复基类兼容性

Python 3.11 不支持 `TypeVar | dict` 语法。必须在 `workers/base.py` 最开头加 `from __future__ import annotations`。

```python
# ✅ 正确 — __future__ 必须紧跟 docstring，在所有 import 之前
"""docstring"""
from __future__ import annotations
from abc import ABC, abstractmethod
```

**检查命令:**
```bash
grep -n "from __future__" molib/agencies/workers/base.py
# 必须输出: 2:from __future__ import annotations
```

### Step 2: 批量迁移基类

每个Worker改两处:
1. import: `from .base import SubsidiaryWorker` → `from .base import SmartSubsidiaryWorker as _Base`
2. class: `class Foo(SubsidiaryWorker):` → `class Foo(_Base):`

**批量脚本模式** (使用 Python 在文件内替换):
```python
# 用 Python 写迁移脚本，避免 bash 转义地狱
import re, pathlib

for f in worker_files:
    content = f.read_text()
    content = re.sub(
        r'from \.base import SubsidiaryWorker',
        'from .base import SmartSubsidiaryWorker as _Base',
        content
    )
    content = re.sub(
        r'class (\w+)\(SubsidiaryWorker\):',
        r'class \1(_Base):',
        content
    )
    f.write_text(content)
```

**注意点:** 如果文件使用 `from molib.agencies.workers.base import ...` 完整路径，也要匹配。

### Step 3: 处理边缘案例

`order_worker.py` 使用了 `class OrderWorker(_Base)` 但 `_Base` 未定义 — 因为之前就没有 import。需手动补:
```python
from molib.agencies.workers.base import SmartSubsidiaryWorker, Task, WorkerResult
class OrderWorker(SmartSubsidiaryWorker):
```

### Step 4: 全量导入验证

```bash
cd /Users/moye/Molin-OS
for w in content_writer research designer short_video ecommerce \
         customer_service education developer ops security finance \
         bd global_marketing legal knowledge data_analyst ip_manager \
         voice_actor auto_dream trading scrapling_worker router9 \
         order_worker cocoindex_sync; do
    python -c "from molib.agencies.workers.$w import *; print('OK', '$w')" 2>&1 | grep -E "OK|FAIL"
done
```

**预期:** 24/24 OK。

### Step 5: 验证继承链

```bash
python -c "
from molib.agencies.workers.content_writer import ContentWriter
cw = ContentWriter()
print('MRO:', [c.__name__ for c in type(cw).__mro__])
print('smart_execute:', hasattr(cw, 'smart_execute'))
print('request_collaboration:', hasattr(cw, 'request_collaboration'))
"
```

**预期MRO:** ContentWriter → SmartSubsidiaryWorker → SmartWorkerMixin → SubsidiaryWorker → ABC → object

## 协作注入模式

迁移后Worker获得了 `smart_execute` 和 `request_collaboration` 能力，但需要**在 execute() 中主动使用**。

### 三路上下文注入 (所有核心Worker)

```python
async def execute(self, task, context=None):
    # ① Pre-flight 经验 (SmartWorkerMixin 自动注入)
    exp_hint = (context or {}).get("exp_hint", "")
    # ② WorkerChain 上游上下文
    chain_ctx = task.payload.get("__context__", "")
    
    # ... 注入到 system prompt ...
```

### 主动协作 (按Worker角色)

```python
# Research → 被ContentWriter/Designer/ShortVideo调用 (trend_scan)
# Designer → 营销设计时调Research获取趋势
# ShortVideo → 调Research热词 + VoiceActor配音建议
# Ecommerce → 商品上架调ContentWriter优化描述

# 协作调用的标准写法:
try:
    r = await self.request_collaboration(
        "research",
        {"action": "trend_scan", "topic": topic, "platform": platform}
    )
    trend_ctx = r.get("summary", "") if isinstance(r, dict) else ""
except Exception:
    pass  # 协作失败不阻塞主流程
```

### 被调用Worker需实现的 action

当Worker被 `request_collaboration` 调用时，需要支持对应的 action:

| 被调用Worker | 需要支持的action | 调用方 |
|-------------|-----------------|--------|
| research | trend_scan | ContentWriter, Designer, ShortVideo |
| content_writer | (标准execute) | Ecommerce |
| voice_actor | recommend_voice | ShortVideo |

## Patch 工具多匹配问题

当 patch 脚本对含有大量重复结构的文件(如 ecommerce.py 有 7+ 个 `elif action == "xxx":` 分支)进行替换时，patch 工具可能匹配到多个位置。

**解决方案:** 使用包含足够唯一上下文的 old_string，至少要包含前后 3-5 行。如果仍然多匹配，将上下文扩展到包含独特的注释或变量名。

**触发条件识别:** 如果某个 Worker 的 execute() 方法是 action-dispatch 模式 (if/elif 链)，patch 时要注意每行结构高度相似。

## 验证清单

- [ ] base.py `from __future__` 在第 1-2 行
- [ ] 所有Worker从 `SmartSubsidiaryWorker` 继承
- [ ] 24/24 导入通过
- [ ] MRO 链包含 SmartWorkerMixin
- [ ] smart_execute 和 request_collaboration 可用
- [ ] 核心Worker (research/designer/short_video/ecommerce) 有协作调用
- [ ] git commit + push
