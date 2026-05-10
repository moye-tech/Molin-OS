"""
飞书富文本结果卡片 v6.6
- CEO 综合分析 → 飞书云文档
- 子公司完整报告 → 飞书云文档
- 卡片仅显示摘要 + 文档链接
"""
import re, json, time, httpx
from typing import Dict, Any, List, Optional
from loguru import logger


def _sanitize(text: str) -> str:
    text = re.sub(r'^#{2,4}\s+', '**', text, flags=re.MULTILINE)
    text = re.sub(r'^#\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n#{2,4}\s+', '\n**', text)
    text = re.sub(r'\n#\s+', '\n', text)
    text = re.sub(r'\n-{3,}\n', '\n\n', text)
    lines = []
    for line in text.split('\n'):
        s = line.rstrip()
        if s.startswith('**') and s.count('**') == 1:
            s += '**'
        lines.append(s)
    return '\n'.join(lines)


def _truncate(text: str, max_len: int = 300) -> str:
    if len(text) <= max_len: return text
    return text[:max_len] + "..."


async def _create_doc(title: str, text: str, token: str = None) -> Optional[str]:
    """创建飞书云文档，返回文档 URL"""
    if not token:
        from molib.integrations.feishu.bridge import _get_feishu_token
        token = await _get_feishu_token()
    if not token: return None
    try:
        async with httpx.AsyncClient(timeout=30) as cli:
            r = await cli.post(
                "https://open.feishu.cn/open-apis/docx/v1/documents",
                headers={"Authorization": f"Bearer {token}"},
                json={"title": f"{title} - 墨麟科技"},
            )
            data = r.json()
            if data.get("code") != 0:
                logger.warning(f"创建飞书文档失败 code={data.get('code')}: {data.get('msg','')}")
                return None
            doc_id = data["data"]["document"]["document_id"]
            doc_url = f"https://bytedance.feishu.cn/docx/{doc_id}"

            # 保留层级: ### → 一级标题, **粗体** → 二级标题, 正文 → 文本
            blocks = []
            buf = ""
            for raw in text.split("\n"):
                line = raw.strip()
                if not line: continue

                # 标题行：优先作为单独标题块
                heading_level = 0
                heading_text = ""
                if line.startswith("### "):
                    heading_level = 3
                    heading_text = line[4:].strip()
                elif line.startswith("## "):
                    heading_level = 3
                    heading_text = line[3:].strip()
                elif line.startswith("# "):
                    heading_level = 3
                    heading_text = line[2:].strip()
                elif line.startswith("**") and line.endswith("**") and len(line) < 80:
                    heading_level = 4
                    heading_text = line.strip("*").strip()

                if heading_text:
                    # 先刷缓冲区
                    if buf:
                        blocks.append({"block_type": 2, "text": {
                            "elements": [{"text_run": {"content": buf[:5000], "text_element_style": {}}}],
                            "style": {},
                        }})
                        buf = ""
                    if heading_level == 3:
                        blocks.append({"block_type": 3, "heading1": {
                            "elements": [{"text_run": {"content": heading_text[:500], "text_element_style": {}}}],
                            "style": {},
                        }})
                    else:
                        blocks.append({"block_type": 4, "heading2": {
                            "elements": [{"text_run": {"content": heading_text[:500], "text_element_style": {}}}],
                            "style": {},
                        }})
                else:
                    # 去除行内 Markdown 符号
                    clean = line.replace("**", "").replace("##", "").replace("###", "").replace("---", "")
                    buf += clean + "\n"
                    if len(buf) > 2000:
                        blocks.append({"block_type": 2, "text": {
                            "elements": [{"text_run": {"content": buf[:5000], "text_element_style": {}}}],
                            "style": {},
                        }})
                        buf = ""
            if buf:
                blocks.append({"block_type": 2, "text": {
                    "elements": [{"text_run": {"content": buf[:5000], "text_element_style": {}}}],
                    "style": {},
                }})

            if blocks:
                r2 = await cli.post(
                    f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}/children",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"children": blocks, "index": 0},
                )
                d2 = r2.json()
                if d2.get("code") != 0:
                    logger.warning(f"文档写入失败 code={d2.get('code')}: {d2.get('msg','')} (blocks={len(blocks)})")
            logger.info(f"飞书文档已创建: {doc_url}")
            return doc_url
    except Exception as e:
        logger.error(f"创建飞书文档异常: {e}")
        return None


# ── 卡片 ──────────────────────────────────────

def build_success_card(synthesized: str, agencies: List[Dict],
                       cost=0.0, latency=0.0,
                       ceo_doc_url: str = "",
                       doc_links: Dict[str, str] = None) -> Dict[str, Any]:
    elements = []
    # 摘要 + CEO 完整报告链接
    summary = _sanitize(synthesized)[:300]
    if ceo_doc_url:
        summary += f"\n\n[查看 CEO 完整分析报告]({ceo_doc_url})"
    else:
        summary += f"\n{_sanitize(synthesized)[300:1000]}"
    elements.append({"tag": "div", "text": {"tag": "lark_md", "content": summary}})
    elements.append({"tag": "hr"})

    lines = ["**子公司执行明细：**"]
    for ag in agencies:
        status = ag.get("status", "unknown")
        name = ag.get("agency", "?")
        icons = {"executed": "✅", "llm_executed": "✅", "success": "✅",
                 "pending_approval": "⏳", "error": "❌"}
        icon = icons.get(status, "❓")
        out = ag.get("output", "")
        preview = _truncate(out.strip(), 80) if out else "无输出"
        doc_url = (doc_links or {}).get(name, "")
        hint = f" [查看完整报告]({doc_url})" if doc_url else ""
        lines.append(f"{icon} **{name}**: {preview}{hint}")

    elements.append({"tag": "div", "text": {"tag": "lark_md", "content": "\n".join(lines)}})
    elements.append({"tag": "hr"})

    meta = []
    if cost > 0: meta.append(f"花费 {cost:.4f}")
    if latency > 0: meta.append(f"耗时 {latency:.1f}s")
    meta.append(f"生成 {time.strftime('%H:%M:%S')}")
    elements.append({"tag": "note", "elements": [{"tag": "plain_text", "content": " · ".join(meta)}]})

    return {"config": {"wide_screen_mode": True},
            "header": {"title": {"tag": "plain_text", "content": "任务执行完成"}, "template": "green"},
            "elements": elements}


