#!/usr/bin/env python3
"""
karpathy-autoresearch 激活脚本 — 自主科研Agent
================================================
实现 auto_research(topic) 函数，完整研究管线：
web_search → extract → LLM分析 → 生成研究简报

对应技能：~/.hermes/skills/meta/karpathy-autoresearch/SKILL.md
对应子公司：墨研竞情（竞争分析、趋势研究、情报扫描）

依赖：纯 Python / subprocess / curl / urllib（无额外第三方包）
网络：所有请求通过 curl 进行（服务器网络受限环境适配）
"""

import os
import re
import sys
import json
import subprocess
from pathlib import Path
from html.parser import HTMLParser
from datetime import datetime


# ═══════════════════════════════════════════════════════════════════
# Step 1: web_search — 网络搜索
# ═══════════════════════════════════════════════════════════════════

def web_search(query: str, num_results: int = 5) -> list[dict]:
    """
    通过 curl 执行网络搜索（Hermes无头服务器适配版）。
    
    后端策略（自动探测，适配中国服务器环境）:
    1. Baidu 搜索（CN服务器首选，HTTPS可达）
    2. Bing 搜索（HTTPS fallback）
    3. DuckDuckGo Lite API（国际fallback）
    4. Google 搜索 HTML 解析（最后尝试）
    
    Args:
        query: 搜索关键词
        num_results: 返回结果数量（默认5）
    
    Returns:
        [{title, url, snippet}, ...]
    """
    # URL-encode the query
    try:
        encoded_query = subprocess.check_output(
            ["python3", "-c", f"import urllib.parse; print(urllib.parse.quote('''{query}'''))"],
            text=True, timeout=5
        ).strip()
    except Exception:
        encoded_query = query.replace(" ", "+")

    results = []
    user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    # ── Method 1: Bing search via HTTP (CN server friendly) ──
    try:
        # Use http:// (not https://) since some CN servers have restrictive HTTPS policies
        search_url = f"http://www.bing.com/search?q={encoded_query}&count={num_results}"
        cmd = [
            "curl", "-s", "-L", search_url,
            "-H", f"User-Agent: {user_agent}",
            "--connect-timeout", "10",
            "--max-time", "15",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)

        if result.returncode == 0 and result.stdout and len(result.stdout) > 1000:
            html = result.stdout
            
            # Parse Bing search results: <li class="b_algo"> blocks
            bing_blocks = re.findall(
                r'<li[^>]*class="[^"]*b_algo[^"]*"[^>]*>(.*?)</li>',
                html, re.DOTALL
            )
            
            for block in bing_blocks[:num_results]:
                # Extract URL and title from <a href="...">...</a>
                link_matches = re.findall(
                    r'<a[^>]*href="(https?://[^"]+)"[^>]*>(.*?)</a>',
                    block, re.DOTALL
                )
                if link_matches:
                    # Take the first meaningful link (skip redirect/service links)
                    for url, title in link_matches:
                        clean_title = re.sub(r'<[^>]+>', '', title).strip()
                        if clean_title and url.startswith('http'):
                            # Extract snippet
                            snippet = ''
                            snippet_matches = re.findall(
                                r'<p[^>]*>(.*?)</p>', block, re.DOTALL
                            )
                            if snippet_matches:
                                snippet = re.sub(r'<[^>]+>', '', snippet_matches[0]).strip()
                                snippet = re.sub(r'\s+', ' ', snippet)
                            
                            results.append({
                                'title': clean_title,
                                'url': url,
                                'snippet': snippet
                            })
                            break
            
            if results:
                return results[:num_results]
    except Exception:
        pass

    # ── Method 2: Baidu search (HTTPS backup for CN) ──
    try:
        search_url = f"https://www.baidu.com/s?wd={encoded_query}&rn={num_results}"
        cmd = [
            "curl", "-s", "-L", search_url,
            "-H", f"User-Agent: {user_agent}",
            "--connect-timeout", "10",
            "--max-time", "15",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)

        if result.returncode == 0 and result.stdout and len(result.stdout) > 500:
            html = result.stdout
            
            # Check if Baidu returned a result page or a captcha page
            if '百度安全验证' not in html and 'result' in html.lower() or 'c-container' in html:
                # Parse Baidu search results
                baidu_blocks = re.findall(
                    r'<div[^>]*class="[^"]*c-container[^"]*"[^>]*>(.*?)</div>\s*</div>',
                    html, re.DOTALL
                )
                if not baidu_blocks:
                    baidu_blocks = re.findall(
                        r'<div[^>]*class="[^"]*result[^"]*"[^>]*>(.*?)</div>',
                        html, re.DOTALL
                    )
                
                for block in baidu_blocks[:num_results]:
                    # Extract title
                    title_match = re.search(r'<a[^>]*>(.*?)</a>', block, re.DOTALL)
                    url_match = re.search(r'href="(https?://[^"]+)"', block)
                    snippet_match = re.search(r'<div[^>]*class="[^"]*c-abstract[^"]*"[^>]*>(.*?)</div>', block, re.DOTALL)
                    
                    if title_match and url_match:
                        clean_title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
                        url = url_match.group(1)
                        snippet = ''
                        if snippet_match:
                            snippet = re.sub(r'<[^>]+>', '', snippet_match.group(1)).strip()
                        if clean_title:
                            results.append({
                                'title': clean_title,
                                'url': url,
                                'snippet': snippet
                            })
                
                if results:
                    return results[:num_results]
    except Exception:
        pass

    # ── Method 3: DuckDuckGo Lite (HTML based, no JS needed) ──
    if not results:
        try:
            cmd = [
                "curl", "-s", "-L",
                f"https://lite.duckduckgo.com/lite/?q={encoded_query}",
                "-H", f"User-Agent: {user_agent}",
                "--connect-timeout", "10",
                "--max-time", "15",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)

            if result.returncode == 0 and result.stdout and len(result.stdout) > 200:
                html = result.stdout

                # Parse DDG lite HTML results
                class DDGResultParser(HTMLParser):
                    def __init__(self):
                        super().__init__()
                        self.results = []
                        self._cur = {}
                        self._in_link = False
                        self._in_snippet = False

                    def handle_starttag(self, tag, attrs):
                        a = dict(attrs)
                        if tag == 'a' and 'class' in a:
                            classes = a['class'].split()
                            if 'result-link' in classes or 'result__a' in classes:
                                self._in_link = True
                                href = a.get('href', '')
                                if href.startswith('//'):
                                    href = 'https:' + href
                                self._cur['url'] = href
                                self._cur['title'] = ''

                    def handle_data(self, data):
                        if self._in_link:
                            self._cur['title'] = (self._cur.get('title', '') + data).strip()
                        elif self._in_snippet:
                            self._cur['snippet'] = (self._cur.get('snippet', '') + data).strip()

                    def handle_endtag(self, tag):
                        if tag == 'a' and self._in_link:
                            self._in_link = False
                            if self._cur.get('title') and self._cur.get('url'):
                                self._cur.setdefault('snippet', '')
                                self.results.append(dict(self._cur))
                                self._cur = {}

                parser = DDGResultParser()
                parser.feed(html)
                results = parser.results[:num_results]
        except Exception:
            pass

    # ── Method 4: Google search HTML parse (last resort) ──
    if not results:
        try:
            search_url = f"https://www.google.com/search?q={encoded_query}&num={num_results}"
            cmd = [
                "curl", "-s", "-L", search_url,
                "-H", f"User-Agent: {user_agent}",
                "--connect-timeout", "10",
                "--max-time", "15",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)

            if result.returncode == 0 and result.stdout:
                html = result.stdout
                titles = re.findall(r'<h3[^>]*>(.*?)</h3>', html, re.DOTALL)
                url_pattern = r'/url\?q=(https?://[^&"\']+)'
                urls = re.findall(url_pattern, html)
                snippets = re.findall(r'<span[^>]*class="[^"]*st[^"]*"[^>]*>(.*?)</span>', html, re.DOTALL)

                for i in range(min(len(titles), num_results)):
                    clean_title = re.sub(r'<[^>]+>', '', titles[i]).strip()
                    snippet = ''
                    if i < len(snippets):
                        snippet = re.sub(r'<[^>]+>', '', snippets[i]).strip()
                    url = urls[i] if i < len(urls) else ''
                    if clean_title:
                        results.append({
                            'title': clean_title,
                            'url': url,
                            'snippet': snippet
                        })
        except Exception:
            pass

    return results[:num_results]


