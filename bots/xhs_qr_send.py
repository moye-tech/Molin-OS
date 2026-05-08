"""
小红书二维码登录 v2 — 处理Captcha + 飞书发送 + 自动保存
运行: python3.12 xhs_qr_send.py
"""
import sys, json, time, os
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".local/share/pipx/venvs/xiaohongshu-cli/lib/python3.12/site-packages"))

import requests as req
from xhs_cli.client import XhsClient
from xhs_cli.qr_login import _generate_a1, _generate_webid, _apply_session_cookies
from xhs_cli.qr_login import _build_saved_cookies
from xhs_cli.cookies import save_cookies
import qrcode

# 飞书
FEISHU_APP_ID = "cli_a956c83187395cd4"
FEISHU_APP_SECRET = "BNoCjgLp6SqdnojTE0BxofA2fyExEpPI"
NOTIFY_CHAT_ID = "oc_94c87f141e118b68c2da9852bf2f3bda"
fs_tok = {"t":"","e":0}
def fs_t():
    if fs_tok["t"] and time.time() < fs_tok["e"] - 60:
        return fs_tok["t"]
    r = req.post("https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        json={"app_id": FEISHU_APP_ID, "app_secret": FEISHU_APP_SECRET}, timeout=10)
    d = r.json()
    fs_tok["t"] = d["tenant_access_token"]
    fs_tok["e"] = time.time() + d.get("expire",7200)
    return fs_tok["t"]

def fs_text(msg):
    t = fs_t()
    req.post("https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id",
        headers={"Authorization":f"Bearer {t}","Content-Type":"application/json"},
        json={"receive_id":NOTIFY_CHAT_ID,"msg_type":"text",
              "content":json.dumps({"text":msg})},timeout=10)

def fs_img(path):
    t = fs_t()
    with open(path,"rb") as f:
        r = req.post("https://open.feishu.cn/open-apis/im/v1/images",
            headers={"Authorization":f"Bearer {t}"},
            files={"image":("qr.png",f,"image/png"),"image_type":(None,"message")},timeout=30)
    k = r.json().get("data",{}).get("image_key","")
    if not k:
        return False
    req.post("https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id",
        headers={"Authorization":f"Bearer {t}","Content-Type":"application/json"},
        json={"receive_id":NOTIFY_CHAT_ID,"msg_type":"image",
              "content":json.dumps({"image_key":k})},timeout=10)
    return True

def fs_card(title, lines, color="purple"):
    t = fs_t()
    el = [{"tag":"hr"} if l.startswith("---") else {"tag":"div","text":{"tag":"lark_md","content":l}} for l in lines]
    req.post("https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id",
        headers={"Authorization":f"Bearer {t}","Content-Type":"application/json"},
        json={"receive_id":NOTIFY_CHAT_ID,"msg_type":"interactive",
              "content":json.dumps({"config":{"wide_screen_mode":True},
                "header":{"title":{"tag":"plain_text","content":title},"template":color},
                "elements":el})},timeout=10)

def main():
    print("📱 小红书扫码登录 v2")
    fs_text("📕 正在生成新的小红书登录二维码...")
    
    # 先清空旧的cookies文件，确保用新session
    old_file = Path.home() / ".xiaohongshu-cli" / "cookies.json"
    if old_file.exists():
        os.rename(old_file, old_file.with_suffix(".json.bak"))
        print("🗑️ 已备份旧Cookie")
    
    # 生成全新的a1/webId
    a1 = _generate_a1()
    webid = _generate_webid()
    tmp_cookies = {"a1": a1, "webId": webid}
    
    with XhsClient(tmp_cookies, request_delay=0) as client:
        # 初始化会话
        try:
            act = client.login_activate()
            _apply_session_cookies(client, act)
        except:
            pass
        
        # 创建二维码
        qr = client.create_qr_login()
        qr_id, code, qr_url = qr["qr_id"], qr["code"], qr["url"]
        print(f"✅ 二维码已创建 (ID: {qr_id[:16]}...)")
        
        # 生成PNG
        img = qrcode.make(qr_url)
        img_path = "/tmp/xhs_qr_login.png"
        img.save(img_path)
        print(f"✅ 二维码图片: {img_path}")
        
        # 发飞书
        fs_img(img_path)
        fs_card("📕 小红书扫码登录", [
            "请用手机小红书App扫下方二维码",
            "---",
            "步骤:",
            "1️⃣ 打开小红书App",
            "2️⃣ 左上角菜单 → 扫一扫",
            "3️⃣ 扫描上方的二维码图片",
            "4️⃣ 在手机上点「确认登录」",
            "---",
            "⚠️ 如果提示验证码:",
            "   在手机上完成验证即可",
            "⏳ 二维码有效期4分钟"
        ])
        print("✅ 二维码已发到飞书控制台群")
        
        # 轮询
        print("\n⏳ 等待扫码...")
        start = time.time()
        notified_scan = False
        
        while time.time() - start < 240:
            time.sleep(2)
            try:
                sd = client.check_qr_status(qr_id, code)
                cs = sd.get("codeStatus", -1)
                
                if cs == 1 and not notified_scan:
                    fs_text("✅ 已扫码！请在手机上确认登录")
                    print("📲 已扫码，等待确认...")
                    notified_scan = True
                
                if cs == 2:
                    uid = sd.get("userId","")
                    print(f"🎉 登录成功！userId: {uid}")
                    
                    # 完成登录确认
                    from xhs_cli.qr_login import _complete_confirmed_session
                    comp = _complete_confirmed_session(client, qr_id, code, uid)
                    
                    # 构建cookie
                    cookies = _build_saved_cookies(a1, webid, client.cookies)
                    
                    # 保存
                    save_file = Path.home() / ".xiaohongshu-cli" / "cookies.json"
                    save_file.parent.mkdir(parents=True, exist_ok=True)
                    with open(save_file, "w") as f:
                        json.dump({
                            "a1": cookies.get("a1", ""),
                            "webId": cookies.get("webId", ""),
                            "web_session": cookies.get("web_session", ""),
                            "acw_tc": cookies.get("acw_tc", ""),
                            "saved_at": time.strftime("%Y-%m-%d %H:%M:%S")
                        }, f, ensure_ascii=False, indent=2)
                    
                    # 验证
                    print("\n验证登录状态...")
                    import subprocess
                    r = subprocess.run(["xhs","status"], capture_output=True, text=True, timeout=10)
                    print(r.stdout[:300])
                    
                    is_guest = '"guest": true' in r.stdout or "guest: true" in r.stdout
                    
                    if is_guest:
                        fs_text("⚠️ 登录后发现仍是guest账号，你可能需要用小🍠App账号而不是浏览器账号。建议在App里扫码")
                    else:
                        fs_card("🎉 小红书登录成功", [
                            "元瑶已就绪，可以发布笔记了！",
                            "---",
                            "自动发布已激活",
                            "每2小时元瑶会生成并发布小红书笔记"
                        ], "green")
                    
                    print(f"\n{'✅ 登录成功!' if not is_guest else '⚠️ 游客模式仍需认证'}")
                    return not is_guest
                    
            except Exception as e:
                err_str = str(e)
                if "Captcha" in err_str or "captcha" in err_str:
                    if not notified_scan:
                        fs_text("⚠️ 小红书需要验证码验证，请完成App内验证")
                        print("⚠️ Captcha触发，请在手机上完成验证")
                elif "timeout" in err_str.lower():
                    pass
                else:
                    pass
        
        fs_text("❌ 二维码已过期(4分钟)，如需登录请重新运行")
        print("❌ 超时")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
