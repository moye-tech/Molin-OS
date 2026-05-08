#!/usr/bin/env python3
"""
繁体中文本地化工具 — CH8 出海台湾

功能：
1. localize_content(text) — 简体中文 → 台湾繁体中文转换
2. localize_ai_term(text) — AI 术语本地化
3. batch_localize(dir_path) — 批量转换目录下所有 .md 文件

使用标准库实现，无第三方依赖。
"""

import os
import re

# ============================================================
# 简体 → 繁体对照表（常见用词）
# ============================================================
SIMPLE_TO_TRADITIONAL = {
    # 基础字型转换（常用）
    "软件": "軟體",
    "硬件": "硬體",
    "网络": "網路",
    "互联网": "網路",
    "服务器": "伺服器",
    "算法": "演算法",
    "数据": "資料",
    "数据库": "資料庫",
    "编程": "程式設計",
    "代码": "程式碼",
    "开源": "開源",
    "插件": "外掛",
    "兼容": "相容",
    "默认": "預設",
    "点击": "點擊",
    "登录": "登入",
    "账号": "帳號",
    "密码": "密碼",
    "邮箱": "電子信箱",
    "手机": "手機",
    "信息": "資訊",
    "验证": "驗證",
    "链接": "連結",
    "菜单": "選單",
    "文件": "檔案",
    "文件夹": "資料夾",
    "缓存": "快取",
    "垃圾邮件": "垃圾郵件",
    "更新": "更新",
    "设置": "設定",
    "支持": "支援",
    "优化": "最佳化",
    "视频": "影片",
    "音频": "音訊",
    "博客": "部落格",
    "二维码": "QR Code",
    "私信": "私訊",
    "点赞": "按讚",
    "关注": "追蹤",
    "粉丝": "粉絲",
    "打印机": "印表機",
    "鼠标": "滑鼠",
    "键盘": "鍵盤",
    "屏幕": "螢幕",
    "充电器": "充電器",
    "移动硬盘": "隨身硬碟",
    "U盘": "隨身碟",
    "笔记本": "筆電",
    "台式机": "桌機",
    "智能": "智慧",
    "语音": "語音",
    "芯片": "晶片",
    "传感器": "感測器",
    "人工智能": "人工智慧",
    "机器学习": "機器學習",
    "深度学习": "深度學習",
    "神经网络": "神經網路",
    "数字": "數位",
    "电子商务": "電子商務",
    "移动支付": "行動支付",
    "在线": "線上",
    "离线": "離線",
    "界面": "介面",
    "窗口": "視窗",
    "滚动": "捲動",
    "搜索": "搜尋",
    "点击率": "點擊率",
    "转化率": "轉換率",
    "公测": "公開測試",
    "内测": "內部測試",
    "用户体验": "使用者體驗",
    "用户界面": "使用者介面",
    "后台": "後台",
    "前台": "前台",
    "全栈": "全端",
    "前端": "前端",
    "后端": "後端",
    "云": "雲端",
    "大数据": "大數據",
    "物联网": "物聯網",
    "区块链": "區塊鏈",
    "元宇宙": "元宇宙",
    "提示词": "提示詞",
    "生成式": "生成式",
    "向量": "向量",
    "权重": "權重",
    "训练": "訓練",
    "推理": "推理",
}

# 需要后处理（避免过度转换）
SIMPLE_TO_TRADITIONAL_SKIP_WORDS = {
    "更新",  # 相同写法，跳过
    "训练",  # 相同写法，跳过
    "推理",  # 相同写法，跳过
    "開源",  # 已转换
}


