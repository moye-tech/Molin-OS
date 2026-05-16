# self-learning-loop · 自学习闭环
# 归属: 全部5个Agent共享 · 版本: v1.0

## 技能身份
任务完成后自动反思→提炼经验→结晶到长期记忆。
是ExperienceVault写入的标准入口。

## 触发词
触发词: 总结经验|复盘|周复盘|学到了什么|优化方案
触发词: 写入记忆|更新SOP|结晶经验
触发时机: 任何复杂任务（>5步骤）完成后自动触发

## 调用时机（自动）
- 复杂任务完成后（Agent自动调用，无需用户触发）
- 明显失败/错误后（强制触发，记录失败原因）
- 用户主动纠正Agent的输出时（纠正=最高价值学习信号）

## 三层结晶流程
Layer 1-工作记忆（即时）: 本次任务的执行步骤和结果
Layer 2-情节记忆（每周）: 本周同类任务的模式归纳
Layer 3-语义记忆（每月）: 跨任务的通用规律和原则

## 执行步骤
Step 1: 读取本次任务的 input/output/errors
Step 2: 提炼3个成功点 + 2个改进点
Step 3: 调用 tools/memory_bridge.py 的 save_task_experience()
Step 4: 更新对应技能文件中的「经验规则」字段
Step 5: 如果是周复盘，更新Obsidian Wiki的SOP文档

## 输出格式
{
  "success_patterns": ["成功模式1", "成功模式2", "成功模式3"],
  "improvement_points": ["改进点1", "改进点2"],
  "updated_skill": "更新了哪个技能的经验规则",
  "memory_saved": true
}
