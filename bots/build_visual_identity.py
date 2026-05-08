#!/usr/bin/env python3
"""
CH7-K: 视觉身份系统
定义Hermes OS品牌的主色调、字体规范、封面模板生成
零外部依赖，使用subprocess/curl/json/os标准库
"""
import os
import json
import uuid
import base64
from pathlib import Path
from typing import Optional, Dict, List, Tuple

OUTPUT_DIR = "/tmp/hermes-visual-identity"


# ──────────────────────────────────────────────
# 1. 主色调定义
# ──────────────────────────────────────────────

def color_palette() -> Dict:
    """
    Hermes OS 品牌主色调定义。

    Returns:
        dict: 完整的调色板定义
    """
    palette = {
        "brand": {
            "primary": {
                "name": "Hermes蓝",
                "hex": "#1A73E8",
                "rgb": (26, 115, 232),
                "usage": "主品牌色，按钮、链接、主要界面元素",
            },
            "secondary": {
                "name": "墨玉黑",
                "hex": "#1E1E2E",
                "rgb": (30, 30, 46),
                "usage": "品牌色深色版本，强调文字、导航栏背景",
            },
            "accent": {
                "name": "活力橙",
                "hex": "#FF6B35",
                "rgb": (255, 107, 53),
                "usage": "CTA按钮、促销标签、重要提示",
            },
        },
        "neutral": {
            "white": {
                "hex": "#FFFFFF",
                "usage": "背景、卡片、文字（深色模式）",
            },
            "gray-50": {
                "hex": "#F8F9FA",
                "usage": "页面背景",
            },
            "gray-100": {
                "hex": "#F1F3F4",
                "usage": "卡片背景、分割线",
            },
            "gray-200": {
                "hex": "#E8EAED",
                "usage": "边框、分割线",
            },
            "gray-400": {
                "hex": "#BDC1C6",
                "usage": "禁用状态、占位符",
            },
            "gray-600": {
                "hex": "#80868B",
                "usage": "辅助文字",
            },
            "gray-800": {
                "hex": "#3C4043",
                "usage": "正文文字",
            },
            "gray-900": {
                "hex": "#202124",
                "usage": "标题文字、重点内容",
            },
        },
        "semantic": {
            "success": {
                "hex": "#34A853",
                "rgb": (52, 168, 83),
                "usage": "成功状态、完成指示",
            },
            "warning": {
                "hex": "#FBBC04",
                "rgb": (251, 188, 4),
                "usage": "警告状态、注意事项",
            },
            "error": {
                "hex": "#EA4335",
                "rgb": (234, 67, 53),
                "usage": "错误状态、删除操作",
            },
            "info": {
                "hex": "#4285F4",
                "rgb": (66, 133, 244),
                "usage": "信息提示、链接",
            },
        },
        "subsidiary": {
            "content": {
                "name": "墨笔文创",
                "hex": "#8E44AD",
                "usage": "内容创作品牌色",
            },
            "design": {
                "name": "墨图设计",
                "hex": "#E67E22",
                "usage": "设计子公司品牌色",
            },
            "video": {
                "name": "墨播短视频",
                "hex": "#E74C3C",
                "usage": "短视频子公司品牌色",
            },
            "voice": {
                "name": "墨声配音",
                "hex": "#3498DB",
                "usage": "语音子公司品牌色",
            },
            "crm": {
                "name": "墨域私域",
                "hex": "#2ECC71",
                "usage": "私域运营品牌色",
            },
            "finance": {
                "name": "墨算财务",
                "hex": "#F39C12",
                "usage": "财务子公司品牌色",
            },
            "tech": {
                "name": "墨码开发",
                "hex": "#9B59B6",
                "usage": "技术子公司品牌色",
            },
        },
        "gradients": {
            "brand_horizontal": {
                "colors": ["#1A73E8", "#4285F4"],
                "direction": "→",
                "usage": "横幅、卡片头部渐变",
            },
            "brand_accent": {
                "colors": ["#1A73E8", "#FF6B35"],
                "direction": "→",
                "usage": "营销素材主渐变",
            },
            "dark_elegant": {
                "colors": ["#1E1E2E", "#2D2D44"],
                "direction": "↓",
                "usage": "深色模式背景渐变",
            },
        },
        "metadata": {
            "version": "1.0.0",
            "updated": "2026-05-08",
            "description": "Hermes OS 视觉识别系统 — 完整品牌色板",
            "color_format": "HEX / RGB",
        },
    }

    return palette


