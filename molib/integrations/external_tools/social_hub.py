"""
Social Hub External Tool (xiaohongshu-cli Integration)
为 IP 孵化与增长子公司提供自动化的社交媒体监控与内容分发能力。
"""
import os
import json
import subprocess
from typing import Dict, Any
from loguru import logger
from molib.integrations.adapters.tool_adapter import ExternalToolAdapter

XHS_CLI_PATH = os.getenv("XHS_CLI_PATH", "xhs")


class SocialHubTool(ExternalToolAdapter):
    def __init__(self):
        super().__init__(tool_name="xiaohongshu_cli")
        self.register_command("post_note", self._post_note)
        self.register_command("monitor_trends", self._monitor_trends)
        logger.info("SocialHubTool initialized for XHS interactions.")

    async def _post_note(self, params: Dict[str, Any]) -> Dict[str, Any]:
        title = params.get("title", "")
        content = params.get("content", "")
        images = params.get("images", [])

        if not title:
            raise ValueError("title parameter is required")

        logger.info(f"[SocialHub] Publishing note to XHS: {title}")

        cmd = [XHS_CLI_PATH, "post", "--title", title, "--content", content]
        for img in images:
            cmd += ["--image", img]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode != 0:
                logger.error(f"[SocialHub] XHS CLI error: {result.stderr}")
                return {"status": "error", "platform": "xiaohongshu", "action": "post", "stderr": result.stderr[:500]}

            output = json.loads(result.stdout) if result.stdout.strip() else {}
            return {
                "status": "success",
                "platform": "xiaohongshu",
                "action": "post",
                "url": output.get("url", ""),
                "note_id": output.get("id", ""),
            }
        except FileNotFoundError:
            logger.warning(f"[SocialHub] XHS CLI 未找到 ({XHS_CLI_PATH})，返回模拟结果")
            return {"status": "simulated", "platform": "xiaohongshu", "action": "post",
                    "title": title, "note": "XHS CLI 未安装，此为模拟响应"}
        except subprocess.TimeoutExpired:
            return {"status": "error", "platform": "xiaohongshu", "action": "post", "message": "发布超时 (>120s)"}

    async def _monitor_trends(self, params: Dict[str, Any]) -> Dict[str, Any]:
        keyword = params.get("keyword", "")
        logger.debug(f"[SocialHub] Monitoring trends for {keyword}")

        try:
            cmd = [XHS_CLI_PATH, "trends", "--keyword", keyword]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0 and result.stdout.strip():
                output = json.loads(result.stdout)
                return {"status": "success", "keyword": keyword, "hot_topics": output.get("topics", [])}
        except (FileNotFoundError, json.JSONDecodeError, subprocess.TimeoutExpired):
            pass

        # 回退：基于搜索的轻量模拟
        return {"status": "simulated", "keyword": keyword,
                "hot_topics": ["AI 自动化", "效率工具", "副业"],
                "note": "XHS CLI 不可用，返回模拟趋势数据"}


_social_hub = SocialHubTool()
def get_social_hub() -> SocialHubTool:
    return _social_hub
