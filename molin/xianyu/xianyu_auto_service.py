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
# AI 客服回复逻辑
# ============================================================

ORDER_QUESTIONS = {
    "价格": "我们的AI商业计划书定制服务统一价 ¥199（约10-15页），含封面+目录+正文+封底+财务模型。现在下单享早鸟价，免费修改一次。",
    "流程": "下单流程很简单：① 拍下商品并付款 → ② 告诉我们您的项目概况（行业/阶段/融资目标）→ ③ 我们AI智能生成框架，人工精修 → ④ 24小时内交付初稿 → ⑤ 免费修改一次到满意。",
    "时间": "从您提供项目信息开始，24小时内出初稿！免费修改一次（一般在2小时内改完）。加急可6小时出稿。",
    "修改": "免费修改一次！包含内容调整、数据更新、排版优化等。超出一次后每次修改收取 ¥50 工本费。",
    "案例": "我们主要服务初创企业融资BP，涵盖AI/电商/本地生活/教育等多个行业。您可以先提供项目概况，我们出框架给您看。",
    "资质": "我们是专业AI内容服务团队，使用最新AI模型+行业模板库，结合人工精修，确保每份BP数据可靠、逻辑清晰、视觉专业。",
    "退款": "如果初稿质量不满意，全额退款。我们对自己的品质有信心！",
    "适用范围": "适用于：① 种子轮/A轮融资BP ② 路演PPT ③ 创业大赛 ④ 商业计划书申报 ⑤ 内部提案。不适用：上市公司年报、学术论文。",
}

def get_auto_reply(user_message_text: str) -> str:
    """根据买家消息自动回复"""
    text = user_message_text.lower()
    
    # 问候
    if any(w in text for w in ["你好", "您好", "hi", "hello", "在吗", "在不在", "嗨"]):
        return ("您好！欢迎来到AI商业计划书定制服务 👋\n\n"
                "我们提供24小时出稿的商业计划书/融资BP定制服务，AI智能生成+人工精修，仅需 ¥199。\n\n"
                "有什么可以帮您的？您可以直接问：价格、流程、案例、时间。")
    
    # 价格
    if any(w in text for w in ["价格", "多少钱", "费用", "价钱", "咋卖", "多少", "贵吗", "价格"]):
        return ORDER_QUESTIONS["价格"]
    
    # 流程/下单
    if any(w in text for w in ["怎么买", "如何下单", "流程", "怎么操作", "拍下", "下单"]):
        return ORDER_QUESTIONS["流程"]
    
    # 时间/速度
    if any(w in text for w in ["多久", "时间", "什么时候", "快吗", "速度", "急", "加急"]):
        return ORDER_QUESTIONS["时间"]
    
    # 修改
    if any(w in text for w in ["修改", "改", "调整", "不满意", "能改"]):
        return ORDER_QUESTIONS["修改"]
    
    # 案例
    if any(w in text for w in ["案例", "作品", "样板", "参考", "看看效果", "有样本吗"]):
        return ORDER_QUESTIONS["案例"]
    
    # 资质
    if any(w in text for w in ["靠谱", "可靠", "正规", "公司", "团队", "学历", "经验"]):
        return ORDER_QUESTIONS["资质"]
    
    # 退款
    if any(w in text for w in ["退款", "退钱", "不满意能退", "保障"]):
        return ORDER_QUESTIONS["退款"]
    
    # 适用范围
    if any(w in text for w in ["能做什么", "适用", "范围", "什么样", "行业", "什么类型"]):
        return ORDER_QUESTIONS["适用范围"]
    
    # 默认回复
    return ("感谢咨询！关于AI商业计划书定制服务，¥199/份，24小时出稿。\n\n"
            "您可以查看商品页面了解更多，或者直接告诉我您的项目和需求，"
            "我先帮您评估能否接单。\n\n"
            "常见问题：价格¥199 / 24h出稿 / 免费修改一次")


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