# ──────────────────────────────────────────────
# 2. 字体规范
# ──────────────────────────────────────────────

def typography_spec() -> Dict:
    """
    Hermes OS 字体规范定义。

    支持：中文字体（思源黑体/宋体）+ 英文字体（Inter/Georgia）

    Returns:
        dict: 完整字体规范
    """
    spec = {
        "chinese": {
            "primary": {
                "family": "Noto Sans CJK SC",
                "fallback": ["思源黑体", "Source Han Sans", "PingFang SC",
                             "Microsoft YaHei", "sans-serif"],
                "usage": "正文、标题、UI 文字",
                "weights": {
                    "light": 300,
                    "regular": 400,
                    "medium": 500,
                    "bold": 700,
                },
            },
            "secondary": {
                "family": "Noto Serif CJK SC",
                "fallback": ["思源宋体", "Source Han Serif", "STSong",
                             "SimSun", "serif"],
                "usage": "正式文档、引用、长文阅读",
                "weights": {
                    "regular": 400,
                    "bold": 700,
                },
            },
        },
        "english": {
            "primary": {
                "family": "Inter",
                "fallback": ["SF Pro Display", "Segoe UI", "Helvetica Neue",
                             "Arial", "sans-serif"],
                "usage": "UI、标题、数字数据",
                "weights": {
                    "light": 300,
                    "regular": 400,
                    "medium": 500,
                    "semibold": 600,
                    "bold": 700,
                },
            },
            "secondary": {
                "family": "Georgia",
                "fallback": ["Times New Roman", "Palatino", "serif"],
                "usage": "英文长文、博客、出版物",
                "weights": {
                    "regular": 400,
                    "bold": 700,
                },
            },
            "mono": {
                "family": "JetBrains Mono",
                "fallback": ["Fira Code", "SF Mono", "Consolas", "monospace"],
                "usage": "代码、技术文档、终端输出",
                "weights": {
                    "regular": 400,
                    "bold": 700,
                },
            },
        },
        "font_sizes": {
            "caption": {"size": "12px", "line_height": 1.4, "usage": "标注、辅助文字"},
            "body_small": {"size": "13px", "line_height": 1.5, "usage": "小号正文"},
            "body": {"size": "14px", "line_height": 1.6, "usage": "正文"},
            "body_large": {"size": "16px", "line_height": 1.6, "usage": "大号正文"},
            "h6": {"size": "14px", "weight": 600, "usage": "六级标题"},
            "h5": {"size": "16px", "weight": 600, "usage": "五级标题"},
            "h4": {"size": "18px", "weight": 600, "usage": "四级标题"},
            "h3": {"size": "20px", "weight": 700, "usage": "三级标题"},
            "h2": {"size": "24px", "weight": 700, "usage": "二级标题"},
            "h1": {"size": "32px", "weight": 700, "usage": "一级标题"},
            "hero": {"size": "48px", "weight": 800, "usage": "Hero标题"},
        },
        "spacing": {
            "paragraph_gap": "1.2em",
            "heading_margin_top": "2em",
            "heading_margin_bottom": "0.5em",
        },
        "metadata": {
            "version": "1.0.0",
            "updated": "2026-05-08",
            "description": "Hermes OS 字体规范 — 中英双语排版系统",
        },
    }

    return spec


# ──────────────────────────────────────────────
# 3. 封面模板生成
# ──────────────────────────────────────────────