# ═══════════════════════════════════════════════════════════════════
# Step 2: extract — 内容提取
# ═══════════════════════════════════════════════════════════════════

def extract_content(url: str, max_chars: int = 15000) -> str:
    """
    从URL提取可读文本内容。
    使用 curl 获取HTML，正则提取主要文本内容。
    
    Args:
        url: 目标网页URL
        max_chars: 最大提取字符数
    
    Returns:
        提取的纯文本内容
    """
    if not url:
        return ""

    user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    try:
        cmd = [
            "curl", "-s", "-L", url,
            "-H", f"User-Agent: {user_agent}",
            "--connect-timeout", "15",
            "--max-time", "30",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=35)

        if result.returncode != 0 or not result.stdout:
            return ""

        html = result.stdout

        # Remove unwanted elements
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
        html = re.sub(r'<nav[^>]*>.*?</nav>', '', html, flags=re.DOTALL)
        html = re.sub(r'<footer[^>]*>.*?</footer>', '', html, flags=re.DOTALL)
        html = re.sub(r'<header[^>]*>.*?</header>', '', html, flags=re.DOTALL)
        html = re.sub(r'<noscript[^>]*>.*?</noscript>', '', html, flags=re.DOTALL)

        # Extract text from content-bearing tags
        texts = []
        for tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li', 'td', 'blockquote', 'pre']:
            matches = re.findall(f'<{tag}[^>]*>(.*?)</{tag}>', html, re.DOTALL)
            for m in matches:
                text = re.sub(r'<[^>]+>', '', m).strip()
                # Clean up whitespace
                text = re.sub(r'\s+', ' ', text).strip()
                if len(text) > 20:  # Only keep substantial content
                    texts.append(text)

        content = '\n'.join(texts)

        # Clean up remaining HTML entities
        content = content.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        content = content.replace('&quot;', '"').replace('&#39;', "'").replace('&#x27;', "'")

        # Truncate if needed
        if len(content) > max_chars:
            content = content[:max_chars] + "\n\n[...内容已截断...]"

        return content

    except subprocess.TimeoutExpired:
        return "[提取超时]"
    except Exception as e:
        return f"[提取失败: {e}]"


