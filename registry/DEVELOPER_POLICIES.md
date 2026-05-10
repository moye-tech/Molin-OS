# Developer Policies

## 提交准则

所有提交必须符合以下政策，对标 [Obsidian Developer Policies](https://docs.obsidian.md/Developer+policies)。

### 1. 原创性

- 插件/技能必须是你的原创作品
- 禁止提交他人作品（除非获得明确授权）
- Fork 必须明确标注原作者

### 2. 功能完整性

- 提交的技能必须有明确的用途和完整的 SKILL.md
- 必须包含 YAML frontmatter（name/description/version/min_hermes_version）
- 推荐包含 tags 和 category 字段

### 3. 安全性

- 禁止收集或传输用户隐私数据
- 禁止包含恶意代码（挖矿、后门、信息窃取）
- API 密钥必须通过环境变量或 ~/.hermes/.env 管理
- 网络请求必须使用 HTTPS

### 4. 内容规范

- 禁止色情、暴力、赌博相关内容
- 禁止政治敏感内容
- 禁止侵犯知识产权的内容
- 遵守中国法律法规

### 5. 版本管理

- 使用语义化版本号（SemVer）：MAJOR.MINOR.PATCH
- 每次更新必须递增版本号
- 必须声明 min_hermes_version（最低兼容 Hermes 版本）

### 6. 命名规范

- 技能 ID 使用小写字母、数字、连字符
- 技能 name 与目录名保持一致
- 避免与已有技能同名

### 7. 提交流程

1. Fork 本仓库
2. 在 community-skills.json 末尾添加你的技能条目
3. 确保 JSON 格式有效
4. 提交 PR 并填写提交清单
5. 等待审核（通常 3-5 个工作日）

### 8. 审核标准

- JSON 格式正确
- 所有必需字段完整
- GitHub 仓库公开可访问
- 技能功能描述准确
- 无安全/合规问题

### 9. 下架政策

- 不再维护的技能移入 community-skills-deprecated.json
- 违规技能立即移除
- 作者可主动申请下架

### 10. 免责声明

- 提交者对其技能内容负全部责任
- 墨麟OS 不担保第三方技能的安全性
- 用户自行承担安装第三方技能的风险
