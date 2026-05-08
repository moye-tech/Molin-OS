"""
小红书登录 — 生成二维码并通过飞书发送
然后自动等待扫码确认

用法: python3.12 xhs_qr_login.py
"""
import sys, json, time, base64, os
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".local/share/pipx/venvs/xiaohongshu-cli/lib/python3.12/site-packages"))
sys.path.insert(0, str(Path.home() / "xianyu_agent"))

import requests as req
from xhs_cli.qr_login import _http_qrcode_login

# ── 飞书配置 ──
FEISHU_APP_ID = "cli_a956c83187395cd4"
FEISHU_APP_SECRET = "BNoCjgLp6SqdnojTE0BxofA2fyExEpPI"
NOTIFY_CHAT_ID = "oc_94c87f141e118b68c2da9852bf2f3bda"

def get_feishu_token():
    r = req.post("https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        json={"app_id": FEISHU_APP_ID, "app_secret": FEISHU_APP_SECRET}, timeout=10)
    return r.json().get("tenant_access_token", "")

def send_feishu_text(text):
    token = get_feishu_token()
    r = req.post(f"https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"receive_id": NOTIFY_CHAT_ID, "msg_type": "text",
              "content": json.dumps({"text": text})}, timeout=10)
    return r.json()

def send_feishu_image(image_path):
    """通过飞书API上传图片并发送"""
    token = get_feishu_token()
    
    # 1. 上传图片
    with open(image_path, "rb") as f:
        r = req.post("https://open.feishu.cn/open-apis/im/v1/images",
            headers={"Authorization": f"Bearer {token}"},
            files={"image": (os.path.basename(image_path), f, "image/png"),
                   "image_type": (None, "message")}, timeout=30)
        img_data = r.json()
    
    image_key = img_data.get("data", {}).get("image_key", "")
    if not image_key:
        print(f"❌ 图片上传失败: {img_data}")
        return False
    
    # 2. 发送图片消息
    r = req.post(f"https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"receive_id": NOTIFY_CHAT_ID, "msg_type": "image",
              "content": json.dumps({"image_key": image_key})}, timeout=10)
    return r.json()

def send_feishu_card(title, lines, color="blue"):
    token = get_feishu_token()
    elements = []
    for line in lines:
        if line.startswith("---"): elements.append({"tag": "hr"})
        else: elements.append({"tag": "div", "text": {"tag": "lark_md", "content": line}})
    r = req.post(f"https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"receive_id": NOTIFY_CHAT_ID, "msg_type": "interactive",
              "content": json.dumps({"config": {"wide_screen_mode": True},
                "header": {"title": {"tag": "plain_text", "content": title}, "template": color},
                "elements": elements})}, timeout=10)
    return r.json()

def main():
    print("🎯 小红书登录流程启动")
    print("请扫码后回答 \"好了\"")
    
    send_feishu_text("📕 元瑶准备登录小红书，请等待二维码...")
    
    # 回调：每次状态变化时发飞书通知
    last_status = ""
    
    def on_status(msg):
        nonlocal last_status
        if msg != last_status:
            print(msg)
            last_status = msg
    
    # 启动登录
    cookies = _http_qrcode_login(on_status=on_status, timeout_s=240)
    
    if not cookies:
        send_feishu_text("❌ 小红书登录超时，请重新运行")
        return False
    
    # 保存Cookie
    save_file = Path.home() / ".xiaohongshu-cli" / "cookies.json"
    save_file.parent.mkdir(parents=True, exist_ok=True)
    save_data = {
        "a1": cookies.get("a1", ""),
        "webId": cookies.get("webId", ""),
        "web_session": cookies.get("web_session", ""),
        "acw_tc": cookies.get("acw_tc", ""),
        "saved_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    save_file.write_text(json.dumps(save_data, ensure_ascii=False, indent=2))
    
    send_feishu_card("📕 小红书登录成功", [
        f"✅ Cookie已保存",
        f"   A1: {cookies.get('a1','')[:8]}...",
        f"   WebSession: {cookies.get('web_session','')[:8]}...",
    ], "green")
    
    return True

if __name__ == "__main__":
    success = main()
    print("✅ 完成" if success else "❌ 失败")