# ═══════════════════════════════════════════════════════════════════
# Step 3: llm_analyze — LLM分析总结
# ═══════════════════════════════════════════════════════════════════

def llm_analyze(prompt: str, system_prompt: str = None) -> str:
    """
    调用 LLM 进行分析总结。
    
    支持方式（自动探测）:
    1. 环境变量 OPENROUTER_API_KEY（首选）
    2. HTTP API 调用（通过 urllib）
    
    Args:
        prompt: 用户提示
        system_prompt: 系统提示（可选）
    
    Returns:
        LLM 生成的文本，或错误信息
    """
    # Default system prompt for research analysis
    if system_prompt is None:
        system_prompt = """你是一位深度研究分析师，风格受 Andrej Karpathy 启发。
你的分析特点是：
1. 第一性原理 — 不满足表面结论，深挖底层机制
2. 原始资料优先 — 直接分析原始信息
3. 批判性审视 — 对每个结论问"证据是什么？"
4. 结构化输出 — 用清晰的逻辑组织分析

请用中文输出分析结果。"""

    api_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY")
    api_base = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    model = os.environ.get("LLM_MODEL", "deepseek/deepseek-chat")

    # ── Method 1: requests library (if available) ──
    if api_key:
        try:
            import requests
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://hermes-os.local",
                "X-Title": "karpathy-autoresearch",
            }
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": 4096,
                "temperature": 0.3,
            }

            resp = requests.post(
                f"{api_base}/chat/completions",
                headers=headers,
                json=payload,
                timeout=120,
            )
            if resp.status_code == 200:
                data = resp.json()
                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"]
            return f"[LLM API 返回错误: HTTP {resp.status_code}]"
        except ImportError:
            pass  # requests not available, try urllib
        except Exception as e:
            return f"[LLM分析失败: {e}]"

    # ── Method 2: urllib (stdlib, always available) ──
    if api_key:
        try:
            import urllib.request
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            payload = json.dumps({
                "model": model,
                "messages": messages,
                "max_tokens": 4096,
                "temperature": 0.3,
            }).encode('utf-8')

            req = urllib.request.Request(
                f"{api_base}/chat/completions",
                data=payload,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://hermes-os.local",
                    "X-Title": "karpathy-autoresearch",
                },
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"]
                return f"[LLM 返回异常: {data}]"

        except Exception as e:
            return f"[LLM分析失败(urllib): {e}]"

    return "[LLM不可用 — 未配置 OPENROUTER_API_KEY。请设置环境变量。]"


