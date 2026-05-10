"""
飞书长连接 WebSocket Bot 主程序（FS-3）
独立进程运行，通过 HTTP 调用本地 CEO API
审批交互式卡片（FS-1）+ 快捷指令（FS-4）+ 操作人鉴权（FS-8）
"""

import os
import json
import asyncio
import time
import httpx
from typing import Dict, Any, List, Optional
from loguru import logger

HERMES_API = os.getenv("HERMES_API_URL", "http://hermes:8000")
CEO_API_URL = os.getenv("CEO_API_URL", f"{HERMES_API}/api/chat")

# FS-8: 操作员白名单
APPROVED_OPERATORS = [
    op.strip() for op in os.getenv("FEISHU_APPROVED_OPERATORS", "").split(",") if op.strip()
]

# FS-4: 快捷指令路由表
SHORTCUTS = {
    r'/approve': 'approve',
    r'/reject': 'reject',
    r'/dashboard': 'dashboard',
    r'/report': 'report',
    r'/status': 'status',
}


def _check_operator(user_id: str) -> bool:
    """FS-8: 验证操作员是否在白名单中"""
    if not APPROVED_OPERATORS:
        return True
    return user_id in APPROVED_OPERATORS


async def send_feishu_reply(chat_id: str, text: str) -> bool:
    """通过飞书 API 发送文本消息到指定聊天"""
    token = await get_feishu_token()
    if not token:
        logger.warning("飞书 token 不可用，无法回复消息")
        return False
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "receive_id": chat_id,
                    "msg_type": "text",
                    "content": json.dumps({"text": text}),
                },
                timeout=10,
            )
            data = resp.json()
            return data.get("code") == 0
    except Exception as e:
        logger.error(f"飞书回复发送失败: {e}")
        return False


async def send_detail_card(chat_id: str, agency_name: str, content: str) -> bool:
    """以飞书交互卡片形式发送子公司完整报告，自动适配 lark_md 富文本格式"""
    token = await get_feishu_token()
    if not token:
        logger.warning("飞书 token 不可用，无法发送详情卡片")
        return False

    safe_content = content[:8000] if content else "暂无详情"

    card = {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": f"{agency_name} 完整报告"},
            "template": "turquoise",
        },
        "elements": [
            {
                "tag": "markdown",
                "content": safe_content,
            },
            {"tag": "hr"},
            {
                "tag": "note",
                "elements": [{"tag": "plain_text", "content": f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}"}],
            },
        ],
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "receive_id": chat_id,
                    "msg_type": "interactive",
                    "content": json.dumps(card),
                },
                timeout=10,
            )
            data = resp.json()
            if data.get("code") == 0:
                logger.info(f"详情卡片发送成功: {agency_name}")
                return True
            else:
                logger.warning(f"详情卡片发送失败 ({data.get('code')}): {data.get('msg')}")
                return False
    except Exception as e:
        logger.error(f"详情卡片发送异常: {e}")
        return False


async def push_approval_card_to_chat(
    chat_id: str,
    approval_id: str,
    title: str,
    description: str,
    tool_name: str = "",
    command: str = "",
    risk_level: str = "MEDIUM",
    params_json: str = "",
) -> bool:
    """推送审批交互式卡片到指定飞书聊天

    v6.6 扩展：支持显示工具名、命令、风险级别、参数 JSON，
    并添加第三个"修改参数"按钮。
    """
    token = await get_feishu_token()
    if not token:
        logger.warning("飞书 token 不可用，审批卡片推送跳过")
        return False

    # 构建结构化描述
    detail_parts = [description]
    if tool_name:
        detail_parts.append(f"**工具：** {tool_name}")
    if command:
        detail_parts.append(f"**命令：** {command}")
    if risk_level:
        risk_labels = {"LOW": "低风险", "MEDIUM": "中风险", "HIGH": "高风险", "HUMAN_REQUIRED": "强制人工"}
        detail_parts.append(f"**风险级别：** {risk_labels.get(risk_level, risk_level)}")
    if params_json:
        detail_parts.append(f"**参数：**\n```json\n{params_json}\n```")

    card = {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": f"待审批：{title}"},
            "template": "red" if risk_level in ("HIGH", "HUMAN_REQUIRED") else "blue",
        },
        "elements": [
            {"tag": "div", "text": {"tag": "lark_md", "content": "\n".join(detail_parts)}},
            {"tag": "hr"},
            {
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "同意"},
                        "type": "primary",
                        "value": {"action": "approve", "approval_id": approval_id},
                    },
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "驳回"},
                        "type": "danger",
                        "value": {"action": "reject", "approval_id": approval_id},
                    },
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "修改参数"},
                        "type": "default",
                        "value": {"action": "modify", "approval_id": approval_id},
                    },
                ],
            },
        ],
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "receive_id": chat_id,
                    "msg_type": "interactive",
                    "content": json.dumps(card),
                },
                timeout=10,
            )
            data = resp.json()
            if data.get("code") == 0:
                logger.info(f"审批卡片推送成功: {approval_id}")
                await _save_approval_chat_mapping(approval_id, chat_id)
                return True
            logger.error(f"审批卡片推送失败: {data}")
            return False
    except Exception as e:
        logger.error(f"审批卡片推送异常: {e}")
        return False