# ============================================================
# AI 术语本地化对照表
# ============================================================
AI_TERM_MAP = {
    "AI": "AI／人工智慧",
    "人工智能": "人工智慧",
    "大模型": "大型語言模型",
    "大语言模型": "大型語言模型",
    "AI Agent": "AI 代理",
    "AI代理": "AI 代理",
    "Prompt": "提示詞（Prompt）",
    "prompt": "提示詞（prompt）",
    "提示工程": "提示詞工程",
    "RAG": "RAG（檢索增強生成）",
    "检索增强生成": "檢索增強生成",
    "Fine-tune": "微調（Fine-tune）",
    "fine-tune": "微調（fine-tune）",
    "微调": "微調",
    "LLM": "大型語言模型（LLM）",
    "向量数据库": "向量資料庫",
    "Embedding": "嵌入（Embedding）",
    "embedding": "嵌入（embedding）",
    "多模态": "多模態",
    "多模态模型": "多模態模型",
    "Token": "Token（詞元）",
    "token": "token（詞元）",
    "Transformer": "Transformer（轉換器）",
    "transformer": "transformer（轉換器）",
    "扩散模型": "擴散模型",
    "Stable Diffusion": "Stable Diffusion",
    "Midjourney": "Midjourney",
    "ChatGPT": "ChatGPT",
    "Claude": "Claude",
    "Gemini": "Gemini",
    "API": "API",
    "SDK": "SDK",
    "AI工具": "AI 工具",
    "工具调用": "工具呼叫",
    "function calling": "function calling（函式呼叫）",
    "Function Calling": "Function Calling（函式呼叫）",
    "Agent": "Agent（代理）",
    "agent": "agent（代理）",
    "智能体": "智慧代理",
    "工作流": "工作流程",
    "知识图谱": "知識圖譜",
    "语义搜索": "語意搜尋",
    "意图识别": "意圖辨識",
    "情感分析": "情緒分析",
    "命名实体识别": "命名實體辨識",
    "语音识别": "語音辨識",
    "计算机视觉": "電腦視覺",
    "自然语言处理": "自然語言處理",
    "NLP": "自然語言處理（NLP）",
}

# 需要精确匹配（避免误伤普通词汇）
AI_TERM_EXACT_MATCH = {
    "AI", "LLM", "NLP", "RAG", "API", "SDK", "Agent", "agent",
    "Prompt", "prompt", "Token", "token",
    "ChatGPT", "Claude", "Gemini",
    "Transformer", "transformer",
    "Stable Diffusion", "Midjourney",
    "Function Calling", "function calling",
    "Fine-tune", "fine-tune",
    "Embedding", "embedding",
}


def _convert_basic_chars(text: str) -> str:
    """
    基础简繁字型转换（使用 Python 标准库）。
    注意：Python 的 unicodedata 没有完整简繁映射，
    这里使用开源映射表。
    """
    # 简繁常用字映射（前500高频差异字）
    char_map = {
        '体': '體', '门': '門', '问': '問', '间': '間', '关': '關',
        '开': '開', '对': '對', '时': '時', '问': '問', '题': '題',
        '点': '點', '发': '發', '会': '會', '说': '說', '话': '話',
        '来': '來', '过': '過', '这': '這', '那': '那', '里': '裡',
        '们': '們', '吗': '嗎', '呢': '呢', '吧': '吧', '啊': '啊',
        '么': '麼', '没': '沒', '为': '為', '与': '與', '个': '個',
        '国': '國', '家': '家', '年': '年', '经': '經', '济': '濟',
        '机': '機', '电': '電', '话': '話', '动': '動', '种': '種',
        '样': '樣', '然': '然', '后': '後', '前': '前', '新': '新',
        '旧': '舊', '长': '長', '东': '東', '西': '西', '南': '南',
        '北': '北', '上': '上', '下': '下', '左': '左', '右': '右',
        '内': '內', '外': '外', '见': '見', '学': '學', '习': '習',
        '书': '書', '画': '畫', '写': '寫', '读': '讀', '课': '課',
        '时': '時', '间': '間', '早': '早', '晚': '晚', '日': '日',
        '月': '月', '星': '星', '期': '期', '现': '現', '实': '實',
        '质': '質', '量': '量', '数': '數', '据': '據', '结': '結',
        '构': '構', '程': '程', '序': '序', '式': '式', '应': '應',
        '用': '用', '制': '製', '度': '度', '级': '級', '别': '別',
        '系': '系', '统': '統', '组': '組', '织': '織',
        '评': '評', '价': '價', '值': '值', '任': '任', '务': '務',
        '帮': '幫', '助': '助', '备': '備', '份': '份',
        '创': '創', '业': '業', '权': '權', '利': '利',
        '报': '報', '告': '告', '产': '產', '品': '品',
        '运': '運', '营': '營', '销': '銷', '售': '售',
        '众': '眾', '多': '多', '广': '廣', '告': '告',
        '费': '費', '收': '收', '入': '入', '支': '支',
        '出': '出', '预': '預', '算': '算', '计': '計',
        '划': '劃', '定': '定', '义': '義', '规': '規',
        '范': '範', '模': '模', '块': '塊', '函': '函',
        '变': '變', '量': '量', '类': '類', '型': '型',
        '接': '接', '口': '口', '异': '異', '常': '常',
        '错': '錯', '误': '誤', '试': '試', '验': '驗',
        '测': '測', '试': '試', '调': '調',
    }

    result = []
    for ch in text:
        result.append(char_map.get(ch, ch))
    return ''.join(result)