# ═══════════════════════════════════════════════════════════════════
# Step 4: generate_briefing — 生成研究简报
# ═══════════════════════════════════════════════════════════════════

def generate_briefing(topic: str, search_results: list, analysis: str) -> str:
    """
    生成最终的研究简报（markdown格式）。
    
    Args:
        topic: 研究主题
        search_results: 搜索结果列表 [{title, url, snippet}]
        analysis: LLM分析文本
    
    Returns:
        格式化的研究简报markdown
    """
    now = datetime.now().strftime('%Y-%m-%d %H:%M')

    briefing = f"""# 🔬 研究简报: {topic}

> 生成时间: {now}
> 来源: karpathy-autoresearch（墨研竞情）

---

## 📊 信息源

"""

    for i, r in enumerate(search_results, 1):
        title = r.get('title', 'Unknown')
        url = r.get('url', '')
        snippet = r.get('snippet', '')
        if url:
            briefing += f"{i}. **[{title}]({url})**  \n"
        else:
            briefing += f"{i}. **{title}**  \n"
        if snippet:
            briefing += f"   > {snippet}\n"
        briefing += "\n"

    briefing += f"""---

## 📝 分析总结

{analysis}

---

## 💡 关键洞察

（核心发现总结）

---

## 🔗 后续行动

1. 针对重点子主题进行深度挖掘
2. 将关键发现更新到墨脑知识知识库
3. 如需要，生成飞书情报简报通知创始人

---
*报告由 karpathy-autoresearch 自主生成 | 墨研竞情 | {now}*
"""
    return briefing


# ═══════════════════════════════════════════════════════════════════
# auto_research — 完整研究管线
# ═══════════════════════════════════════════════════════════════════