# ── 审批 → chat_id 映射（容器重启后可通过 SQLite 恢复）──
_approval_chat_ids: Dict[str, str] = {}  # approval_id -> chat_id


async def _save_approval_chat_mapping(approval_id: str, chat_id: str):
    """持久化审批ID到chat_id的映射"""
    _approval_chat_ids[approval_id] = chat_id
    try:
        from molib.infra.memory.sqlite_client import SQLiteClient
        db = SQLiteClient()
        await db.store_memory(
            key=f"feishu_approval_chat:{approval_id}",
            data={"chat_id": chat_id},
            scenario="feishu_bot",
        )
    except Exception as e:
        logger.warning(f"审批映射持久化失败: {e}")


async def _lookup_chat_id(approval_id: str) -> str:
    """查找审批对应的chat_id，优先内存，回退SQLite"""
    if approval_id in _approval_chat_ids:
        return _approval_chat_ids[approval_id]
    try:
        from molib.infra.memory.sqlite_client import SQLiteClient
        db = SQLiteClient()
        results = await db.retrieve_memory(
            key=f"feishu_approval_chat:{approval_id}",
            scenario="feishu_bot",
        )
        if results:
            chat_id = results[0].get("data", {}).get("chat_id", "")
            if chat_id:
                _approval_chat_ids[approval_id] = chat_id
                return chat_id
    except Exception as e:
        logger.warning(f"审批映射查询失败: {e}")
    return ""


# ── Token 管理（v2.0: 统一从 token_manager 导入，消除 BUG-02）─
from molib.integrations.feishu.token_manager import get_feishu_token, invalidate_token

# ── 审批快捷指令 ──────────────────────────────────────────────

async def handle_shortcut(cmd: str) -> str:
    """FS-4: 处理飞书快捷指令 — 全部通过 HTTP 调用 Hermes API"""
    cmd_lower = cmd.strip().lower()
    api_url = os.getenv("HERMES_API_URL", "http://hermes:8000")

    if cmd_lower.startswith("/approve"):
        parts = cmd.split()
        if len(parts) >= 2:
            approval_id = parts[1]
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    await client.post(f"{api_url}/api/approve/{approval_id}", json={"comment": ""})
                return f"审批已通过: {approval_id}"
            except Exception as e:
                return f"审批失败: {e}"
        # 无参数时列出待审批
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{api_url}/api/pending-approvals")
                pending = resp.json() if resp.status_code == 200 else []
        except Exception:
            pending = []
        if not pending:
            return "当前没有待审批项"
        lines = ["待审批列表:"]
        for item in pending[:10]:
            lines.append(f"  - {item.get('approval_id', '?')}: {item.get('title', '')[:50]}")
        lines.append("\n审批命令: /approve <审批ID>")
        return "\n".join(lines)

    elif cmd_lower.startswith("/reject"):
        parts = cmd.split()
        if len(parts) >= 2:
            approval_id = parts[1]
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    await client.post(f"{api_url}/api/reject/{approval_id}", json={"comment": ""})
                return f"审批已驳回: {approval_id}"
            except Exception as e:
                return f"驳回失败: {e}"
        return "用法: /reject <审批ID>"

    elif cmd_lower.startswith("/dashboard"):
        # 返回标记，由 _handle_message_async 实际发送卡片
        return "__DASHBOARD_CARD__"

    elif cmd_lower.startswith("/report"):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{api_url}/api/daily-summary")
                summary = resp.json() if resp.status_code == 200 else {}
        except Exception:
            summary = {}
        return (
            f"每日报告:\n"
            f"  线索: {summary.get('leads', 0)}\n"
            f"  成交: {summary.get('deals', 0)}\n"
            f"  收入: {summary.get('total_revenue', 0)}\n"
            f"  ROI: {summary.get('roi', 0):.2f}"
        )

    elif cmd_lower.startswith("/status"):
        return "系统运行正常，所有服务在线。"

    return None


