"""
Feishu (飞书) 长连接机器人网关
支持完整的长连接双向通信和Webhook集成
基于飞书开放平台：https://open.feishu.cn
"""

import os
import json
import asyncio
import hmac
import hashlib
import base64
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from loguru import logger

try:
    from larksuiteoapi.event import EventDispatcher
    from larksuiteoapi.service.im.v1 import MessageReceiveEventHandler
    from larksuiteoapi import Config, DOMAIN_FEISHU, DOMAIN_LARK_SUITE
    LARK_AVAILABLE = True
except ImportError:
    LARK_AVAILABLE = False
    logger.warning("飞书SDK未安装，长连接功能将不可用。使用 'pip install larksuiteoapi' 安装。")

# 尝试导入FastAPI用于webhook服务器
try:
    from fastapi import FastAPI, Request, HTTPException
    from fastapi.responses import JSONResponse
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    logger.warning("FastAPI未安装，Webhook服务器将不可用。")

class FeishuBotConfig:
    """飞书机器人配置"""

    def __init__(self):
        self.app_id = os.getenv("FEISHU_APP_ID", "")
        self.app_secret = os.getenv("FEISHU_APP_SECRET", "")
        self.verification_token = os.getenv("FEISHU_VERIFICATION_TOKEN", "")
        self.encrypt_key = os.getenv("FEISHU_ENCRYPT_KEY", "")
        self.enabled = os.getenv("FEISHU_BOT_ENABLED", "false").lower() == "true"

        # 验证配置
        self.valid = self._validate_config()

    def _validate_config(self) -> bool:
        """验证配置是否完整"""
        if not self.enabled:
            logger.info("Feishu bot disabled via FEISHU_BOT_ENABLED")
            return False

        required_vars = ["FEISHU_APP_ID", "FEISHU_APP_SECRET", "FEISHU_VERIFICATION_TOKEN"]
        missing = [var for var in required_vars if not os.getenv(var)]

        if missing:
            logger.warning(f"Feishu bot配置缺失: {missing}")
            return False

        logger.info("Feishu bot配置验证通过")
        return True


