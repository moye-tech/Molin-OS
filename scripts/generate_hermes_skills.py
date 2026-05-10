#!/usr/bin/env python3
"""
为所有子公司生成墨麟AI原生格式的SKILL.md文件
"""

import os
import sys
import yaml
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def load_subsidiary_config(skill_id):
    """加载子公司配置"""
    config_path = f"config/hermes-agent/skills/{skill_id}.yaml"
    if not os.path.exists(config_path):
        return None

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    return config.get(skill_id) if config else None

def generate_skill_md(skill_id, skill_config):
    """生成SKILL.md文件内容"""

    # 从配置中提取信息
    name = skill_config.get('name', skill_id)
    description = skill_config.get('description', '')
    triggers = skill_config.get('triggers', {})
    keywords = triggers.get('keywords', [])
    tools = skill_config.get('tools', [])
    approval_level = skill_config.get('approval_level', 'low')
    cost_level = skill_config.get('cost_level', 'medium')
    max_concurrent = skill_config.get('max_concurrent', 2)
    model_preference = skill_config.get('model_preference', 'qwen3.6-plus')

    # 映射子公司类型到英文ID
    subsidiary_mapping = {
        'edu': 'education',
        'order': 'order',
        'ip': 'ip-content',
        'dev': 'development',
        'ai': 'ai-model',
        'shop': 'ecommerce',
        'data': 'data-analysis',
        'growth': 'user-growth',
        'secure': 'security',
        'research': 'market-research',
        'product': 'product-management',
        'ceo_decision': 'ceo-decision'
    }

    skill_dir_name = subsidiary_mapping.get(skill_id, skill_id)

    # 生成SKILL.md内容
    content = f"""---
name: {name}
description: {description}
version: 1.0.0
author: 墨麟AI智能系统
license: MIT
dependencies: []
metadata:
  hermes:
    tags: [{skill_id}, subsidiary, business]
    config:
      approval_level: {approval_level}
      cost_level: {cost_level}
      max_concurrent: {max_concurrent}
      model_preference: {model_preference}
---

# {name}

{description}

## 功能

{get_subsidiary_functionality(skill_id)}

## 触发关键词

{', '.join(keywords)}

## 使用示例

```json
{{
  "task": "请处理以下{name}相关任务",
  "context": "具体任务描述..."
}}
```

## 配置

在config.yaml中添加：

```yaml
skills:
  {skill_id}:
    implementation:
      module: hermes_fusion.skills.hermes_native.subsidiary_base_skill
      class: SubsidiaryMolinSkill
      config:
        subsidiary_type: '{skill_id}'
    approval_level: {approval_level}
    cost_level: {cost_level}
    max_concurrent: {max_concurrent}
    model_preference: {model_preference}
```

## 工具

{get_subsidiary_tools_list(skill_id, tools)}

## 性能配置

- 最大并发: {max_concurrent}
- 成本级别: {cost_level}
- 审批级别: {approval_level}
- 模型偏好: {model_preference}
"""
    return content, skill_dir_name

def get_subsidiary_functionality(skill_id):
    """获取子公司功能描述"""
    functionality_map = {
        'edu': '1. **课程管理**: 课程创建、编辑、发布\n2. **培训材料**: 培训内容开发、资料管理\n3. **知识付费**: 付费课程、订阅管理\n4. **教学支持**: 学习路径规划、进度跟踪',
        'order': '1. **订单处理**: 订单创建、修改、取消\n2. **价格管理**: 定价策略、折扣管理\n3. **交易处理**: 支付处理、退款管理\n4. **物流跟踪**: 发货、配送、签收跟踪',
        'ip': '1. **内容创作**: 文案、视频、图片创作\n2. **IP管理**: IP孵化、版权管理\n3. **社交媒体**: 内容发布、粉丝互动\n4. **品牌建设**: 品牌形象、宣传材料',
        'dev': '1. **代码开发**: 代码编写、调试、优化\n2. **技术架构**: 系统设计、架构规划\n3. **部署运维**: 部署上线、监控维护\n4. **测试验证**: 单元测试、集成测试',
        'ai': '1. **模型训练**: AI模型训练、优化\n2. **提示工程**: 提示词优化、模板设计\n3. **模型部署**: 模型部署、API服务\n4. **性能评估**: 模型评估、性能监控',
        'shop': '1. **商品管理**: 商品上架、库存管理\n2. **营销推广**: 促销活动、广告投放\n3. **客户服务**: 客服支持、售后处理\n4. **销售分析**: 销售数据、业绩分析',
        'data': '1. **数据分析**: 数据清洗、分析处理\n2. **报表生成**: 报表制作、可视化展示\n3. **业务洞察**: 业务分析、趋势预测\n4. **数据挖掘**: 模式发现、价值提取',
        'growth': '1. **用户获取**: 获客策略、渠道拓展\n2. **用户激活**: 激活流程、体验优化\n3. **用户留存**: 留存策略、忠诚度管理\n4. **转化优化**: 转化率提升、漏斗分析',
        'secure': '1. **安全审计**: 安全检查、漏洞扫描\n2. **合规管理**: 合规检查、风险管理\n3. **数据保护**: 数据加密、隐私保护\n4. **安全监控**: 实时监控、事件响应',
        'research': '1. **市场研究**: 市场分析、趋势研究\n2. **竞品分析**: 竞争对手、产品分析\n3. **机会识别**: 机会发现、风险评估\n4. **研究报告**: 报告撰写、成果展示',
        'product': '1. **产品规划**: 产品路线图、版本规划\n2. **需求分析**: 需求收集、优先级排序\n3. **用户体验**: 交互设计、可用性测试\n4. **产品迭代**: 版本迭代、功能优化',
        'ceo_decision': '1. **ROI分析**: 分析项目预算、时间线、目标收入，计算ROI\n2. **三层决策**: 基于ROI分析和记忆系统做出GO/NO_GO/NEED_INFO决策\n3. **记忆集成**: 查询分层记忆系统（SQLite/Qdrant/Redis/Supermemory）\n4. **每日优化**: 执行每日决策优化和系统调优'
    }
    return functionality_map.get(skill_id, '具体功能根据业务需求确定。')