# ── 响应解析与审批检测 ─────────────────────────────────────────

def _format_reasoning_chain(chain: dict) -> str:
    """格式化 CEO 推理链为纯文本（飞书 text 消息不支持 markdown）"""
    if not chain:
        return ""
    parts = ["━━━ CEO 推理过程 ━━━"]
    understanding = chain.get("understanding", "")
    if understanding and understanding != "未记录":
        parts.append(f"理解：{understanding}")
    assumption = chain.get("assumption", "")
    if assumption and assumption != "无":
        parts.append(f"假设：{assumption}")
    decision = chain.get("decision_type", "")
    confidence = chain.get("confidence", 0)
    parts.append(f"决策：{decision}（置信度 {confidence}）")
    agencies = chain.get("agencies_involved", [])
    if agencies:
        parts.append(f"调度：{' → '.join(agencies)}")
    pending = chain.get("pending_question", "")
    if pending:
        parts.append(f"追问：{pending}")
    risks = chain.get("risks", [])
    if risks:
        parts.append(f"风险：{'；'.join(risks)}")
    latency = chain.get("latency_seconds", 0)
    parts.append(f"耗时 {latency:.1f}s")
    parts.append("━━━━━━━━━━━━━━")
    return "\n".join(parts)


def _sanitize_for_feishu(text: str) -> str:
    """清洗文本用于飞书 text 消息（不支持 markdown，需转为纯文本）"""
    import re
    # 去掉 markdown 标题 ### / ## / #
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    # 去掉加粗 **text**
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    # 去掉斜体 *text*（但不影响 * 列表项）
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'\1', text)
    # 去掉水平线 --- / ***
    text = re.sub(r'^[-*]{3,}\s*$', '', text, flags=re.MULTILINE)
    # 去掉代码块 ```
    text = text.replace('```', '')
    # 表格行：| col1 | col2 | → col1 | col2
    text = re.sub(r'^\|(.+)\|$', lambda m: m.group(1).replace('|', ' | ').strip(), text, flags=re.MULTILINE)
    # 表格分隔线 |---|---|
    text = re.sub(r'^\|[-:\s|]+\|$', '', text, flags=re.MULTILINE)
    return text


def _extract_text(data: Dict[str, Any]) -> str:
    """从 CEO API 响应中提取可回复文本"""
    decision = data.get("decision", "")
    chain_text = _format_reasoning_chain(data.get("reasoning_chain", {}))

    if decision == "DIRECT_RESPONSE":
        msg = _sanitize_for_feishu(data.get("message", ""))
        return f"{chain_text}\n\n{msg}" if chain_text else msg

    if decision == "NEED_INFO":
        questions = data.get("questions", []) or data.get("pending_questions", [])
        msg = _sanitize_for_feishu(data.get("message", ""))
        q_text = "\n".join(f"• {q}" for q in questions) if questions else ""
        return f"{chain_text}\n\n{msg}\n\n{q_text}" if chain_text else f"{msg}\n\n{q_text}"

    if decision == "GO":
        execution = data.get("execution_result", {})
        if not execution:
            msg = data.get("message", "任务已执行完成")
            return f"{chain_text}\n\n---\n{msg}" if chain_text else msg

        results = execution.get("results", [])
        if not isinstance(results, list) or not results:
            output = execution.get("output", {})
            if isinstance(output, dict):
                return output.get("summary", output.get("result", str(output)))
            msg = str(output) if output else data.get("message", "任务已执行完成")
            return f"{chain_text}\n\n---\n{msg}" if chain_text else msg

        lines = [chain_text, "————————"] if chain_text else []
        base_msg = _sanitize_for_feishu(data.get("message", ""))
        if base_msg:
            lines.append(base_msg)

        for r in results:
            if not isinstance(r, dict):
                continue
            agency = r.get("agency", "?")
            status = r.get("status", "unknown")
            output = r.get("output", "")

            if status in ("success", "llm_executed"):
                preview = _sanitize_for_feishu(output[:800]) + ("..." if len(output) > 800 else "")
                label = "LLM执行" if status == "llm_executed" else "完成"
                lines.append(f"\n[{agency}] {label}:\n{preview}")
            elif status == "pending_approval":
                approval_id = r.get("approval_id", "?")
                lines.append(f"\n[{agency}] 需要审批 (ID: {approval_id})")
            elif status == "error":
                error = r.get("error", "未知错误")
                lines.append(f"\n[{agency}] 错误: {error}")

        return "\n".join(lines) if lines else data.get("message", "任务已执行完成")

    # 未知决策类型
    msg = data.get("message", "")
    return f"{chain_text}\n\n{msg}" if chain_text else msg

    return data.get("message", str(data))


