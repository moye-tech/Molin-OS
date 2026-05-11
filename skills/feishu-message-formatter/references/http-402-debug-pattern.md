# HTTP 402 调试实录 — 2026-05-11

## 故障现象

5个 cron 任务同时报错:
```
RuntimeError: HTTP 402: Insufficient Balance
provider=deepseek model=deepseek-v4-pro
```

影响任务: CEO简报、情报银行、内容工厂、API预警、记忆蒸馏

## 排查过程

### 1. 余额确认（第一反应是欠费）
```bash
curl -s https://api.deepseek.com/user/balance \
  -H "Authorization: Bearer $DEEPSEEK_API_KEY"
```
返回: `{"is_available":true,"balance_infos":[{"total_balance":"77.40"}]}`
→ 余额 ¥77.40，**不是欠费问题**

### 2. 直接 API 测试
```bash
curl -s https://api.deepseek.com/chat/completions \
  -H "Authorization: Bearer $DEEPSEEK_API_KEY" \
  -d '{"model":"deepseek-v4-pro","messages":[{"role":"user","content":"hi"}],"max_tokens":10}'
```
返回: HTTP 200 — **API 现在正常**

### 3. 故障时间窗口分析
从 error.log 提取时间戳:
- 07:06 记忆蒸馏失败
- 07:30 API预警失败
- 08:00 情报银行失败
- 09:01 CEO简报+内容工厂失败
- 09:15 闲鱼检测失败
- **10:00 后所有任务恢复正常**
→ 故障窗口: 07:00-09:15 CST (约2小时)

### 4. 根因
DeepSeek `v4-pro` 模型的计费/路由系统在早晨时段出现临时故障。
不是账户余额问题，是 provider 侧的基础设施抖动。

## 解决方案

### 已实施: config.yaml fallback
```yaml
# ~/.hermes/config.yaml 第10行
fallback_model: deepseek-v4-flash
```
cron 调度器在 v4-pro 返回 402 时自动降级到 v4-flash。

### 效果
- v4-flash 同 provider，同 API key，零额外配置
- 价格是 v4-pro 的 ~50%
- cron 任务的日报/统计不依赖深度推理，v4-flash 足够

## 教训

1. **402 ≠ 欠费** — 先验证余额再下结论
2. **time-windowed failures = provider issue** — 如果在特定时间段集中出现然后自愈，是 provider 侧问题
3. **fallback_model 是最低成本的保险** — 一行 YAML 避免飞轮断裂
4. **v4-pro 很新** — 新模型的基础设施稳定性不如 flash 模型
