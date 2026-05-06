"""
墨麟AIOS — MetricsCollector
指标采集器
===========================
参考吸收:
- Vibe-Trading (4K⭐): 市场分析+数据源统一抽象
- Google ADK (19K⭐): 评估指标框架

核心能力:
1. collect          — 平台指标采集（阅读量、互动率、转化率等）
2. dashboard        — 生成概览仪表盘数据
3. compare_periods  — 环比分析
"""

import math
import hashlib
from datetime import datetime, timedelta
from typing import Any

# ── 模拟指标数据库（Vibe-Trading 数据源统一抽象层） ──────────

# 平台基础流量配置
_PLATFORM_PROFILES: dict[str, dict[str, float]] = {
    "xiaoHongShu": {
        "daily_active_users": 2_500_000,
        "avg_read_rate": 0.038,
        "avg_interaction_rate": 0.042,
        "avg_conversion_rate": 0.012,
        "avg_share_rate": 0.008,
        "base_exposure": 10_000,
    },
    "weChat": {
        "daily_active_users": 8_000_000,
        "avg_read_rate": 0.045,
        "avg_interaction_rate": 0.018,
        "avg_conversion_rate": 0.006,
        "avg_share_rate": 0.005,
        "base_exposure": 5_000,
    },
    "weiBo": {
        "daily_active_users": 5_000_000,
        "avg_read_rate": 0.025,
        "avg_interaction_rate": 0.035,
        "avg_conversion_rate": 0.008,
        "avg_share_rate": 0.015,
        "base_exposure": 20_000,
    },
    "dyKuaishou": {
        "daily_active_users": 6_500_000,
        "avg_read_rate": 0.055,
        "avg_interaction_rate": 0.050,
        "avg_conversion_rate": 0.018,
        "avg_share_rate": 0.020,
        "base_exposure": 30_000,
    },
    "bilibili": {
        "daily_active_users": 1_800_000,
        "avg_read_rate": 0.048,
        "avg_interaction_rate": 0.038,
        "avg_conversion_rate": 0.010,
        "avg_share_rate": 0.012,
        "base_exposure": 8_000,
    },
    "zhihu": {
        "daily_active_users": 1_200_000,
        "avg_read_rate": 0.032,
        "avg_interaction_rate": 0.025,
        "avg_conversion_rate": 0.009,
        "avg_share_rate": 0.006,
        "base_exposure": 4_000,
    },
}

# 指标类型映射
_METRIC_TYPES = {
    "impressions": "曝光量",           # total times content is displayed
    "reads": "阅读量",                 # unique readers
    "interactions": "互动量",          # likes + comments + shares
    "engagement_rate": "互动率",       # interactions / impressions
    "read_rate": "阅读率",             # reads / impressions
    "conversions": "转化量",           # clicks / signups / purchases
    "conversion_rate": "转化率",       # conversions / reads
    "shares": "分享量",               # share count
    "share_rate": "分享率",           # shares / interactions
    "dau_reach": "DAU触达率",         # reads / daily_active_users
    "avg_time": "平均阅读时长(秒)",   # seconds
    "bounce_rate": "跳出率",          # % who leave immediately
}

# 指标分组
_METRIC_CATEGORIES: dict[str, list[str]] = {
    "volume": ["impressions", "reads", "interactions", "conversions", "shares"],
    "rate": ["engagement_rate", "read_rate", "conversion_rate", "share_rate", "dau_reach", "bounce_rate"],
    "quality": ["avg_time"],
}