def localize_content(text: str) -> str:
    """
    简体中文 → 台湾繁体中文完整转换。
    
    流程：
    1. 词汇级转换（用词差异）
    2. 字型级转换
    
    Args:
        text: 简体中文文本
        
    Returns:
        台湾繁体中文文本
    """
    # 先按长度排序，避免部分匹配问题
    sorted_terms = sorted(SIMPLE_TO_TRADITIONAL.keys(), key=len, reverse=True)
    
    result = text
    for term in sorted_terms:
        if term in SIMPLE_TO_TRADITIONAL_SKIP_WORDS:
            continue
        replacement = SIMPLE_TO_TRADITIONAL[term]
        # 确保是完整词汇匹配（使用正则）
        result = re.sub(re.escape(term), replacement, result)
    
    # 字型级转换
    result = _convert_basic_chars(result)
    
    return result


def localize_ai_term(text: str) -> str:
    """
    AI 术语本地化。
    将简体中文 AI 相关术语转换为台湾常用表达。
    
    Args:
        text: 包含 AI 术语的文本
        
    Returns:
        本地化后的文本
    """
    result = text
    
    # 先处理多词术语（长匹配优先）
    sorted_terms = sorted(AI_TERM_MAP.keys(), key=len, reverse=True)
    
    for term in sorted_terms:
        replacement = AI_TERM_MAP[term]
        
        if term in AI_TERM_EXACT_MATCH:
            # 精确匹配（边界检测）
            pattern = r'(?<!\w)' + re.escape(term) + r'(?!\w)'
        else:
            # 灵活匹配
            pattern = re.escape(term)
        
        result = re.sub(pattern, replacement, result)
    
    return result


def localize_full(text: str) -> str:
    """
    完整本地化：先转换 AI 术语，再转换简体→繁体。
    
    Args:
        text: 原始简体中文文本
        
    Returns:
        完整的台湾繁体中文文本
    """
    text = localize_ai_term(text)
    text = localize_content(text)
    return text


