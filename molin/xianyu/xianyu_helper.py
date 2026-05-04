#!/usr/bin/env python3.12
"""
Hermes 闲鱼助手 v3 — 极致简化版
一句话 = 出图 + 发布 + 监控
"""

import sys, os, json, time, base64, asyncio, requests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from goofish_apis import XianyuApis
from utils.goofish_utils import trans_cookies, generate_device_id, generate_sign, generate_mid, get_session_cookies_str
import websockets

HOME = os.path.expanduser("~")
COOKIE_FILE = os.path.join(HOME, ".xianyu_cookies_new.txt")
BAILIAN_KEY = os.environ.get("DASHSCOPE_API_KEY")
BAILIAN_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"

# ============================================================
# 核心：千问 AI 能力
# ============================================================

def qwen_chat(prompt, model="qwen-plus"):
    """千问对话"""
    r = requests.post(BAILIAN_URL.replace("multimodal-generation", "text-generation"), 
        headers={"Content-Type":"application/json","Authorization":f"Bearer {BAILIAN_KEY}"},
        json={"model":model,"input":{"messages":[{"role":"user","content":prompt}]}},
        timeout=30)
    return r.json().get("output",{}).get("text","")

def qwen_image(prompt, output="/tmp/product_cover.png", size="1024*1024"):
    """千问文生图"""
    r = requests.post(BAILIAN_URL,
        headers={"Content-Type":"application/json","Authorization":f"Bearer {BAILIAN_KEY}"},
        json={"model":"qwen-image-2.0-pro","input":{"messages":[{"role":"user","content":[{"text":prompt}]}]},
              "parameters":{"size":size,"n":1}}, timeout=60)
    try:
        url = r.json()["output"]["choices"][0]["message"]["content"][0]["image"]
        img = requests.get(url, timeout=30).content
        with open(output, "wb") as f: f.write(img)
        return output
    except Exception as e:
        print(f"❌ 生图失败: {e}")
        return None

def qwen_vl(image_url, question):
    """千问看图"""
    r = requests.post(BAILIAN_URL,
        headers={"Content-Type":"application/json","Authorization":f"Bearer {BAILIAN_KEY}"},
        json={"model":"qwen-vl-plus","input":{"messages":[{"role":"user","content":[{"text":question},{"image":image_url}]}]}},
        timeout=30)
    try:
        content = r.json()["output"]["choices"][0]["message"]["content"]
        if isinstance(content, list): return " ".join(c.get("text","") for c in content)
        return str(content)
    except: return str(r.json())[:200]

# ============================================================
# 闲鱼 API 工具
# ============================================================

def init_api():
    cookie_str = open(COOKIE_FILE).read().strip()
    cookies = trans_cookies(cookie_str)
    return XianyuApis(cookies, generate_device_id(cookies.get("unb", "test")))

def upload_to_xianyu(api, path):
    """上传图片到闲鱼CDN"""
    r = api.upload_media(path)
    if r.get("success"):
        return r["object"]["url"], r["object"]["fileId"], r["object"]["pix"]
    return None, None, None

