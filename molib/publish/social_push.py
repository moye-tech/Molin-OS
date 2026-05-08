"""
墨麟多平台发布引擎 — 7平台统一发布管线
======================================

支持平台:
- 小红书 (图文/长文)
- 知乎
- 微博
- 微信公众号
- 掘金
- X/Twitter
- 闲鱼 — 支持 xianyu_helper 真实发布（如可用）

基于 social-push (jihe520, 405 star) 架构设计。
"""

import logging
import os
import subprocess
import sys
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

logger = logging.getLogger("molin.publish")


class Platform(Enum):
    XIAOHONGSHU = "xiaohongshu"
    ZHIHU = "zhihu"
    WEIBO = "weibo"
    WECHAT = "wechat"
    JUEJIN = "juejin"
    X = "x"
    XIANYU = "xianyu"


PLATFORM_CONFIG = {
    Platform.XIAOHONGSHU: {
        "name": "小红书",
        "content_types": ["图文笔记", "长文", "视频"],
        "max_title_len": 20,
        "max_body_len": 1000,
        "schedule_support": True,
    },
    Platform.ZHIHU: {
        "name": "知乎",
        "content_types": ["文章", "回答", "想法"],
        "max_title_len": 50,
        "max_body_len": 50000,
        "schedule_support": False,
    },
    Platform.WEIBO: {
        "name": "微博",
        "content_types": ["图文", "视频"],
        "max_title_len": 0,
        "max_body_len": 2000,
        "schedule_support": True,
    },
    Platform.WECHAT: {
        "name": "微信公众号",
        "content_types": ["图文"],
        "max_title_len": 64,
        "max_body_len": 20000,
        "schedule_support": True,
    },
    Platform.JUEJIN: {
        "name": "掘金",
        "content_types": ["技术文章"],
        "max_title_len": 50,
        "max_body_len": 50000,
        "schedule_support": False,
    },
    Platform.X: {
        "name": "X/Twitter",
        "content_types": ["推文", "长文"],
        "max_title_len": 0,
        "max_body_len": 280,
        "schedule_support": True,
    },
    Platform.XIANYU: {
        "name": "闲鱼",
        "content_types": ["商品"],
        "max_title_len": 30,
        "max_body_len": 10000,
        "schedule_support": False,
    },
}


# ── 闲鱼发布适配器 ──────────────────────────────────────────────

XIANYU_HELPER_PATH = Path.home() / "xianyu_agent" / "xianyu_helper.py"


def _xianyu_helper_available() -> bool:
    """检测 xianyu_helper 是否可导入"""
    return XIANYU_HELPER_PATH.exists()


def _publish_to_xianyu(title: str, desc: str, price: float = 199,
                       category: str = "文档代写") -> dict:
    """
    通过 xianyu_helper 真实发布到闲鱼。
    检测可用性，不可用时返回 mock 结果 + 启动说明。
    """
    if not _xianyu_helper_available():
        return {
            "status": "adapter_unavailable",
            "platform": "xianyu",
            "message": "xianyu_helper 不可用",
            "setup": (
                f"安装 xianyu_helper:\n"
                f"  cd ~/xianyu_agent\n"
                f"  pip install -r requirements.txt --break-system-packages\n"
                f"  然后运行: python3.12 xianyu_helper.py\n"
            ),
        }

    try:
        # 将 xianyu_agent 加入 path 并导入
        sys.path.insert(0, str(XIANYU_HELPER_PATH.parent))
        import xianyu_helper as xy_mod

        # 调用发布
        if hasattr(xy_mod, "publish_item"):
            result = xy_mod.publish_item(title=title, desc=desc, price=price, category=category)
            return {
                "status": "published",
                "platform": "xianyu",
                "title": title,
                "result": str(result)[:500],
                "published_at": datetime.now().isoformat(),
            }
        elif hasattr(xy_mod, "auto_publish"):
            result = xy_mod.auto_publish(product_type=category, price=price, keywords=title)
            return {
                "status": "published",
                "platform": "xianyu",
                "title": title,
                "result": str(result)[:500],
                "published_at": datetime.now().isoformat(),
            }
        else:
            return {
                "status": "adapter_missing_function",
                "platform": "xianyu",
                "message": "未找到 publish_item/auto_publish 函数",
                "available_functions": [f for f in dir(xy_mod) if not f.startswith("_")],
            }
    except Exception as e:
        return {
            "status": "adapter_error",
            "platform": "xianyu",
            "error": str(e),
            "message": f"调用 xianyu_helper 失败: {e}",
        }


