# FeishuReplyPipeline 实战示例

> 来源: molin_reply_upgrade_v68.html + 本 session v2.2 实现

## 输入

```python
ceo_result = {
    'status': 'completed',
    'intent': {
        'type': '分析',
        'target_subsidiaries': ['research', 'shop', 'ip', 'data', 'legal'],
        'target_vps': ['VP战略', 'VP营销'],
        'complexity_score': 7,
        'risk_level': 'low',
        'confidence': 0.94,
    },
    'risk': {
        'risk_score': 15,
        'requires_approval': False,
        'flags': ['平台合规需注意'],
    },
    'execution': {
        'vps_used': [
            {'name': 'research', 'status': 'completed'},
            {'name': 'shop', 'status': 'completed'},
        ],
        'results': [
            {'vp': 'research', 'summary': '找到6类可接单服务·AI文案29-99元·自动填表400元'},
            {'vp': 'shop', 'summary': '生成了3套商品文案·含阶梯定价'},
        ],
    },
    'quality_gate': {'score': 85},
    'sop_record_id': 'sop-abc12345',
    'duration': 1.2,
}
```

## 输出

```
4 messages:
  消息1: "🧠 CEO 推理过程" (3 elements)
    └─ L1: 意图类型: 分析
       L2: 复杂度: 7/10 · 匹配 5 个子公司
       L3: 风险等级: low · 需审批: False
       └─ ⏱ 1s · 5子公司 · 信心度 94%

  消息2: "✅ 任务完成" (7 elements)
    └─ 调度子公司: research · shop
       任务状态: completed
       质量评分: 85/100
       [results sections...]
       [actions: 导出报告 / 继续提问]

  消息3: "📊 research · 完整报告" (3 elements)

  消息4: "📊 shop · 完整报告" (3 elements)
```

## 接入网关

`molib/infra/gateway/platforms/feishu.py`:

```python
def _format_ceo_response(self, ceo_result):
    from molib.infra.gateway.feishu_reply_pipeline import FeishuReplyPipeline
    pipeline = FeishuReplyPipeline()
    user_query = ceo_result.get("intent", {}).get("raw_text", "") or ceo_result.get("task_id", "")
    messages = pipeline.build(user_query, ceo_result)
    return {
        "msg_type": "interactive",
        "card": messages[1]["card"],      # 主回复
        "_all_messages": messages,         # 全部（上游可遍历发送）
    }
```

## 测试命令

```bash
cd /Users/moye/Molin-OS && python -c "
from molib.infra.gateway.feishu_reply_pipeline import FeishuReplyPipeline
p = FeishuReplyPipeline()
r = p.build('测试查询', { ...ceo_result... })
for i, msg in enumerate(r):
    c = msg['card']
    hdr = c.get('header',{}).get('title',{}).get('content','?')
    print(f'消息{i+1}: {hdr} ({len(c[\"elements\"])} elements)')
"
```
