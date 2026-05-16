#!/usr/bin/env python3
"""
墨麟OS · 智能模型路由器
标准任务走 DeepSeek v4 flash，复杂任务走 DeepSeek v4 pro。
根据任务关键词自动判断复杂度，返回对应模型配置。

用法:
  python3 ~/Molin-OS/tools/cost_router.py "任务描述"
  返回最优模型配置 dict
"""
import os
import sys
from enum import Enum


class TaskComplexity(Enum):
    SIMPLE   = "simple"    # 简单→ v4 flash
    STANDARD = "standard"  # 标准→ v4 flash
    HEAVY    = "heavy"     # 复杂→ v4 pro


def classify_complexity(task_description: str) -> TaskComplexity:
    """根据任务描述判断复杂度"""
    simple_keywords = {"分类", "判断", "是否", "摘要", "总结", "路由",
                       "识别类型", "打标签", "关键词提取", "打分", "评分",
                       "排序", "过滤", "匹配", "转换", "格式化"}
    heavy_keywords = {"深度分析", "复杂推理", "长篇", "完整报告", "战略",
                      "全面", "综合分析", "1000字以上", "系统设计",
                      "架构", "竞品分析", "市场调研", "整体方案",
                      "详细规划", "技术方案", "设计文档"}

    if any(kw in task_description for kw in heavy_keywords):
        return TaskComplexity.HEAVY
    if any(kw in task_description for kw in simple_keywords):
        return TaskComplexity.SIMPLE
    return TaskComplexity.STANDARD


def get_model_config(complexity: TaskComplexity) -> dict:
    """根据复杂度返回模型配置"""
    configs = {
        TaskComplexity.SIMPLE: {
            "model": "deepseek-v4-flash",
            "cost_level": "标准",
            "note": "分类/判断/摘要等简单任务",
        },
        TaskComplexity.STANDARD: {
            "model": "deepseek-v4-flash",
            "cost_level": "标准",
            "note": "内容生成/文案/翻译/代码等常规任务",
        },
        TaskComplexity.HEAVY: {
            "model": "deepseek-v4-pro",
            "cost_level": "高",
            "note": "深度分析/完整报告/战略/架构等复杂任务",
        },
    }
    return configs[complexity]


def smart_model(task: str) -> dict:
    """一行调用：输入任务描述，返回最优模型配置"""
    complexity = classify_complexity(task)
    config = get_model_config(complexity)
    print(f"📊 任务复杂度: {complexity.value} → 模型: {config['model']} ({config['cost_level']})")
    return config


if __name__ == "__main__":
    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
        smart_model(task)
    else:
        test_tasks = [
            "判断这条消息是否包含成交意向关键词",
            "帮我写一篇1200字的小红书爆款笔记",
            "对本月全部业务进行深度综合分析并生成战略报告",
        ]
        for task in test_tasks:
            smart_model(task)