def _extract_pending_approvals(data: Dict[str, Any]) -> List[Dict[str, str]]:
    """从 CEO API 响应中提取待审批项"""
    approvals = []
    execution = data.get("execution_result", {})
    if not execution:
        return approvals
    results = execution.get("results", [])
    if not isinstance(results, list):
        return approvals
    for r in results:
        if isinstance(r, dict) and r.get("status") == "pending_approval":
            approvals.append({
                "approval_id": r.get("approval_id", ""),
                "agency": r.get("agency", ""),
                "output": r.get("output", ""),
            })
    return approvals


# ── 仪表盘卡片发送 ────────────────────────────────────────────────

async def _send_dashboard_card(chat_id: str):
    """发送 /dashboard 交互式卡片到当前聊天"""
    api_url = os.getenv("HERMES_API_URL", "http://hermes:8000")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{api_url}/api/dashboard")
            dashboard_data = resp.json() if resp.status_code == 200 else {}
    except Exception:
        dashboard_data = {}
    if not dashboard_data:
        await send_feishu_reply(chat_id, "仪表盘数据暂不可用，请稍后重试")
        return
    try:
        from molib.integrations.feishu.bitable_sync import build_dashboard_summary_card
        token = await get_feishu_token()
        if not token:
            await send_feishu_reply(chat_id, "飞书 token 不可用，无法发送仪表盘卡片")
            return
        card = build_dashboard_summary_card(dashboard_data)
        async with httpx.AsyncClient() as http_client:
            card_resp = await http_client.post(
                "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "receive_id": chat_id,
                    "msg_type": "interactive",
                    "content": json.dumps(card),
                },
                timeout=10,
            )
            card_data = card_resp.json()
            if card_data.get("code") == 0:
                logger.info("仪表盘卡片发送成功")
            else:
                await send_feishu_reply(chat_id, f"仪表盘卡片推送失败: {card_data.get('msg', '未知错误')}")
    except Exception as e:
        await send_feishu_reply(chat_id, f"仪表盘生成失败: {e}")


# ── 消息处理 ──────────────────────────────────────────────────

