# Chatwoot MCP 部署分析报告

## 结论：当前不满足部署条件，不建议立即执行

---

## 前置条件检查

| 项目 | 状态 | 详情 |
|------|------|------|
| Docker | ❌ 未安装 | 需要 sudo apt install docker + docker compose |
| PostgreSQL | ❌ 未安装 | Chatwoot 需要 pgvector/pgvector:pg16 |
| Redis | ❌ 未安装 | Chatwoot 需要 Redis (sidekiq 任务队列) |
| 内存 | ⚠️ 3.6GB 总量 | 1.6GB 已用 → 剩余 ~2GB，Chatwoot 3容器预计占用1-1.5GB |
| 磁盘 | ⚠️ 40GB 总量 | 54% 已用 → 剩余 ~18GB，Chatwoot 数据卷预计增加2-5GB |
| 端口 3000/5432/6379 | ✅ 空闲 | 无冲突 |
| 域/DNS | ❌ 未配置 | Chatwoot 需要域名配置 SSL（生产环境）|
| 现有 Chatwoot | ❌ 无 | 全新部署 |

## 部署资源估算

Chatwoot 使用 Docker Compose 部署，包含 4 个容器：

| 容器 | 镜像 | 预估内存 | 说明 |
|------|------|---------|------|
| rails | chatwoot/chatwoot:latest | ~400-600MB | Rails 主应用 |
| sidekiq | chatwoot/chatwoot:latest | ~200-300MB | 异步任务队列 |
| postgres | pgvector/pgvector:pg16 | ~200-400MB | +向量搜索 |
| redis | redis:alpine | ~50-100MB | 缓存/队列 |
| **合计** | | **~850-1400MB** | 可用内存约2GB → **刚好够，但紧张** |

## 建议的操作顺序（如需执行）

```
1. sudo apt update && sudo apt install -y docker.io docker-compose-v2
2. sudo systemctl start docker && sudo systemctl enable docker
3. sudo usermod -aG docker $USER && newgrp docker  # 或登出重登
4. 配置 .env 文件（SECRET_KEY, DB_PASS, REDIS_PASS 等）
5. docker compose -f docker-compose.production.yaml up -d
6. docker compose exec rails bundle exec rails db:seed  # 初始化
7. docker compose exec rails bundle exec rails chatwoot:setup  # 创建管理员账号
```

## 替代方案：Chatwoot Cloud

如果只是需要测试 MCP 包装，推荐先用 Chatwoot Cloud：
- 无需基础设施投入
- 有完整的 REST API 可直接开发 MCP Server
- 免费版支持 3 个客服席位（一个人够用）
- Chatwoot API Key 获取：Settings → API → Generate Token

## 真正值得部署的条件

当以下条件满足 2+ 时，Chatwoot 自部署有意义：
1. ✅ **有真实客服需求**（闲鱼买家、公众号咨询 每天>10条）
2. ⬜ **多通道聚合**（微信+闲鱼+邮件+Web Chat 合一）
3. ⬜ **有足够的可用内存**（建议 4GB+，当前 3.6GB 偏紧）
4. ⬜ **需要 AI 辅助回复**（Chatwoot 内置 AI Assistant）
5. ⬜ **需要长期保存对话历史做分析**

当前只有条件1部分满足（闲鱼有消息但量极少）。

## 关于 MCP 包装

当 Chatwoot 就绪后，MCP 工具规划：
```
tools:
  - chatwoot_list_conversations  # 获取未读/活跃会话
  - chatwoot_send_message        # 在会话中回复
  - chatwoot_create_contact      # 创建客户资料
  - chatwoot_get_conversation    # 查看完整对话历史
  - chatwoot_assign_agent        # 分配客服（未来）
  - chatwoot_toggle_status       # 开启/关闭 bot 接管
```

**MCP 比 SKILL 更适合 Chatwoot 的原因**：实时长连接。客服会话是持续流（有新消息会推），REST API 轮询不如 WebSocket/Webhook 推送实时。MCP 可以维持长连接状态，让 Hermes 在客户发消息的第一时间响应。
