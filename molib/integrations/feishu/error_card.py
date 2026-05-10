"""飞书错误优雅降级卡片 — 不让用户看到技术错误"""
from typing import Dict, Any


def build_error_card(error_type: str, user_msg: str = "", retry_count: int = 0) -> Dict[str, Any]:
    """用户友好的错误卡片，隐藏技术细节"""
    msgs = {
        "timeout": (
            "⏱️ 这个任务有点复杂，多花了些时间",
            "我已经在后台继续处理，完成后会通知您"
        ),
        "overload": (
            "🔧 系统正在处理较多任务",
            "请稍等片刻，或回复「重试」重新执行"
        ),
        "api_error": (
            "🌐 AI 服务临时波动",
            "已自动切换备用模型，正在重试"
        ),
    }
    title, body = msgs.get(error_type, (
        "⚡ 遇到了一个小问题",
        "团队正在排查，请回复「重试」或联系墨烨"
    ))
    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": title},
            "template": "yellow",
        },
        "elements": [{
            "tag": "div",
            "text": {"tag": "lark_md", "content": body}
        }]
    }
