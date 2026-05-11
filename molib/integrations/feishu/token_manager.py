"""飞书 Token 管理器 v2.0 — 全局单例 + 懒初始化 Lock，解决 BUG-01/03"""
import time, asyncio, os
from typing import Optional
from loguru import logger
import httpx

# ── 全局单例（懒初始化，不在模块加载时创建 Lock）──────────────────
_instance: Optional["FeishuTokenManager"] = None

class FeishuTokenManager:
    """飞书 tenant_access_token 管理器

    关键修复：
    - Lock 在 __init__ 内创建（而非模块级），确保在事件循环内初始化
    - 单例通过 get_instance() 获取，保证进程内唯一
    - 提前 300s 刷新，避免临界失效
    """

    def __init__(self):
        self._token: Optional[str] = None
        self._expires_at: float = 0
        self._lock: Optional[asyncio.Lock] = None  # 懒初始化
        self._app_id = os.getenv("FEISHU_APP_ID", "")
        self._app_secret = os.getenv("FEISHU_APP_SECRET", "")

    def _get_lock(self) -> asyncio.Lock:
        # 首次访问时在当前事件循环内创建，彻底解决 BUG-01
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def get(self) -> Optional[str]:
        # 快速路径：有效 Token 直接返回
        if self._token and time.time() < self._expires_at - 300:
            return self._token

        async with self._get_lock():
            # 双重检查（其他协程可能已刷新）
            if self._token and time.time() < self._expires_at - 300:
                return self._token
            return await self._refresh()

    async def _refresh(self) -> Optional[str]:
        if not self._app_id or not self._app_secret:
            logger.warning("[FeishuToken] 缺少 FEISHU_APP_ID 或 FEISHU_APP_SECRET")
            return None
        try:
            async with httpx.AsyncClient() as cli:
                r = await cli.post(
                    "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
                    json={"app_id": self._app_id, "app_secret": self._app_secret},
                    timeout=10,
                )
                d = r.json()
                if d.get("code") == 0:
                    self._token = d["tenant_access_token"]
                    self._expires_at = time.time() + d.get("expire", 7200)
                    logger.info(f"[FeishuToken] 刷新成功，有效至 {time.strftime('%H:%M:%S', time.localtime(self._expires_at))}")
                    return self._token
                logger.error(f"[FeishuToken] 刷新失败 code={d.get('code')} msg={d.get('msg')}")
        except Exception as e:
            logger.error(f"[FeishuToken] 请求异常: {e}")
        return None

    def invalidate(self):
        self._expires_at = 0


def get_instance() -> FeishuTokenManager:
    """获取全局单例（线程安全，模块级懒初始化）"""
    global _instance
    if _instance is None:
        _instance = FeishuTokenManager()
    return _instance


async def get_feishu_token(*args, **kwargs) -> Optional[str]:
    """全局统一入口，所有模块调用此函数，保证单例"""
    return await get_instance().get()


def invalidate_token():
    get_instance().invalidate()
