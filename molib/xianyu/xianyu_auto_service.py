#!/usr/bin/env python3
"""
Hermes 闲鱼自动客服 - 商品发布验证 + WebSocket消息监听 + AI自动回复
使用 XianYuApis 的 goofish_live.py WebSocket 实时监听
"""

import sys, os, json, time, base64, asyncio, threading, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from goofish_apis import XianyuApis
from goofish_live import XianyuLive
from utils.goofish_utils import trans_cookies, generate_device_id, get_session_cookies_str
from message import Message, make_text, make_image

import websockets
from loguru import logger

COOKIE_FILE = os.path.expanduser("~/.xianyu_cookies_new.txt")
ITEM_ID = "1049910720757"  # 已发布的AI商业计划书

# ============================================================
# AI 客服回复逻辑 — LLM 驱动（废弃关键词匹配）
# ============================================================

import logging

logger = logging.getLogger("molin.xianyu.auto_service")

AUTO_REPLY_SYSTEM_PROMPT = (
    "你是墨麟AI集团·墨声客服（自动化客服系统）。\n"
    "产品：AI商业计划书定制服务，¥199，24小时交付，免费修改一次。\n\n"
    "你的客户服务风格：\n"
    "- 热情友好、简洁专业\n"
    "- 不过度推销\n"
    "- 回复字数控制在100字以内\n"
    "- 根据买家的真实问题给出个性化回复\n\n"
    "治理规则（必须严格遵守）：\n"
    "- L0 自动：回答产品信息、流程、价格、时间 — 直接回复，无需审批\n"
    "- L2 审批：买家出价>¥500或询问复杂定制价格，必须告知需要跟团队确认后回复您\n"
    "- L3 坚决不做：不碰任何涉及退款操作、改价操作、转账链接\n\n"
    "常见产品信息（用于参考，不是模板套话）：\n"
    "- 价格：¥199/份\n"
    "- 交付时间：24小时出初稿\n"
    "- 修改政策：免费修改一次\n"
    "- 适用场景：种子轮/A轮融资BP、路演PPT、创业大赛\n"
    "- 退款政策：初稿不满意全额退款"
)


