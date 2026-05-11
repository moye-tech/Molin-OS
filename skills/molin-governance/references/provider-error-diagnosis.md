# API Provider Error Diagnosis

> 快速诊断 DeepSeek / DashScope / OpenRouter 等 LLM Provider 的 HTTP 错误。

## HTTP 402: Insufficient Balance

### 不要被错误消息骗了

`HTTP 402: Insufficient Balance` 有两种可能：

| 情况 | 特征 | 处理 |
|------|------|------|
| **真·余额不足** | 所有时间段持续失败 | 充值 |
| **临时计费故障** | 仅在特定窗口失败，其他时段正常 | 等自愈 / 降级模型 |

### 三步诊断法

```bash
# Step 1: 检查余额 API（独立于 chat API，不受模型计费影响）
curl -s https://api.deepseek.com/user/balance \
  -H "Authorization: Bearer $DEEPSEEK_API_KEY"
# 返回: {"is_available":true,"balance_infos":[{"total_balance":"77.40",...}]}

# Step 2: 直接测试 chat API（排除中间层问题）
curl -s -w "\nHTTP_CODE:%{http_code}" \
  https://api.deepseek.com/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $DEEPSEEK_API_KEY" \
  -d '{"model":"deepseek-v4-pro","messages":[{"role":"user","content":"hi"}],"max_tokens":5}'

# Step 3: 检查错误日志的时域分布
grep "402" ~/.hermes/logs/errors.log | grep "$(date +%Y-%m-%d)"
# 如果错误集中在某个时段（如 07:00-09:00），10:00 后自愈 → 临时故障
```

### 已知故障模式

| Provider | Model | 故障类型 | 持续时间 | 处理 |
|----------|-------|---------|---------|------|
| DeepSeek | v4-pro | 临时 402（余额充足） | ~2h (07:00-09:00 CST) | 自愈。期间可降级到 v4-flash |

### 降级策略

```yaml
# config.yaml 配置 fallback（推荐）
model:
  default: deepseek-v4-pro
  provider: deepseek
  fallback:
    - model: deepseek-v4-flash
      provider: deepseek
    - model: qwen-plus
      provider: dashscope
```

### 自愈验证

故障窗口结束后，验证步骤：
1. 检查最近一次 cron 执行状态：`hermes cron list` 查看 `last_status`
2. 手动触发一个轻量任务测试：直接对话测试
3. 确认日志中 402 错误已停止出现
