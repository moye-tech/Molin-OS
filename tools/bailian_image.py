#!/usr/bin/env python3
"""
百炼千问图片生成工具
用 dashscope SDK 调用 qwen-image-2.0-pro 生图，自动下载并发送到飞书

用法:
  python3 tools/bailian_image.py --prompt "描述" [--size 1024*1024] [--n 1] [--output output.jpg] [--feishu]
"""
import os
import sys
import time
import json
import argparse
import requests
from datetime import datetime

API_KEY = "sk-2d3ce929a91f433cac2d7acffc7b9707"
MAX_RETRIES = 5
RETRY_DELAY = 20
OUTPUT_DIR = os.path.expanduser("~/goofish_listing_outputs")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── 飞书发送（直接走 FeishuAdapter，不需要MEDIA语法） ──
def send_to_feishu(image_path, caption=""):
    """通过 FeishuAdapter.send_image_file() 发送图片到飞书"""
    try:
        # 直接导入 Hermes 的 FeishuAdapter
        sys.path.insert(0, os.path.expanduser("~/hermes-os"))
        from molib.ceo.main import app
        from hermes_agent.tools.feishu_adapter import FeishuAdapter
        
        # 找到 FeishuAdapter 实例 (从 app.state)
        adapter = None
        for tool in app.state.tool_registry.values():
            if hasattr(tool, 'send_image_file'):
                adapter = tool
                break
        
        if adapter is None:
            print("  未找到 FeishuAdapter 实例")
            return False
        
        # 发送图片
        result = adapter.send_image_file(
            image_path=image_path,
            chat_type="user",
            user_id="oc_16b4568be8c63c198b2cd6c4d3d11b85"
        )
        print(f"  飞书发送: {result}")
        if caption:
            adapter.send_message(chat_id="oc_16b4568be8c63c198b2cd6c4d3d11b85", text=caption)
        return True
    except Exception as e:
        print(f"  飞书发送失败: {e}")
        # fallback: 用 send_message 工具发路径
        print(f"  图片路径: {image_path}，可通过 send_message MEDIA 发送")
        return False


def generate_and_download(prompt, size="1024*1024", n=1, output=None, feishu=False):
    """调用百炼生图 + 下载 + 可选飞书发送"""
    import dashscope
    from dashscope.aigc.image_generation import ImageGeneration
    from dashscope.api_entities.dashscope_response import Message
    
    dashscope.base_http_api_url = 'https://dashscope.aliyuncs.com/api/v1'
    
    print(f"🎨 百炼·文生图")
    print(f"   模型: qwen-image-2.0-pro")
    print(f"   尺寸: {size} ×{n}")
    print(f"   提示: {prompt[:120]}{'...' if len(prompt)>120 else ''}")
    
    message = Message(role="user", content=[{"text": prompt}])
    
    for attempt in range(MAX_RETRIES):
        try:
            response = ImageGeneration.call(
                model="qwen-image-2.0-pro",
                api_key=API_KEY,
                messages=[message],
                n=n,
                size=size
            )
            
            if response.status_code == 200:
                choices = response.output.choices
                downloaded = []
                
                for i, choice in enumerate(choices):
                    for item in choice.message.content:
                        # item.keys = ['image'] (没有'type'字段)
                        url = item.get("image", "")
                        if not url:
                            continue
                        print(f"  [{i+1}] ✓ 生成成功，正在下载...")
                        
                        # 下载图片
                        session = requests.Session()
                        session.headers.update({
                            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
                            'Accept': 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8',
                            'Referer': 'https://dashscope.aliyuncs.com/'
                        })
                        r = session.get(url, allow_redirects=True, timeout=30)
                        
                        if len(r.content) > 200:
                            # 保存文件
                            if output:
                                if i == 0:
                                    fname = output
                                else:
                                    base, ext = os.path.splitext(output)
                                    fname = f"{base}_{i+1}{ext}"
                            else:
                                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                                fname = os.path.join(OUTPUT_DIR, f"bailian_{ts}_{i+1}.png")
                            
                            with open(fname, "wb") as f:
                                f.write(r.content)
                            print(f"  ✅ 已保存: {fname} ({len(r.content)/1024:.0f}KB)")
                            downloaded.append(fname)
                            
                            # 发送到飞书
                            if feishu:
                                caption = f"📸 百炼生图: {prompt[:80]}..."
                                # 用 feishu_send_image.py 发
                                import subprocess
                                subprocess.run(
                                    [sys.executable, 
                                     os.path.join(os.path.dirname(__file__), "feishu_send_image.py"),
                                     fname, caption],
                                    capture_output=True, timeout=30
                                )
                        else:
                            print(f"  ⚠️ 下载内容太小: {r.content[:50]}")
                
                if downloaded:
                    print(f"\n📎 共下载 {len(downloaded)} 张图片")
                    return {"status": "ok", "files": downloaded}
                else:
                    return {"status": "error", "message": "无有效图片下载"}
            
            elif "RateQuota" in str(response) or "Throttling" in str(response):
                wait = RETRY_DELAY * (attempt + 1)
                print(f"  ⏳ 限流，等{wait}秒... ({attempt+1}/{MAX_RETRIES})")
                time.sleep(wait)
            else:
                return {"status": "error", "code": response.status_code, "message": str(response)}
                
        except Exception as e:
            if "RateQuota" in str(e) or "Throttling" in str(e):
                wait = RETRY_DELAY * (attempt + 1)
                print(f"  ⏳ 限流异常，等{wait}秒... ({attempt+1}/{MAX_RETRIES})")
                time.sleep(wait)
            else:
                return {"status": "error", "message": f"{type(e).__name__}: {e}"}
    
    return {"status": "error", "message": "超过最大重试次数（持续限流）"}


def main():
    parser = argparse.ArgumentParser(description="百炼千问图片生成")
    parser.add_argument("--prompt", "-p", required=True, help="图片描述提示词")
    parser.add_argument("--size", "-s", default="1024*1024", help="图片尺寸 (例: 1024*1024, 1440*1440)")
    parser.add_argument("--n", type=int, default=1, help="生成数量")
    parser.add_argument("--output", "-o", help="保存文件路径")
    parser.add_argument("--feishu", action="store_true", help="发送到飞书")
    args = parser.parse_args()
    
    result = generate_and_download(args.prompt, args.size, args.n, args.output, args.feishu)
    
    if result["status"] == "ok":
        print(f"\n✅ 全部完成！")
    else:
        print(f"\n❌ 失败: {result.get('message')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
