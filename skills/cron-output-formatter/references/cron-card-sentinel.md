# Cron 卡片 sentinel 标记文件机制

## 问题

Cron 作业输出经过两条完全独立的发送管道：

```
管道②: FeishuCardSender.send_card() → 飞书 Open API → 群内卡片
管道①: Cron scheduler._deliver_result() → final response 文本 → 群内文本
```

两条管道互不知情。Agent 通过管道②发了卡片后，管道①照常投递 final response 文本，导致群内出现一张卡片+一条文本的重复输出。

## 方案A 为何失败

最初尝试在 `cron-output-formatter` 技能中要求 Agent "发送卡片后 final response 必须为空字符串或单 emoji"。这是 Agent 行为指令，依赖模型遵守。

**失败原因**：模型行为不稳定，Agent 仍可能产生有意义的 final response 文本。用户反馈「群内依然是一张卡片 + 一条纯文本的重复输出」，证实此方案不可靠。

## 方案B：Sentinel 标记文件机制（当前方案）

### 设计

在两条管道的必经路径上插入一个基于文件系统的协调信号：

```
Agent 运行中
  FeishuCardSender.send_card() ──► 飞书 API ──► 群 [卡片]
       │
       └── 写入 ~/.hermes/cron/card_sent/{chat_id}
              (仅 HERMES_CRON_SESSION=1 时，含时间戳)

Agent 返回 final response

Cron scheduler._process_job()
  ① SILENT_MARKER 检查 (已有)
  ② _check_card_sentinels(job) ← 新增
       ├── 发现标记（< 5分钟）→ 跳过文本投递 + 删除标记
       ├── 标记过期（≥ 5分钟）→ 清理 + 正常投递
       └── 无标记 → 正常投递
```

### 涉及文件

- `molib/ceo/cards/sender.py` — `send_card()` 成功后调用 `_write_card_sentinel()`
- `hermes-agent/cron/scheduler.py` — `_process_job()` 投递前调用 `_check_card_sentinels()`

### sender.py 关键代码

```python
_CARD_SENT_DIR = Path.home() / ".hermes" / "cron" / "card_sent"

def _write_card_sentinel(chat_id: str) -> None:
    if os.environ.get("HERMES_CRON_SESSION") != "1":
        return  # 仅 cron 会话
    try:
        _CARD_SENT_DIR.mkdir(parents=True, exist_ok=True)
        (_CARD_SENT_DIR / chat_id).write_text(str(time.time()))
    except OSError:
        pass  # 静默降级
```

### scheduler.py 关键代码

```python
def _check_card_sentinels(job: dict) -> bool:
    sentinel_dir = Path(get_hermes_home()) / "cron" / "card_sent"
    if not sentinel_dir.is_dir():
        return False
    targets = _resolve_delivery_targets(job)
    now_ts = time.time()
    for target in targets:
        chat_id = target.get("chat_id", "")
        sentinel_file = sentinel_dir / chat_id
        if sentinel_file.exists():
            sentinel_ts = float(sentinel_file.read_text().strip())
            if now_ts - sentinel_ts < 300:  # 5分钟窗口
                sentinel_file.unlink(missing_ok=True)
                return True
            sentinel_file.unlink(missing_ok=True)  # 清理过期标记
    return False
```

### 调用位置

在 `_process_job()` 中，SILENT_MARKER 检查和 `_deliver_result()` 之间：

```python
# Sentinel check: suppress text if card already sent
if should_deliver and success:
    if _check_card_sentinels(job):
        logger.info("Job '%s': card sentinel found — suppressing text delivery", job["id"])
        should_deliver = False
```

## 为什么此方案可靠

1. **不依赖 Agent 行为** — 检查在 cron 调度器的 `_process_job()` 中执行，是投递管道的必经路径
2. **自动清理** — 标记文件被消费后立即删除，不会累积
3. **5 分钟过期** — 防止异常情况下的误抑制（标记文件残留）
4. **仅 cron 生效** — `_write_card_sentinel()` 检查 `HERMES_CRON_SESSION`，交互会话不受影响
5. **静默降级** — sentinel 写入失败不影响卡片发送；sentinel 目录不存在不影响文本投递
