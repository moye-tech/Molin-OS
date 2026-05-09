"""
墨麟OS — Health Probe 健康检查探针
====================================
每60秒探测一次：DeepSeek API(通过OpenRouter)、飞书WebSocket心跳、本地进程。
失败时触发飞书告警。可手动调用。

使用方式:
    python -m molib.infra.health_probe              # 运行一次
    python -m molib.infra.health_probe --daemon      # 后台循环运行
    python -m molib.infra.health_probe --status      # 查看当前状态
"""
import json
import logging
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger("molin.infra.health_probe")

# ── 状态数据结构 ──


@dataclass
class ProbeResult:
    name: str
    status: bool  # True = healthy
    latency_ms: float = 0.0
    error: str = ""
    detail: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


class HealthProbe:
    """系统健康检查探针

    探测项:
    1. DeepSeek API — 通过OpenRouter的API可达性
    2. 飞书WebSocket — 闲鱼Bot的WebSocket心跳
    3. 本地进程 — 关键进程运行状态
    """

    PROBE_INTERVAL = 60  # 秒

    def __init__(self):
        self.results: dict[str, ProbeResult] = {}
        self.fail_count: dict[str, int] = {}
        self.last_status = True

    # ── 探针1: DeepSeek API ──

    def probe_deepseek_api(self) -> ProbeResult:
        """探测 DeepSeek API (via OpenRouter) 连通性"""
        import requests
        start = time.time()
        try:
            api_key = os.environ.get("OPENROUTER_API_KEY", "")
            if not api_key:
                # 尝试从.env加载
                env_path = Path.home() / ".hermes" / ".env"
                if env_path.exists():
                    for line in env_path.read_text().splitlines():
                        line = line.strip()
                        if line.startswith("OPENROUTER_API_KEY="):
                            api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
            if not api_key:
                return ProbeResult("deepseek_api", False, error="未配置 OPENROUTER_API_KEY")

            r = requests.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10,
            )
            elapsed = (time.time() - start) * 1000
            if r.status_code == 200:
                models = r.json().get("data", [])
                has_deepseek = any("deepseek" in m.get("id", "").lower() for m in models)
                return ProbeResult(
                    "deepseek_api", True,
                    latency_ms=round(elapsed, 1),
                    detail=f"OpenRouter可达, DeepSeek {'可用' if has_deepseek else '未找到'}",
                )
            return ProbeResult(
                "deepseek_api", False,
                latency_ms=round(elapsed, 1),
                error=f"HTTP {r.status_code}",
            )
        except requests.exceptions.ConnectionError as e:
            return ProbeResult("deepseek_api", False, error=f"连接失败: {str(e)[:80]}")
        except Exception as e:
            return ProbeResult("deepseek_api", False, error=str(e)[:100])

    # ── 探针2: 飞书WebSocket心跳 ──

    def probe_feishu_ws(self) -> ProbeResult:
        """探测闲鱼Bot的飞书WebSocket心跳"""
        try:
            # 检查闲鱼Bot进程是否存活
            r = subprocess.run(
                ["pgrep", "-f", "xianyu_bot"],
                capture_output=True, text=True, timeout=5,
            )
            if r.returncode == 0:
                pids = r.stdout.strip().split("\n")
                return ProbeResult("feishu_ws", True, detail=f"闲鱼Bot进程存活 (PID: {pids[0]})")
            # 检查feishu-cli认证状态
            r2 = subprocess.run(
                ["feishu-cli", "auth", "status", "-o", "json"],
                capture_output=True, text=True, timeout=5,
            )
            if r2.returncode == 0 and '"access_token_valid": true' in r2.stdout:
                return ProbeResult("feishu_ws", True, detail="feishu-cli 已登录")
            return ProbeResult("feishu_ws", False, error="飞书进程未运行且feishu-cli未登录")
        except FileNotFoundError:
            # 没有feishu-cli
            return ProbeResult("feishu_ws", False, error="feishu-cli 未安装")
        except Exception as e:
            return ProbeResult("feishu_ws", False, error=str(e)[:100])

    # ── 探针3: 本地进程 ──

    def probe_local_processes(self) -> ProbeResult:
        """探测关键本地进程"""
        process_checks = [
            ("Hermes Agent", ["hermes"]),
            ("飞书CLI", ["feishu-cli"]),
            ("Python", ["python"]),
        ]
        healthy = True
        details = []
        for name, keywords in process_checks:
            try:
                r = subprocess.run(
                    ["pgrep", "-f", keywords[0]],
                    capture_output=True, text=True, timeout=5,
                )
                if r.returncode == 0:
                    pids = r.stdout.strip().split("\n")
                    count = len(pids)
                    details.append(f"{name}: {count}进程")
                else:
                    details.append(f"{name}: 未运行")
                    healthy = False
            except Exception:
                details.append(f"{name}: 检查失败")
                healthy = False
        return ProbeResult(
            "local_processes", healthy,
            detail=" | ".join(details),
        )

    # ── 全量检查 ──

    def run_all(self) -> dict[str, ProbeResult]:
        """运行所有探针"""
        results = {}
        results["deepseek_api"] = self.probe_deepseek_api()
        results["feishu_ws"] = self.probe_feishu_ws()
        results["local_processes"] = self.probe_local_processes()
        self.results = results
        return results

    # ── 告警发送 ──

    def send_alert(self, failed: list[ProbeResult]):
        """发送飞书告警"""
        try:
            from molib.ceo.cards import FeishuCardSender, build_report_card
        except ImportError:
            try:
                from molib.ceo.feishu_card import FeishuCardSender, build_report_card
            except ImportError:
                logger.error("无法导入 FeishuCardSender，跳过告警")
                return

        lines = []
        for r in failed:
            lines.append(f"❌ **{r.name}**: {r.error or '无响应'}")
        content = "\n".join(lines)

        card = build_report_card(
            "⚠️ 系统健康告警",
            content,
            meta={"检查时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
            color="red",
        )
        try:
            sender = FeishuCardSender()
            chat_id = os.environ.get("FEISHU_ALERT_CHAT_ID", "oc_94c87f141e118b68c2da9852bf2f3bda")
            sender.send_card(card, chat_id)
            logger.info("告警已发送至飞书")
        except Exception as e:
            logger.error("告警发送失败: %s", e)

    # ── 循环运行 ──

    def daemon_loop(self):
        """后台循环运行，每60秒一次"""
        logger.info("HealthProbe 守护模式启动，间隔 %ds", self.PROBE_INTERVAL)
        while True:
            results = self.run_all()
            failed = [r for r in results.values() if not r.status]
            all_ok = len(failed) == 0

            if all_ok and not self.last_status:
                logger.info("✅ 系统恢复健康")
            elif not all_ok:
                logger.warning("⚠️ 检测到 %d 项异常: %s", len(failed),
                               [r.name for r in failed])
                # 累计失败次数
                for r in failed:
                    self.fail_count[r.name] = self.fail_count.get(r.name, 0) + 1
                # 连续失败3次才触发告警（避免抖动）
                for r in failed:
                    if self.fail_count.get(r.name, 0) >= 3:
                        self.send_alert([r])
                        self.fail_count[r.name] = 0  # 重置

            self.last_status = all_ok

            # 输出状态摘要
            status_line = " | ".join(
                f"{name}: {'✅' if r.status else '❌'} ({r.latency_ms}ms)"
                if r.status
                else f"{name}: ❌ {r.error[:30]}"
                for name, r in results.items()
            )
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {status_line}")

            time.sleep(self.PROBE_INTERVAL)


# ── CLI入口 ──

def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    probe = HealthProbe()

    if "--daemon" in sys.argv:
        probe.daemon_loop()
    elif "--status" in sys.argv:
        results = probe.run_all()
        for name, r in results.items():
            status_icon = "✅" if r.status else "❌"
            print(f"{status_icon} {name}: {'正常' if r.status else '异常'}")
            if r.detail:
                print(f"   详情: {r.detail}")
            if r.error:
                print(f"   错误: {r.error}")
            if r.latency_ms:
                print(f"   延迟: {r.latency_ms}ms")
    else:
        # 单次运行
        results = probe.run_all()
        all_ok = all(r.status for r in results.values())
        print(json.dumps(
            {name: {"status": "ok" if r.status else "fail",
                     "latency_ms": r.latency_ms,
                     "error": r.error,
                     "detail": r.detail}
             for name, r in results.items()},
            ensure_ascii=False, indent=2,
        ))
        if not all_ok:
            failed = [r for r in results.values() if not r.status]
            probe.send_alert(failed)
        return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