COVER_TEMPLATES = {
    "minimal": {
        "name": "简约白",
        "description": "白底+品牌蓝标题+简约布局，适合通用场景",
        "spec": {
            "background": "#FFFFFF",
            "accent_bar": "#1A73E8",
            "title_color": "#1E1E2E",
            "subtitle_color": "#5F6368",
            "font_title": "Inter / Noto Sans CJK SC",
            "border_radius": "12px",
            "shadow": "0 4px 16px rgba(0,0,0,0.08)",
        },
    },
    "dark": {
        "name": "深色科技",
        "description": "深蓝黑底+渐变色+科技感，适合技术/产品展示",
        "spec": {
            "background": "#1E1E2E",
            "accent_bar": "#4285F4",
            "title_color": "#FFFFFF",
            "subtitle_color": "#BDC1C6",
            "font_title": "Inter / Noto Sans CJK SC",
            "border_radius": "12px",
            "shadow": "0 4px 20px rgba(0,0,0,0.3)",
        },
    },
    "vibrant": {
        "name": "活力渐变",
        "description": "蓝橙渐变背景+白色文字，适合营销/推广内容",
        "spec": {
            "background": "linear-gradient(135deg, #1A73E8, #FF6B35)",
            "accent_bar": "#FFFFFF",
            "title_color": "#FFFFFF",
            "subtitle_color": "rgba(255,255,255,0.85)",
            "font_title": "Inter / Noto Sans CJK SC",
            "border_radius": "12px",
            "shadow": "0 8px 32px rgba(26,115,232,0.3)",
        },
    },
    "elegant": {
        "name": "雅致商务",
        "description": "浅灰底+金色强调+宋体标题，适合正式报告/财务内容",
        "spec": {
            "background": "#F8F9FA",
            "accent_bar": "#D4AF37",
            "title_color": "#1E1E2E",
            "subtitle_color": "#5F6368",
            "font_title": "Noto Serif CJK SC / Georgia",
            "border_radius": "8px",
            "shadow": "0 2px 12px rgba(0,0,0,0.06)",
        },
    },
    "social": {
        "name": "社交媒体",
        "description": "鲜艳配色+大标题+CTA区域，适合小红书/公众号封面",
        "spec": {
            "background": "#FFFFFF",
            "accent_bar": "#FF6B35",
            "title_color": "#1E1E2E",
            "subtitle_color": "#80868B",
            "font_title": "Inter / Noto Sans CJK SC",
            "border_radius": "0px",
            "shadow": "0 2px 8px rgba(0,0,0,0.1)",
        },
    },
}


def cover_templates(template_name: Optional[str] = None) -> Dict:
    """
    封面模板定义。可作为HTML/CSS/SVG生成的基础规范。

    Args:
        template_name: 指定模板名称，None返回全部

    Returns:
        dict: 封面模板规范
    """
    if template_name:
        if template_name in COVER_TEMPLATES:
            return {template_name: COVER_TEMPLATES[template_name]}
        else:
            available = ", ".join(COVER_TEMPLATES.keys())
            return {
                "error": f"模板 '{template_name}' 不存在。可用模板: {available}",
                "available": list(COVER_TEMPLATES.keys()),
            }

    return COVER_TEMPLATES


# ──────────────────────────────────────────────
# HTML 封面预览生成
# ──────────────────────────────────────────────

def generate_html_preview(
    title: str,
    subtitle: str = "Hermes OS",
    template: str = "minimal",
    output_path: Optional[str] = None,
) -> str:
    """
    生成封面预览HTML文件，可在浏览器中查看效果。

    Args:
        title: 封面标题
        subtitle: 副标题
        template: 模板名称
        output_path: 输出HTML路径

    Returns:
        str: HTML文件路径
    """
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    if template not in COVER_TEMPLATES:
        template = "minimal"

    tpl = COVER_TEMPLATES[template]
    spec = tpl["spec"]

    bg = spec["background"]
    bar = spec["accent_bar"]
    tc = spec["title_color"]
    sc = spec["subtitle_color"]
    br = spec["border_radius"]
    shadow = spec["shadow"]

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{tpl['name']} — Hermes OS 封面预览</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700&display=swap');
  
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  
  body {{
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    background: #f0f0f0;
    font-family: 'Inter', 'Noto Sans SC', sans-serif;
  }}
  
  .cover {{
    width: 800px;
    height: 450px;
    background: {bg};
    border-radius: {br};
    box-shadow: {shadow};
    position: relative;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: flex-start;
    padding: 60px;
  }}
  
  .accent-bar {{
    position: absolute;
    top: 0;
    left: 0;
    width: 8px;
    height: 100%;
    background: {bar};
  }}
  
  .tag {{
    display: inline-block;
    background: {bar};
    color: #FFFFFF;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 1px;
    padding: 4px 12px;
    border-radius: 4px;
    margin-bottom: 24px;
    text-transform: uppercase;
  }}
  
  .title {{
    font-size: 42px;
    font-weight: 800;
    color: {tc};
    line-height: 1.2;
    margin-bottom: 16px;
    max-width: 80%;
  }}
  
  .subtitle {{
    font-size: 18px;
    font-weight: 400;
    color: {sc};
    line-height: 1.5;
  }}
  
  .footer {{
    position: absolute;
    bottom: 30px;
    right: 40px;
    font-size: 12px;
    color: {sc};
    opacity: 0.6;
    letter-spacing: 2px;
  }}
