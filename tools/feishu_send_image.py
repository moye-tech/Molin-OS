#!/usr/bin/env python3
"""
飞书图片发送工具 - 用 requests 直调飞书 API

用法:
  python3 tools/feishu_send_image.py <图片路径> [可选说明文字]
  
环境变量:
  FEISHU_APP_ID, FEISHU_APP_SECRET 或硬编码
"""
import sys
import os
import json
import requests

# ── 配置 ──
# 从环境变量读取（与 Hermes 共用配置）
APP_ID = os.environ.get("FEISHU_APP_ID", "")
APP_SECRET = os.environ.get("FEISHU_APP_SECRET", "")
CHAT_ID = "oc_16b4568be8c63c198b2cd6c4d3d11b85"


def get_tenant_token():
    """获取飞书 tenant_access_token"""
    resp = requests.post(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        json={"app_id": APP_ID, "app_secret": APP_SECRET}
    )
    data = resp.json()
    if data.get("code") != 0:
        raise Exception(f"获取token失败: {data}")
    return data["tenant_access_token"]


def upload_image(token, image_path):
    """上传图片获取 image_key"""
    with open(image_path, "rb") as f:
        resp = requests.post(
            "https://open.feishu.cn/open-apis/im/v1/images",
            headers={"Authorization": f"Bearer {token}"},
            files={"image": (os.path.basename(image_path), f, "image/png")},
            data={"image_type": "message"}
        )
    data = resp.json()
    if data.get("code") != 0:
        raise Exception(f"上传失败: {data}")
    return data["data"]["image_key"]


def send_image_message(token, image_key, chat_id, text=""):
    """发送图片消息到飞书对话"""
    content = json.dumps({"image_key": image_key})
    
    resp = requests.post(
        "https://open.feishu.cn/open-apis/im/v1/messages",
        params={"receive_id_type": "chat_id"},
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={
            "receive_id": chat_id,
            "msg_type": "image",
            "content": content
        }
    )
    data = resp.json()
    if data.get("code") != 0:
        raise Exception(f"发送失败: {data}")
    
    # 如果有说明文字，发一条文本
    if text:
        text_content = json.dumps({"text": text})
        resp2 = requests.post(
            "https://open.feishu.cn/open-apis/im/v1/messages",
            params={"receive_id_type": "chat_id"},
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json={
                "receive_id": chat_id,
                "msg_type": "text",
                "content": text_content
            }
        )
        data2 = resp2.json()
        if data2.get("code") != 0:
            print(f"⚠️ 文字说明发送失败: {data2}")
    
    return data


def send_image(image_path, text=""):
    """完整流程：获取 token → 上传 → 发送"""
    if not os.path.exists(image_path):
        print(f"❌ 文件不存在: {image_path}")
        return False
    
    file_size = os.path.getsize(image_path)
    print(f"📎 图片: {os.path.basename(image_path)} ({file_size/1024:.0f}KB)")
    
    # 1. 获取 token
    print("🔑 获取 token...")
    token = get_tenant_token()
    print("✅ token 获取成功")
    
    # 2. 上传
    print("📤 上传图片...")
    image_key = upload_image(token, image_path)
    print(f"✅ 上传成功, key={image_key}")
    
    # 3. 发送
    print("📨 发送到飞书...")
    result = send_image_message(token, image_key, CHAT_ID, text)
    print("✅ 发送成功!")
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 feishu_send_image.py <图片路径> [说明文字]")
        print("示例: python3 feishu_send_image.py test.png '这是一张测试图'")
        sys.exit(1)
    
    img_path = sys.argv[1]
    text = sys.argv[2] if len(sys.argv) > 2 else ""
    send_image(img_path, text)
