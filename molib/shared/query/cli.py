"""
墨麟OS v2.0 — MQL CLI 入口

用法:
  python -m molib query "FROM skills WHERE category = 'mlops' LIMIT 5"
  python -m molib query --search "AI agent"
  python -m molib query --lookup name obsidian --source skills
  python -m molib query --index               # 重建索引
  python -m molib query --sources             # 列出数据源
"""

import argparse
import sys
from pathlib import Path

from .indexer import get_indexer


def cmd_query(args):
    """执行 MQL 查询"""
    from .executor import MQLExecutor

    executor = MQLExecutor()

    if args.search:
        from .executor import search
        result = search(args.search, source=args.source or "all",
                       limit=args.limit or 20)
    elif args.lookup_field and args.lookup_value:
        from .executor import lookup
        result = lookup(args.lookup_field, args.lookup_value,
                       source=args.source or "all")
    elif args.query:
        result = executor.execute_text(args.query)
    else:
        print("请提供查询字符串、--search 或 --lookup 参数")
        sys.exit(1)

    # 输出结果
    print(f"\n查询: {result.query_text}")
    print(f"来源: {', '.join(result.stats.sources_searched)}")
    print(f"扫描: {result.stats.entries_scanned}  匹配: {result.stats.entries_matched}")
    print(f"耗时: {result.stats.time_ms:.1f}ms")
    print()

    if args.json:
        import json
        print(json.dumps(result.to_dicts(), ensure_ascii=False, indent=2))
    elif args.table:
        print(result.table_view())
    else:
        for i, entry in enumerate(result.entries):
            tags_str = ", ".join(entry.tags[:5]) if entry.tags else ""
            print(f"{i+1}. [{entry.source}] {entry.name}")
            if entry.description:
                desc = entry.description[:100]
                print(f"   {desc}")
            if tags_str:
                print(f"   🏷️  {tags_str}")
            if entry.version:
                print(f"   📌 v{entry.version}")
            print()

    print(f"共 {len(result)} 条结果")


def cmd_index(args):
    """重建或查看索引"""
    indexer = get_indexer()

    if args.rebuild:
        print("重建索引...")
        sources = args.sources.split(",") if args.sources else None
        if sources:
            for src in sources:
                print(f"  索引 {src}...")
                indexer.refresh(src)
        else:
            indexer.refresh()
        print("完成 ✅")
    else:
        print("数据源状态:")
        all_sources = ["skills", "notes", "memory", "experiences", "hermes_sessions"]
        for src in all_sources:
            entries = indexer.get_entries(src)
            last = indexer._last_indexed.get(src)
            status = f"{len(entries)} 条" if entries else "未索引"
            time_str = f" (最后: {last.strftime('%H:%M:%S')})" if last else ""
            print(f"  {src:20s} {status}{time_str}")


def cmd_sources(args):
    """列出可用数据源及统计"""
    indexer = get_indexer()
    print("\n可用数据源:")
    print("-" * 50)
    for src in ["skills", "notes", "memory", "experiences", "hermes_sessions"]:
        entries = indexer.get_entries(src)
        count = len(entries)
        icon = "✅" if count > 0 else "⚠️"
        print(f"  {icon} {src:20s} {count} 条记录")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="MQL — Molin Query Language 查询引擎",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python -m molib query "FROM skills WHERE category = 'mlops' LIMIT 5"
  python -m molib query --search "AI agent"
  python -m molib query --lookup name obsidian --source skills
  python -m molib query --index
  python -m molib query --sources
        """
    )

    parser.add_argument("query", nargs="?", help="MQL 查询字符串")
    parser.add_argument("--search", "-s", help="全文搜索")
    parser.add_argument("--lookup", nargs=2, metavar=("FIELD", "VALUE"),
                        dest="lookup_raw", help="精确查找")
    parser.add_argument("--source", help="数据源过滤")
    parser.add_argument("--limit", "-n", type=int, help="结果数量限制")
    parser.add_argument("--json", "-j", action="store_true", help="JSON 输出")
    parser.add_argument("--table", "-t", action="store_true", help="表格输出")
    parser.add_argument("--index", "-i", action="store_true", help="索引管理")
    parser.add_argument("--rebuild", "-r", action="store_true", help="重建索引")
    parser.add_argument("--sources", action="store_true", help="列出数据源")

    args = parser.parse_args()

    # 处理 --lookup
    if args.lookup_raw:
        args.lookup_field = args.lookup_raw[0]
        args.lookup_value = args.lookup_raw[1]
    else:
        args.lookup_field = None
        args.lookup_value = None

    if args.sources:
        cmd_sources(args)
    elif args.index or args.rebuild:
        cmd_index(args)
    else:
        cmd_query(args)


if __name__ == "__main__":
    main()
