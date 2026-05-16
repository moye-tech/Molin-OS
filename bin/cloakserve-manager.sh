#!/bin/bash
# Molin-OS CloakServe Manager — start/stop/restart/status

CLOAKSERVE_PORT=9222
CLOAKSERVE_BIN="$HOME/Molin-OS/bin/cloakserve"
CLOAKSERVE_PLIST="$HOME/Library/LaunchAgents/com.molin.cloakserve.plist"
CLOAKSERVE_LOG="$HOME/.cloakbrowser/cloakserve.log"
CLOAKSERVE_ERR="$HOME/.cloakbrowser/cloakserve.err.log"

case "${1:-status}" in
  start)
    echo "Starting cloakserve via launchd..."
    launchctl load "$CLOAKSERVE_PLIST" 2>&1
    sleep 2
    curl -s http://localhost:$CLOAKSERVE_PORT/ 2>/dev/null && echo "✓ cloakserve running on port $CLOAKSERVE_PORT" || echo "✗ cloakserve not ready yet. Check logs."
    ;;

  stop)
    echo "Stopping cloakserve..."
    launchctl unload "$CLOAKSERVE_PLIST" 2>&1
    echo "✓ cloakserve stopped"
    ;;

  restart)
    $0 stop
    sleep 1
    $0 start
    ;;

  status)
    if launchctl list | grep -q com.molin.cloakserve; then
      echo "launchd: ✓ loaded"
    else
      echo "launchd: ✗ not loaded"
    fi

    if curl -s http://localhost:$CLOAKSERVE_PORT/ > /dev/null 2>&1; then
      echo "HTTP:   ✓ reachable on port $CLOAKSERVE_PORT"
      curl -s http://localhost:$CLOAKSERVE_PORT/ | python3 -m json.tool 2>/dev/null
    else
      echo "HTTP:   ✗ not reachable"
    fi

    echo "---"
    ls -lh "$CLOAKSERVE_LOG" 2>/dev/null && echo "Log: $CLOAKSERVE_LOG" || echo "Log: (not yet created)"
    echo "---"
    echo "Binary: $(python3 -m cloakbrowser info 2>/dev/null | head -4)"
    ;;

  logs)
    tail -f "$CLOAKSERVE_LOG"
    ;;

  logs-err)
    tail -f "$CLOAKSERVE_ERR"
    ;;

  ps)
    echo "Active seeds via HTTP API:"
    curl -s http://localhost:$CLOAKSERVE_PORT/ | python3 -m json.tool 2>/dev/null || echo "(not running)"
    echo ""
    echo "Chrome processes:"
    ps aux | grep -i chromium | grep -v grep
    ;;

  install-binary)
    echo "Installing CloakBrowser binary..."
    python3 -m cloakbrowser install
    echo "✓ Binary info:"
    python3 -m cloakbrowser info
    ;;

  docker-manager)
    echo "Starting CloakBrowser Manager (profile UI)..."
    docker run -d --name cloakbrowser-manager \
      -p 8080:8080 \
      -v cloakprofiles:/data \
      cloakhq/cloakbrowser-manager \
      2>/dev/null && echo "✓ Manager at http://localhost:8080" \
      || docker start cloakbrowser-manager 2>/dev/null && echo "✓ Manager already running at http://localhost:8080" \
      || echo "Please install Docker first"
    ;;

  test)
    python3 "$HOME/Molin-OS/bin/cloakserve_test.py" "${2:-}"
    ;;

  *)
    echo "Usage: $0 {start|stop|restart|status|logs|logs-err|ps|install-binary|docker-manager|test [seed]}"
    exit 1
    ;;
esac