def auto_research(topic: str, save_path: str = None) -> dict:
    """
    执行完整的自动研究管线。
    
    流程: web_search → extract → LLM分析 → 生成研究简报
    
    Args:
        topic: 研究主题
        save_path: 简报保存路径（可选，如 ~/hermes-os/relay/research_xxx.md）
    
    Returns:
        dict: {
            "topic": 研究主题,
            "search_results": 搜索结果列表,
            "analysis": LLM分析文本,
            "briefing": 研究简报markdown,
            "saved_to": 保存路径（如果提供save_path）,
            "status": "ok" | "partial" | "error",
            "error": 错误信息（仅status=error时）
        }
    """
    print(f"\n{'='*60}")
    print(f"🔍 开始研究: [{topic}]")
    print(f"{'='*60}\n")

    result = {
        "topic": topic,
        "search_results": [],
        "analysis": "",
        "briefing": "",
        "status": "ok",
    }

    # ── Step 1: Web Search ──
    print("📡 Step 1/4: 搜索网络信息...")
    search_results = web_search(topic)
    print(f"   → 找到 {len(search_results)} 个结果")
    
    if not search_results:
        print("   ⚠️  搜索未返回结果，尝试简化查询...")
        # Try with simplified query
        simple_query = topic.replace("2026", "").replace("趋势", "").strip()
        if simple_query and simple_query != topic:
            search_results = web_search(simple_query)
            print(f"   → 简化查询后找到 {len(search_results)} 个结果")

    if not search_results:
        result["status"] = "error"
        result["error"] = "搜索未返回结果（网络受限或搜索后端不可用）"
        result["briefing"] = generate_briefing(topic, [], "[搜索阶段失败]")
        print("   ❌ 搜索失败")
        print(f"{'='*60}")
        return result

    result["search_results"] = search_results
    for i, r in enumerate(search_results, 1):
        print(f"   [{i}] {r.get('title', 'Unknown')[:60]}")

    # ── Step 2: Extract Content ──
    print("\n📖 Step 2/4: 提取内容...")
    extracted_content = []
    for i, r in enumerate(search_results):
        title = r.get('title', 'Unknown')
        url = r.get('url', '')
        print(f"   → 提取 [{i+1}/{len(search_results)}]: {title[:50]}...", end=" ")
        content = extract_content(url)
        if content and not content.startswith("[提取"):
            print(f"✓ ({len(content)} chars)")
            extracted_content.append({
                "title": title,
                "url": url,
                "content": content[:3000],  # Each source: first 3000 chars
            })
        else:
            print(f"⚠️  使用摘要")
            extracted_content.append({
                "title": title,
                "url": url,
                "content": r.get('snippet', content),
            })

    if not extracted_content:
        print("   ⚠️  所有页面提取失败，使用搜索摘要")
        for i, r in enumerate(search_results):
            extracted_content.append({
                "title": r.get('title', 'Unknown'),
                "url": r.get('url', ''),
                "content": r.get('snippet', ''),
            })

    # ── Step 3: LLM Analysis ──
    print("\n🧠 Step 3/4: LLM分析总结...")

    # Build analysis prompt
    sources_text = ""
    for i, ec in enumerate(extracted_content, 1):
        sources_text += f"\n### 来源{i}: {ec['title']}\nURL: {ec['url']}\n{ec['content'][:2000]}\n"

    analysis_prompt = f"""请对以下关于「{topic}」的研究资料进行深度分析。

要求：
1. 提炼核心观点和趋势
2. 识别不同来源的一致性和矛盾点
3. 第一性原理分析：底层机制是什么？
4. 批判性审视：哪些结论缺乏足够证据？
5. 独立判断：你对该主题的总体评估

研究资料：
{sources_text}

请输出结构化的中文分析报告（约500-1500字）。"""

    analysis = llm_analyze(analysis_prompt)
    result["analysis"] = analysis
    print(f"   → 分析完成 ({len(analysis)} chars)")

    # ── Step 4: Generate Briefing ──
    print("\n📋 Step 4/4: 生成研究简报...")
    briefing = generate_briefing(topic, search_results, analysis)
    result["briefing"] = briefing

    # Save if path provided
    if save_path:
        save_path_full = str(Path(save_path).expanduser().resolve())
        Path(save_path_full).parent.mkdir(parents=True, exist_ok=True)
        with open(save_path_full, 'w', encoding='utf-8') as f:
            f.write(briefing)
        result["saved_to"] = save_path_full
        print(f"   → 简报已保存: {save_path_full}")
    else:
        # Save to default location
        default_path = Path.home() / "hermes-os" / "relay" / f"research_{_sanitize_filename(topic)}.md"
        default_path.parent.mkdir(parents=True, exist_ok=True)
        with open(default_path, 'w', encoding='utf-8') as f:
            f.write(briefing)
        result["saved_to"] = str(default_path)
        print(f"   → 简报已保存: {default_path}")

    print(f"\n{'='*60}")
    print(f"✅ 研究完成: [{topic}]")
    print(f"{'='*60}")
    return result


def _sanitize_filename(name: str) -> str:
    """将主题转换为安全的文件名"""
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'\s+', '_', name)
    name = name.strip().lower()[:80]
    return name or "research"


# ═══════════════════════════════════════════════════════════════════
# 自检功能
# ═══════════════════════════════════════════════════════════════════

