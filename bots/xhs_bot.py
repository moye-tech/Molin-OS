"""
小红书自动化机器人 v3 — 完整版
热点采集 → AI内容生成 → 自动发布 全链路
运行: python3.12 xhs_bot.py check          # 单次热点检测+生成笔记 (推荐)
      python3.12 xhs_bot.py publish <title> <text> <image1> [image2...]  # 直接发布
      python3.12 xhs_bot.py generate <topic>  # 根据话题生成笔记并发布
      python3.12 xhs_bot.py hotspots         # 仅显示热点
      python3.12 xhs_bot.py test              # 测试飞书连接
"""

import os, sys, json, time, random, re, subprocess
from pathlib import Path
from datetime import datetime

# ── 机器人凭证 ─────────────────────────────────────
# 优先从.env读取，否则用硬编码默认值
try:
    from dotenv import load_dotenv
    env_path = Path.home() / ".hermes" / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass
APP_ID = os.environ.get("FEISHU_APP_ID", "cli_a956c83187395cd4")
APP_SECRET = os.environ.get("FEISHU_APP_SECRET", "")

# ── 路径 ───────────────────────────────────────────
STATE_DIR = Path.home() / ".hermes" / "xhs_bot"
STATE_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_FILE = STATE_DIR / "config.json"
STATE_FILE = STATE_DIR / "state.json"
LOG_FILE = STATE_DIR / "activity.log"