</style>
</head>
<body>
<div class="cover">
  <div class="accent-bar"></div>
  <div class="tag">HERMES OS</div>
  <div class="title">{title}</div>
  <div class="subtitle">{subtitle}</div>
  <div class="footer">✦ {tpl['name']}</div>
</div>
</body>
</html>"""

    if not output_path:
        output_path = os.path.join(OUTPUT_DIR, f"cover_{template}_{uuid.uuid4().hex[:8]}.html")

    Path(output_path).write_text(html, encoding="utf-8")
    print(f"✅ 封面预览已生成: {output_path}")
    print(f"   打开浏览器查看: file://{os.path.abspath(output_path)}")

    return output_path


# ──────────────────────────────────────────────
# SVG 封面生成（纯矢量，可嵌入/转换）
# ──────────────────────────────────────────────

def generate_svg_cover(
    title: str,
    subtitle: str = "Hermes OS",
    template: str = "minimal",
    width: int = 800,
    height: int = 450,
    output_path: Optional[str] = None,
) -> str:
    """
    生成SVG格式封面（纯矢量，无需浏览器渲染）。

    Args:
        title: 标题
        subtitle: 副标题
        template: 模板名
        width, height: 尺寸
        output_path: 输出路径

    Returns:
        str: SVG文件路径
    """
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    if template not in COVER_TEMPLATES:
        template = "minimal"

    tpl = COVER_TEMPLATES[template]
    spec = tpl["spec"]
    bg = spec["background"]
    bar = spec["accent_bar"]
    tc = spec["title_color"]
    sc = spec["subtitle_color"]
    br = spec.get("border_radius", "12")

    # 处理渐变背景
    svg_bg = f'<rect width="{width}" height="{height}" rx="{br}" fill="{bg}"/>'
    if "gradient" in bg.lower():
        svg_bg = f'''
        <defs>
            <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:#1A73E8"/>
                <stop offset="100%" style="stop-color:#FF6B35"/>
            </linearGradient>
        </defs>
        <rect width="{width}" height="{height}" rx="{br}" fill="url(#grad)"/>
        '''

    # Build SVG manually to avoid f-string quote conflicts
    def _xml_escape(s):
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&apos;")

    svg_lines = []
    svg_lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    svg_lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">')
    svg_lines.append(f'  {svg_bg.strip()}')
    svg_lines.append(f'  <rect x="0" y="0" width="8" height="{height}" fill="{bar}"/>')
    svg_lines.append(f'  <text x="60" y="90" font-family="Inter, sans-serif" font-size="14"')
    svg_lines.append(f'        font-weight="600" fill="{bar}" letter-spacing="2">HERMES OS</text>')
    svg_lines.append(f'  <text x="60" y="220" font-family="Inter, sans-serif" font-size="42"')
    svg_lines.append(f'        font-weight="800" fill="{tc}">{_xml_escape(title)}</text>')
    svg_lines.append(f'  <text x="60" y="270" font-family="Inter, sans-serif" font-size="18"')
    svg_lines.append(f'        fill="{sc}">{_xml_escape(subtitle)}</text>')
    svg_lines.append(f'  <text x="{width-40}" y="{height-30}" font-family="Inter, sans-serif"')
    svg_lines.append(f'        font-size="12" fill="{sc}" text-anchor="end" opacity="0.6">')
    svg_lines.append(f'    &#10022; {tpl["name"]}')
    svg_lines.append('  </text>')
    svg_lines.append('</svg>')
    svg = "\n".join(svg_lines)

    if not output_path:
        output_path = os.path.join(OUTPUT_DIR, f"cover_{template}_{uuid.uuid4().hex[:8]}.svg")

    Path(output_path).write_text(svg, encoding="utf-8")
    print(f"✅ SVG封面已生成: {output_path}")

    return output_path


# ──────────────────────────────────────────────
# JSON 导出
# ──────────────────────────────────────────────

def export_identity_json(output_path: str) -> str:
    """
    导出完整的视觉身份定义为单JSON文件。

    Args:
        output_path: JSON输出路径

    Returns:
        str: 输出路径
    """
    identity = {
        "identity": {
            "name": "Hermes OS Visual Identity",
            "version": "1.0.0",
            "updated": "2026-05-08",
        },
        "color_palette": color_palette(),
        "typography": typography_spec(),
        "cover_templates": cover_templates(),
    }

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(
        json.dumps(identity, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"✅ 视觉身份定义已导出: {output_path}")

    return output_path


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="CH7-K: 视觉身份系统 — Hermes OS 品牌视觉定义"
    )
    parser.add_argument("--action", "-a", default="show",
                        choices=["show", "html", "svg", "export"],
                        help="操作: show(显示定义), html(生成HTML预览), svg(生成SVG), export(导出JSON)")
    parser.add_argument("--title", "-t", default="构建AI Agent系统",
                        help="封面标题")
    parser.add_argument("--subtitle", "-s", default="Hermes OS · 墨麟 AI 集团",
                        help="封面副标题")
    parser.add_argument("--template", "-tp", default="minimal",
                        choices=list(COVER_TEMPLATES.keys()),
                        help="封面模板")
    parser.add_argument("--output", "-o", help="输出文件路径")

    args = parser.parse_args()

    if args.action == "show":
        print("\n🎨 Hermes OS 视觉身份系统\n")

        print("━" * 50)
        print("1. 主色调")
        print("━" * 50)
        palette = color_palette()
        for category, colors in palette.items():
            print(f"\n  [{category}]")
            for name, info in colors.items():
                if isinstance(info, dict) and "hex" in info:
                    hex_val = info["hex"]
                    usage = info.get("usage", "")
                    print(f"    {hex_val}  — {info.get('name', name)} ({usage})")
                elif isinstance(info, dict) and "colors" in info:
                    colors_list = info.get("colors", [])
                    print(f"    {' → '.join(colors_list)}  — {name} ({info.get('usage', '')})")

        print("\n" + "━" * 50)
        print("2. 字体规范")
        print("━" * 50)
        spec = typography_spec()
        for lang, fonts in spec.items():
            if isinstance(fonts, dict) and "primary" in fonts:
                print(f"\n  [{lang}]")
                primary = fonts["primary"]
                print(f"    主字体: {primary['family']}")
                print(f"    备选: {', '.join(primary['fallback'][:3])}")
                print(f"    用途: {primary['usage']}")

        print("\n" + "━" * 50)
        print("3. 封面模板")
        print("━" * 50)
        for name, tpl in cover_templates().items():
            print(f"\n  [{name}] {tpl['name']}")
            print(f"    {tpl['description']}")
            spec = tpl["spec"]
            print(f"    背景: {spec['background']}")
            print(f"    强调色: {spec['accent_bar']}")

        print("\n" + "━" * 50)

    elif args.action == "html":
        generate_html_preview(
            title=args.title,
            subtitle=args.subtitle,
            template=args.template,
            output_path=args.output,
        )

    elif args.action == "svg":
        generate_svg_cover(
            title=args.title,
            subtitle=args.subtitle,
            template=args.template,
            output_path=args.output,
        )

    elif args.action == "export":
        if not args.output:
            args.output = os.path.join(OUTPUT_DIR, "hermes_visual_identity.json")
        export_identity_json(args.output)


if __name__ == "__main__":
    main()
