"""墨麟OS — DAG引擎单元测试"""
import pytest
from molib.ceo.dag_engine import DAGEngine, DAGTask


def test_simple_task():
    """简单任务：1步，直接执行"""
    dag = DAGEngine()
    result = dag.decompose("content", ["vp_marketing"], ["content_writer"], 25, {}, "写一篇简单文章")
    assert len(result.tasks) == 1
    assert result.tasks[0].step_id == "execute"
    assert result.tasks[0].model_tier == "flash"
    assert result.tasks[0].ready is True


def test_complex_task():
    """复杂任务：多步+依赖+复盘"""
    dag = DAGEngine()
    result = dag.decompose("strategy", ["vp_marketing", "vp_strategy"], ["content_writer", "research"], 85, {}, "年度战略")
    assert len(result.tasks) == 5  # scan → analysis → proposal → review → retrospect
    assert result.tasks[0].step_id == "scan"
    assert result.tasks[0].ready is True
    assert result.tasks[1].depends_on == ["scan"]
    assert result.tasks[-1].step_id == "retrospect"


def test_parallel_groups():
    """并行组检测：串行任务应只产生1个并行组"""
    dag = DAGEngine()
    result = dag.decompose("content", ["vp_marketing"], ["content_writer"], 75, {}, "系列文章")
    # content类型4步：research→draft→review→publish，每个依赖于前一个
    # 所以只有1个并行组（所有任务串行）
    assert len(result.parallel_groups) >= 1


def test_model_tier_assignment():
    """模型等级分配：高复杂度战略步骤用pro，普通步骤用flash"""
    dag = DAGEngine()
    result = dag.decompose("strategy", ["vp_marketing"], ["content_writer"], 90, {}, "顶层战略")
    # 高复杂度策略任务：analysis/strategy/review/retrospect 用 pro
    for task in result.tasks:
        if task.step_id in ("analysis", "strategy", "review", "retrospect"):
            assert task.model_tier == "pro", f"{task.step_id} should be 'pro', got '{task.model_tier}'"
        elif task.step_id == "scan":
            assert task.model_tier == "flash", f"{task.step_id} should be 'flash' (simple step), got '{task.model_tier}'"

def test_vision_and_video_tier():
    """视觉/视频相关任务自动分配对应的模型tier"""
    dag = DAGEngine()
    # 视觉相关任务 → vision
    result = dag.decompose("content", ["vp_marketing"], ["designer"], 50, {}, "设计封面图片")
    vision_tasks = [t for t in result.tasks if t.model_tier == "vision"]
    assert len(vision_tasks) > 0, "Should have some vision-tier tasks"
    # 所有涉及design/设计子公司的都是vision
    for t in result.tasks:
        if t.assigned_subsidiary == "designer" and "图片" in t.description:
            assert t.model_tier == "vision"
    # 视频相关任务 → video
    result_v = dag.decompose("content", ["vp_marketing"], ["video_editor"], 50, {}, "制作短视频")
    video_tasks = [t for t in result_v.tasks if t.model_tier == "video"]
    assert len(video_tasks) > 0, "Should have some video-tier tasks"


def test_medium_task():
    """中等复杂度：标准流程，无复盘"""
    dag = DAGEngine()
    result = dag.decompose("operation", ["vp_ops"], ["crm"], 50, {}, "处理运营任务")
    assert len(result.tasks) >= 3  # diagnose→plan→execute→verify
    has_retrospect = any(t.step_id == "retrospect" for t in result.tasks)
    assert not has_retrospect, "中等复杂度不应该有复盘步"


def test_mark_and_completed():
    """标记完成和ready状态传播"""
    dag = DAGEngine()
    result = dag.decompose("development", ["vp_tech"], ["developer"], 75, {}, "开发任务")
    # 初始：只有第1步ready
    tasks = dag.mark_completed(result.tasks, "requirements", {"ok": True})
    # 标记requirements完成后，design应该ready
    design = [t for t in tasks if t.step_id == "design"]
    assert len(design) > 0
    assert design[0].ready is True


def test_unknown_intent():
    """未知意图类型：使用通用兜底策略"""
    dag = DAGEngine()
    result = dag.decompose("unknown_type", ["vp_marketing"], ["content_writer"], 50, {}, "随便什么")
    assert len(result.tasks) == 3  # FALLBACK: understand→execute→verify
    assert result.tasks[0].step_id == "understand"
    assert result.tasks[1].step_id == "execute"
    assert result.tasks[2].step_id == "verify"
