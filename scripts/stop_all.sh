#!/bin/bash
echo "🛑 停止墨麟OS所有服务..."
for p in media edu side shared global; do
    hermes -p "$p" gateway stop 2>/dev/null && \
        echo "  ✅ $p 已停止" || echo "  ⚠️  $p 未运行"
done
pkill -f "memory_bridge.py" 2>/dev/null && echo "  ✅ Memory Bridge 已停止"
pkill -f "hermes-web-ui"    2>/dev/null && echo "  ✅ Web UI 已停止"
pkill -f "open-design.*3001" 2>/dev/null && echo "  ✅ Open-Design 已停止"
echo "🛑 所有服务已停止"
