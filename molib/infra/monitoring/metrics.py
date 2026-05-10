"""Prometheus 监控指标"""
from prometheus_client import Counter, Histogram, Gauge, generate_latest

api_calls = Counter('molin_api_calls_total', 'Total API calls', ['agency', 'status'])
api_latency = Histogram('molin_api_latency_seconds', 'API latency', ['agency'])
daily_cost = Gauge('molin_daily_cost_cny', 'Daily API cost in CNY')
agency_executions = Counter('molin_agency_executions_total', 'Agency executions', ['agency_id', 'result_status'])
quality_scores = Histogram('molin_quality_score', 'SOP quality scores', ['agency_id'])
memory_entries = Gauge('molin_memory_entries', 'Memory entries by type', ['type'])


def record_api_call(agency: str, status: str, latency: float):
    """记录一次 API 调用"""
    api_calls.labels(agency=agency, status=status).inc()
    api_latency.labels(agency=agency).observe(latency)


def record_agency_execution(agency_id: str, result_status: str, quality_score: float = None):
    """记录一次 Agency 执行"""
    agency_executions.labels(agency_id=agency_id, result_status=result_status).inc()
    if quality_score is not None:
        quality_scores.labels(agency_id=agency_id).observe(quality_score)


def get_metrics_response() -> bytes:
    """返回 Prometheus 格式的指标数据"""
    return generate_latest()