DEFAULT_CONFIG = {
    "notify_chat_id": "oc_94c87f141e118b68c2da9852bf2f3bda",
    "auto_publish": False,       # 默认不自动发，让人确认
    "auto_generate": True,       # 默认自动生成笔记内容
    "daily_topics": 3,           # 每天最多生成3个话题
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
    return {"last_check": "", "notes_generated": 0, "notes_published": 0, "status": "idle",
            "today_generated": 0, "today_date": time.strftime("%Y-%m-%d")}

def save_state(st):
    STATE_FILE.write_text(json.dumps(st, ensure_ascii=False))

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

# ── 内容生成 ───────────────────────────────────────
class XHSEngine:
    """小红书内容引擎：热点采集→AI生成→封面制作→发布"""
    
    def __init__(self):
        self.fs = FeishuClient()
        self.config = load_config()
        self.state = load_state()
        self.chat_id = self.config.get("notify_chat_id", "")
        self.key = self._get_dashscope_key()
    
    def _get_dashscope_key(self):
        try:
            env_file = Path.home() / ".hermes" / ".env"
            if env_file.exists():
                for line in env_file.read_text().splitlines():
                    if "DASHSCOPE_API_KEY" in line and "=" in line:
                        return line.split("=", 1)[1].strip()
        except:
            pass
        return os.environ.get("DASHSCOPE_API_KEY", "")
    
    def get_hotspots(self):
        """采集热点（微博+百度），返回适合小红书的选题列表"""
        hotspots = []
        import requests
        
        try:
            r = requests.get("https://weibo.com/ajax/side/hotSearch", timeout=10)
            data = r.json()
            realtime = data.get("data", {}).get("realtime", [])[:15]
            for item in realtime:
                word = item.get("word", "")
                num = item.get("num", 0)
                if word and num > 100000:
                    hotspots.append({"source": "微博", "title": word, "hot": num})
        except:
            log("⚠️ 微博热搜采集失败")
        
        try:
            r = requests.get("https://top.baidu.com/board?tab=realtime", timeout=10, 
                headers={"User-Agent": "Mozilla/5.0"})
            import re
            cards = re.findall(r'"word":"([^"]+)"', r.text)
            for card in cards[:10]:
                if not any(h["title"] == card for h in hotspots):
                    hotspots.append({"source": "百度", "title": card, "hot": 0})
        except:
            log("⚠️ 百度热搜采集失败")
        
        return hotspots
    
    def _find_xhs_angle(self, topic):
        """用千问找小红书切入角度"""
        if not self.key:
            return [f"# {topic}\n\n今天来聊聊{topic}这个话题。\n\n你觉得呢？评论区告诉我~"]
        
        import requests
        prompt = (
            f"你是一个小红书爆款笔记策划专家。话题「{topic}」\n"
            "请给出3个适合小红书的内容切入角度，每个角度包含：标题(15字内)+正文(60字左右)+表情符号。\n"
            "回复格式：每条用\"---\"分隔。要接地气、有情绪价值、适合图文笔记。"
        )
        try:
            r = requests.post(
                "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.key}"},
                json={
                    "model": "qwen-plus",
                    "input": {"messages": [
                        {"role": "system", "content": "你是小红书爆款笔记策划专家，擅长找到话题的爆款切入角度。"},
                        {"role": "user", "content": prompt}
                    ]},
                    "parameters": {"temperature": 0.8, "max_tokens": 800}
                }, timeout=20)
            text = r.json().get("output", {}).get("text", "")
            ideas = [x.strip() for x in text.split("---") if x.strip()]
            return ideas if ideas else [text]
        except Exception as e:
            log(f"⚠️ 千问生成失败: {e}")
            return [f"# {topic}\n\n{topic}这个话题最近很火，大家怎么看？"]
    
    def generate_cover(self, topic, ideas=""):
        """生成封面图——用千问文生图，带重试退避"""
        if not self.key:
            log("⚠️ 无百炼Key，跳过封面生成")
            return None
        
        import requests
        import time as _time
        
        prompt_text = (
            f"小红书封面设计，主题：{topic}。"
            f"风格：高级简约，暖色调，有文字排版感。"
            f"画面干净，ins风，适合作为小红书笔记封面。"
            f"不要出现文字。图像比例为3:4竖版。"
        )
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    wait = 5 * attempt  # 退避: 5s, 10s
                    log(f"⏳ 封面生成重试 {attempt+1}/{max_retries} (等待{wait}s)")
                    _time.sleep(wait)
                else:
                    _time.sleep(2)
                
                r = requests.post(
                    "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation",
                    headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.key}"},
                    json={
                        "model": "qwen-image-2.0-pro",
                        "input": {"messages": [{"role": "user", "content": [{"text": prompt_text}]}]},
                        "parameters": {"size": "768*1024", "n": 1}
                    }, timeout=15)
                data = r.json()
                
                # 检查API返回的错误码（限流等）
                api_code = data.get("code")
                if api_code:
                    msg = data.get("message", "")
                    log(f"⚠️ 封面API错误: {msg} (code={api_code}), attempt {attempt+1}/{max_retries}")
                    if "RateQuota" in msg or "Throttling" in api_code:
                        continue  # 限流则重试
                    return None
                
                url = data.get("output", {}).get("choices", [{}])[0].get("message", {}).get("content", [{}])[0].get("image", "")
                if url:
                    img_resp = requests.get(url, timeout=10)
                    ts = int(time.time())
                    img_path = str(STATE_DIR / f"cover_{ts}.jpg")
                    with open(img_path, "wb") as f:
                        f.write(img_resp.content)
                    log(f"✅ 封面已生成: {img_path}")
                    return img_path
                else:
                    log(f"⚠️ 封面API未返回图片URL")
                    return None
                    
            except Exception as e:
                log(f"⚠️ 封面生成异常: {e} (attempt {attempt+1}/{max_retries})")
                if attempt < max_retries - 1:
                    _time.sleep(5)
                else:
                    return None
        
        return None
    
    def publish_to_xiaohongshu(self, title, text, images):
        """用playwright发布到小红书（无头模式）
        
        如果有social-auto-upload，用sau CLI发布
        否则用Playwright模拟发布
        """
        # 方案A：检查是否有xhs-cli（首选——已在系统安装且功能完整）
        try:
            result = subprocess.run(
                ["which", "xhs"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                log("✅ 检测到xhs CLI，优先使用xhs-cli发布")
                return self._publish_via_xhs_cli(title, text, images)
        except:
            pass
        
        # 方案B：检查sau CLI是否可用（备选）
        try:
            result = subprocess.run(
                ["which", "sau"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                log("✅ 检测到sau CLI，使用social-auto-upload发布")
                return self._publish_via_sau(title, text, images)
        except:
            pass
        
        log("⚠️ 无可用发布工具（xhs-cli / sau），无法自动发布")
        return False
    
    def _publish_via_sau(self, title, text, images):
        """通过social-auto-upload的CLI发布"""
        try:
            image_args = []
            for img in images:
                image_args.extend(["--images", img])
            
            cmd = ["sau", "xiaohongshu", "upload-note"] + image_args + [
                "--title", title,
                "--note", text[:500],
                "--account", "yuanyao"
            ]
            log(f"执行: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                log(f"✅ 发布成功: {result.stdout[:200]}")
                return True
            else:
                log(f"❌ 发布失败: {result.stderr[:200]}")
                return False
        except subprocess.TimeoutExpired:
            log("❌ 发布超时")
        except Exception as e:
            log(f"❌ 发布异常: {e}")
        return False
    
    def _publish_via_xhs_cli(self, title, text, images):
        """通过xhs-cli发布小红书图文笔记"""
        try:
            image_args = []
            for img in images:
                image_args.extend(["--images", img])
            
            clean_title = title[:30]
            clean_body = text[:500]
            
            cmd = ["xhs", "post"] + image_args + [
                "--title", clean_title,
                "--body", clean_body
            ]
            log(f"📤 执行xhs-cli发布: {clean_title}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                output = result.stdout[:300]
                log(f"✅ 小红书发布成功: {output}")
                return True
            else:
                err = result.stderr[:300]
                log(f"❌ 小红书发布失败: {err}")
                return False
        except subprocess.TimeoutExpired:
            log("❌ 发布超时(120s)")
        except FileNotFoundError:
            log("❌ xhs CLI未安装")
        except Exception as e:
            log(f"❌ 发布异常: {e}")
        return False
    
    def run_check(self):
        """完整检测循环：热点→生成→通知"""
        config = load_config()
        state = load_state()
        
        log("🔍 元瑶v3 完整检测")
        
        # 检查每日限额
        today = time.strftime("%Y-%m-%d")
        if state.get("today_date") != today:
            state["today_date"] = today
            state["today_generated"] = 0
        
        if state.get("today_generated", 0) >= config.get("daily_topics", 3):
            log("⏸️ 今日生成已满额")
            if self.chat_id:
                self.fs.send_card(self.chat_id, "📕 元瑶日报", 
                    [f"今日已生成 {state.get('today_generated',0)}篇笔记",
                     f"累计生成: {state.get('notes_generated',0)}篇",
                     f"累计发布: {state.get('notes_published',0)}篇",
                     "---", "限额已用完，明天再来~"], "purple")
            return
        
        # 1. 采集热点
        hotspots = self.get_hotspots()
        if not hotspots:
            if self.chat_id:
                self.fs.send_text(self.chat_id, "⚠️ 热点采集失败")
            return
        
        log(f"📈 采集到 {len(hotspots)} 个热点")
        
        # 2. 选择话题（去掉太敏感的，选适合小红书的）
        xhs_topics = [h for h in hotspots 
                     if not any(kw in h["title"] for kw in [
                         "疫情", "政治", "死亡", "事故", "爆炸",
                         "死缓", "判刑", "死刑", "审判", "拘留",
                         "查处", "被抓", "落马", "腐败", "反腐",
                         "基层治理", "治理现代化", "统一思想", "会议精神",
                         "商务部", "外交部", "国防部", "外交部回应",
                         "中方", "坚决", "抗议", "反对", "制裁",
                         "军事", "军队", "战机", "导弹", "冲突",
                         "省委", "党支部", "党代会",
                     ])]
        selected = xhs_topics[:3]
        
        # 3. 为每个话题生成内容（最多2个话题，避免API超时）
        generated_count = state.get("today_generated", 0)
        max_topics = min(2, config.get("daily_topics", 3) - generated_count)
        notes_for_review = []
        
        for topic in selected[:max_topics]:
            title = topic["title"]
            log(f"📝 生成笔记: {title}")
            
            # 3a. 找切入角度
            ideas = self._find_xhs_angle(title)
            if not ideas:
                continue
            
            # 3b. 取第一个作为笔记内容
            note_content = ideas[0]
            
            # 3c. 生成封面
            cover_path = self.generate_cover(title)
            
            state["notes_generated"] = state.get("notes_generated", 0) + 1
            generated_count += 1
            
            note_info = {
                "topic": title,
                "content": note_content[:200],
                "cover": cover_path or "无封面",
                "source": topic.get("source", "热搜"),
                "hot": topic.get("hot", 0)
            }
            notes_for_review.append(note_info)
        
        state["today_generated"] = generated_count
        save_state(state)
        
        # 4. 飞书通知+审核请求
        if notes_for_review and self.chat_id:
            lines = []
            today_str = time.strftime("%Y-%m-%d %H:%M")
            lines.append(f"🕐 {today_str}")
            lines.append(f"📈 热点源: {len(hotspots)}条 | 已生成: {len(notes_for_review)}篇")
            lines.append("---")
            
            for i, note in enumerate(notes_for_review, 1):
                lines.append(f"## 📝 笔记 {i}: {note['topic']}")
                lines.append(f"内容: {note['content'][:100]}...")
                lines.append(f"封面: {'✅ 已生成' if note['cover'] != '无封面' else '❌ 无'}")
                lines.append(f"来源: {note['source']} (🔥{note['hot']})")
                lines.append("---")
            
            lines.append("需要我发布吗？回复\"发\"或到飞书控制台确认")
            
            result = self.fs.send_card(self.chat_id, "📕 元瑶内容生成", lines, "purple")
            log(f"📨 飞书卡片已发送 (code={result.get('code')})")
            
            if cover_path:
                log(f"📸 封面路径: {cover_path}")
        
        # 5. 如果auto_publish开启，直接发
        if config.get("auto_publish", False):
            for note in notes_for_review:
                if note["cover"] and note["cover"] != "无封面":
                    success = self.publish_to_xiaohongshu(
                        note["topic"],
                        note["content"],
                        [note["cover"]]
                    )
                    if success:
                        state["notes_published"] += 1
        
        # 更新最后检查时间
        state["last_check"] = time.strftime("%Y-%m-%d %H:%M:%S")
        state["status"] = "ok"
        save_state(state)

# ── 直接发布模式 ───────────────────────────────────
def direct_publish():
    """从命令行参数直接发布"""
    if len(sys.argv) < 4:
        print("用法: python3.12 xhs_bot.py publish <title> <text> <image1> [image2...]")
        sys.exit(1)
    
    title = sys.argv[2]
    text = sys.argv[3]
    images = sys.argv[4:]
    
    engine = XHSEngine()
    engine.publish_to_xiaohongshu(title, text, images)
    
    state = load_state()
    state["notes_published"] += 1
    save_state(state)

# ── 根据话题生成 ───────────────────────────────────
def generate_note():
    if len(sys.argv) < 3:
        print("用法: python3.12 xhs_bot.py generate <topic>")
        sys.exit(1)
    
    topic = sys.argv[2]
    engine = XHSEngine()
    
    log(f"📝 生成话题: {topic}")
    ideas = engine._find_xhs_angle(topic)
    cover = engine.generate_cover(topic)
    
    if engine.chat_id:
        lines = [f"话题: {topic}", "---"]
        for i, idea in enumerate(ideas[:2], 1):
            lines.append(f"## 方案{i}")
            lines.append(idea[:200])
            lines.append("---")
        lines.append(f"封面: {'✅' if cover else '❌'} | 路径: {cover or '无'}")
        lines.append("需要发布吗？回复\"发\"确认")
        engine.fs.send_card(engine.chat_id, "📕 新生成笔记", lines, "purple")
    
    print(f"✅ 生成完成，封面: {cover}")

# ── 入口 ───────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("""小红书机器人 v3 — 元瑶
用法:
  python3.12 xhs_bot.py check            热点检测+AI生成+通知 (推荐)
  python3.12 xhs_bot.py publish <title> <text> <img1>...  直接发布
  python3.12 xhs_bot.py generate <topic>  根据话题生成笔记
  python3.12 xhs_bot.py hotspots         仅显示热点
  python3.12 xhs_bot.py test             测试飞书连接
""")
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == "check":
        engine = XHSEngine()
        engine.run_check()
    elif action == "publish":
        direct_publish()
    elif action == "generate":
        generate_note()
    elif action == "hotspots":
        engine = XHSEngine()
        hotspots = engine.get_hotspots()
        print(f"📈 热点共 {len(hotspots)} 条:")
        for h in hotspots[:10]:
            print(f"  🔥 {h['title']} ({h['source']}) [热度:{h.get('hot','N/A')}]")
    elif action == "test":
        FeishuClient().send_text(load_config().get("notify_chat_id",""), "🤖 元瑶v3(小红书)连接测试 ✅ 支持AI内容生成")
        print("测试消息已发送")
    elif action == "send" and len(sys.argv) >= 4:
        # send <chat_id> <text>
        chat_id = sys.argv[2]
        text = " ".join(sys.argv[3:])
        FeishuClient().send_text(chat_id, text)
        print(f"已发送到 {chat_id}")
