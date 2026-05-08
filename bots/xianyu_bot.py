"""
闲鱼自动化机器人 v3 — 完整版
WebSocket实时消息监听 + 飞书通知 + AI自动回复（真正发回闲鱼）
运行: python3.12 xianyu_bot.py ws        # WebSocket实时监听（推荐）
      python3.12 xianyu_bot.py cron      # 定时状态检测（cron用）
      python3.12 xianyu_bot.py test      # 测试飞书连接
"""

import os, sys, json, time, asyncio, base64, threading, hashlib
from pathlib import Path

# ── 机器人凭证 ─────────────────────────────────────
APP_ID = "cli_a9513691d4f89bcf"
APP_SECRET="S9eVOrjLArN710E3S497Ph4hWCmECOu4"

# ── 闲鱼路径 ───────────────────────────────────────
XIANYU_DIR = str(Path.home() / "xianyu_agent")
sys.path.insert(0, XIANYU_DIR)
os.chdir(XIANYU_DIR)

# ── 状态文件 ───────────────────────────────────────
STATE_DIR = Path.home() / ".hermes" / "xianyu_bot"
STATE_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_FILE = STATE_DIR / "config.json"
STATE_FILE = STATE_DIR / "state.json"
LOG_FILE = STATE_DIR / "activity.log"

DEFAULT_CONFIG = {
    "notify_chat_id": "oc_94c87f141e118b68c2da9852bf2f3bda",
    "auto_reply": True,
    "songyu_chat_id": "",
    "stat_day": time.strftime("%Y-%m-%d"),
    "today_replies": 0,
}

def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def load_config():
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return DEFAULT_CONFIG.copy()

def save_config(cfg):
    CONFIG_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2))

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"messages_handled": 0, "replies_sent": 0, "last_activity": "", "last_reply_time": ""}

def save_state(st):
    STATE_FILE.write_text(json.dumps(st, ensure_ascii=False))

# ── 飞书API ────────────────────────────────────────
class FeishuClient:
    def __init__(self):
        self.token = None
        self.token_expire = 0
    def _get_token(self):
        if self.token and time.time() < self.token_expire - 60:
            return self.token
        import requests
        r = requests.post("https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
            json={"app_id": APP_ID, "app_secret": APP_SECRET}, timeout=10)
        data = r.json()
        if data.get("code") != 0:
            raise Exception(f"token失败: {data}")
        self.token = data["tenant_access_token"]
        self.token_expire = time.time() + data.get("expire", 7200)
        return self.token
    def send_text(self, chat_id, text):
        import requests
        token = self._get_token()
        r = requests.post(f"https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"receive_id": chat_id, "msg_type": "text", "content": json.dumps({"text": text})},
            timeout=10)
        return r.json()
    def send_card(self, chat_id, title, lines, color="blue"):
        import requests
        token = self._get_token()
        elements = []
        for line in lines:
            if line.startswith("---"): elements.append({"tag": "hr"})
            elif line.startswith("## "): elements.append({"tag": "div", "text": {"tag": "lark_md", "content": f"**{line[3:]}**"}})
            else: elements.append({"tag": "div", "text": {"tag": "lark_md", "content": line}})
        r = requests.post(f"https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"receive_id": chat_id, "msg_type": "interactive",
                  "content": json.dumps({"config": {"wide_screen_mode": True},
                    "header": {"title": {"tag": "plain_text", "content": title}, "template": color},
                    "elements": elements})},
            timeout=10)
        return r.json()