class MetricsCollector:
    """指标采集器。

    基于 Vibe-Trading 平台抽象 + Google ADK 评估框架设计。
    支持单平台/全平台指标采集，仪表盘概览，环比分析。
    所有方法均包含模拟业务逻辑，可直接用于 API 响应。
    """

    # ── 指标采集 ─────────────────────────────────────────────

    def collect(
        self,
        platform: str,
        metric_type: str,
        period: str = "7d",
    ) -> dict[str, Any]:
        """采集指定平台的指标数据。

        Args:
            platform:    平台名称 ("xiaoHongShu"/"weChat"/... 或 "all")
            metric_type: 指标类型 ("engagement_rate"/"reads"/"conversions"/... 或 "all")
            period:      时间窗口 ("1d"/"3d"/"7d"/"14d"/"30d")

        Returns:
            dict: {
                platform: {metric_name: {value, change, trend, ...}},
                meta: {period, collected_at, platform_count}
            }
        """
        if platform == "all":
            # 汇总所有平台
            all_data = {}
            for pf in _PLATFORM_PROFILES:
                all_data[pf] = self._collect_single(pf, metric_type, period)
            # 计算汇总
            aggregated = self._aggregate_platforms(all_data, metric_type)
            return {
                "platforms": all_data,
                "aggregated": aggregated,
                "meta": {
                    "period": period,
                    "collected_at": datetime.now().isoformat(),
                    "platform_count": len(_PLATFORM_PROFILES),
                    "metric_type": metric_type,
                    "metric_label": _METRIC_TYPES.get(metric_type, metric_type),
                },
            }

        # 单平台采集
        if platform not in _PLATFORM_PROFILES:
            return {
                "error": f"不支持的平台: {platform}",
                "supported_platforms": list(_PLATFORM_PROFILES.keys()),
                "meta": {"period": period, "collected_at": datetime.now().isoformat()},
            }

        single_data = self._collect_single(platform, metric_type, period)
        return {
            "platforms": {platform: single_data},
            "aggregated": self._aggregate_platforms({platform: single_data}, metric_type),
            "meta": {
                "period": period,
                "collected_at": datetime.now().isoformat(),
                "platform_count": 1,
                "metric_type": metric_type,
                "metric_label": _METRIC_TYPES.get(metric_type, metric_type),
            },
        }

    # ── 仪表盘概览 ───────────────────────────────────────────

    def dashboard(self, metrics_list: list[str]) -> dict[str, Any]:
        """生成概览仪表盘数据。

        基于 Google ADK 评估框架的指标聚合思想，
        将多个指标组合为统一的监控面板视图。

        Args:
            metrics_list: 指标列表，如 ["reads", "engagement_rate", "conversion_rate"]

        Returns:
            dict: {
                overview: {kpi_name: {current, change, status}},
                per_platform: {platform: {kpi: value, ...}},
                summary: 关键洞察文本
            }
        """
        if not metrics_list:
            metrics_list = ["impressions", "reads", "interactions", "engagement_rate", "conversion_rate"]

        # 采集全平台数据
        all_data = {}
        for pf in _PLATFORM_PROFILES:
            pf_data = {}
            for mt in metrics_list:
                result = self._collect_single(pf, mt, "7d")
                if mt in result:
                    pf_data[mt] = result[mt]
            all_data[pf] = pf_data

        # 构建概览KPI
        overview = {}
        for mt in metrics_list:
            total_value = 0
            changes = []
            statuses = []

            for pf in _PLATFORM_PROFILES:
                if mt in all_data.get(pf, {}):
                    metric_info = all_data[pf][mt]
                    total_value += metric_info.get("value", 0)
                    changes.append(metric_info.get("change", 0))
                    statuses.append(metric_info.get("trend", "stable"))

            avg_change = round(sum(changes) / len(changes), 2) if changes else 0.0

            # 状态判断（Google ADK 评估指标框架风格）
            trend_count = {"up": 0, "down": 0, "stable": 0}
            for s in statuses:
                trend_count[s] = trend_count.get(s, 0) + 1

            overall_status = "up" if trend_count.get("up", 0) > trend_count.get("down", 0) else "down"
            if trend_count.get("up", 0) == trend_count.get("down", 0):
                overall_status = "stable"

            # 健康度打分（0-100）
            health_score = self._compute_health_score(mt, total_value, avg_change)

            overview[mt] = {
                "label": _METRIC_TYPES.get(mt, mt),
                "total_value": round(total_value, 2) if not isinstance(total_value, int) else total_value,
                "avg_change_pct": avg_change,
                "trend": overall_status,
                "health_score": health_score,
                "status": "good" if health_score >= 70 else ("warning" if health_score >= 40 else "critical"),
                "platforms_reporting": len([pf for pf in _PLATFORM_PROFILES if mt in all_data.get(pf, {})]),
            }

        # 每平台KPI快照
        per_platform = {}
        for pf in _PLATFORM_PROFILES:
            pf_snapshot = {}
            for mt in metrics_list:
                if mt in all_data.get(pf, {}):
                    pf_snapshot[mt] = all_data[pf][mt].get("value", 0)
            per_platform[pf] = pf_snapshot

        # 关键洞察
        summary = self._generate_dashboard_insight(overview, per_platform)

        return {
            "overview": overview,
            "per_platform": per_platform,
            "summary": summary,
            "meta": {
                "metrics_count": len(metrics_list),
                "platforms_count": len(_PLATFORM_PROFILES),
                "generated_at": datetime.now().isoformat(),
                "framework": "Google ADK 评估指标聚合",
            },
        }

    # ── 环比分析 ─────────────────────────────────────────────

    def compare_periods(
        self,
        metric: str,
        period1: str,
        period2: str,
    ) -> dict[str, Any]:
        """环比分析：对比两个时间段的指标变化。

        Args:
            metric:  指标名称
            period1: 基期（"1d"/"3d"/"7d"/"14d"/"30d"）
            period2: 报告期

        Returns:
            dict: {
                metric: str,
                period1_data: {platform: value},
                period2_data: {platform: value},
                changes: {platform: {absolute_change, relative_change, direction}},
                summary: 整体环比结论
            }
        """
        if metric not in _METRIC_TYPES:
            return {"error": f"不支持的指标: {metric}", "supported_metrics": list(_METRIC_TYPES.keys())}

        # 采集双期数据
        p1_data = {}
        p2_data = {}

        for pf in _PLATFORM_PROFILES:
            p1 = self._collect_single(pf, metric, period1)
            p2 = self._collect_single(pf, metric, period2)
            if metric in p1 and "value" in p1[metric]:
                p1_data[pf] = p1[metric]["value"]
            if metric in p2 and "value" in p2[metric]:
                p2_data[pf] = p2[metric]["value"]

        # 计算变化
        changes = {}
        for pf in _PLATFORM_PROFILES:
            v1 = p1_data.get(pf, 0)
            v2 = p2_data.get(pf, 0)
            if v1 == 0 and v2 == 0:
                changes[pf] = {
                    "absolute_change": 0,
                    "relative_change": 0.0,
                    "direction": "no_data",
                }
            elif v1 == 0:
                changes[pf] = {
                    "absolute_change": v2,
                    "relative_change": 100.0,
                    "direction": "new",
                }
            else:
                abs_change = round(v2 - v1, 2)
                rel_change = round((v2 - v1) / v1 * 100, 2)
                direction = "up" if abs_change > 0 else ("down" if abs_change < 0 else "flat")
                changes[pf] = {
                    "absolute_change": abs_change,
                    "relative_change": rel_change,
                    "direction": direction,
                }

        # 汇总
        total_p1 = sum(p1_data.values())
        total_p2 = sum(p2_data.values())
        if total_p1 == 0:
            overall_change_str = "基期无数据，无法计算整体环比"
        else:
            overall_pct = round((total_p2 - total_p1) / total_p1 * 100, 2)
            direction = "上升" if overall_pct > 0 else ("下降" if overall_pct < 0 else "持平")
            overall_change_str = f"整体{direction} {abs(overall_pct)}%"

        up_count = sum(1 for c in changes.values() if c["direction"] == "up")
        down_count = sum(1 for c in changes.values() if c["direction"] == "down")

        return {
            "metric": metric,
            "metric_label": _METRIC_TYPES.get(metric, metric),
            "period1": period1,
            "period1_label": f"基期 ({period1})",
            "period2": period2,
            "period2_label": f"报告期 ({period2})",
            "period1_data": p1_data,
            "period2_data": p2_data,
            "changes": changes,
            "summary": {
                "overall_change": overall_change_str,
                "total_period1": round(total_p1, 2),
                "total_period2": round(total_p2, 2),
                "absolute_change": round(total_p2 - total_p1, 2),
                "relative_change": round((total_p2 - total_p1) / max(total_p1, 1) * 100, 2),
                "platforms_up": up_count,
                "platforms_down": down_count,
                "platforms_total": len(_PLATFORM_PROFILES),
            },
            "meta": {
                "generated_at": datetime.now().isoformat(),
                "methodology": "环比分析 (sequential comparison)",
            },
        }

    # ── 内部采集方法 ─────────────────────────────────────────

    def _collect_single(
        self,
        platform: str,
        metric_type: str,
        period: str,
    ) -> dict[str, Any]:
        """单个平台指标采集实现。"""
        profile = _PLATFORM_PROFILES.get(platform)
        if profile is None:
            return {}

        period_days = _period_to_days(period)
        time_factor = max(0.1, min(1.0, period_days / 7.0))

        if metric_type == "all":
            # 返回该平台所有可用指标
            result = {}
            for mt in _METRIC_TYPES:
                result[mt] = self._compute_metric(platform, mt, period_days, time_factor)
            return result

        # 单指标采集
        metric_data = self._compute_metric(platform, metric_type, period_days, time_factor)
        return {metric_type: metric_data}

    def _compute_metric(
        self,
        platform: str,
        metric_type: str,
        period_days: int,
        time_factor: float,
    ) -> dict[str, Any]:
        """计算具体指标值。"""
        profile = _PLATFORM_PROFILES.get(platform)
        if profile is None:
            return {"value": 0, "change": 0, "trend": "stable", "unit": ""}

        seed = platform + metric_type + datetime.now().strftime("%Y%m")
        noise = _metric_noise(seed) * 0.15  # ±15% 噪声

        base_exposure = profile["base_exposure"] * period_days

        if metric_type == "impressions":
            value = int(base_exposure * (1 + noise))
            change = round(_metric_noise(seed + "change") * 8, 1)
            unit = "次"
        elif metric_type == "reads":
            raw = base_exposure * profile["avg_read_rate"] * (1 + noise)
            value = int(raw)
            change = round(_metric_noise(seed + "change") * 6, 1)
            unit = "人"
        elif metric_type == "interactions":
            raw = base_exposure * profile["avg_read_rate"] * profile["avg_interaction_rate"] * (1 + noise)
            value = int(raw)
            change = round(_metric_noise(seed + "change") * 10, 1)
            unit = "次"
        elif metric_type == "engagement_rate":
            value = round(profile["avg_interaction_rate"] * (1 + noise), 4)
            change = round(_metric_noise(seed + "change") * 0.5, 2)
            unit = "%"
        elif metric_type == "read_rate":
            value = round(profile["avg_read_rate"] * (1 + noise), 4)
            change = round(_metric_noise(seed + "change") * 0.3, 2)
            unit = "%"
        elif metric_type == "conversions":
            imp = base_exposure * (1 + noise * 0.5)
            raw = imp * profile["avg_conversion_rate"]
            value = int(raw)
            change = round(_metric_noise(seed + "change") * 12, 1)
            unit = "次"
        elif metric_type == "conversion_rate":
            value = round(profile["avg_conversion_rate"] * (1 + noise), 4)
            change = round(_metric_noise(seed + "change") * 0.4, 2)
            unit = "%"
        elif metric_type == "shares":
            raw = base_exposure * profile["avg_share_rate"] * (1 + noise)
            value = int(raw)
            change = round(_metric_noise(seed + "change") * 8, 1)
            unit = "次"
        elif metric_type == "share_rate":
            value = round(profile["avg_share_rate"] * (1 + noise), 4)
            change = round(_metric_noise(seed + "change") * 0.3, 2)
            unit = "%"
        elif metric_type == "dau_reach":
            reads = base_exposure * profile["avg_read_rate"] * (1 + noise)
            dau = profile["daily_active_users"]
            value = round(reads / max(dau, 1), 4)
            change = round(_metric_noise(seed + "change") * 0.2, 2)
            unit = "%"
        elif metric_type == "avg_time":
            base_times = {"xiaoHongShu": 45, "weChat": 32, "weiBo": 28, "dyKuaishou": 55,
                          "bilibili": 62, "zhihu": 52}
            value = round(base_times.get(platform, 40) * (1 + noise * 0.3), 1)
            change = round(_metric_noise(seed + "change") * 3, 1)
            unit = "秒"
        elif metric_type == "bounce_rate":
            base_bounce = {"xiaoHongShu": 0.38, "weChat": 0.42, "weiBo": 0.55, "dyKuaishou": 0.35,
                           "bilibili": 0.32, "zhihu": 0.45}
            value = round(base_bounce.get(platform, 0.40) * (1 + noise * 0.2), 3)
            change = round(_metric_noise(seed + "change") * 0.3, 2)
            unit = "%"
        else:
            return {"value": 0, "change": 0, "trend": "stable", "unit": ""}

        # 趋势判定
        trend = "up" if change > 0.5 else ("down" if change < -0.5 else "stable")

        return {
            "value": value,
            "change": change,
            "trend": trend,
            "unit": unit,
            "platform": platform,
            "period_days": period_days,
        }

    def _aggregate_platforms(
        self,
        all_data: dict[str, dict[str, Any]],
        metric_type: str,
    ) -> dict[str, Any]:
        """跨平台聚合汇总。"""
        total_value = 0
        total_prev_value = 0
        platform_count = 0

        for pf, data in all_data.items():
            if metric_type in data:
                info = data[metric_type]
                if isinstance(info, dict) and "value" in info:
                    total_value += info["value"]
                    # 用 change 反推基期值
                    if info["change"] != 0:
                        prev = info["value"] / (1 + info["change"] / 100)
                        total_prev_value += prev
                    else:
                        total_prev_value += info["value"]
                    platform_count += 1

        if total_prev_value == 0:
            overall_change = 0
        else:
            overall_change = round((total_value - total_prev_value) / total_prev_value * 100, 2)

        return {
            "total_value": round(total_value, 2),
            "overall_change_pct": overall_change,
            "contributing_platforms": platform_count,
            "metric_type": metric_type,
            "metric_label": _METRIC_TYPES.get(metric_type, metric_type),
        }

    def _compute_health_score(self, metric: str, value: float, change: float) -> int:
        """基于 Google ADK 评估框架思想计算指标健康度。"""
        # 不同指标的基准不同
        if metric in ("engagement_rate", "conversion_rate", "share_rate", "read_rate"):
            # 比率型：越高越好
            score = min(100, max(0, int(value * 500 + change * 2 + 50)))
        elif metric in ("impressions", "reads", "interactions", "conversions", "shares"):
            # 体量型：变化方向更重要
            score = min(100, max(0, int(50 + change * 1.5)))
        elif metric == "bounce_rate":
            # 跳出率：越低越好
            score = min(100, max(0, int(100 - value * 100 - change * 0.5)))
        elif metric == "avg_time":
            # 时长：越长越好
            score = min(100, max(0, int(value * 1.5 + change * 0.5)))
        else:
            score = 50
        return int(score)

    def _generate_dashboard_insight(
        self,
        overview: dict[str, Any],
        per_platform: dict[str, dict[str, Any]],
    ) -> list[str]:
        """基于数据生成关键洞察文本。"""
        insights = []

        # 1. 整体健康度
        healths = [m.get("health_score", 50) for m in overview.values()]
        avg_health = sum(healths) / len(healths) if healths else 0
        if avg_health >= 75:
            insights.append(f"整体指标健康状况良好（平均健康度 {avg_health:.0f}/100），各平台表现稳定")
        elif avg_health >= 50:
            insights.append(f"整体指标中等（平均健康度 {avg_health:.0f}/100），部分指标需关注")
        else:
            insights.append(f"整体指标偏低（平均健康度 {avg_health:.0f}/100），建议排查问题")

        # 2. 表现最佳/最差平台
        platform_scores = {}
        for pf, metrics in per_platform.items():
            vals = [v for v in metrics.values() if isinstance(v, (int, float))]
            platform_scores[pf] = sum(vals) / len(vals) if vals else 0

        if platform_scores:
            best = max(platform_scores, key=platform_scores.get)
            worst = min(platform_scores, key=platform_scores.get)
            insights.append(f"平台表现排名：{best} 领先，{worst} 需优化")

        # 3. 指标趋势分析
        up_metrics = [k for k, v in overview.items() if v.get("trend") == "up"]
        down_metrics = [k for k, v in overview.items() if v.get("trend") == "down"]
        if up_metrics:
            names = [_METRIC_TYPES.get(m, m) for m in up_metrics[:3]]
            insights.append(f"上升指标：{'、'.join(names)} 呈上升趋势")
        if down_metrics:
            names = [_METRIC_TYPES.get(m, m) for m in down_metrics[:3]]
            insights.append(f"下降指标：{'、'.join(names)} 呈下降趋势，建议关注")

        return insights


# ── 辅助函数 ────────────────────────────────────────────────

def _period_to_days(period: str) -> int:
    """时间窗口转天数。"""
    mapping = {"1d": 1, "3d": 3, "7d": 7, "14d": 14, "30d": 30, "90d": 90}
    return mapping.get(period, 7)


def _metric_noise(seed: str) -> float:
    """基于种子的确定性噪声 [-1, 1]。"""
    hash_bytes = hashlib.md5(seed.encode()).digest()
    return (int.from_bytes(hash_bytes[:4], "big") / 2**32) * 2 - 1