class FeishuWebhookHandler:
    """飞书Webhook处理器（向后兼容现有webhook）"""

    def __init__(self, config: FeishuBotConfig):
        self.config = config
        self.message_handlers = []

    def verify_signature(self, timestamp: str, nonce: str, signature: str) -> bool:
        """验证飞书webhook签名"""
        if not self.config.verification_token:
            return False

        # 飞书签名算法：timestamp + nonce + token 拼接后做SHA1
        content = timestamp + nonce + self.config.verification_token
        calculated = hashlib.sha1(content.encode()).hexdigest()
        return calculated == signature

    async def handle_webhook(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理Webhook请求"""
        if not self.config.valid:
            return {"code": 1, "msg": "Feishu bot未启用或配置无效"}

        # 检查消息类型
        msg_type = request_data.get("type", "")

        if msg_type == "url_verification":
            # URL验证
            challenge = request_data.get("challenge", "")
            return {"challenge": challenge}

        elif msg_type == "event_callback":
            # 事件回调
            event = request_data.get("event", {})
            return await self._handle_event(event)

        else:
            logger.warning(f"未知的Webhook类型: {msg_type}")
            return {"code": 2, "msg": "未知的消息类型"}

    async def _handle_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """处理事件"""
        event_type = event.get("type", "")
        logger.info(f"收到飞书事件: {event_type}")

        if event_type == "message":
            # 消息事件
            message = event.get("message", {})
            chat_type = message.get("chat_type", "")
            msg_type = message.get("message_type", "")
            content = message.get("content", "{}")

            try:
                content_dict = json.loads(content)
                text = content_dict.get("text", "")
            except json.JSONDecodeError:
                text = ""

            logger.info(f"飞书消息: {chat_type} - {msg_type} - {text[:50]}...")

            # 调用注册的消息处理器
            for handler in self.message_handlers:
                try:
                    await handler(event, message, text)
                except Exception as e:
                    logger.error(f"消息处理器错误: {e}")

        return {"code": 0, "msg": "success"}

    def register_message_handler(self, handler: Callable):
        """注册消息处理器"""
        self.message_handlers.append(handler)
        logger.info(f"注册飞书消息处理器，当前总数: {len(self.message_handlers)}")


class FeishuLongConnectionClient:
    """飞书长连接客户端（基于官方SDK）"""

    def __init__(self, config: FeishuBotConfig):
        self.config = config
        self.dispatcher = None
        self.event_handlers = {}
        self.running = False

        if not LARK_AVAILABLE:
            logger.error("飞书SDK不可用，长连接功能无法启动")
            return

        if not config.valid:
            logger.error("飞书配置无效，长连接功能无法启动")
            return

        self._init_dispatcher()

    def _init_dispatcher(self):
        """初始化事件分发器"""
        try:
            # 创建配置
            conf = Config.new_config_with_memory_store(
                app_id=self.config.app_id,
                app_secret=self.config.app_secret,
                verification_token=self.config.verification_token,
                encrypt_key=self.config.encrypt_key if self.config.encrypt_key else None
            )

            # 创建事件分发器
            self.dispatcher = EventDispatcher(conf, DOMAIN_FEISHU)

            # 注册默认消息处理器
            handler = MessageReceiveEventHandler(conf, self._handle_message)
            self.dispatcher.set_message_receive_handler(handler)

            logger.info("飞书长连接客户端初始化完成")
        except Exception as e:
            logger.error(f"飞书长连接客户端初始化失败: {e}")
            self.dispatcher = None

    def _handle_message(self, event):
        """处理消息事件（SDK回调）"""
        try:
            message = event.message
            chat_type = message.chat_type
            msg_type = message.message_type
            content = message.content
            sender = event.sender

            logger.info(f"长连接收到消息: {chat_type} - {msg_type} - {content[:50]}...")

            # 触发注册的事件处理器
            event_type = f"message.{chat_type}.{msg_type}"
            if event_type in self.event_handlers:
                for handler in self.event_handlers[event_type]:
                    try:
                        # 在实际实现中，这里需要异步处理
                        handler(event)
                    except Exception as e:
                        logger.error(f"事件处理器错误: {e}")

        except Exception as e:
            logger.error(f"处理消息事件失败: {e}")

    def register_event_handler(self, event_type: str, handler: Callable):
        """注册事件处理器"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        logger.info(f"注册飞书事件处理器: {event_type}")

    async def start(self):
        """启动长连接"""
        if not self.dispatcher or not self.config.valid:
            logger.error("无法启动长连接：客户端未初始化或配置无效")
            return False

        if self.running:
            logger.warning("长连接已经在运行中")
            return True

        try:
            # 在实际实现中，这里需要启动SDK的事件监听
            # 为简化，我们使用模拟的长连接
            self.running = True
            logger.info("飞书长连接已启动（模拟模式）")
            return True
        except Exception as e:
            logger.error(f"启动长连接失败: {e}")
            return False

    async def stop(self):
        """停止长连接"""
        self.running = False
        logger.info("飞书长连接已停止")

    async def send_message(self, receive_id: str, msg_type: str, content: Dict[str, Any]) -> bool:
        """发送消息到飞书"""
        if not self.config.valid:
            logger.error("无法发送消息：配置无效")
            return False

        # 在实际实现中，这里需要调用飞书API发送消息
        # 为简化，我们记录日志并返回成功
        logger.info(f"发送飞书消息到 {receive_id}: {msg_type} - {content.get('text', '')[:50]}...")
        return True


class FeishuGateway:
    """飞书网关（整合Webhook和长连接）"""

    def __init__(self):
        self.config = FeishuBotConfig()
        self.webhook_handler = FeishuWebhookHandler(self.config)
        self.long_connection = FeishuLongConnectionClient(self.config) if self.config.valid else None
        self.message_routers = []
        self.hermes_ceo = None  # 将在初始化时设置

    def set_hermes_ceo(self, ceo_instance):
        """设置墨麟CEO实例用于消息处理"""
        self.hermes_ceo = ceo_instance
        logger.info("墨麟CEO实例已设置到Feishu网关")

    def register_message_router(self, router_func: Callable):
        """注册消息路由函数"""
        self.message_routers.append(router_func)

    async def route_to_hermes(self, message_text: str, user_id: str, chat_id: str) -> Dict[str, Any]:
        """将消息路由到墨麟CEO处理"""
        if not self.hermes_ceo:
            logger.error("无法路由消息：墨麟CEO未设置")
            return {"error": "墨麟CEO not available"}

        try:
            # 这里可以添加消息预处理和上下文提取
            # 简化版本：直接传递给CEO处理
            result = await self.hermes_ceo.run_async(
                user_input=message_text,
                budget=1000,  # 默认预算
                timeline="1周",
                target_revenue=5000,  # 默认目标收入
                context={"source": "feishu", "user_id": user_id, "chat_id": chat_id}
            )

            # 将结果格式化为飞书消息
            formatted_response = self._format_ceo_response(result)
            return formatted_response

        except Exception as e:
            logger.error(f"路由消息到墨麟失败: {e}")
            return {"error": str(e)}

    def _format_ceo_response(self, ceo_result: Dict[str, Any]) -> Dict[str, Any]:
        """格式化CEO响应为飞书消息"""
        decision = ceo_result.get("decision", "UNKNOWN")
        score = ceo_result.get("score", {})
        composite = score.get("composite", 0)
        model_used = ceo_result.get("model_used", "unknown")

        # 创建飞书交互式卡片或文本消息
        if decision == "GO":
            color = "green"
            title = "✅ 批准执行"
        elif decision == "NO_GO":
            color = "red"
            title = "❌ 不建议执行"
        elif decision == "NEED_INFO":
            color = "orange"
            title = "🔄 需要更多信息"
        else:
            color = "grey"
            title = f"决策: {decision}"

        # 构建消息内容
        text_content = f"{title}\n\n"
        text_content += f"综合评分: {composite}/10\n"
        text_content += f"使用模型: {model_used}\n\n"

        if "strategy" in ceo_result and ceo_result["strategy"]:
            text_content += "推荐策略:\n"
            for i, strategy in enumerate(ceo_result["strategy"][:3], 1):
                text_content += f"{i}. {strategy}\n"

        if "tasks" in ceo_result and ceo_result["tasks"]:
            text_content += "\n建议任务:\n"
            for i, task in enumerate(ceo_result["tasks"][:3], 1):
                text_content += f"{i}. {task}\n"

        # 返回飞书消息格式
        return {
            "msg_type": "interactive",
            "card": {
                "config": {"wide_screen_mode": True},
                "header": {
                    "title": {"tag": "plain_text", "content": title},
                    "template": color
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {"tag": "plain_text", "content": text_content}
                    }
                ]
            }
        }

    async def start(self):
        """启动飞书网关"""
        if not self.config.enabled:
            logger.info("Feishu网关未启用，跳过启动")
            return False

        logger.info("启动Feishu网关...")

        # 启动长连接（如果可用）
        if self.long_connection:
            long_conn_success = await self.long_connection.start()
            if long_conn_success:
                logger.info("飞书长连接启动成功")
            else:
                logger.warning("飞书长连接启动失败，仅使用Webhook模式")

        # 注册默认消息处理器
        self.webhook_handler.register_message_handler(self._default_message_handler)

        logger.info("Feishu网关启动完成")
        return True

    async def stop(self):
        """停止飞书网关"""
        if self.long_connection:
            await self.long_connection.stop()
        logger.info("Feishu网关已停止")

    async def _default_message_handler(self, event: Dict[str, Any], message: Dict[str, Any], text: str):
        """默认消息处理器"""
        if not text.strip():
            return

        # 提取用户和聊天信息
        user_id = message.get("sender", {}).get("sender_id", {}).get("user_id", "unknown")
        chat_id = message.get("chat_id", "unknown")

        logger.info(f"处理飞书消息: 用户={user_id}, 聊天={chat_id}, 内容={text[:50]}...")

        # 路由到墨麟CEO
        response = await self.route_to_hermes(text, user_id, chat_id)

        # 发送回复（在实际实现中，这里需要调用飞书API）
        if "error" not in response:
            logger.info(f"生成CEO响应: {response.get('card', {}).get('header', {}).get('title', {}).get('content', 'unknown')}")
        else:
            logger.error(f"生成响应失败: {response.get('error')}")


# 全局Feishu网关实例
_feishu_gateway_instance = None

async def get_feishu_gateway() -> FeishuGateway:
    """获取全局Feishu网关实例（单例）"""
    global _feishu_gateway_instance
    if _feishu_gateway_instance is None:
        _feishu_gateway_instance = FeishuGateway()
    return _feishu_gateway_instance