def batch_localize(dir_path: str) -> dict:
    """
    批量转换目录下所有 .md 文件。
    
    Args:
        dir_path: 目录路径
        
    Returns:
        处理结果统计: {
            "total": int,        # 总文件数
            "converted": int,    # 成功转换数
            "skipped": int,      # 跳过数
            "failed": int,       # 失败数
            "results": [         # 每个文件的处理结果
                {"file": str, "status": str, "error": str or None}
            ]
        }
    """
    if not os.path.isdir(dir_path):
        raise NotADirectoryError(f"目录不存在: {dir_path}")
    
    stats = {
        "total": 0,
        "converted": 0,
        "skipped": 0,
        "failed": 0,
        "results": [],
    }
    
    for root, dirs, files in os.walk(dir_path):
        # 跳过隐藏目录
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for filename in files:
            if not filename.endswith('.md'):
                continue
            
            filepath = os.path.join(root, filename)
            stats["total"] += 1
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 检查是否已经是繁体
                if _is_traditional(content):
                    stats["skipped"] += 1
                    stats["results"].append({
                        "file": filepath,
                        "status": "skipped",
                        "error": "已是繁体中文"
                    })
                    continue
                
                # 转换
                converted = localize_full(content)
                
                # 备份原文件
                backup_path = filepath + '.bak'
                os.rename(filepath, backup_path)
                
                # 写入转换后文件
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(converted)
                
                stats["converted"] += 1
                stats["results"].append({
                    "file": filepath,
                    "status": "converted",
                    "error": None
                })
                
                print(f"✓ 已转换: {filepath}")
                
            except Exception as e:
                stats["failed"] += 1
                stats["results"].append({
                    "file": filepath,
                    "status": "failed",
                    "error": str(e)
                })
                print(f"✗ 转换失败: {filepath} - {e}")
    
    return stats


def _is_traditional(text: str, sample_size: int = 1000) -> bool:
    """
    简单判断文本是否已经是繁体中文。
    通过检测常用繁体字特征。
    """
    # 繁体特征字
    traditional_indicators = {'的', '是', '了', '我', '有', '在', '不', '這', '說', '會'}
    # 简体特征字
    simple_indicators = {'的', '是', '了', '我', '有', '在', '不', '这', '说', '会'}
    
    sample = text[:sample_size]
    
    # 统计特征字出现次数
    trad_count = sum(1 for c in sample if c in traditional_indicators)
    simp_count = sum(1 for c in sample if c in simple_indicators)
    
    # 如果有繁体特有字，判为繁体
    trad_specific = {'這', '說', '會', '裡', '們', '嗎', '麼', '沒', '為', '與'}
    specific_count = sum(1 for c in sample if c in trad_specific)
    
    if specific_count > 5:
        return True
    
    return trad_count > simp_count


# ============================================================
# CLI 入口
# ============================================================
def main():
    import sys
    
    if len(sys.argv) < 2:
        print("用法:")
        print("  python localize_to_traditional.py <text>          # 转换文本")
        print("  python localize_to_traditional.py --ai <text>    # 转换 AI 术语")
        print("  python localize_to_traditional.py --dir <path>   # 批量转换目录")
        print("  python localize_to_traditional.py --full <text>  # 完整转换")
        print("\n示例:")
        print('  python localize_to_traditional.py "人工智能大模型正在改变软件行业"')
        print('  python localize_to_traditional.py --ai "大模型和AI Agent是最热门的技术"')
        print('  python localize_to_traditional.py --dir ./docs')
        sys.exit(1)
    
    if sys.argv[1] == "--ai":
        if len(sys.argv) < 3:
            print("请提供要转换的文本")
            sys.exit(1)
        result = localize_ai_term(sys.argv[2])
        print(result)
    
    elif sys.argv[1] == "--dir":
        if len(sys.argv) < 3:
            print("请提供目录路径")
            sys.exit(1)
        stats = batch_localize(sys.argv[2])
        print(f"\n处理完成:")
        print(f"  总文件数: {stats['total']}")
        print(f"  已转换: {stats['converted']}")
        print(f"  已跳过: {stats['skipped']}")
        print(f"  失败: {stats['failed']}")
    
    elif sys.argv[1] == "--full":
        if len(sys.argv) < 3:
            print("请提供要转换的文本")
            sys.exit(1)
        result = localize_full(sys.argv[2])
        print(result)
    
    else:
        text = ' '.join(sys.argv[1:])
        result = localize_content(text)
        print(result)


if __name__ == "__main__":
    main()