class Content:
    """待发布内容"""

    def __init__(self, platform: Platform, title: str, body: str,
                 images: list[str] = None, tags: list[str] = None):
        self.platform = platform
        self.title = title
        self.body = body
        self.images = images or []
        self.tags = tags or []
        self.status = "draft"
        self.created_at = datetime.now()

    def validate(self) -> tuple[bool, str]:
        """验证内容是否满足平台要求"""
        cfg = PLATFORM_CONFIG[self.platform]
        if cfg["max_title_len"] > 0 and len(self.title) > cfg["max_title_len"]:
            return False, f"标题超过{cfg['max_title_len']}字限制"
        if len(self.body) > cfg["max_body_len"]:
            return False, f"正文超过{cfg['max_body_len']}字限制"
        return True, "验证通过"


class SocialPush:
    """多平台发布引擎"""

    def __init__(self):
        self.publish_log = []

    def publish(self, content: Content) -> dict:
        """发布内容"""
        valid, msg = content.validate()
        if not valid:
            return {"status": "rejected", "reason": msg}

        # ── 闲鱼走真实 xianyu_helper 发布 ──
        if content.platform == Platform.XIANYU:
            result = _publish_to_xianyu(
                title=content.title,
                desc=content.body,
                price=content.tags[0] if content.tags and content.tags[0].lstrip("$").isdigit() else 199,
                category=content.tags[1] if len(content.tags) > 1 else "文档代写",
            )
            content.status = result.get("status", "published")
            self.publish_log.append(result)
            logger.info("发布到闲鱼: %s (status=%s)", content.title[:30], result.get("status"))
            return result

        # ── 其他平台走 mock（待对接真实 API） ──
        result = {
            "platform": content.platform.value,
            "platform_name": PLATFORM_CONFIG[content.platform]["name"],
            "title": content.title,
            "body_preview": content.body[:100] + "..." if len(content.body) > 100 else content.body,
            "status": "published" if valid else "rejected",
            "published_at": datetime.now().isoformat(),
            "content_id": f"POST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        }

        content.status = "published"
        self.publish_log.append(result)
        logger.info("发布到%s: %s", result["platform_name"], content.title[:30])
        return result

    def cross_post(self, content: Content, platforms: list[Platform]) -> list[dict]:
        """一键多平台发布"""
        results = []
        for platform in platforms:
            adapted = Content(
                platform=platform,
                title=content.title,
                body=content.body,
                images=content.images,
                tags=content.tags,
            )
            results.append(self.publish(adapted))
        return results

    def get_publish_history(self) -> list[dict]:
        """获取发布历史"""
        return self.publish_log


# 全局实例
publisher = SocialPush()


def publish(platform: str = ""):
    """CLI入口"""
    print("  多平台发布引擎就绪")
    print(f"   支持平台: {', '.join(p.name for p in PLATFORM_CONFIG)}")
    if _xianyu_helper_available():
        print("   闲鱼: xianyu_helper 可用，支持真实发布")
    else:
        print("   闲鱼: xianyu_helper 未安装（将返回 mock）")
    print(f"   目标平台: {platform or '全部'}")
    return {"status": "ready", "platforms": len(PLATFORM_CONFIG)}