async def _handle_message_async(data: Any):
    """消息事件异步处理"""
    try:
        content = json.loads(data.event.message.content) if hasattr(data.event.message, 'content') else {}
        text = content.get("text", "").strip()
        sender = data.event.sender if hasattr(data, 'event') and hasattr(data.event, 'sender') else None
        user_id = getattr(getattr(sender, 'sender_id', None), 'open_id', 'unknown')
        chat_id = getattr(data.event.message, 'chat_id', 'unknown')

        # 结构化日志：追踪身份标识格式
        logger.info(f"飞书标识: open_id={user_id}, chat_id={chat_id}")

        # FS-8: 操作员鉴权
        if not _check_operator(user_id):
            logger.warning(f"未授权操作员尝试操作: {user_id}")
            await send_feishu_reply(chat_id, "您没有权限操作此机器人。")
            return

        # FS-4: 快捷指令优先匹配
        if text.startswith("/"):
            shortcut = await handle_shortcut(text)
            if shortcut == "__DASHBOARD_CARD__":
                await _send_dashboard_card(chat_id)
                return
            if shortcut:
                await send_feishu_reply(chat_id, shortcut)
                return

        # v8: 人性化进度反馈 — CEO 在思考，让用户知道系统在做什么
        if len(text) > 15:
            # 复杂问题：给具体一点的反馈
            await send_feishu_reply(chat_id, "收到，正在分析调度中……")
        else:
            await send_feishu_reply(chat_id, "收到，正在处理……")

        progress_message_id = None
        logger.info(f"飞书消息: user={user_id}, chat={chat_id}, text={text[:50]}...")
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                resp = await client.post(
                    CEO_API_URL,
                    json={
                        "session_id": f"feishu_bot_{user_id}",
                        "input": text,
                        "progress_message_id": progress_message_id,
                        "chat_id": chat_id,
                    },
                )
                resp.raise_for_status()
                result = resp.json()
        except httpx.TimeoutException:
            logger.error(f"CEO API 超时: {text[:50]}")
            await send_feishu_reply(chat_id, "这个问题比我想的要复杂，让我再想想。你可以先补充一些具体信息吗？比如你最关心的方向是什么？")
            return
        except Exception as api_err:
            logger.error(f"CEO API 调用失败: {api_err}")
            await send_feishu_reply(chat_id, "系统遇到了一些问题，请稍后再试。")
            return

        # v7: 发送结果卡前，先把进度卡更新到100%（避免竞态）
        if progress_message_id:
            try:
                from molib.integrations.feishu.progress_card import update_progress_card
                await update_progress_card(
                    message_id=progress_message_id,
                    current_step=9,  # 10步版: step=9 = 100%
                    task_id=f"feishu_{user_id}",
                    description=text[:50],
                    token=await get_feishu_token(),
                )
            except Exception:
                pass  # 进度卡更新失败不阻塞主流程

        # v8: 始终发送带推理链的文本回复（透明度优先于卡片）
        reply = _extract_text(result)
        await send_feishu_reply(chat_id, reply)

        # 检查是否有待审批项，推送交互式卡片
        pending = _extract_pending_approvals(result)
        logger.info(f"审批检测: 发现 {len(pending)} 个待审批项: {pending}")
        for item in pending:
            logger.info(f"推送审批卡片: {item}")
            ok = await push_approval_card_to_chat(
                chat_id=chat_id,
                approval_id=item["approval_id"],
                title=f"{item['agency']} 任务审批",
                description=item.get("output", ""),
            )
            logger.info(f"审批卡片推送结果: {'成功' if ok else '失败'}")

    except Exception as e:
        logger.error(f"飞书消息处理异常: {e}")


def on_message(data: Any):
    """lark-oapi 同步回调 — 线程中同步处理，完全不干扰 WebSocket 事件循环"""
    import threading, requests
    def _sync_handler():
        try:
            _handle_message_sync(data)
        except Exception as e:
            logger.error(f"on_message 处理异常: {e}")
    threading.Thread(target=_sync_handler, daemon=True).start()


def _handle_message_sync(data: Any):
    """同步版本的消息处理（在线程中运行，无需 event loop）"""
    import requests
    content = json.loads(data.event.message.content) if hasattr(data.event.message, 'content') else {}
    text = content.get("text", "").strip()
    sender = data.event.sender if hasattr(data, 'event') and hasattr(data.event, 'sender') else None
    user_id = getattr(getattr(sender, 'sender_id', None), 'open_id', 'unknown')
    chat_id = getattr(data.event.message, 'chat_id', 'unknown')

    logger.info(f"飞书标识: open_id={user_id}, chat_id={chat_id}")

    if not _check_operator(user_id):
        _send_feishu_reply_sync(chat_id, "您没有权限操作此机器人。")
        return

    if text.startswith("/"):
        # 快捷指令用异步处理
        return

    # 初始反馈
    _send_feishu_reply_sync(chat_id, "收到，正在分析调度中，预计1-2分钟……")

    logger.info(f"飞书消息: user={user_id}, chat={chat_id}, text={text[:50]}... → POST {CEO_API_URL}")
    try:
        resp = requests.post(
            CEO_API_URL,
            json={
                "session_id": f"feishu_bot_{user_id}",
                "input": text,
                "chat_id": chat_id,
            },
            timeout=300,
        )
        resp.raise_for_status()
        result = resp.json()
        logger.info(f"CEO API 返回: decision={result.get('decision')}, len={len(result.get('message',''))}")
    except requests.Timeout:
        logger.error(f"CEO API 超时: {text[:50]}")
        _send_feishu_reply_sync(chat_id, "这个问题比我预期的复杂，正在后台继续处理，完成后会通知你。")
        return
    except Exception as api_err:
        logger.error(f"CEO API 调用失败: {api_err}")
        _send_feishu_reply_sync(chat_id, "系统遇到了一些波动，请稍后再试。")
        return

    # 发送带推理链的文本回复
    reply = _extract_text(result)
    ok = _send_feishu_reply_sync(chat_id, reply)
    logger.info(f"飞书回复 {'成功' if ok else '失败'}: {len(reply)} chars")