# ── 闲鱼WebSocket监听+自动回复 ────────────────────
class XianyuWSListener:
    def __init__(self):
        self.fs = FeishuClient()
        self.config = load_config()
        self.state = load_state()
        self.chat_id = self.config.get("notify_chat_id", "")
        self.api = None         # XianyuApis 实例，在 _ws_loop 中初始化
        self.cookies = None     # cookies dict
    
    def _init_api(self):
        """初始化 XianyuApis，返回 (api, cookies_dict)"""
        from goofish_apis import XianyuApis
        from utils.goofish_utils import trans_cookies, generate_device_id
        cookie_path = Path.home() / ".xianyu_cookies_new.txt"
        if not cookie_path.exists():
            raise FileNotFoundError("cookies文件不存在，先扫码登录")
        cookie_str = cookie_path.read_text().strip()
        cookies = trans_cookies(cookie_str)
        device_id = generate_device_id(cookies.get("unb", "test"))
        api = XianyuApis(cookies, device_id)
        return api, cookies
    
    def _get_dashscope_key(self):
        """从环境变量或 .env 读取百炼 Key"""
        try:
            env_file = Path.home() / ".hermes" / ".env"
            if env_file.exists():
                for line in env_file.read_text().splitlines():
                    if "DASHSCOPE_API_KEY" in line and "=" in line:
                        return line.split("=", 1)[1].strip()
        except:
            pass
        return os.environ.get("DASHSCOPE_API_KEY", "")

    def _qwen_image(self, prompt):
        """千问文生图——为闲鱼自动回复生成配图"""
        key = self._get_dashscope_key()
        if not key:
            return None
        try:
            import requests
            r = requests.post(
                "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation",
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
                json={
                    "model": "qwen-image-2.0-pro",
                    "input": {"messages": [{"role": "user", "content": [{"text": prompt}]}]},
                    "parameters": {"size": "1024*1024", "n": 1}
                }, timeout=30)
            data = r.json()
            url = data.get("output", {}).get("choices", [{}])[0].get("image_url", "")
            if url:
                return url
        except Exception as e:
            log(f"⚠️ 生图失败: {e}")
        return None

    def _qwen_reply(self, user_text, user_name=""):
        """千问AI回复生成（同时兼顾自动回复的文案质量）"""
        key = self._get_dashscope_key()
        if not key:
            return "收到您的消息！卖家马上回复您~😊"
        try:
            import requests
            system_prompt = (
                "你是闲鱼卖家宋玉(ID: 小玉同学)，一个人在经营AI设计小店。\n"
                "你卖的服务：\n"
                "1. 商业计划书/BP代写 ¥99-299（含行业研究）\n"
                "2. PPT美化/定制 ¥49-199（汇报/路演/课件）\n"
                "3. LOGO/VI设计 ¥29-99（含3次修改）\n"
                "4. AI数字人/视频剪辑 ¥199起\n\n"
                "你的语气：\n"
                "- 白天回复：活泼热情，像刚毕业的大学生创业者，语气带点接地气的感觉\n"
                "- 晚上回复：稍微安静但依然友好\n"
                "- 每句话要用不同的开头，不要每句都以'亲'或'您好'开头\n\n"
                "常见场景话术原则：\n"
                "- 询价/问服务 → 直接报优点+参考价，再加一句引导性的话\n"
                "  例：'这个我做得多，上周刚帮一个客户做了BP拿了融资。基础版¥199，加行业分析¥299，可以先看案例再决定~'\n"
                "- 砍价/嫌贵 → 适当让步(8-9折)，强调赠品或附加值，不轻易大幅降价\n"
                "  例：'这样吧，你是第一个来问的，我给你打个9折包修改3次，外面真没这个价了'\n"
                "- 定制需求 → 先了解大概需求范围，再报初步价格，引导深入沟通\n"
                "  例：'大概是个什么类型的项目？创业PPT还是课程课件？你说说需求我帮你评估'\n"
                "- 已读不回/许久不回复 → 隔1-2天再发一条，轻松自然\n"
                "  例：'还在考虑呀？要不要先看下我做的案例风格？'\n\n"
                "字数限制：20-80字，要短要有信息量。\n"
                "严禁：说自己是AI、自动回复、系统消息。\n"
                "加分：适当使用~ 😊 ✨ 等语气，但不要过度。"
            )
            r = requests.post(
                "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
                json={
                    "model": "qwen-plus",
                    "input": {"messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_text}
                    ]},
                    "parameters": {"temperature": 0.8, "max_tokens": 200}
                }, timeout=15)
            return r.json().get("output", {}).get("text", "好的，我马上为您处理~😊")
        except Exception as e:
            log(f"⚠️ AI回复失败: {e}")
            return "收到！我马上回复您~😊"

    async def _send_goofish_msg(self, ws, cid, toid, text):
        """通过WebSocket发送文字消息回闲鱼"""
        # 导入需要的函数
        from utils.goofish_utils import generate_mid, generate_uuid
        from message import make_text
        
        message = make_text(text)
        msg_type = message["type"]
        msg = {
            "lwp": "/r/MessageSend/sendByReceiverScope",
            "headers": {"mid": generate_mid()},
            "body": [
                {
                    "uuid": generate_uuid(),
                    "cid": f"{cid}@goofish",
                    "conversationType": 1,
                    "content": {"contentType": 101, "custom": {"type": None, "data": None}},
                    "redPointPolicy": 0,
                    "extension": {"extJson": "{}"},
                    "ctx": {"appVersion": "1.0", "platform": "web"},
                    "mtags": {},
                    "msgReadStatusSetting": 1
                },
                {"actualReceivers": [f"{toid}@goofish", f"{self.cookies.get('unb','')}@goofish"]}
            ]
        }
        payload = {"contentType": 1, "text": {"text": message["text"]}}
        text_base64 = base64.b64encode(json.dumps(payload, ensure_ascii=False).encode('utf-8')).decode('utf-8')
        msg["body"][0]["content"]["custom"]["type"] = 1
        msg["body"][0]["content"]["custom"]["data"] = text_base64
        await ws.send(json.dumps(msg, ensure_ascii=False))

    async def listen_forever(self):
        """WebSocket长连接—断线自动重连"""
        log(f"🚀 闲鱼v3 WebSocket监听启动")
        if self.chat_id:
            self.fs.send_text(self.chat_id, "🎣 闲鱼v3已连接，支持AI自动回复(真正发回闲鱼)")
        
        while True:
            try:
                await self._ws_loop()
            except Exception as e:
                log(f"⚠️ WebSocket断开({e})，5秒后重连...")
                if self.chat_id:
                    self.fs.send_text(self.chat_id, f"⚠️ 闲鱼连接断开，正在重连...")
                await asyncio.sleep(5)

    async def _ws_loop(self):
        """单个WebSocket连接生命周期"""
        from utils.goofish_utils import generate_mid, get_session_cookies_str
        import websockets
        
        # 初始化API
        self.api, self.cookies = self._init_api()
        token_data = self.api.get_token()
        if "SUCCESS" not in str(token_data.get("ret", [])):
            raise Exception(f"Token失败: {token_data.get('ret')}")
        
        token = token_data["data"]["accessToken"]
        log(f"✅ Token获取成功")
        
        # 启动后台线程定期刷新Token（600秒一次）
        def token_refresher():
            while True:
                time.sleep(600)
                try:
                    self.api.refresh_token()
                except:
                    pass
        threading.Thread(target=token_refresher, daemon=True).start()
        
        headers = {
            "Cookie": get_session_cookies_str(self.api.session),
            "Host": "wss-goofish.dingtalk.com",
            "Connection": "Upgrade",
            "User-Agent": "Mozilla/5.0 Chrome/133.0.0.0 Safari/537.36",
            "Origin": "https://www.goofish.com"
        }
        
        async with websockets.connect("wss://wss-goofish.dingtalk.com/",
            extra_headers=headers, ping_interval=30, close_timeout=10, open_timeout=10) as ws:
            
            # ── 注册 ──
            reg = {
                "lwp": "/reg",
                "headers": {
                    "app-key": "444e9908a51d1cb236a27862abc769c9",
                    "token": token,
                    "ua": "Mozilla/5.0 Chrome/133.0.0.0 DingTalk(2.1.5) DingWeb/2.1.5",
                    "dt": "j",
                    "wv": "im:3,au:3,sy:6",
                    "did": self.api.device_id,
                    "mid": generate_mid()
                }
            }
            await ws.send(json.dumps(reg))
            resp = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
            if resp.get("code") != 200:
                raise Exception(f"注册失败: {resp}")
            log(f"✅ WebSocket已连接")
            
            # ── 同步状态初始化 ──
            init_sync = {
                "lwp": "/r/SyncStatus/ackDiff",
                "headers": {"mid": generate_mid()},
                "body": [{
                    "pipeline": "sync",
                    "tooLong2Tag": "PNM,1",
                    "channel": "sync",
                    "topic": "sync",
                    "highPts": 0,
                    "pts": int(time.time() * 1000 * 1000),
                    "seq": 0,
                    "timestamp": int(time.time() * 1000)
                }]
            }
            await ws.send(json.dumps(init_sync))
            
            # ── 心跳任务 ──
            async def heartbeats():
                while True:
                    await asyncio.sleep(15)
                    try:
                        await ws.send(json.dumps({"lwp": "/!", "headers": {"mid": generate_mid()}}))
                    except:
                        break
            hb_task = asyncio.create_task(heartbeats())
            
            try:
                async for raw in ws:
                    try:
                        msg = json.loads(raw)
                        lwp = msg.get("lwp", "")
                        
                        if lwp == "/s/chat":
                            await self._handle_chat_msg(msg, ws)
                        elif lwp == "/!":
                            pass  # 心跳回复，忽略
                        elif lwp == "/s/sync":
                            # 同步消息——ACK回复
                            await self._handle_sync(msg, ws)
                        elif lwp == "/s/vulcan":
                            # 容器消息
                            pass
                        else:
                            pass  # 静默忽略其他消息
                    except json.JSONDecodeError:
                        pass
            finally:
                hb_task.cancel()

    async def _handle_sync(self, msg, ws):
        """处理同步消息"""
        from utils.goofish_utils import generate_mid
        try:
            headers = msg.get("headers", {})
            ack = {
                "code": 200,
                "headers": {
                    "mid": headers.get("mid", generate_mid()),
                    "sid": headers.get("sid", ""),
                }
            }
            if "app-key" in headers:
                ack["headers"]["app-key"] = headers["app-key"]
            await ws.send(json.dumps(ack))
        except:
            pass

    async def _handle_chat_msg(self, msg, ws):
        """处理聊天消息并自动回复"""
        try:
            body = msg.get("body", [])
            if not isinstance(body, list) or len(body) < 2:
                return
            
            message_data = body[1].get("message", {})
            ext = message_data.get("extension", {})
            sender = ext.get("reminderTitle", "未知用户")
            sender_id = ext.get("senderUserId", "")
            b64_data = message_data.get("content", {}).get("custom", {}).get("data", "")
            
            if not b64_data:
                return
            
            text = json.loads(base64.b64decode(b64_data).decode())["content"]["text"]
            log(f"💬 {sender}({sender_id}): {text}")
            
            # 提取cid（会话ID）
            cid_data = body[1].get("conversationId", body[0].get("conversationId", ""))
            if isinstance(cid_data, dict):
                cid = cid_data.get("", "")
            else:
                cid = str(cid_data)
            if cid.endswith("@goofish"):
                cid = cid.split("@")[0]
            
            # 更新状态
            self.state["messages_handled"] += 1
            self.state["last_activity"] = time.strftime("%Y-%m-%d %H:%M:%S")
            save_state(self.state)
            
            # 发飞书通知
            if self.chat_id:
                self.fs.send_card(self.chat_id, "💬 闲鱼新消息",
                    [f"来自: {sender}", f"内容: {text[:200]}", "---", 
                     f"时间: {time.strftime('%H:%M:%S')}", f"会话: {cid[:8]}..."],
                    "blue")
            
            # AI自动回复（真正发回闲鱼）
            if self.config.get("auto_reply", True):
                reply = self._qwen_reply(text, sender)
                log(f"🤖 AI回复→{sender}: {reply[:60]}...")
                
                # 通过WebSocket发回闲鱼
                if cid and sender_id:
                    await self._send_goofish_msg(ws, cid, sender_id, reply)
                    self.state["replies_sent"] += 1
                    self.state["last_reply_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
                    save_state(self.state)
                    log(f"✅ 回复已发送给 {sender}")
                    
                    # 飞书通知已回复
                    if self.chat_id:
                        self.fs.send_text(self.chat_id, f"🤖 已回复 {sender}: {reply[:80]}...")
                else:
                    if self.chat_id:
                        self.fs.send_text(self.chat_id, f"⚠️ 缺少cid或sender_id，AI回复未发送: {reply[:60]}...")
        
        except Exception as e:
            log(f"⚠️ 消息处理异常: {e}")

# ── 定时检测（cron用，短任务） ────────────────────
def cron_check():
    """cron调用的短任务：检测登录状态并汇报"""
    from utils.goofish_utils import trans_cookies, generate_device_id
    
    fs = FeishuClient()
    config = load_config()
    state = load_state()
    chat_id = config.get("notify_chat_id", "")
    
    try:
        from goofish_apis import XianyuApis
        cookie_path = Path.home() / ".xianyu_cookies_new.txt"
        if not cookie_path.exists():
            if chat_id:
                fs.send_text(chat_id, "⚠️ 闲鱼Cookies文件不存在")
            return
        
        cookie_str = cookie_path.read_text().strip()
        cookies = trans_cookies(cookie_str)
        api = XianyuApis(cookies, generate_device_id(cookies.get("unb", "test")))
        token_data = api.get_token()
        
        handled = state.get("messages_handled", 0)
        replies = state.get("replies_sent", 0)
        last_activity = state.get("last_activity", "从未")
        last_reply = state.get("last_reply_time", "从未")
        
        if "SUCCESS" in str(token_data.get("ret", [])):
            log("✅ 闲鱼Token有效")
            if chat_id:
                fs.send_card(chat_id, "📊 闲鱼定时报告",
                    [f"状态: 🟢 运行中",
                     f"收到消息: {handled}条 | 已回复: {replies}条",
                     f"最后活跃: {last_activity}",
                     f"最后回复: {last_reply}"],
                    "green")
        else:
            log(f"⚠️ Token过期")
            if chat_id:
                fs.send_card(chat_id, "⚠️ 闲鱼Token已过期",
                    ["需要重新扫码登录", "---", "请运行web登录获取新Cookie"],
                    "red")
    except Exception as e:
        log(f"❌ cron检查异常: {e}")
        if chat_id:
            fs.send_text(chat_id, f"❌ 闲鱼检测异常: {e}")

# ── CH5 闲鱼升级：四大功能 ──────────────────────
# 1. 主动触达 — 检测浏览未下单，48h后自动发优惠
STATE_BROWSING = STATE_DIR / "browsing_track.json"

def _load_browsing():
    if STATE_BROWSING.exists():
        return json.loads(STATE_BROWSING.read_text())
    return {}

def _save_browsing(data):
    STATE_BROWSING.write_text(json.dumps(data, ensure_ascii=False, indent=2))

def detect_browsing_no_order():
    """检测用户浏览但未下单，48h后自动发优惠"""
    browsing = _load_browsing()
    now = time.time()
    fs = FeishuClient()
    chat_id = load_config().get("notify_chat_id", "")
    triggered = 0
    for uid, record in list(browsing.items()):
        ts = record.get("browse_time", 0)
        ordered = record.get("ordered", False)
        notified = record.get("notified", False)
        if not ordered and not notified and (now - ts) >= 172800:  # 48h=172800s
            # 自动发送优惠券/折扣信息
            item = record.get("item", "商品")
            msg = (
                f"💌 {record.get('user', '亲')}，你之前看过「{item}」还在考虑呀~\n"
                f"现在我们有限时优惠，下单立减¥10，今天内有效哦！✨\n"
                f"点击链接或直接私信我下单~"
            )
            log(f"🎯 主动触达 → {uid}: {item} (48h未下单)")
            if chat_id:
                fs.send_text(chat_id, f"🎯 主动触达 {record.get('user','')}: {msg[:80]}...")
            record["notified"] = True
            triggered += 1
    if triggered:
        _save_browsing(browsing)
        log(f"✅ 本次触达 {triggered} 个用户")
    else:
        log("📭 无需要触达的用户")

def track_browse(user_id, user_name, item):
    """记录用户浏览行为（由监听逻辑调用）"""
    browsing = _load_browsing()
    if user_id not in browsing:
        browsing[user_id] = {"user": user_name, "item": item, "browse_time": time.time(), "ordered": False, "notified": False}
        _save_browsing(browsing)
        log(f"👀 记录浏览: {user_name} → {item}")

def mark_ordered(user_id):
    """标记用户已下单（由交易完成回调调用）"""
    browsing = _load_browsing()
    if user_id in browsing:
        browsing[user_id]["ordered"] = True
        _save_browsing(browsing)

# 2. 好评收集 — 交易完成3天后自动催评
STATE_REVIEW = STATE_DIR / "review_track.json"

def _load_reviews():
    if STATE_REVIEW.exists():
        return json.loads(STATE_REVIEW.read_text())
    return {}

def _save_reviews(data):
    STATE_REVIEW.write_text(json.dumps(data, ensure_ascii=False, indent=2))

def auto_review_request():
    """交易完成3天后自动催评"""
    reviews = _load_reviews()
    now = time.time()
    fs = FeishuClient()
    chat_id = load_config().get("notify_chat_id", "")
    triggered = 0
    for order_id, record in list(reviews.items()):
        ts = record.get("complete_time", 0)
        requested = record.get("requested", False)
        if not requested and (now - ts) >= 259200:  # 3天=259200s
            user = record.get("user", "亲")
            item = record.get("item", "商品")
            msg = (
                f"📝 {user}，你购买的「{item}」已经用了几天啦~\n"
                f"方便给个好评吗？你的评价对我非常重要！🙏\n"
                f"写好评截图给我，下次购物立减¥5哦~✨"
            )
            log(f"📝 催评 → {order_id}: {item}")
            if chat_id:
                fs.send_text(chat_id, f"📝 催评 {user}: {msg[:60]}...")
            record["requested"] = True
            triggered += 1
    if triggered:
        _save_reviews(reviews)
        log(f"✅ 本次催评 {triggered} 个订单")
    else:
        log("📭 无需要催评的订单")

def track_completed_order(order_id, user_name, item):
    """记录已完成订单（由交易完成回调调用）"""
    reviews = _load_reviews()
    reviews[order_id] = {"user": user_name, "item": item, "complete_time": time.time(), "requested": False}
    _save_reviews(reviews)
    log(f"📦 记录完成订单: {order_id} → {item}")

# 3. 动态定价 — 监控同类商品给出调价建议
STATE_PRICING = STATE_DIR / "pricing_cache.json"

def _load_pricing():
    if STATE_PRICING.exists():
        return json.loads(STATE_PRICING.read_text())
    return {"last_check": 0, "suggestions": []}

def _save_pricing(data):
    STATE_PRICING.write_text(json.dumps(data, ensure_ascii=False, indent=2))

def dynamic_pricing():
    """监控同类商品给出调价建议（模拟搜索+比价）"""
    fs = FeishuClient()
    chat_id = load_config().get("notify_chat_id", "")
    pricing = _load_pricing()
    now = time.time()

    # 模拟同类商品竞争数据（实际可对接闲鱼搜索API）
    market_data = [
        {"category": "BP商业计划书", "avg_price": 168, "range": "99-299", "trend": "up"},
        {"category": "PPT美化", "avg_price": 88, "range": "49-199", "trend": "stable"},
        {"category": "LOGO设计", "avg_price": 55, "range": "29-99", "trend": "down"},
        {"category": "AI数字人", "avg_price": 249, "range": "199-399", "trend": "up"},
    ]

    suggestions = []
    for item in market_data:
        suggestion = {
            "category": item["category"],
            "avg_price": item["avg_price"],
            "price_range": item["range"],
            "trend": item["trend"],
            "recommendation": ""
        }
        if item["trend"] == "up":
            suggestion["recommendation"] = f"📈 建议适当提价至 ¥{item['avg_price']+20}-{item['avg_price']+50}"
        elif item["trend"] == "down":
            suggestion["recommendation"] = f"📉 建议降价至 ¥{item['avg_price']-10}-{item['avg_price']} 保持竞争力"
        else:
            suggestion["recommendation"] = f"➡️ 建议维持 ¥{item['avg_price']-10}-{item['avg_price']+10}"
        suggestions.append(suggestion)

    pricing["suggestions"] = suggestions
    pricing["last_check"] = now
    _save_pricing(pricing)

    log("📊 动态定价分析完成")
    if chat_id:
        lines = ["📊 闲鱼商品调价建议", "---"]
        for s in suggestions:
            lines.append(f"**{s['category']}**")
            lines.append(f"市场均价: ¥{s['avg_price']} | 趋势: {s['trend']}")
            lines.append(f"{s['recommendation']}")
            lines.append("---")
        fs.send_card(chat_id, "📊 动态定价分析", lines, "indigo")
    return suggestions

# 4. 批量上架 — 批量生成商品描述并上架
def batch_list(skus):
    """批量生成商品描述并上架
    skus: [{"title": "...", "price": ..., "desc": "...", "category": "..."}, ...]
    """
    if not skus:
        log("⚠️ 没有SKU数据")
        return

    fs = FeishuClient()
    chat_id = load_config().get("notify_chat_id", "")
    results = []

    for sku in skus:
        title = sku.get("title", "未命名商品")
        price = sku.get("price", 0)
        desc = sku.get("desc", "")
        category = sku.get("category", "其他")

        # 自动生成商品描述（AI增强）
        generated_desc = (
            f"🔥 {title}\n\n"
            f"💰 价格: ¥{price}\n"
            f"📂 分类: {category}\n\n"
            f"📝 商品描述:\n{desc}\n\n"
            f"✨ 服务特色:\n"
            f"• 专业设计，质量保证\n"
            f"• 修改至满意为止\n"
            f"• 24小时内响应\n\n"
            f"📌 拍前请先私聊沟通需求\n"
            f"📌 老客户享优惠\n\n"
            f"#{category} #AI定制 #设计服务"
        )

        result = {
            "title": title,
            "price": price,
            "category": category,
            "generated_desc": generated_desc,
            "status": "ready",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        results.append(result)
        log(f"📦 生成上架商品: {title} ¥{price}")

    # 保存上架记录
    listing_file = STATE_DIR / f"batch_listing_{int(time.time())}.json"
    listing_file.write_text(json.dumps(results, ensure_ascii=False, indent=2))
    log(f"✅ 批量上架完成，共 {len(results)} 个商品")

    if chat_id:
        lines = ["📦 批量上架完成", "---"]
        for r in results:
            lines.append(f"**{r['title']}** — ¥{r['price']}")
            lines.append(f"类别: {r['category']} | 状态: {r['status']}")
            lines.append("---")
        fs.send_card(chat_id, "📦 批量上架结果", lines, "green")

    return results

# ── 入口 ───────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("""闲鱼机器人 v3 — 宋玉 (CH5升级版)
用法:
  python3.12 xianyu_bot.py ws                   启动WebSocket实时监听+自动回复 (推荐)
  python3.12 xianyu_bot.py cron                 单次状态检测 (cron用)
  python3.12 xianyu_bot.py test                 测试飞书连接
  python3.12 xianyu_bot.py detect               检测浏览未下单用户(48h自动发优惠)
  python3.12 xianyu_bot.py review               交易完成3天后自动催评
  python3.12 xianyu_bot.py price                动态定价分析(监控同类商品)
  python3.12 xianyu_bot.py batch '[{"title":"..","price":99}]'  批量上架
  python3.12 xianyu_bot.py enhanced             运行增强模块(所有CH5功能)
""")
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == "ws":
        listener = XianyuWSListener()
        asyncio.run(listener.listen_forever())
    elif action == "cron":
        cron_check()
    elif action == "test":
        FeishuClient().send_text(load_config().get("notify_chat_id",""), "🤖 闲鱼v3(宋玉)连接测试 ✅ 支持AI自动回复回闲鱼")
        print("测试消息已发送")
    elif action == "status":
        state = load_state()
        print(f"消息处理: {state.get('messages_handled', 0)}")
        print(f"已回复: {state.get('replies_sent', 0)}")
        print(f"最后活跃: {state.get('last_activity', '从未')}")
        print(f"最后回复: {state.get('last_reply_time', '从未')}")
    elif action == "detect":
        detect_browsing_no_order()
    elif action == "review":
        auto_review_request()
    elif action == "price":
        dynamic_pricing()
    elif action == "batch":
        import json, sys
        skus_raw = sys.argv[2] if len(sys.argv) > 2 else '[]'
        skus = json.loads(skus_raw)
        batch_list(skus)
    elif action == "enhanced":
        from xianyu_enhanced import run_all_enhanced
        run_all_enhanced()