def publish_item(api, title, desc, price=199, image_paths=None, category="文档代写"):
    """发布商品"""
    if not image_paths:
        image_paths = ["/tmp/product_cover.png"]
    
    # 上传图片
    images = []
    for p in image_paths:
        url, fid, pix = upload_to_xianyu(api, p)
        if url:
            w, h = map(int, pix.split("x"))
            images.append({"url": url, "width": w, "height": h, "fileId": fid})
    
    if not images:
        print("❌ 图片上传全部失败")
        return None
    
    cat = {"文档代写":{"catId":"50023914","catName":"文章/软文写作服务","channelCatId":"201460608","tbCatId":"50015123"},
           "设计服务":{"catId":"50023913","catName":"创意设计服务","channelCatId":"201460609","tbCatId":"50015123"},
           "编程开发":{"catId":"50023915","catName":"编程开发服务","channelCatId":"201460610","tbCatId":"50015123"}}.get(category, {})
    
    data = {
        "itemTextDTO":{"desc":desc,"title":title,"titleDescSeparate":False},
        "itemPriceDTO":{"priceInCent":str(price*100),"origPriceInCent":str(int(price*1.5*100))},
        "freebies":False,"itemTypeStr":"b","quantity":"1","simpleItem":"true",
        "imageInfoDOList":[{"extraInfo":{"isH":"false","isT":"false","raw":"false"},"isQrCode":False,
            "url":img["url"],"heightSize":img["width"],"widthSize":img["height"],
            "major":i==0,"type":0,"status":"done"} for i,img in enumerate(images)],
        "itemPostFeeDTO":{"canFreeShipping":False,"supportFreight":False,"onlyTakeSelf":False,"templateId":"0"},
        "itemCatDTO":{"catId":cat.get("catId","50023914"),"catName":cat.get("catName","文章/软文写作服务"),
            "channelCatId":cat.get("channelCatId","201460608"),"tbCatId":cat.get("tbCatId","50015123")},
        "itemLabelExtList":[{"channelCateId":cat.get("channelCatId","201460608"),"isUserClick":"1",
            "labelType":"common","from":"newPublishChoice","text":cat.get("catName","文章/软文写作服务"),
            "propertyId":"-10000","labelFrom":"newPublish","properties":f'-10000##分类:{cat.get("channelCatId","201460608")}##{cat.get("catName","文章/软文写作服务")}'}],
        "userRightsProtocols":[{"enable":False,"serviceCode":"SKILL_PLAY_NO_MIND"}],
        "itemAddrDTO":{"area":"朝阳区","city":"北京","divisionId":"110105",
            "gps":"39.921444,116.443136","poiId":"B0FFICO1DW","poiName":"龙湖冠寓(松果冠寓店)","prov":"北京"},
        "defaultPrice":False,"uniqueCode":str(int(time.time()*1000000)),
        "sourceId":"pcMainPublish","bizcode":"pcMainPublish","publishScene":"pcMainPublish"}
    
    url = "https://h5api.m.goofish.com/h5/mtop.idle.pc.idleitem.publish/1.0/"
    params = {"jsv":"2.7.2","appKey":"34839810","t":str(int(time.time()*1000)),"v":"1.0","type":"originaljson",
              "api":"mtop.idle.pc.idleitem.publish","sessionOption":"AutoLoginOnly","dataType":"json","timeout":"20000"}
    data_val = json.dumps(data, separators=(',', ':'))
    token = api.session.cookies.get("_m_h5_tk","").split("_")[0]
    params["sign"] = generate_sign(params["t"], token, data_val)
    
    r = api.session.post(url, headers={"accept":"application/json","content-type":"application/x-www-form-urlencoded",
        "origin":"https://www.goofish.com","referer":"https://www.goofish.com/",
        "user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}, 
        params=params, data={"data":data_val}, timeout=15)
    res = r.json()
    
    if "SUCCESS" in str(res.get("ret",[""])[0]):
        item_id = res.get("data",{}).get("itemId","")
        print(f"\n🎉 发布成功！商品ID: {item_id}")
        return item_id
    else:
        print(f"❌ 发布失败: {res.get('ret')}")
        return None

# ============================================================
# 商品一键发布（AI自动生成一切）
# ============================================================

PRODUCT_TEMPLATES = {
    "商业计划书": {
        "prompt_img": "一张专业商务风商品封面，深藏蓝色渐变背景，左上角有红色装饰线。中央白色大标题\"商业计划书定制\"，下方浅灰小标题\"融资BP · 路演PPT · 创业计划书\"。右下角红色价格标签\"¥199\"。底部服务列表：AI智能框架、24小时出稿、免费修改。风格高端专业。",
        "prompt_detail": "一张白色背景信息图，顶部灰色大号字\"服务流程\"。三步骤卡片竖排：①拍下付款 → ②提供项目概况 → ③24小时交付初稿。卡片浅灰圆角边框。底部：\"免费修改一次 · 不满意全额退款\"。风格简洁。",
        "title_format": "商业计划书代写 融资BP定制 {kw}",
        "category": "文档代写",
    },
    "LOGO设计": {
        "prompt_img": "一张简洁商品封面，深蓝紫渐变背景，左上角金色装饰线。中央白色大标题\"LOGO设计定制\"，下方灰字\"品牌Logo · VI设计 · 电商主图\"。右下角红色价格标签\"¥199\"。底部：专业AI设计、无限次修改、24小时交付。",
        "prompt_detail": "白色背景信息图，顶部\"设计流程\"。四步骤横排图标卡：①需求沟通→②AI生成3稿→③选定修改→④交付源文件。底部：\"含AI源文件+高清PNG\"。风格清爽。",
        "title_format": "LOGO设计定制 品牌Logo VI设计 {kw}",
        "category": "设计服务",
    },
}

def auto_publish(product_type, price=199, keywords=""):
    """一键发布：自动生成封面+详情+标题+描述+发布"""
    print(f"\n🚀 一键发布: {product_type} (¥{price})")
    
    template = PRODUCT_TEMPLATES.get(product_type)
    if not template:
        print(f"❌ 未知品类: {product_type}")
        return None
    
    api = init_api()
    
    # 1. 生成封面图
    print("📸 生成商品封面...")
    cover = qwen_image(template["prompt_img"], "/tmp/cover.png")
    if not cover: return None
    
    # 2. 生成详情图
    print("📄 生成服务流程详情图...")
    detail = qwen_image(template["prompt_detail"], "/tmp/detail.png")
    
    # 3. 用千问生成标题和描述
    print("✍️ AI生成商品文案...")
    title = template["title_format"].format(kw=keywords if keywords else "24h出稿 无限修改")
    
    desc_prompt = f"""写一段闲鱼商品描述，品类：{product_type}，价格¥{price}。
要求：有【服务内容】【价格说明】【适用场景】三个分段，简洁有力，带emoji点缀。不要多余的话，直接给我描述文本。"""
    desc = qwen_chat(desc_prompt)
    if not desc: desc = f"{product_type}定制服务，AI智能生成+人工精修，¥{price}/份。拍前联系说明需求！"
    
    # 4. 发布（可以传多图）
    images = [cover]
    if detail: images.append(detail)
    item_id = publish_item(api, title, desc, price=price, image_paths=images, category=template["category"])
    
    if item_id:
        print(f"\n{'='*40}")
        print(f"✅ 全部完成！商品已上线")
        print(f"   标题: {title[:40]}...")
        print(f"   价格: ¥{price}")
        print(f"   商品ID: {item_id}")
        print(f"{'='*40}")
    
    return item_id

# ============================================================
# WebSocket 消息监听
# ============================================================

class XianyuMonitor:
    def __init__(self):
        self.cookie_str = open(COOKIE_FILE).read().strip()
        self.cookies = trans_cookies(self.cookie_str)
        self.myid = self.cookies.get("unb","")
        self.api = XianyuApis(self.cookies, generate_device_id(self.myid))
        self._running = True
    
    async def listen(self):
        headers = {"Cookie":get_session_cookies_str(self.api.session),"Host":"wss-goofish.dingtalk.com",
            "Connection":"Upgrade","User-Agent":"Mozilla/5.0 Chrome/133.0.0.0 Safari/537.36",
            "Origin":"https://www.goofish.com"}
        while self._running:
            try:
                async with websockets.connect("wss://wss-goofish.dingtalk.com/", extra_headers=headers,
                    ping_interval=30, close_timeout=10, open_timeout=10) as ws:
                    token = self.api.get_token()["data"]["accessToken"]
                    await ws.send(json.dumps({"lwp":"/reg","headers":{"cache-header":"app-key token ua wv",
                        "app-key":"444e9908a51d1cb236a27862abc769c9","token":token,
                        "ua":"Mozilla/5.0 Chrome/133.0.0.0 DingTalk(2.1.5) DingWeb/2.1.5",
                        "dt":"j","wv":"im:3,au:3,sy:6","did":generate_device_id(self.myid),"mid":generate_mid()}}))
                    
                    async def hb():
                        while self._running:
                            await ws.send(json.dumps({"lwp":"/!","headers":{"mid":generate_mid()}}))
                            await asyncio.sleep(15)
                    hb_task = asyncio.create_task(hb())
                    
                    print("\n✅ 消息监听已启动，等待买家咨询...")
                    try:
                        async for raw in ws:
                            try:
                                msg = json.loads(raw)
                                # ack
                                ack = {"code":200,"headers":{"mid":msg["headers"].get("mid",""),"sid":msg["headers"].get("sid","")}}
                                for k in ["app-key","ua","dt"]:
                                    if k in msg["headers"]: ack["headers"][k] = msg["headers"][k]
                                await ws.send(json.dumps(ack))
                                
                                if msg.get("lwp")=="/s/chat":
                                    try:
                                        body = msg.get("body",[])
                                        if isinstance(body,list) and len(body)>1:
                                            ext = body[1].get("message",{}).get("extension",{})
                                            sender = ext.get("reminderTitle","未知")
                                            b64 = body[1].get("message",{}).get("content",{}).get("custom",{}).get("data","")
                                            if b64:
                                                text = json.loads(base64.b64decode(b64).decode())["content"]["text"]
                                                print(f"\n💬 {sender}: {text}")
                                                # AI回复
                                                reply = qwen_chat(f"用户问：{text}\n你是闲鱼卖家，卖AI设计服务。用中文简短回复，体现专业和热情。")
                                                print(f"🤖 AI回复: {reply[:60]}...")
                                    except: pass
                            except: continue
                    finally:
                        hb_task.cancel()
            except Exception as e:
                print(f"⚠️ 重连...")
                await asyncio.sleep(5)

# ============================================================
# 主入口
# ============================================================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("""
闲鱼助手 v3 — 一句话搞定

用法:
  python3.12 xianyu_helper.py publish <品类> [价格] [关键词]
    品类: 商业计划书, LOGO设计, PPT设计, AI绘画, 小红书文案
    例子: python3.12 xianyu_helper.py publish LOGO设计 199
  
  python3.12 xianyu_helper.py monitor
    启动消息监听+AI自动回复

  python3.12 xianyu_helper.py ask <问题>
    用千问对话（备用能力）

  python3.12 xianyu_helper.py see <图片URL>
    用千问看图
""")
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == "publish":
        product = sys.argv[2] if len(sys.argv) > 2 else "商业计划书"
        price = int(sys.argv[3]) if len(sys.argv) > 3 else 199
        kw = " ".join(sys.argv[4:]) if len(sys.argv) > 4 else ""
        auto_publish(product, price, kw)
    
    elif action == "monitor":
        m = XianyuMonitor()
        asyncio.run(m.listen())
    
    elif action == "ask":
        print(qwen_chat(" ".join(sys.argv[2:])))
    
    elif action == "see":
        print(qwen_vl(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "描述这张图片的内容"))
    
    elif action == "verify":
        api = init_api()
        t = api.get_token()
        print("✅ Token有效" if "SUCCESS" in str(t.get("ret",[])) else f"❌ {t.get('ret')}")