def _send_feishu_reply_sync(chat_id: str, text: str) -> bool:
    """同步发送飞书消息（线程安全）"""
    import requests
    token = _get_feishu_token_sync()
    if not token:
        return False
    try:
        resp = requests.post(
            "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id",
            headers={"Authorization": f"Bearer {token}"},
            json={"receive_id": chat_id, "msg_type": "text", "content": json.dumps({"text": text})},
            timeout=10,
        )
        return resp.json().get("code") == 0
    except Exception as e:
        logger.error(f"飞书回复发送失败: {e}")
        return False


def _get_feishu_token_sync() -> Optional[str]:
    """同步获取飞书 token（使用模块级缓存，线程安全）"""
    import requests
    app_id = os.getenv("FEISHU_APP_ID", "")
    app_secret = os.getenv("FEISHU_APP_SECRET", "")
    if not app_id or not app_secret:
        return None
    try:
        resp = requests.post(
            "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
            json={"app_id": app_id, "app_secret": app_secret},
            timeout=10,
        )
        data = resp.json()
        return data.get("tenant_access_token", "")
    except Exception as e:
        logger.error(f"飞书 token 获取失败: {e}")
        return None


def on_message_read(data: Any):
    """消息已读事件 — 无需处理，避免 lark-oapi 报 processor not found 错误"""
    pass


def on_card_action(data: Any):
    """处理飞书交互式卡片按钮点击事件 — 后台异步处理"""
    import threading

    event = data.event if hasattr(data, 'event') else {}
    action = getattr(event, 'action', {}) if hasattr(event, 'action') else {}
    value = getattr(action, 'value', {}) if hasattr(action, 'value') else {}

    if isinstance(value, dict):
        action_type = value.get("action")
        approval_id = value.get("approval_id")
    else:
        action_type = getattr(value, 'action', None)
        approval_id = getattr(value, 'approval_id', None)

    if not action_type:
        return None

    # 后台异步处理（Hermes API 调用 + 聊天回复 + Bitable 同步）
    def _run_async():
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(_handle_card_action_async(data))
        except Exception as e:
            logger.error(f"on_card_action 后台处理失败: {e}")
        finally:
            loop.close()
    threading.Thread(target=_run_async, daemon=True).start()

    # lark-oapi v1.5.5 不支持 P2CardActionTriggerResponse，返回 None
    # 卡片状态通过后续聊天回复更新
    return None


def on_p2p_chat_entered(data: Any):
    """用户首次与飞书 Bot 建立私聊时的处理器 — 消除日志噪音"""
    pass


