"""
墨麟 Hermes OS — Web仪表盘
============================

提供系统状态总览、内容管理、发布监控。

启动: molin serve  或  python -m molin.dashboard
"""

import json
from datetime import datetime
from pathlib import Path

# Flask 可选依赖, 优雅降级
try:
    from flask import Flask, jsonify, render_template_string
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

from molin.core.engine import engine
from molin.core.scheduler import scheduler
from molin.publish.xianyu import store

app = Flask(__name__) if FLASK_AVAILABLE else None

# ── HTML 模板 ──
DASHBOARD_HTML = r"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>墨麟 Hermes OS — 一人公司控制台</title>
    <style>
        :root {
            --bg: #0a0a1a;
            --card: #1a1a2e;
            --border: #2a2a4e;
            --accent: #6c5ce7;
            --green: #00b894;
            --yellow: #fdcb6e;
            --red: #e17055;
            --text: #dfe6e9;
            --muted: #636e72;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
        }
        header {
            background: linear-gradient(135deg, var(--card), #2d1b69);
            padding: 24px 32px;
            border-bottom: 1px solid var(--border);
        }
        header h1 { font-size: 24px; }
        header .subtitle { color: var(--muted); margin-top: 4px; }
        .container { max-width: 1200px; margin: 0 auto; padding: 24px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; }
        .card {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
        }
        .card h3 { font-size: 14px; color: var(--muted); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px; }
        .stat { font-size: 32px; font-weight: bold; }
        .stat.green { color: var(--green); }
        .stat.yellow { color: var(--yellow); }
        .badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }
        .badge.ok { background: rgba(0,184,148,0.15); color: var(--green); }
        .badge.warn { background: rgba(253,203,110,0.15); color: var(--yellow); }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 10px 12px; text-align: left; border-bottom: 1px solid var(--border); }
        th { color: var(--muted); font-size: 12px; text-transform: uppercase; }
        .refresh { color: var(--muted); font-size: 12px; text-align: right; margin-top: 16px; }
    </style>
</head>
<body>
    <header>
        <h1>🐉 墨麟 Hermes OS</h1>
        <div class="subtitle">AI一人公司操作系统 · 控制台 v2.0</div>
    </header>
    <div class="container">
        <div class="grid">
            <div class="card">
                <h3>系统状态</h3>
                <div class="stat green">{{ health.status }}</div>
                <div style="margin-top:8px">
                    <span class="badge ok">运行中</span>
                    <span class="badge ok">{{ departments }} 部门</span>
                </div>
            </div>
            <div class="card">
                <h3>本月预算</h3>
                <div class="stat yellow">¥{{ budget }}</div>
                <div style="margin-top:4px; color:var(--muted)">月度AI服务预算</div>
            </div>
            <div class="card">
                <h3>技能库</h3>
                <div class="stat">{{ skills_count }}</div>
                <div style="margin-top:4px; color:var(--muted)">SKILL.md 知识模块</div>
            </div>
            <div class="card">
                <h3>闲鱼商品</h3>
                <div class="stat">{{ products_count }}</div>
                <div style="margin-top:4px; color:var(--muted)">待/已上架商品</div>
            </div>
        </div>

        <div class="grid" style="margin-top:16px;">
            <div class="card" style="grid-column: span 2;">
                <h3>发布渠道</h3>
                <table>
                    <thead>
                        <tr><th>平台</th><th>状态</th><th>类型</th><th>日限</th></tr>
                    </thead>
                    <tbody>
                        {% for ch in channels %}
                        <tr>
                            <td>{{ ch.name }}</td>
                            <td><span class="badge {{ 'ok' if ch.enabled else 'warn' }}">{{ '启用' if ch.enabled else '禁用' }}</span></td>
                            <td>{{ ch.types }}</td>
                            <td>{{ ch.limit }}/天</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="card" style="margin-top:16px;">
            <h3>定时任务</h3>
            <table>
                <thead>
                    <tr><th>任务</th><th>调度</th><th>描述</th></tr>
                </thead>
                <tbody>
                    {% for job in jobs %}
                    <tr>
                        <td>{{ job.name }}</td>
                        <td><code>{{ job.schedule }}</code></td>
                        <td>{{ job.description }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <div class="refresh">最后更新: {{ now }}</div>
    </div>
</body>
</html>
"""


def create_app():
    """创建Flask应用"""
    if not FLASK_AVAILABLE:
        raise ImportError("Flask未安装: pip install flask flask-cors")

    @app.route("/")
    def index():
        health = engine.health_check()
        products = store.list_products()
        jobs = scheduler.list_jobs()

        channels = [
            {"name": "小红书", "enabled": True, "types": "图文/视频", "limit": 3},
            {"name": "知乎", "enabled": True, "types": "文章/回答", "limit": 2},
            {"name": "微博", "enabled": True, "types": "图文/视频", "limit": 5},
            {"name": "微信公众号", "enabled": True, "types": "图文", "limit": 1},
            {"name": "掘金", "enabled": True, "types": "技术文章", "limit": 1},
            {"name": "X/Twitter", "enabled": True, "types": "推文", "limit": 10},
            {"name": "闲鱼", "enabled": True, "types": "商品", "limit": 3},
        ]

        # Count SKILL.md files
        skills_dir = Path(__file__).parent.parent / "skills"
        skills_count = len(list(skills_dir.rglob("SKILL.md"))) if skills_dir.exists() else 0

        return render_template_string(
            DASHBOARD_HTML,
            health=health,
            departments=health.get("departments", 6),
            budget=1360,
            skills_count=skills_count,
            products_count=len(products),
            channels=channels,
            jobs=jobs,
            now=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

    @app.route("/api/health")
    def api_health():
        return jsonify(engine.health_check())

    @app.route("/api/products")
    def api_products():
        products = store.list_products()
        return jsonify([{"title": p.title, "price": p.price, "status": p.status} for p in products])

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8080, debug=True)
