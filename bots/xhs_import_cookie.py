"""
小红书Cookie导入工具
把你浏览器里的Cookie粘贴进来，自动保存

用法: python3.12 xhs_import_cookie.py
然后粘贴 Cookie 字符串
"""
import sys, json, time
from pathlib import Path

def parse_cookie_js(cookie_str):
    """解析 document.cookie 输出的字符串"""
    cookies = {}
    for part in cookie_str.split(";"):
        part = part.strip()
        if "=" in part:
            key, val = part.split("=", 1)
            cookies[key.strip()] = val.strip()
    return cookies

def parse_cookie_json(json_str):
    """解析 JSON 格式的 Cookie"""
    try:
        data = json.loads(json_str)
        if isinstance(data, list):
            # Chrome EditThisCookie 格式
            return {c["name"]: c["value"] for c in data}
        elif isinstance(data, dict):
            return data
    except:
        pass
    return None

def main():
    save_file = Path.home() / ".xiaohongshu-cli" / "cookies.json"
    save_file.parent.mkdir(parents=True, exist_ok=True)
    
    print("📕 小红书Cookie导入工具")
    print("=" * 40)
    print("请从浏览器Cookie粘贴 (两种格式都支持):\n")
    print("方式1: F12 → Console → document.cookie → 复制结果")
    print("方式2: 用 EditThisCookie 扩展导出JSON\n")
    print("粘贴后按 Ctrl+D (或输入 END 单独一行后回车):")
    
    lines = []
    while True:
        try:
            line = input()
            if line.strip() == "END":
                break
            lines.append(line)
        except EOFError:
            break
    
    cookie_str = "\n".join(lines).strip()
    
    if not cookie_str:
        print("❌ 未输入任何内容")
        return False
    
    # 尝试解析
    cookies = parse_cookie_json(cookie_str)
    if not cookies:
        cookies = parse_cookie_js(cookie_str)
    
    if not cookies:
        print("❌ 无法解析Cookie，请确认格式正确")
        print(f"收到的内容: {cookie_str[:100]}...")
        return False
    
    # 检查关键字段
    has_a1 = "a1" in cookies
    has_web_session = "web_session" in cookies
    has_webId = "webId" in cookies
    
    if not has_a1:
        print("⚠️ 缺少 a1 cookie")
    if not has_web_session:
        print("⚠️ 缺少 web_session cookie (未登录?)") 
    if not has_webId:
        print("⚠️ 缺少 webId cookie")
    
    if not has_a1 and not has_web_session:
        print("❌ Cookie缺少关键字段，请确认已登录小红书网页版")
        return False
    
    # 保存
    save_data = {
        "a1": cookies.get("a1", ""),
        "webId": cookies.get("webId", cookies.get("web_session", "")[:16]),
        "web_session": cookies.get("web_session", ""),
        "acw_tc": cookies.get("acw_tc", ""),
        "web_session_sec": cookies.get("web_session_sec", ""),
        "id_token": cookies.get("id_token", ""),
        "saved_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    save_file.write_text(json.dumps(save_data, ensure_ascii=False, indent=2))
    print(f"\n✅ Cookie已保存: {save_file}")
    print(f"   字段: {list(save_data.keys())[:6]}")
    print(f"   a1: {cookies.get('a1','')[:8]}...")
    print(f"   web_session: {cookies.get('web_session','')[:8]}..." if has_web_session else "")
    
    # 验证
    import subprocess
    print("\n验证登录状态...")
    r = subprocess.run(["xhs", "status"], capture_output=True, text=True, timeout=10)
    print(r.stdout[:300])
    
    if "guest: true" in r.stdout or "'guest': True" in r.stdout:
        print("⚠️ 当前Cookie为游客模式，可能缺少完整登录态")
        print("   请确认: 1)已在浏览器登录小红书 2)复制的是完整Cookie")
    else:
        print("\n🎉 登录成功！元瑶可以发布笔记了！")
    
    return True

if __name__ == "__main__":
    main()
