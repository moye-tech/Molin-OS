# 墨麟OS v2.0 升级工作流

> 经验来源: 2026-05-10 — molin-os-ultra.zip + molin-os-upgrade-plan.html

## 升级流程（五步法）

### Step 1: 结构对照
解压升级包，与当前 molib/ 做目录级 diff：
```python
ultra_dirs = {d for d in Path("/tmp/ultra").rglob("*") if d.is_dir()}
current_dirs = {d for d in Path("~/Molin-OS/molib").rglob("*") if d.is_dir()}
new = ultra_dirs - current_dirs
missing = current_dirs - ultra_dirs
```

### Step 2: 增量注入
不要全量替换——只复制当前没有的目录和文件：
```bash
# 仅复制新模块
cp -r /tmp/ultra/infra ~/Molin-OS/molib/infra
cp -r /tmp/ultra/integrations ~/Molin-OS/molib/integrations
cp -r /tmp/ultra/core/ceo ~/Molin-OS/molib/core/ceo
```

### Step 3: 导入路径批量修复
升级包的代码通常用相对导入（`from agencies.`），需修复为 molib 前缀：
```python
import re
fixes = {
    r'from agencies\.': 'from molib.agencies.',
    r'from core\.': 'from molib.core.',
    r'from infra\.': 'from molib.infra.',
    r'from integrations\.': 'from molib.integrations.',
    r'from utils\.': 'from molib.utils.',
}
for py_file in base.rglob("*.py"):
    content = py_file.read_text()
    modified = False
    for old, new in fixes.items():
        if re.search(old, content):
            content = re.sub(old, new, content)
            modified = True
    if modified:
        py_file.write_text(content)
```

### Step 4: __init__.py 补全
升级包解压后很多子目录缺少 __init__.py，批量创建：
```python
for d in base.rglob("*"):
    if d.is_dir() and not d.name.startswith("__"):
        (d / "__init__.py").touch()
```

### Step 5: 重依赖延迟导入
infra/ceo 等层依赖 redis、fastapi、aiosqlite 等可能未安装的包。
在 __init__.py 中不主动导入，改为 `# 延迟导入` 注释：
```python
# __init__.py
"""模块名 — 延迟导入"""
```

## 常见陷阱

### 嵌套目录 (infra/infra/)
cp -r 拷贝时如果目标目录已存在，会产生嵌套：
```
cp -r /tmp/molin/infra ~/Molin-OS/molib/infra
# 结果: ~/Molin-OS/molib/infra/infra/  ← 嵌套！
```
修复：`rm -rf 嵌套目录 && cp -r 源 目标/`

### 升级方案 HTML 含内嵌代码
升级方案通常以 HTML 形式提供，代码内嵌在 `<pre>` 标签中。
直接从 HTML 提取代码块，不需要整体解析。

### 不要全量替换 molib
molib 是 pip editable install 的入口，__main__.py 和 CLI 不能动。
只注入新模块到现有 molib/ 子目录下。

## v2.0 六大核心模块

| 模块 | 文件 | 解决BUG |
|:-----|:-----|:--------|
| ExperienceVault | shared/experience/vault.py | BUG-01 经验黑洞 |
| SmartWorkerMixin | workers/smart_mixin.py | BUG-03,04 |
| SmartDispatcher | agencies/smart_dispatcher.py | BUG-02 |
| WorkerChain+ContextBus | agencies/worker_chain.py | BUG-04,05 |
| PlanningBridge | agencies/planning_bridge.py | BUG-06 |
| ContentWriter升级 | workers/content_writer.py | BUG-04示范 |

## 验证清单

```bash
python3 -c "
from molib.shared.experience.vault import vault
from molib.agencies.workers.smart_mixin import SmartSubsidiaryWorker
from molib.agencies.smart_dispatcher import smart_dispatcher
from molib.agencies.worker_chain import WorkerChain
from molib.agencies.planning_bridge import PlanningBridge
print('✅ v2.0 core')
"
```
