#!/bin/bash
# 墨麟OS · 每日 arxiv 论文扫描
# 用途: 每天早上扫描 AI Agent / LLM 领域最新论文
# 输出: relay/shared/daily_papers_$(date +%Y%m%d).json

TOOLS_DIR="$HOME/Molin-OS/tools"
OUTPUT_DIR="$HOME/Molin-OS/relay/shared/results"
mkdir -p "$OUTPUT_DIR"

DATE=$(date +%Y%m%d)
OUTPUT_FILE="$OUTPUT_DIR/daily_papers_${DATE}.json"

# 搜索 arxiv 最新论文
python3 "$HOME/Molin-OS/skills/arxiv/scripts/search_arxiv.py" \
  "AI Agent LLM 2026" --max-results 10 \
  2>/dev/null > "$OUTPUT_FILE" || \
  echo '{"status":"error","date":"'$DATE'","message":"扫描失败"}' > "$OUTPUT_FILE"

echo "arxiv 每日扫描完成 → $OUTPUT_FILE"
wc -c "$OUTPUT_FILE"