def self_check() -> dict:
    """
    运行环境自检，确认各功能可用性。
    
    Returns:
        dict: {
            "curl": bool,
            "python3": bool,
            "api_key_configured": bool,
            "openrouter_api_key": bool,
            "internet_reachable": bool,
            "total": "ok" | "partial" | "error"
        }
    """
    status = {}

    # Check curl
    curl_check = subprocess.run(
        ["which", "curl"], capture_output=True, text=True
    )
    status["curl"] = curl_check.returncode == 0

    # Check python3
    py_check = subprocess.run(
        ["which", "python3"], capture_output=True, text=True
    )
    status["python3"] = py_check.returncode == 0

    # Check API key
    api_key = os.environ.get("OPENROUTER_API_KEY")
    status["openrouter_api_key"] = bool(api_key)

    # Check internet (simple ping test via curl)
    try:
        r = subprocess.run(
            ["curl", "-s", "--connect-timeout", "5", "--max-time", "5",
             "https://www.google.com"],
            capture_output=True, text=True, timeout=10
        )
        status["internet_reachable"] = r.returncode == 0 and len(r.stdout) > 0
    except Exception:
        status["internet_reachable"] = False

    # Overall status
    ok_count = sum(1 for v in status.values() if v is True)
    total = len(status)
    if ok_count == total:
        status["total"] = "ok"
    elif ok_count >= total // 2:
        status["total"] = "partial"
    else:
        status["total"] = "error"

    return status


# ═══════════════════════════════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="karpathy-autoresearch — 自主科研Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python activate_karpathy_research.py --topic "AI Agent 2026趋势"
  python activate_karpathy_research.py --topic "开源LLM格局" --save /tmp/briefing.md
  python activate_karpathy_research.py --self-check
        """
    )
    parser.add_argument("--topic", "-t", type=str, help="研究主题")
    parser.add_argument("--save", "-s", type=str, help="简报保存路径")
    parser.add_argument("--self-check", "-c", action="store_true", help="运行环境自检")

    args = parser.parse_args()

    if args.self_check:
        print("=" * 60)
        print("karpathy-autoresearch · 环境自检")
        print("=" * 60)
        check = self_check()
        for key, val in check.items():
            icon = "✓" if val is True else ("✗" if val is False else "~")
            print(f"  {icon} {key}: {val}")
        print("=" * 60)
        sys.exit(0)

    if args.topic:
        result = auto_research(args.topic, save_path=args.save)
        if result["status"] == "ok":
            print("\n📄 简报预览（前500字符）:")
            print("-" * 40)
            print(result["briefing"][:500])
            print("-" * 40)
            print(f"...完整简报已保存至: {result.get('saved_to', 'N/A')}")
        else:
            print(f"\n❌ 研究失败: {result.get('error', '未知错误')}")
        sys.exit(0 if result["status"] == "ok" else 1)

    # Default: run self-check then a demo
    print("=" * 60)
    print("karpathy-autoresearch 激活脚本")
    print("=" * 60)
    print()

    check = self_check()
    print("环境自检:")
    for key, val in check.items():
        icon = "✓" if val is True else ("✗" if val is False else "~")
        print(f"  {icon} {key}: {val}")
    print()

    if check["total"] in ("partial", "ok"):
        print("准备运行演示研究: 'AI Agent 2026趋势'")
        print("（按 Ctrl+C 取消，或等待5秒自动开始）")
        try:
            import time
            time.sleep(5)
        except KeyboardInterrupt:
            print("\n已取消。运行: python activate_karpathy_research.py --topic \"你的主题\"")
            sys.exit(0)

        print()
        result = auto_research("AI Agent 2026趋势")
        if result["status"] == "ok":
            print("\n📄 简报预览（前500字符）:")
            print("-" * 40)
            print(result["briefing"][:500])
            print("-" * 40)
            print(f"\n✓ karpathy-autoresearch 激活完成")
            print(f"  简报: {result.get('saved_to', 'N/A')}")
        else:
            print(f"\n⚠️ 研究部分失败: {result.get('error', '')}")
            print("  网络中可能存在限制，但功能已激活。")
    else:
        print("❌ 环境不满足最低要求:")
        if not check.get("curl"):
            print("   - 需要 curl 命令")
        if not check.get("python3"):
            print("   - 需要 python3")
        print("请安装依赖后重试。")
