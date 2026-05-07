# 墨麟 OS 系统状态报告 — 2026-05-07

## 版本
- **当前版本**: v5.1（墨域OS v1.0 已建成）
- **架构**: 6层架构 (L0控制台→L1 CEO→L2 5VP→L3 20子公司→L4基础设施→L5存储)
- **技能**: 336+ 个 SKILL.md
- **子公司**: 22家营收 + 5家内部 + 1个中枢 + 共享层 = 28实体

## 网络状态
### 连接情况
| 域名 | 状态 | 说明 |
|------|------|------|
| sentinel.openai.com | ✅ 直连通 | CF CDN (172.64.x.x) |
| auth.openai.com | ✅ 直连通 | CF CDN (104.18.x.x) |
| github.com | ✅ 直连通 | |
| chatgpt.com | ❌ DNS污染+SNI RST | Cogent直连IP被墙 |
| api.openai.com | ❌ DNS污染+SNI RST | Cogent直连IP被墙 |
| google.com | ❌ TCP全封 | |

### 关键发现
- 服务器443/TLS**非全局封锁**，是选择性拦截
- 之前"443全封"结论为误判（`curl https://1.1.1.1` 超时 ≠ 443被封）

## 工具状态
| 工具 | 版本 | 位置 |
|------|------|------|
| Hermes Agent | v5.1 | `~/hermes-os/` |
| Codex CLI | v0.128.0 | `~/.local/bin/codex` |
| Playwright | v1.59.0 | `~/.cache/ms-playwright/chromium-1217` |
| curl_cffi | v0.15.0 | Python venv |
| WARP (Cloudflare) | 已装·隧道健康 | Proxy Mode 502 |
| Docker | 已装 | Docker Compose v2 |
| sing-box | ❌ 已彻底卸载 | |

## 认证状态
- **auth.json** (Codex CLI): ✅ 有效，~253天过期
- **access_token**: 3934 chars
- **session_token**: 196 chars
- **SSH公钥(用户Mac)**: ✅ 已添加 ed25519 到 authorized_keys

## GPT Image 2 集成状态
### 现状
- 服务器直连 `chatgpt.com` 被墙（DNS污染 + SNI RST）
- `sentinel.openai.com` (CF CDN) 直连正常，但被 Cloudflare WAF 拦截（返回403验证页）
- **Playwright 无头浏览器**也无法绕过 CF（服务器 IP 被标记）
- **WARP** 隧道健康但 Proxy Mode 502

### 可行路径
**SSH隧道方案**（最终方案）：通过 Mac 网络做 SOCKS5 代理
```bash
# Mac上运行
ssh -i ~/.ssh/id_ed25519 -N -D 1080 ubuntu@111.229.205.127
```

## 清理历史
- ✅ sing-box v1.13.11 已卸载（包+配置+systemd+临时文件全清）
- ✅ 9个 sing-box 配置文件删除（各种 anytls 版本尝试）
- ✅ 错误"443全封"结论已纠正为"选择性拦截"
- ✅ 网络诊断 skill 已创建

## 下一步
1. 打通 SSH 隧道 → 测试 GPT Image 2 调用
2. 或使用通义千问 qwen-image-2.0-pro（已集成到百炼工具）
3. 每周自主进化扫描（计划 2026-05-11 周一）
