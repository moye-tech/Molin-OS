# 飞书网关故障诊断参考

> 2026-05-10 实战诊断记录

## SSL UNEXPECTED_EOF_WHILE_READING 模式

这是飞书网关最常见的故障模式。完整错误栈：

```
ssl.SSLEOFError: [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1016)

During handling of the above exception, another exception occurred:

urllib3.exceptions.SSLError: [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1016)

The above exception was the direct cause of the following exception:

urllib3.exceptions.MaxRetryError: HTTPSConnectionPool(host='open.feishu.cn', port=443): Max retries exceeded with url: /open-apis/im/v1/messages/om_xxx/reactions

During handling of the above exception, another exception occurred:

requests.exceptions.SSLError: HTTPSConnectionPool(host='open.feishu.cn', port=443): Max retries exceeded
```

关键信息：
- 错误源：`gateway/platforms/feishu.py` line 2777, `_add_reaction` 方法
- 触发：网关在收到消息后添加「typing...」表情反应时
- 调用链：`gateway.run → feishu._add_reaction → lark_oapi im.v1.message_reaction.create → requests → urllib3 → ssl`
- 影响范围：仅表情反应失败，消息收发不受影响
- 网关已 try/except 捕获此异常，不会崩溃

## 诊断清单

1. 确认飞书客户端运行：`pgrep -fl Feishu`
2. 确认网关进程：`pgrep -fl "hermes.*gateway"`
3. 查看网关状态：`curl -s http://localhost:8648/api/status | python3 -m json.tool`
4. 检查收消息记录：`grep "Inbound dm message" ~/.hermes/logs/agent.log | tail -5`
5. 检查发消息记录：`grep "Sending response" ~/.hermes/logs/agent.log | tail -5`
6. 测试 SSL：`openssl s_client -connect open.feishu.cn:443 -servername open.feishu.cn </dev/null 2>&1 | head -5`
7. 测试 Token：`feishu-cli msg send <chat_id> --msg-type text --content "test"`
8. 检查退出诊断：`cat ~/.hermes/logs/gateway-exit-diag.log | python3 -m json.tool`

## 2026-05-10 实战记录

用户报告「飞书网关不回复了」。诊断结果：
- 网关进程正常运行（PID 15484，自 14:56 起连续运行）
- 收到了「现在进度如何了」消息（19:49:12）
- SSL 错误仅发生在 `_add_reaction`，被网关捕获
- 实际消息发送成功（19:53:07，2407 chars）
- SSL 测试通过（TLSv1.3）
- Token 测试通过（200 OK）
- 结论：网关正常工作，SSL 为间歇性瞬时错误

## 网关进程生命周期

当天网关经历了 5 次重启（exit_nonzero），当前实例稳定：
- PID 9405: 12:58 启动 → 12:59 退出（正常）
- PID 9878: 13:15 启动（无退出记录，可能被 --replace）
- PID 10557: 13:28 启动 → 13:33 退出（非零）
- PID 10980: 13:33 启动 → 14:56 退出（非零）
- PID 15470: 14:56 启动 → 14:56 退出（非零，5秒内）
- PID 15484: 14:56 启动 → 运行至今

多次快速重启表明当时环境不稳定，可能也是 SSL 相关问题。
