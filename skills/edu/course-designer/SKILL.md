# course-designer · 课程设计引擎
# 归属: Agent B (edu) 独占 · 版本: v1.0
## 触发词
触发词: 课程设计|大纲|教案|知识点拆解|学习路径
触发词: 模块设计|课程结构|教学方案|章节规划
## 调用格式
INPUT: { "course_title": "课程名称", "target_audience": "受众描述", "duration_hours": 10, "level": "入门|进阶|高级" }
OUTPUT: { "modules": [{"title":"","objectives":[],"content_points":[],"exercises":[]}], "learning_outcomes": [], "assessment_design": "" }
## 执行步骤（集成STORM深度调研）
Step 1: 调用Agent D的research-engine扫描同类课程竞品大纲
Step 2: 调用gpt-researcher联网获取该主题最新知识体系
Step 3: 基于ADDIE模型 + 布鲁姆分类设计课程结构
Step 4: 逆向设计：先定学习成果，再定内容，再定练习
Step 5: 输出完整课程大纲（含每模块学习目标+内容要点+练习题设计）
## 设计原则
- 每个模块不超过45分钟（成人注意力阈值）
- 理论:实践 = 3:7（知识付费用户需要即学即用）
- 每模块至少1个可交付的练习作业
## 经验规则
- 逻辑思维课程：先讲框架，再讲工具，最后讲案例（学员完课率最高）
- 视频时长10-15分钟比30分钟完播率高40%