def build_error_card(error: str, task_id="", agencies: List[Dict] = None) -> Dict[str, Any]:
    elements = [{"tag": "div", "text": {"tag": "lark_md",
                 "content": f"**执行遇到问题：**\n{_truncate(error, 400)}"}}]
    if agencies:
        elements.append({"tag": "hr"})
        ok = [a for a in agencies if a.get("status") in ("executed", "llm_executed", "success")]
        errs = [a for a in agencies if a.get("status") == "error"]
        if ok:
            lines = ["**部分完成：**"]
            for a in ok: lines.append(f"✅ **{a.get('agency','?')}**: {_truncate(a.get('output',''), 80)}")
            elements.append({"tag": "div", "text": {"tag": "lark_md", "content": "\n".join(lines)}})
        if errs:
            lines = ["**失败项：**"]
            for a in errs: lines.append(f"❌ **{a.get('agency','?')}**: {_truncate(a.get('error',''), 80)}")
            elements.append({"tag": "div", "text": {"tag": "lark_md", "content": "\n".join(lines)}})
    elements.append({"tag": "hr"})
    elements.append({"tag": "action", "actions": [
        {"tag": "button", "text": {"tag": "plain_text", "content": "重新生成"}, "type": "primary",
         "value": {"action": "regenerate", "task_id": task_id}}
    ]})
    elements.append({"tag": "note", "elements": [{"tag": "plain_text", "content": f"时间: {time.strftime('%H:%M:%S')}"}]})
    return {"config": {"wide_screen_mode": True},
            "header": {"title": {"tag": "plain_text", "content": "任务执行失败"}, "template": "red"},
            "elements": elements}


def has_execution_content(data: Dict) -> bool:
    if data.get("decision") != "GO": return False
    ex = data.get("execution_result")
    if not ex or not isinstance(ex, dict): return False
    results = ex.get("results", [])
    return isinstance(results, list) and len(results) > 0


def build_result_card_from_response(data: Dict) -> Optional[Dict[str, Any]]:
    if not has_execution_content(data): return None
    ex = data["execution_result"]
    results = ex.get("results", [])
    synthesized = ex.get("synthesized", data.get("message", ""))
    cost = data.get("cost", 0.0)
    latency = data.get("latency", 0.0)
    all_err = all(r.get("status") == "error" for r in results if isinstance(r, dict))
    if all_err:
        msg = "；".join(r.get("error", "未知错误") for r in results if isinstance(r, dict))
        return build_error_card(msg, agencies=results)
    has_err = any(r.get("status") == "error" for r in results if isinstance(r, dict))
    if has_err: return build_error_card("部分子公司执行失败", agencies=results)
    return build_success_card(synthesized=synthesized, agencies=results, cost=cost, latency=latency)


async def build_result_card_with_docs(data: Dict, token: str = None) -> Optional[Dict[str, Any]]:
    """CEO综合 + 子公司完整报告 → 飞书云文档"""
    if not has_execution_content(data): return None
    ex = data["execution_result"]
    results = ex.get("results", [])
    synthesized = ex.get("synthesized", data.get("message", ""))

    # CEO 综合分析 → 云文档
    ceo_doc_url = ""
    if synthesized and len(synthesized) > 200:
        ceo_doc_url = await _create_doc("墨麟科技 CEO 综合分析报告",
                                         _sanitize(synthesized), token=token) or ""

    # 子公司报告 → 云文档
    doc_links = {}
    for r in results:
        if isinstance(r, dict) and r.get("output") and len(r.get("output", "")) > 200:
            agency = r.get("agency", "unknown")
            url = await _create_doc(f"墨麟科技 - {agency} 执行报告",
                                     _sanitize(r["output"]), token=token)
            if url: doc_links[agency] = url

    all_err = all(r.get("status") == "error" for r in results if isinstance(r, dict))
    if all_err:
        msg = "；".join(r.get("error", "未知错误") for r in results if isinstance(r, dict))
        return build_error_card(msg, agencies=results)
    has_err = any(r.get("status") == "error" for r in results if isinstance(r, dict))
    if has_err: return build_error_card("部分子公司执行失败", agencies=results)

    return build_success_card(synthesized=synthesized, agencies=results,
                              cost=data.get("cost", 0.0), latency=data.get("latency", 0.0),
                              ceo_doc_url=ceo_doc_url, doc_links=doc_links)

# 详情缓存
_detail_store: dict = {}

def store_detail_content(detail_id: str, agency_name: str, content: str):
    _detail_store[detail_id] = {"agency": agency_name, "content": content}

def get_detail_content(detail_id: str) -> dict:
    return _detail_store.get(detail_id, {"agency": "未知", "content": "内容已过期"})
