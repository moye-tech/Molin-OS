# 飞书文档导入 — 正确方式

> 经验来源: 2026-05-10 — content-update 超时 + 格式混乱

## 推荐: `feishu-cli doc import`

一次性将 Markdown 文件导入飞书文档，自动处理表格、标题、列表格式。

```bash
# 创建新文档
feishu-cli doc import file.md --title "文档标题"

# 更新已有文档
feishu-cli doc import file.md --document-id DOC_ID --verbose

# 大表格优化
feishu-cli doc import file.md --document-id DOC_ID --table-workers 5 --diagram-workers 3
```

特性:
- 三阶段流水线: 顺序创建 → 并发处理 → 降级容错
- 表格自动并发填充（大表格自动拆分）
- Mermaid/PlantUML 自动转飞书画板
- 详细进度和耗时统计

## 避免: `feishu-cli doc content-update`

此命令容易超时（大文档 >50KB），且 `--mode replace_all` 需要额外参数。
仅在需要精确替换文档中某个段落时使用。

## 避免: `feishu-cli doc add`

逐块添加效率极低，500块的文档需要几百次 API 调用。
仅用于修补小段落。

## 关键参数

| 参数 | 用途 | 默认 |
|:-----|:-----|:----:|
| --table-workers | 表格并发数 | 3 |
| --diagram-workers | 图表并发数 | 5 |
| --image-workers | 图片上传并发 | 2 |
| --document-id | 更新已有文档 | 新建 |
| -t / --title | 新建文档标题 | 必填 |
| -v / --verbose | 显示进度 | false |
