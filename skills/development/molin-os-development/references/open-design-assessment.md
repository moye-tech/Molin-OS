# Open Design 评估框架

> 2026-05-11 — 评估 nexu-io/open-design (34K★) 的完整方法论

## 评估流程（可复用于任何外部GitHub项目）

### Phase 1: 信息收集 (3条并行线)

```
1. web_search: 项目简介/star数/技术栈/社区评价
2. web_extract: README (raw.githubusercontent.com + 普通URL)
3. git clone: 本地分析代码结构、技能/设计系统数量、依赖列表
```

### Phase 2: 维度评分 (4维度)

| 维度 | 权重 | 评估点 |
|------|------|--------|
| 架构匹配度 | 0.35 | 技术栈兼容性、接口对接方式、数据流匹配 |
| 能力增强度 | 0.30 | 填补什么空白、提升多少层次、与现有模块关系 |
| 部署可行性 | 0.20 | M1 8GB约束、网络依赖、pip/npm安装复杂度 |
| 维护成本 | 0.15 | 依赖栈深度、更新频率、与主系统耦合度 |

### Phase 3: 集成方案 (3选1)

```
A. 技能移植 — 提取子能力到 molib，最低耦合
B. CLI桥接 — subprocess/HTTP API 调用，保留原项目完整性
C. 全栈部署 — 本地启动完整服务，最高耦合但最全能力
```

### Phase 4: 行动建议

- 明确优先级 + 时间估算
- 标注阻塞项（内存/网络/API key）
- 提供可执行的 Day1-3 计划

## Open Design 评估实例

### 项目数据
- ⭐ 34K, Apache 2.0, 57.9万行 TypeScript
- 248 skills + 150+ design systems
- Node.js 24 + pnpm 10.33 + Next.js 16 + React 18

### 对墨麟OS的增强点
1. 墨图设计 Worker: 单图生成 → 全栈设计工程 (landing/page/prototype/deck)
2. 技能库: 248 设计技能可移植到 molib/skills/design/
3. 设计系统: 150品牌系统可喂养 FeishuCardRouter
4. Agent桥接: 自动检测16种coding agent → 与WorkerChain互补

### 部署约束
- M1 8GB: Next.js dev server 300-500MB, 无法全栈部署
- pnpm install: 通过Clash代理超2分钟, 需直连或国内镜像
- 推荐方案B: daemon-only CLI桥接, ~200MB内存开销

### 决策
- 评分: 8.5/10 (架构级增强)
- 时机: ComfyUI/MuseTalk 稳定后再部署，避免资源争抢
- 短期替代: popular-web-designs 技能(71设计系统×纯HTML)

## 部署结果 (2026-05-11)

**实际执行:** 用户说"开始"→Day1克隆+安装+启动daemon→Day2编写designer.py v2.2集成

| 里程碑 | 结果 |
|--------|------|
| 仓库克隆 | ✅ `~/Projects/open-design` |
| pnpm install | ✅ 861 包, 3m36s, 直连无代理 |
| Daemon 运行 | ✅ `http://127.0.0.1:55888`, 161MB RSS |
| designer.py v2.2 | ✅ 13878B, 14个快捷action + 149设计系统 |
| 集成测试 | ✅ 墨麟AI集团落地页生成, 13KB HTML, Apple设计系统, 0 lint错误 |
| 内存友好 | ✅ 161MB RSS < 500MB M2约束 |

**方案选择:** B (CLI桥接) — daemon-only模式, 未启动Next.js web前端

**核心发现:**
1. `corepack enable` 需sudo → 用 `corepack pnpm@10.33.2` 直调绕过
2. `pnpm tools-dev` 版本检查对corepack不友好 → 用系统pnpm 11.0.9直调
3. Hermes被自动检测为唯一可用Agent (available=true), 16个中仅此一个
4. Daemon是被动服务 — 不生成内容,只存skills/DS/artifacts; Hermes LLM负责生成
