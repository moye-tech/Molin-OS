# Worker Activation Pattern — 从"仅技能"到实际 Worker 代码

> 来源: 2026-05-10 系统诊断会话
> 触发: 用户诊断 27 个吸收项目中大量处于"仅 SKILL.md"状态

## 问题诊断

```
诊断前: 27 个项目 → ~520K 星标 → 仅 ~10 有代码+CLI
致命短板: 墨单订单(骨架) 墨链电商(无交易) 墨域私域(无邮件) 墨图设计(仅技能) 墨声配音(仅技能)
```

## 激活模式

三步: 识别对标 → 评估 M2 可行性 → 纯 Python stdlib 替代

### 本轮激活清单

| 原"仅技能" | 对标(★) | 替代模块 | 行数 | CLI |
|-----------|---------|---------|------|-----|
| 墨单订单 | MedusaJS 27K + KillBill 4K | molib_order.py | 380 | order create/list/invoice/stats |
| 墨域邮件 | listmonk 15K | molib_mail.py | 350 | mail list/subscriber/campaign/stats |
| 墨域CRM | twenty 20K | crm_worker.py | 130 | crm create/list/pipeline |
| 墨测数据 | Umami 23K | molib_analytics.py | 200 | analytics track/stats/top-pages |
| 墨图设计 | ComfyUI 60K | designer_worker.py | 100 | PyTorch MPS 生成 |
| 墨声配音 | Whisper | voice_actor_worker.py | 115 | macOS say TTS |
| 墨音STT | Whisper | molib_stt.py | 130 | stt check/transcribe |
| 统一后端 | PocketBase 54K | molib_db.py | 370 | db collection/record/auth/stats |

### 关键经验

1. GitHub 大文件(>10MB)下载必然失败 → 直接写纯 Python 替代
2. 每个模块一个 SQLite 文件，<10MB 内存，不需要 PostgreSQL/Redis
3. 写完立即验证: `python -c "from x import X; X().stats()"`
4. stdlib 铁律: 除非桥接层(如 feishu.py 需 larksuiteoapi)，否则 zero deps