def get_subsidiary_tools_list(skill_id, tools):
    """获取子公司工具列表"""
    if not tools:
        return '具体工具根据业务需求配置。'

    tool_list = '\n'.join([f'- {tool}' for tool in tools])
    return tool_list

def create_all_skills():
    """为所有子公司创建SKILL.md文件"""
    print("=" * 60)
    print("为所有子公司创建墨麟AI原生格式SKILL.md文件")
    print("=" * 60)

    # 子公司列表
    subsidiaries = [
        'edu', 'order', 'ip', 'dev', 'ai', 'shop',
        'data', 'growth', 'secure', 'research', 'product', 'ceo_decision'
    ]

    skills_base_dir = "hermes-agent-skills"

    # 确保基础目录存在
    os.makedirs(skills_base_dir, exist_ok=True)

    created_count = 0
    skipped_count = 0

    for skill_id in subsidiaries:
        print(f"\n处理 {skill_id}...")

        # 加载配置
        skill_config = load_subsidiary_config(skill_id)
        if not skill_config:
            print(f"  ✗ 配置不存在: {skill_id}.yaml")
            skipped_count += 1
            continue

        # 生成SKILL.md内容
        skill_content, skill_dir_name = generate_skill_md(skill_id, skill_config)

        # 创建技能目录
        skill_dir = os.path.join(skills_base_dir, skill_dir_name)
        os.makedirs(skill_dir, exist_ok=True)

        # 写入SKILL.md文件
        skill_md_path = os.path.join(skill_dir, "SKILL.md")
        with open(skill_md_path, 'w', encoding='utf-8') as f:
            f.write(skill_content)

        print(f"  ✓ 创建: {skill_md_path}")
        print(f"    技能名称: {skill_config.get('name', skill_id)}")

        created_count += 1

    print(f"\n" + "=" * 60)
    print("创建完成")
    print("=" * 60)
    print(f"成功创建: {created_count} 个技能")
    print(f"跳过: {skipped_count} 个技能")

    # 验证创建的文件
    print(f"\n验证创建的文件...")
    skill_dirs = [d for d in os.listdir(skills_base_dir) if os.path.isdir(os.path.join(skills_base_dir, d))]

    for skill_dir in skill_dirs:
        skill_md_path = os.path.join(skills_base_dir, skill_dir, "SKILL.md")
        if os.path.exists(skill_md_path):
            print(f"  ✓ {skill_dir}/SKILL.md")
        else:
            print(f"  ✗ {skill_dir}/SKILL.md 不存在")

    return created_count > 0

def test_skill_discovery():
    """测试技能发现"""
    print("\n" + "=" * 60)
    print("测试技能发现")
    print("=" * 60)

    try:
        from tools.skills_tool import _find_all_skills
        all_skills = _find_all_skills()

        # 查找我们的技能
        our_skills = []
        for skill in all_skills:
            name = skill.get('name', '').lower()
            if any(keyword in name for keyword in ['子公司', 'ceo', '决策', 'education', 'order', 'ip', 'dev', 'ai', 'shop', 'data', 'growth', 'secure', 'research', 'product']):
                our_skills.append(skill)

        print(f"总共发现 {len(all_skills)} 个技能")
        print(f"其中我们的技能: {len(our_skills)} 个")

        for skill in our_skills[:5]:  # 显示前5个
            print(f"  - {skill.get('name')}: {skill.get('description', '')[:80]}...")

        if len(our_skills) >= 5:
            print(f"  ... 还有 {len(our_skills) - 5} 个技能")

        return len(our_skills) >= 5  # 期望至少5个技能被发现

    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("生成墨麟AI原生技能文件")
    print("=" * 60)

    # 创建所有技能
    success = create_all_skills()

    if success:
        # 测试技能发现
        print("\n" + "=" * 60)
        print("运行技能发现测试")
        print("=" * 60)

        # 等待配置生效
        import time
        print("等待配置生效...")
        time.sleep(1)

        test_success = test_skill_discovery()

        if test_success:
            print("\n✓ 所有技能成功创建并可被发现")
            print("\n下一步:")
            print("  1. 验证hermes skills list命令显示我们的技能")
            print("  2. 测试实际hermes-agent会话中的技能调用")
            print("  3. 验证技能路由和执行")
        else:
            print("\n⚠️ 技能创建成功但发现测试失败")
            print("  可能需要重启hermes-agent或等待配置刷新")
    else:
        print("\n✗ 技能创建失败")

    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)