async def _handle_card_action_async(data: Any):
    """异步处理卡片按钮点击（后台执行）"""
    try:
        event = data.event if hasattr(data, 'event') else {}
        action = getattr(event, 'action', {}) if hasattr(event, 'action') else {}
        value = getattr(action, 'value', {}) if hasattr(action, 'value') else {}

        if isinstance(value, dict):
            action_type = value.get("action")
            approval_id = value.get("approval_id")
            detail_id = value.get("detail_id")
        else:
            action_type = getattr(value, 'action', None)
            approval_id = getattr(value, 'approval_id', None)
            detail_id = getattr(value, 'detail_id', None)

        if not action_type:
            logger.warning(f"卡片回调缺少 action")
            return

        # 查看子公司详情回调（非审批）
        if action_type == "view_detail" and detail_id:
            logger.info(f"查看详情回调: detail_id={detail_id}")
            try:
                from molib.integrations.feishu.result_card_v7 import get_detail_content
                result = get_detail_content(detail_id)
                if result:
                    agency_name, content = result
                    context = getattr(event, 'context', None)
                    chat_id = getattr(context, 'open_chat_id', '') if context else ''
                    if not chat_id:
                        chat_id = ''
                    if chat_id:
                        await send_detail_card(chat_id, agency_name, content)
            except Exception as ve:
                logger.error(f"查看详情失败: {ve}")
            return

        if not approval_id:
            logger.warning(f"卡片回调缺少 approval_id: action={action_type}")
            return

        logger.info(f"飞书审批卡片回调: action={action_type}, approval_id={approval_id}")

        # FS-8: 操作员鉴权
        operator = getattr(event, 'operator', None)
        user_open_id = getattr(operator, 'open_id', '') if operator else ''
        if user_open_id and not _check_operator(user_open_id):
            logger.warning(f"未授权操作员尝试审批操作: {user_open_id}")
            return

        # 提取 chat_id：优先事件上下文，其次内存映射，最后 SQLite
        context = getattr(event, 'context', None)
        chat_id = getattr(context, 'open_chat_id', '') if context else ''
        if not chat_id:
            chat_id = await _lookup_chat_id(approval_id)
        logger.info(f"卡片回调 chat_id: {chat_id or '(未找到)'}")

        # 通过 HTTP 调用 Hermes API 更新审批状态
        async with httpx.AsyncClient(timeout=30.0) as client:
            api_url = os.getenv("HERMES_API_URL", "http://hermes:8000")
            if action_type == "approve":
                resp = await client.post(f"{api_url}/api/approve/{approval_id}", json={"comment": ""})
                resp.raise_for_status()
                result_text = f"[已通过] 审批: {approval_id}"
            elif action_type == "reject":
                resp = await client.post(f"{api_url}/api/reject/{approval_id}", json={"comment": ""})
                resp.raise_for_status()
                result_text = f"[已驳回] 审批: {approval_id}"
            elif action_type == "modify":
                result_text = (
                    f"请回复此消息并提供修改后的参数（JSON 格式），"
                    f"例如：{{\"key\": \"new_value\"}}\n"
                    f"审批 ID: {approval_id}"
                )
                logger.info(f"用户请求修改参数: {approval_id}")
            else:
                result_text = f"未知操作: {action_type}"
        logger.info(f"审批状态已更新: {result_text}")

        # 回复到飞书聊天
        if chat_id:
            await send_feishu_reply(chat_id, result_text)
        else:
            logger.warning(f"未找到 chat_id: approval_id={approval_id}，无法回复用户")

        # Bitable 同步（通过 HTTP 调用 Hermes 触发）
        if os.getenv("FEISHU_BITABLE_SYNC_ENABLED", "false").lower() == "true":
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    api_url = os.getenv("HERMES_API_URL", "http://hermes:8000")
                    await client.post(
                        f"{api_url}/api/bitable-sync",
                        json={
                            "approval_id": approval_id,
                            "action": action_type,
                            "user_id": user_open_id,
                        },
                    )
            except Exception as bitable_e:
                logger.warning(f"Bitable 同步触发失败: {bitable_e}")

    except Exception as e:
        logger.error(f"卡片回调处理异常: {e}")


def run_bot():
    """
    启动飞书长连接 Bot
    使用 lark-oapi WebSocket 长连接模式，无需公网IP
    """
    # Feature 1: 启动进度卡片订阅器
    try:
        import sys, os; sys.path.insert(0, "/app")
        from molib.integrations.feishu.progress_subscriber import start_progress_subscriber
        start_progress_subscriber()
    except Exception as e:
        logger.warning(f"ProgressSubscriber 启动失败: {e}")

    try:
        import lark_oapi as lark
        from lark_oapi import EventDispatcherHandler
    except ImportError:
        logger.error("lark-oapi 未安装，飞书长连接 Bot 不可用。请执行: pip install lark-oapi")
        return

    app_id = os.getenv("FEISHU_APP_ID", "")
    app_secret = os.getenv("FEISHU_APP_SECRET", "")
    if not app_id or not app_secret:
        logger.error("FEISHU_APP_ID / FEISHU_APP_SECRET 未配置")
        return

    try:
        encrypt_key = os.getenv("FEISHU_ENCRYPT_KEY", "")
        verification_token = os.getenv("FEISHU_VERIFICATION_TOKEN", "")

        event_handler = (
            EventDispatcherHandler.builder(encrypt_key, verification_token)
            .register_p2_im_message_receive_v1(on_message)
            .register_p2_im_message_message_read_v1(on_message_read)
            .register_p2_card_action_trigger(on_card_action)
            # .register_p2p_chat_entered_v1(on_p2p_chat_entered)  # not in lark-oapi 1.5.5
            .build()
        )

        cli = lark.ws.Client(
            app_id=app_id,
            app_secret=app_secret,
            event_handler=event_handler,
        )
        logger.info("飞书长连接 Bot 启动中...")
        cli.start()
    except Exception as e:
        logger.error(f"飞书长连接 Bot 启动失败: {e}")


if __name__ == "__main__":
    run_bot()
