"""
墨麟OS — 运营看板 v2
========================
蓝图概念代码化。

零依赖Web仪表盘（Python内置http.server），
展示：系统健康、子公司状态、DAG任务、质量门控、Plan Mode待审批。

启动: python3 -m molib.dashboard [port]
启动: python3 molib/dashboard.py [port]
"""

import http.server
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("molin.dashboard")

# ── 指标采集 ──────────────────────────────────────────────────────────


def collect_metrics() -> dict[str, Any]:
    """采集全系统指标"""
    return {
        "system": _collect_system(),
        "skills": _collect_skills(),
        "subsidiaries": _collect_subsidiaries(),
        "cron": _collect_cron(),
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def _collect_system() -> dict[str, Any]:
    """系统基本信息"""
    import platform
    return {
        "name": "墨麟OS (Molin OS)",
        "version": "5.0.0",
        "hostname": platform.node(),
        "python": platform.python_version(),
        "uptime_seconds": time.monotonic() if hasattr(time, "monotonic") else 0,
        "total_entities": 28,  # L0 + 22L1 + 5L2
        "revenue_target": 52000,
        "budget_total": 3490,
        "roi": "14.9x",
    }


def _collect_skills() -> dict[str, Any]:
    """技能系统统计"""
    skills_dir = Path.home() / ".hermes" / "skills"
    if not skills_dir.exists():
        return {"total": 0, "with_code": 0, "by_owner": {}}
    
    total = len(list(skills_dir.rglob("SKILL.md")))
    with_code = len(list(skills_dir.rglob("*.py")))
    
    # 按 molin_owner 统计
    owners = {}
    for skill_file in skills_dir.rglob("SKILL.md"):
        try:
            content = skill_file.read_text()
            for line in content.splitlines():
                if "molin_owner:" in line:
                    owner = line.split("molin_owner:")[-1].strip().strip('"').strip("'")
                    owners[owner] = owners.get(owner, 0) + 1
                    break
        except Exception:
            pass
    
    return {
        "total": total,
        "with_code": with_code,
        "code_rate": round(with_code / total * 100, 1) if total > 0 else 0,
        "by_owner": owners,
    }


def _collect_subsidiaries() -> list[dict[str, Any]]:
    """22家营收子公司列表（从 molib C O引擎获取）"""
    try:
        from molib.ceo.intent_router import SUBSIDIARY_KEYWORDS
        subsidiaries = []
        for sid, keywords in SUBSIDIARY_KEYWORDS.items():
            subsidiaries.append({
                "id": sid,
                "name": sid.replace("_", " ").title(),
                "keywords_sample": keywords[:3] if keywords else [],
                "keyword_count": len(keywords),
            })
        return subsidiaries
    except Exception:
        return []


def _collect_cron() -> list[dict[str, Any]]:
    """Cronjob状态"""
    cron_dir = Path.home() / ".hermes" / "cron"
    jobs = []
    if cron_dir.exists():
        jobs_file = cron_dir / "jobs.json"
        if jobs_file.exists():
            try:
                data = json.loads(jobs_file.read_text())
                if isinstance(data, list):
                    for j in data:
                        jobs.append({
                            "name": j.get("name", "未知"),
                            "schedule": j.get("schedule", ""),
                            "enabled": j.get("enabled", True),
                            "next_run": j.get("next_run_at", ""),
                        })
            except Exception:
                pass
    return jobs


# ── HTTP 处理器 ──────────────────────────────────────────────────────


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>墨麟OS — 运营看板</title>
<style>
:root{--bg:#0a0a1a;--card:#1a1a2e;--border:#2a2a4e;--accent:#6c5ce7;--green:#00b894;--yellow:#fdcb6e;--red:#e17055;--text:#dfe6e9;--muted:#636e72}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:var(--bg);color:var(--text);min-height:100vh}
header{background:linear-gradient(135deg,var(--card),#2d1b69);padding:24px 32px;border-bottom:1px solid var(--border)}
header h1{font-size:22px}header .sub{color:var(--muted);font-size:13px;margin-top:4px}
.container{max-width:1200px;margin:0 auto;padding:24px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px}
.card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:20px}
.card h3{font-size:13px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:10px}
.stat{font-size:28px;font-weight:bold}.stat.green{color:var(--green)}.stat.yellow{color:var(--yellow)}.stat.red{color:var(--red)}
.badge{display:inline-block;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;margin:2px}
.badge.ok{background:rgba(0,184,148,0.15);color:var(--green)}
.badge.warn{background:rgba(253,203,110,0.15);color:var(--yellow)}
.badge.red{background:rgba(225,112,85,0.15);color:var(--red)}
.badge.sub{background:rgba(108,92,231,0.15);color:var(--accent)}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{padding:8px 10px;text-align:left;border-bottom:1px solid var(--border)}
th{color:var(--muted);font-size:11px;text-transform:uppercase}
.refresh{color:var(--muted);font-size:12px;text-align:right;margin-top:14px}
pre{font-size:11px;color:var(--muted);overflow-x:auto;max-height:400px}
.g2{grid-column:span 2}.g3{grid-column:span 3}
</style>
</head>
<body>
<header>
<h1>🏛️ 墨麟OS (Molin OS)</h1>
<div class="sub">运营看板 · 28实体 · 22营收子公司 · 339技能</div>
</header>
<div class="container" id="app"></div>
<script>
const API = '/api/metrics';
async function load(){
  try{
    const r=await fetch(API);
    const d=await r.json();
    render(d);
  }catch(e){
    document.getElementById('app').innerHTML='<div class="card"><h3>连接失败</h3><p>'+e+'</p></div>';
  }
}
function render(d){
  const s=d.system,sk=d.skills,sub=d.subsidiaries,cr=d.cron;
  const html=`
    <div class="grid">
      <div class="card">
        <h3>系统状态</h3>
        <div class="stat green">${s.name}</div>
        <div style="margin-top:6px">
          <span class="badge ok">${s.version}</span>
          <span class="badge sub">${s.total_entities}实体</span>
          <span class="badge ok">¥${(s.revenue_target/1000).toFixed(0)}K/月</span>
        </div>
        <div style="margin-top:8px;font-size:12px;color:var(--muted)">
          ROI ${s.roi} · Python ${s.python} · ${s.hostname}
        </div>
      </div>
      <div class="card">
        <h3>技能体系</h3>
        <div class="stat">${sk.total}</div>
        <div style="margin-top:6px">
          <span class="badge ok">${sk.with_code}个有代码</span>
          <span class="badge ${sk.code_rate>50?'ok':'warn'}">穿透率${sk.code_rate}%</span>
        </div>
        <div style="margin-top:8px;font-size:11px;color:var(--muted)">
          ${Object.entries(sk.by_owner).sort((a,b)=>b[1]-a[1]).slice(0,5).map(([k,v])=>k+':'+v).join(' · ')}
        </div>
      </div>
      <div class="card">
        <h3>营收子公司</h3>
        <div class="stat">${sub.length}</div>
        <div style="margin-top:6px">
          ${sub.slice(0,6).map(s=>'<span class="badge sub">'+s.name+'</span>').join('')}
          ${sub.length>6?'<span class="badge">+'+ (sub.length-6) +'</span>':''}
        </div>
      </div>
      <div class="card">
        <h3>定时任务</h3>
        <div class="stat ${cr.filter(j=>j.enabled).length>0?'yellow':'green'}">${cr.filter(j=>j.enabled).length}/${cr.length}</div>
        <div style="margin-top:6px;font-size:12px;color:var(--muted)">
          ${cr.filter(j=>j.enabled).length>0?'活跃':'全部暂停（零空转）'}
        </div>
      </div>
    </div>
    <div class="grid" style="margin-top:14px">
      <div class="card g2">
        <h3>技能分布（按molin_owner TOP 10）</h3>
        <table>
          <thead><tr><th>所属</th><th>数量</th><th>占比</th></tr></thead>
          <tbody>
            ${Object.entries(sk.by_owner).sort((a,b)=>b[1]-a[1]).slice(0,10).map(([k,v])=>{
              const pct=(v/sk.total*100).toFixed(1);
              return '<tr><td>'+k+'</td><td>'+v+'</td><td>'+pct+'%</td></tr>';
            }).join('')}
          </tbody>
        </table>
      </div>
      <div class="card">
        <h3>定时任务详情</h3>
        ${cr.length===0?'<p style="color:var(--muted);font-size:13px">暂无定时任务</p>':
        '<table><thead><tr><th>名称</th><th>状态</th></tr></thead><tbody>'+
        cr.map(j=>'<tr><td>'+j.name+'</td><td><span class="badge '+(j.enabled?'ok':'warn')+'">'+(j.enabled?'运行中':'暂停')+'</span></td></tr>').join('')+
        '</tbody></table>'}
      </div>
    </div>
    <div class="card" style="margin-top:14px">
      <h3>营收子公司关键词覆盖</h3>
      <table>
        <thead><tr><th>Worker ID</th><th>关键词示例</th><th>总数</th></tr></thead>
        <tbody>
          ${sub.map(s=>'<tr><td>'+s.id+'</td><td>'+(s.keywords_sample||[]).join(', ')+'</td><td>'+s.keyword_count+'</td></tr>').join('')}
        </tbody>
      </table>
    </div>
    <div class="refresh">最后更新: ${d.time} · <a href="javascript:load()" style="color:var(--accent);text-decoration:none">刷新</a></div>
  `;
  document.getElementById('app').innerHTML=html;
}
load();
setInterval(load,30000);
</script>
</body>
</html>"""


class DashboardHandler(http.server.BaseHTTPRequestHandler):
    """HTTP请求处理器"""

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self._send_html(200, DASHBOARD_HTML)
        elif self.path == "/api/metrics":
            data = collect_metrics()
            self._send_json(200, data)
        else:
            self._send_json(404, {"error": "not_found"})

    def _send_html(self, status: int, html: str):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def _send_json(self, status: int, data: dict):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def log_message(self, fmt, *args):
        logger.debug(fmt, *args)


def serve(port: int = 9898):
    """启动看板服务"""
    server = http.server.HTTPServer(("127.0.0.1", port), DashboardHandler)
    print(f"🏛️ 墨麟OS 运营看板: http://127.0.0.1:{port}")
    print(f"   API端点: http://127.0.0.1:{port}/api/metrics")
    print(f"   按 Ctrl+C 停止")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 停止看板服务")
        server.server_close()


def main():
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9898
    logging.basicConfig(level=logging.INFO)
    serve(port)


if __name__ == "__main__":
    main()
