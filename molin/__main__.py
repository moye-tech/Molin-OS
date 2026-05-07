#!/usr/bin/env python3
"""墨麟 CLI — molib 的薄包装层"""
import sys
import json

try:
    from molib.__main__ import main as molib_main
except ImportError:
    print(json.dumps({"error": "molib 包未安装。请确保 molib/ 在 Python 路径中。"}, ensure_ascii=False))
    sys.exit(1)

if __name__ == "__main__":
    molib_main()