async def get_auto_reply_llm(user_message_text: str) -> str:
    """基于LLM的智能客服回复"""
    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.environ.get("OPENROUTER_API_KEY", ""),
        )

        response = await client.chat.completions.create(
            model="deepseek/deepseek-chat",
            messages=[
                {"role": "system", "content": AUTO_REPLY_SYSTEM_PROMPT},
                {"role": "user", "content": user_message_text},
            ],
            max_tokens=200,
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.warning(f"LLM 回复失败，回退到模板: {e}")
        return _fallback_reply(user_message_text)


def _fallback_reply(text: str) -> str:
    """LLM 不可用时的降级回复"""
    text_lower = text.lower()
    if any(w in text_lower for w in ["你好", "您好", "hi", "hello", "在吗"]):
        return "您好！欢迎来到AI商业计划书定制服务 👋 有什么可以帮您的？"
    if any(w in text_lower for w in ["价格", "多少钱", "费用"]):
        return "我们的AI商业计划书定制服务统一价 ¥199（约10-15页），含封面+目录+正文+封底+财务模型。"
    return "感谢咨询！关于AI商业计划书定制服务，¥199/份，24小时出稿。您可以告诉我具体需求，我帮您评估。"


def get_auto_reply(user_message_text: str) -> str:
    """同步兼容包装 — 保持原调用接口不变"""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return asyncio.ensure_future(get_auto_reply_llm(user_message_text))
        return asyncio.run(get_auto_reply_llm(user_message_text))
    except Exception:
        return _fallback_reply(user_message_text)


# ============================================================
# WebSocket 消息监听 - 基于 goofish_live.py 改造
# ============================================================

class XianyuAutoAgent(XianyuLive):
    """扩展XianyuLive，加入自动回复功能"""
    
    def __init__(self, cookies_str):
        super().__init__(cookies_str)
        self.item_id = ITEM_ID
        self.token_result = None
        self._running = True
    
    async def message_handler(self, ws, cid, message_body):
        """处理收到的消息并自动回复"""
        try:
            base64_data = message_body["content"]["custom"]["data"]
            msg_json = json.loads(base64.b64decode(base64_data).decode('utf-8'))
            sender_id = message_body["extension"]["senderUserId"]
            sender_name = message_body["extension"]["reminderTitle"]
            text = msg_json.get("content", {}).get("text", "")
            
            logger.info(f"[消息] 来自 {sender_name}({sender_id}): {text}")
            print(f"\n💬 [{time.strftime('%H:%M:%S')}] {sender_name}: {text}")
            
            # 自己发的消息不回复
            if sender_id == self.myid:
                return
            
            # 自动回复
            reply_text = get_auto_reply(text)
            logger.info(f"[回复] 向 {sender_name}: {reply_text[:50]}...")
            
            # 发送回复
            await self.send_msg(ws, cid, sender_id, make_text(reply_text))
            print(f"🤖 [{time.strftime('%H:%M:%S')}] 已自动回复 {sender_name}")
            
        except Exception as e:
            logger.error(f"消息处理失败: {e}")
            traceback.print_exc()
    
    async def listen_forever(self):
        """持续监听消息"""
        logger.info("正在连接闲鱼WebSocket...")
        
        headers = {
            "Cookie": get_session_cookies_str(self.xianyu.session),
            "Host": "wss-goofish.dingtalk.com",
            "Connection": "Upgrade",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            "Origin": "https://www.goofish.com",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
        
        while self._running:
            try:
                async with websockets.connect(self.base_url, extra_headers=headers, ping_interval=30) as ws:
                    self.ws = ws
                    logger.info("✅ WebSocket 已连接")
                    print("\n✅ 闲鱼消息监听已启动！等待买家消息...")
                    print("=" * 50)
                    
                    # 执行初始化
                    init_result = await self.init(ws)
                    logger.info(f"初始化完成: {init_result}")
                    
                    # 开始监听
                    async for raw_msg in ws:
                        try:
                            msg = json.loads(raw_msg)
                            
                            # 回复ack
                            ack = {
                                "code": 200,
                                "headers": {
                                    "mid": msg["headers"].get("mid", ""),
                                    "sid": msg["headers"].get("sid", ""),
                                }
                            }
                            if "app-key" in msg["headers"]:
                                ack["headers"]["app-key"] = msg["headers"]["app-key"]
                            if "ua" in msg["headers"]:
                                ack["headers"]["ua"] = msg["headers"]["ua"]
                            if "dt" in msg["headers"]:
                                ack["headers"]["dt"] = msg["headers"]["dt"]
                            await ws.send(json.dumps(ack))
                            
                            # 处理消息
                            lwp = msg.get("lwp", "")
                            if lwp == "/s/chat":
                                # 新消息通知
                                body_list = msg.get("body", [])
                                for item in body_list:
                                    if isinstance(item, dict) and "message" in item:
                                        await self.message_handler(ws, body_list[0], item)
                                if body_list:
                                    logger.debug(f"chat通知: {str(msg)[:200]}")
                            elif lwp == "/s/vulcan":
                                # 发送商品信息请求
                                await ws.send(json.dumps({
                                    "lwp": "/r/MessageManager/listUserMessages",
                                    "headers": {"mid": "".join(__import__('random').choices('0123456789abcdef', k=24))},
                                    "body": [f"{self.myid}@goofish", False, 9007199254740991, 20, False]
                                }))
                                
                        except json.JSONDecodeError:
                            continue
                        except Exception as e:
                            logger.error(f"消息处理异常: {e}")
                            
            except Exception as e:
                logger.error(f"WebSocket连接断开，5秒后重连: {e}")
                print(f"\n⚠️ 连接断开: {e}，5秒后重连...")
                await asyncio.sleep(5)

    def stop(self):
        self._running = False


def run_listener():
    """在单独线程中运行WebSocket监听"""
    cookie_str = open(COOKIE_FILE).read().strip()
    agent = XianyuAutoAgent(cookie_str)
    
    async def main():
        await agent.listen_forever()
    
    asyncio.run(main())


# ============================================================
# 主入口
# ============================================================

if __name__ == "__main__":
    print("=" * 50)
    print("Hermes 闲鱼自动客服 v1.0")
    print(f"商品ID: {ITEM_ID}")
    print(f"Cookie: {COOKIE_FILE}")
    print("=" * 50)
    
    # 先验证Cookie
    cookie_str = open(COOKIE_FILE).read().strip()
    cookies = trans_cookies(cookie_str)
    api = XianyuApis(cookies, generate_device_id(cookies.get('unb', 'test')))
    
    print("\n🔑 验证Token...")
    token = api.get_token()
    if 'SUCCESS' in str(token.get('ret', [''])):
        print("✅ Token有效，开始监听消息...")
    else:
        print(f"❌ Token无效: {token.get('ret')}")
        sys.exit(1)
    
    # 启动监听
    try:
        run_listener()
    except KeyboardInterrupt:
        print("\n\n服务已停止")
