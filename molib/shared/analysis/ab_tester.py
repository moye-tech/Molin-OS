"""
墨麟AIOS — ABTester
A/B测试评估器
===========================
参考吸收:
- Google ADK (19K⭐): 评估指标框架 — 统计显著性评估方法论
- opensre (4.4K⭐): 假设驱动调查循环 — 实验设计状态机

核心能力:
1. design_experiment — A/B测试设计（样本量估算、时长建议）
2. evaluate_results  — 统计显著性评估（z-test / chi-squared）
3. recommend         — 基于结果推荐胜出版本
"""

import math
from datetime import datetime, timedelta
from typing import Any

# ── 置信度Z值表（Google ADK 评估框架标准） ──────────────────
_Z_TABLE: dict[float, float] = {
    0.80: 1.28,
    0.85: 1.44,
    0.90: 1.645,
    0.95: 1.96,
    0.99: 2.576,
    0.999: 3.291,
}

# ── 效果量标准（Cohen's d） ─────────────────────────────────
_EFFECT_SIZE_THRESHOLDS: dict[str, float] = {
    "small": 0.2,
    "medium": 0.5,
    "large": 0.8,
}

# ── 流量水平估算基准 ─────────────────────────────────────────
_TRAFFIC_BASELINE = {
    "low": {"daily_visitors": 500, "label": "低流量（日均500）"},
    "medium": {"daily_visitors": 5000, "label": "中等流量（日均5K）"},
    "high": {"daily_visitors": 50000, "label": "高流量（日均50K）"},
}


class ABTester:
    """A/B测试评估器。

    基于 Google ADK 评估指标框架的统计方法论，提供：
    - design_experiment: A/B测试实验设计（样本量估算、时长建议、分流方案）
    - evaluate_results:  结果统计显著性评估（z-test 和 chi-squared）
    - recommend:         基于统计显著性和实际业务影响推荐胜出版本
    """

    # ── 实验设计 ─────────────────────────────────────────────

    def design_experiment(
        self,
        variant_a: dict[str, Any],
        variant_b: dict[str, Any],
        metrics: list[str],
    ) -> dict[str, Any]:
        """A/B测试实验设计。

        基于 Google ADK 评估框架，自动计算：
        - 最小样本量（min_sample_size）
        - 推荐实验时长（recommended_duration）
        - 分流方案（traffic_split）
        - 统计功效分析（statistical_power）

        Args:
            variant_a: 对照组配置，如 {"name": "原版", "current_rate": 0.12, "traffic_level": "medium"}
            variant_b: 实验组配置，如 {"name": "新版", "expected_rate": 0.15, "traffic_level": "medium"}
            metrics:    需要评估的指标列表，如 ["click_rate", "conversion_rate"]

        Returns:
            dict: {
                experiment_id, variants, metrics,
                min_sample_size, recommended_duration,
                traffic_split, statistical_power,
                design_notes
            }
        """
        # 提取关键参数
        name_a = variant_a.get("name", "对照组")
        name_b = variant_b.get("name", "实验组")
        current_rate = variant_a.get("current_rate", 0.10)
        expected_rate = variant_b.get("expected_rate", 0.12)
        traffic_level = variant_a.get("traffic_level", "medium")

        # 预期效果量（绝对值差异）
        effect_size_abs = abs(expected_rate - current_rate)
        # 相对提升
        if current_rate > 0:
            relative_improvement = effect_size_abs / current_rate
        else:
            relative_improvement = float("inf")

        # 1. 最小样本量估算（基于两比例z检验公式）
        # n = (Z_alpha/2 + Z_beta)^2 * (p1*(1-p1) + p2*(1-p2)) / (p2 - p1)^2
        z_alpha = _Z_TABLE.get(0.95, 1.96)  # 95% 置信度
        z_beta = _Z_TABLE.get(0.80, 1.28)   # 80% 统计功效

        p1 = current_rate
        p2 = expected_rate
        p_avg = (p1 + p2) / 2

        if effect_size_abs == 0:
            min_sample_size = float("inf")
        else:
            numerator = (z_alpha + z_beta) ** 2 * (p1 * (1 - p1) + p2 * (1 - p2))
            denominator = (p2 - p1) ** 2
            min_sample_size = math.ceil(numerator / denominator) if denominator > 0 else float("inf")

        # 总样本量（两组）
        total_sample_size = min_sample_size * 2 if min_sample_size != float("inf") else float("inf")

        # 2. 流量估算与实验时长
        daily_traffic_per_variant = _TRAFFIC_BASELINE.get(traffic_level, _TRAFFIC_BASELINE["medium"])["daily_visitors"]

        if total_sample_size == float("inf"):
            recommended_duration = float("inf")
        else:
            # 每组各一半流量
            recommended_duration = math.ceil(total_sample_size / (daily_traffic_per_variant * 2))

        # 最少运行天数约束（至少7天以覆盖周末波动）
        recommended_duration = max(recommended_duration, 7)

        # 3. 分流方案
        traffic_split = {
            "variant_a": {"name": name_a, "percentage": 50, "daily_visitors": daily_traffic_per_variant},
            "variant_b": {"name": name_b, "percentage": 50, "daily_visitors": daily_traffic_per_variant},
            "splitting_method": "均匀随机分流（UUID哈希）",
            "note": "建议按用户ID哈希取模，保证同一用户始终看到同一版本",
        }

        # 4. 统计功效分析
        # 对不同效果量计算可达功效
        power_analysis = self._power_analysis(
            min_sample_size, effect_size_abs, current_rate
        )

        # 5. 根据效果量大小给出设计建议
        design_notes = self._generate_design_notes(
            effect_size_abs, relative_improvement, recommended_duration,
            min_sample_size, traffic_level
        )

        # 构建metrics详情
        metrics_detail = []
        for m in metrics:
            metrics_detail.append({
                "metric": m,
                "test_type": "z-test（两比例）" if "rate" in m.lower() else "t-test（均值）",
                "expected_lift": round(relative_improvement * 100, 2) if relative_improvement != float("inf") else 0,
                "baseline": round(current_rate, 4),
                "target": round(expected_rate, 4),
            })

        return {
            "experiment_id": f"ABX-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "design_timestamp": datetime.now().isoformat(),
            "variants": {
                "a": {"name": name_a, "config": variant_a},
                "b": {"name": name_b, "config": variant_b},
            },
            "metrics": metrics_detail,
            "min_sample_size_per_group": min_sample_size,
            "total_sample_size": total_sample_size,
            "recommended_duration_days": recommended_duration,
            "traffic_split": traffic_split,
            "effect_size": {
                "absolute": round(effect_size_abs, 4),
                "relative_improvement_pct": round(relative_improvement * 100, 2) if relative_improvement != float("inf") else 0,
                "effect_magnitude": self._classify_effect_size(effect_size_abs / max(current_rate, 0.001)),
            },
            "statistical_power": power_analysis,
            "design_notes": design_notes,
            "framework": "Google ADK 评估指标框架",
        }

    # ── 结果评估 ─────────────────────────────────────────────

    def evaluate_results(
        self,
        results: dict[str, Any],
        confidence: float = 0.95,
    ) -> dict[str, Any]:
        """统计显著性评估。

        支持两大测试方法：
        - z-test: 用于比率型指标（点击率、转化率、留存率等）
        - chi-squared: 用于计数型指标（独立事件频次比较）

        Args:
            results: 实验原始结果，格式：
                {
                    "variant_a": {"visitors": 10000, "conversions": 1200},
                    "variant_b": {"visitors": 10000, "conversions": 1350},
                    "metric_name": "conversion_rate",
                    "metric_type": "rate" | "count"
                }
            confidence: 置信度水平（默认0.95）

        Returns:
            dict: {
                is_significant, p_value, z_score/chi2_stat,
                effect_size, confidence_interval,
                variant_a: {rate, conversions, ...},
                variant_b: {rate, conversions, ...},
                interpretation
            }
        """
        # 参数校验
        if confidence not in _Z_TABLE:
            # 找到最近的置信度
            confidence = min(_Z_TABLE.keys(), key=lambda k: abs(k - confidence))

        z_critical = _Z_TABLE[confidence]

        # 提取数据
        var_a = results.get("variant_a", {})
        var_b = results.get("variant_b", {})
        metric_type = results.get("metric_type", "rate")

        n_a = var_a.get("visitors", 0) or var_a.get("samples", 0)
        n_b = var_b.get("visitors", 0) or var_b.get("samples", 0)

        if n_a == 0 or n_b == 0:
            return {
                "error": "样本量不能为0",
                "is_significant": False,
            }

        if metric_type == "rate":
            # z-test 两比例检验
            conversions_a = var_a.get("conversions", 0)
            conversions_b = var_b.get("conversions", 0)

            p_a = conversions_a / n_a
            p_b = conversions_b / n_b

            # 合并比例
            p_pool = (conversions_a + conversions_b) / (n_a + n_b)

            # 标准误
            se = math.sqrt(p_pool * (1 - p_pool) * (1 / n_a + 1 / n_b))

            # z统计量
            if se == 0:
                z_score = 0.0
            else:
                z_score = (p_b - p_a) / se

            # p值（双尾检验）
            p_value = self._z_to_p_value(abs(z_score))

            # 置信区间（对差异）
            diff = p_b - p_a
            margin = z_critical * se
            ci_lower = diff - margin
            ci_upper = diff + margin

            # Cohen's h（效果量）
            effect_size = self._cohens_h(p_a, p_b)

            test_stat = z_score
            test_name = "z-test（双比例检验）"

            # 统计显著性判定
            is_significant = abs(z_score) > z_critical and p_value < (1 - confidence)

        elif metric_type == "count":
            # chi-squared 独立性检验
            # 构建2x2列联表
            count_a = var_a.get("count", 0)
            count_b = var_b.get("count", 0)
            # 非事件数
            non_a = n_a - count_a
            non_b = n_b - count_b

            # 卡方统计量
            total = n_a + n_b
            row1_total = count_a + count_b
            row2_total = non_a + non_b
            col1_total = n_a
            col2_total = n_b

            # 期望频次
            e1 = row1_total * col1_total / total if total > 0 else 0
            e2 = row1_total * col2_total / total if total > 0 else 0
            e3 = row2_total * col1_total / total if total > 0 else 0
            e4 = row2_total * col2_total / total if total > 0 else 0

            # 卡方 = sum((O-E)^2/E)
            chi2 = 0
            if e1 > 0:
                chi2 += (count_a - e1) ** 2 / e1
            if e2 > 0:
                chi2 += (count_b - e2) ** 2 / e2
            if e3 > 0:
                chi2 += (non_a - e3) ** 2 / e3
            if e4 > 0:
                chi2 += (non_b - e4) ** 2 / e4

            # p值（df=1）
            p_value = self._chi2_to_p_value(chi2, df=1)

            # 效果量（Cramer's V）
            effect_size = math.sqrt(chi2 / (total * 1)) if total > 0 else 0

            test_stat = chi2
            test_name = "chi-squared检验（独立性）"

            # 统计显著性判定（卡方临界值 α=0.05, df=1 → 3.841）
            chi2_critical = 3.841  # 对应 0.95 置信度
            if confidence == 0.99:
                chi2_critical = 6.635
            elif confidence == 0.90:
                chi2_critical = 2.706

            is_significant = chi2 > chi2_critical and p_value < (1 - confidence)

            p_a = count_a / n_a if n_a > 0 else 0
            p_b = count_b / n_b if n_b > 0 else 0
            ci_lower = 0
            ci_upper = 0

        else:
            return {
                "error": f"不支持的指标类型: {metric_type}，仅支持 'rate' 或 'count'",
                "is_significant": False,
            }

        # 业务显著性评估
        lift_pct = ((p_b - p_a) / max(p_a, 0.0001)) * 100
        business_significance = self._evaluate_business_significance(
            lift_pct, effect_size, is_significant
        )

        # 解读
        interpretation = self._generate_interpretation(
            is_significant, p_value, test_stat, effect_size,
            lift_pct, confidence, test_name
        )

        return {
            "is_statistically_significant": is_significant,
            "confidence_level": confidence,
            "p_value": round(p_value, 6),
            "test_statistic": round(test_stat, 4),
            "test_name": test_name,
            "effect_size": round(effect_size, 4),
            "effect_size_label": self._classify_effect_size_label(effect_size),
            "confidence_interval": {
                "lower": round(ci_lower, 6),
                "upper": round(ci_upper, 6),
            },
            "variants": {
                "a": {
                    "name": var_a.get("name", "对照组"),
                    "rate": round(p_a, 6),
                    "conversions": var_a.get("conversions", 0),
                    "samples": n_a,
                },
                "b": {
                    "name": var_b.get("name", "实验组"),
                    "rate": round(p_b, 6),
                    "conversions": var_b.get("conversions", 0),
                    "samples": n_b,
                },
            },
            "lift": {
                "absolute": round(p_b - p_a, 6),
                "relative_pct": round(lift_pct, 2),
            },
            "business_significance": business_significance,
            "interpretation": interpretation,
            "evaluated_at": datetime.now().isoformat(),
        }

    # ── 推荐决策 ─────────────────────────────────────────────

    def recommend(self, results: dict[str, Any]) -> str:
        """基于统计结果推荐胜出版本。

        综合考量：
        - 统计显著性
        - 效果量大小
        - 业务影响
        - 实施风险

        Args:
            results: evaluate_results 的输出

        Returns:
            str: 推荐意见文本
        """
        # 检查是否有错误
        if "error" in results:
            return f"⚠️ 无法推荐：{results['error']}"

        is_significant = results.get("is_statistically_significant", False)
        p_value = results.get("p_value", 1.0)
        effect_size = results.get("effect_size", 0)
        lift_pct = results.get("lift", {}).get("relative_pct", 0)
        ci = results.get("confidence_interval", {"lower": 0, "upper": 0})

        variants = results.get("variants", {})
        name_a = variants.get("a", {}).get("name", "对照组")
        name_b = variants.get("b", {}).get("name", "实验组")
        rate_a = variants.get("a", {}).get("rate", 0)
        rate_b = variants.get("b", {}).get("rate", 0)

        if not is_significant:
            # 统计不显著：判断是功率不足还是确实无差异
            if effect_size < 0.1:
                return (
                    f"📊 推荐：维持 {name_a}（对照组）\n\n"
                    f"分析结果：p={p_value:.4f}，效果量={effect_size:.3f}\n"
                    f"{name_b} 相比 {name_a} 无统计显著差异，且效果量极小。\n"
                    f"建议：实验到此为止。差异过小，即使增加样本量也难以达到商业上有意义的水平。\n"
                    f"当前 {name_a} 转化率：{rate_a:.4f}，{name_b} 转化率：{rate_b:.4f}"
                )
            else:
                return (
                    f"⏳ 暂不推荐 — 需要更多数据\n\n"
                    f"分析结果：p={p_value:.4f}（未达统计显著），效果量={effect_size:.3f}\n"
                    f"{name_b} 相比 {name_a} 有 {lift_pct:+.2f}% 的相对差异，"
                    f"但当前样本量不足以得出统计结论。\n"
                    f"建议：继续实验，或在业务影响大的情况下增加实验流量。\n"
                    f"置信区间：[{ci['lower']:.4f}, {ci['upper']:.4f}]"
                )

        # 统计显著
        if lift_pct > 0:
            # 实验组胜出
            if effect_size >= 0.5:
                return (
                    f"✅ 强烈推荐：采用 {name_b}（实验组）\n\n"
                    f"分析结果：p={p_value:.6f}，效果量={effect_size:.3f}（效果显著）\n"
                    f"{name_b} 相比 {name_a} 提升 {lift_pct:+.2f}%\n"
                    f"（转化率：{rate_a:.4f} → {rate_b:.4f}）\n"
                    f"统计显著 ✅ | 业务影响大 ✅ | 推荐执行全量切换"
                )
            else:
                return (
                    f"✅ 推荐：采用 {name_b}（实验组）\n\n"
                    f"分析结果：p={p_value:.6f}，效果量={effect_size:.3f}\n"
                    f"{name_b} 相比 {name_a} 提升 {lift_pct:+.2f}%\n"
                    f"（转化率：{rate_a:.4f} → {rate_b:.4f}）\n"
                    f"效果量中等偏小，建议结合实施成本和长期效果综合评估后再做全量切换。"
                )
        else:
            # 对照组更优（反向显著）
            return (
                f"🔄 推荐：维持 {name_a}（对照组）\n\n"
                f"分析结果：p={p_value:.6f}，效果量={effect_size:.3f}\n"
                f"实验组 {name_b} 反而比对照组 {name_a} 低 {abs(lift_pct):.2f}%\n"
                f"（转化率：{rate_a:.4f} → {rate_b:.4f}）\n"
                f"统计显著但方向为负。验证实验组是否存在实现缺陷，或设计假设本身有误。"
            )

    # ── 内部统计方法 ─────────────────────────────────────────

    def _power_analysis(
        self,
        sample_size: int,
        effect_size_abs: float,
        baseline_rate: float,
    ) -> dict[str, Any]:
        """统计功效分析。"""
        if sample_size == float("inf") or sample_size <= 0:
            return {
                "power_80pct": False,
                "note": "样本量不足或效果量为0，无法计算功效",
                "achievable_effect_sizes": {},
            }

        # 对不同效果量计算可达功效
        achievable = {}
        for label, cohen_d in _EFFECT_SIZE_THRESHOLDS.items():
            # 简化计算：用Z检验功效公式
            adjusted_effect = effect_size_abs * (cohen_d / 0.5) if cohen_d > 0 else 0
            # 估算z值
            se_approx = math.sqrt(baseline_rate * (1 - baseline_rate) * 2 / sample_size)
            if se_approx > 0:
                z_power = adjusted_effect / se_approx - 1.28  # 减去Z_beta=0.8对应的值
                power = min(0.99, max(0.05, 0.5 + z_power * 0.15))
                achievable[label] = round(power, 3)
            else:
                achievable[label] = 0.5

        # 当前效果量的功效
        current_power = achievable.get("medium", 0)

        return {
            "current_effect_power": round(current_power, 3),
            "power_80pct_reached": current_power >= 0.80,
            "achievable_effect_sizes": achievable,
            "note": "功效 ≥ 0.80 表明有足够把握检测到该效果量",
        }

    def _cohens_h(self, p1: float, p2: float) -> float:
        """Cohen's h 效果量。"""
        def arcsin_transform(p: float) -> float:
            return 2 * math.asin(math.sqrt(max(0, min(1, p))))
        return abs(arcsin_transform(p2) - arcsin_transform(p1))

    def _z_to_p_value(self, z: float) -> float:
        """近似计算双尾z检验的p值。"""
        # 标准正态CDF近似
        if z > 6:
            return 0.0
        if z < 0:
            z = -z
        # Abramowitz and Stegun 近似
        b0 = 0.2316419
        b1 = 0.319381530
        b2 = -0.356563782
        b3 = 1.781477937
        b4 = -1.821255978
        b5 = 1.330274429

        t = 1.0 / (1.0 + b0 * z)
        phi = 0.39894228 * math.exp(-z * z / 2.0)
        cdf = 1.0 - phi * (b1 * t + b2 * t**2 + b3 * t**3 + b4 * t**4 + b5 * t**5)

        # 双尾p值
        p = 2.0 * (1.0 - cdf)
        return max(0.0, min(1.0, p))

    def _chi2_to_p_value(self, chi2: float, df: int = 1) -> float:
        """卡方分布p值近似。"""
        if chi2 <= 0:
            return 1.0
        # 对于df=1，直接用正态近似
        if df == 1:
            z = math.sqrt(chi2)
            return self._z_to_p_value(z)
        # 一般情况：用简单近似
        x = chi2 / df
        p = math.exp(-x / 2) * (x ** (df / 2 - 1))
        return min(1.0, max(0.0, p))

    def _classify_effect_size(self, relative_lift: float) -> str:
        """分类效果量大小。"""
        if relative_lift >= 0.5:
            return "large"
        elif relative_lift >= 0.25:
            return "medium"
        elif relative_lift >= 0.05:
            return "small"
        else:
            return "negligible"

    def _classify_effect_size_label(self, effect_size: float) -> str:
        """用Cohen's d标准标记效果量。"""
        if effect_size >= 0.8:
            return "大效果量 (Large)"
        elif effect_size >= 0.5:
            return "中效果量 (Medium)"
        elif effect_size >= 0.2:
            return "小效果量 (Small)"
        else:
            return "极小效果量 (Negligible)"

    def _evaluate_business_significance(
        self,
        lift_pct: float,
        effect_size: float,
        is_significant: bool,
    ) -> dict[str, Any]:
        """评估业务显著性。"""
        if not is_significant:
            return {
                "is_business_significant": False,
                "reason": "统计不显著，无法评估业务影响",
            }

        # 不同提升幅度的业务影响分级
        if lift_pct >= 20:
            impact = "重大提升"
            level = "high"
        elif lift_pct >= 10:
            impact = "显著提升"
            level = "medium"
        elif lift_pct >= 5:
            impact = "小幅提升"
            level = "low"
        elif lift_pct > 0:
            impact = "微小提升"
            level = "negligible"
        else:
            impact = "负向变化"
            level = "negative"

        return {
            "is_business_significant": level in ("high", "medium"),
            "impact_level": level,
            "impact_description": impact,
            "relative_lift_pct": round(lift_pct, 2),
            "effect_size": round(effect_size, 3),
        }

    def _generate_design_notes(
        self,
        effect_size_abs: float,
        relative_improvement: float,
        duration: int,
        sample_size: int,
        traffic_level: str,
    ) -> list[str]:
        """生成实验设计建议。"""
        notes = []

        if sample_size == float("inf"):
            notes.append("预期效果量为0，实验没有意义（两组预期无差异）")
            return notes

        if sample_size < 100:
            notes.append("⚠️ 所需样本量极小，请确认预期提升率输入是否正确")
        elif sample_size > 1000000:
            notes.append(f"⚠️ 所需样本量较大（{sample_size:,}），建议延长实验周期或增加流量")

        if duration > 30:
            notes.append(f"推荐实验时长 {duration} 天，建议至少覆盖2个完整自然周以降低周期性偏差")
        elif duration > 14:
            notes.append(f"推荐实验时长 {duration} 天，建议覆盖完整的周一到周日周期")
        else:
            notes.append(f"推荐实验时长 {duration} 天（含周末覆盖）")

        notes.append(f"预期相对提升：{relative_improvement*100:.1f}%")
        notes.append("分流建议：按用户ID哈希取模，保证同一用户始终看到同一版本")
        notes.append("建议设置AA测试验证分流均匀性（分流后监控两组基线的差异）")

        if traffic_level == "low":
            notes.append("低流量场景：考虑降低置信度要求至90%以缩短实验周期")
        elif traffic_level == "high":
            notes.append("高流量场景：可考虑多臂实验（同时测试多个变体）")

        return notes

    def _generate_interpretation(
        self,
        is_significant: bool,
        p_value: float,
        test_stat: float,
        effect_size: float,
        lift_pct: float,
        confidence: float,
        test_name: str,
    ) -> list[str]:
        """生成统计结果解读。"""
        lines = []
        sig_level = int(confidence * 100)

        if is_significant:
            lines.append(
                f"在 {sig_level}% 置信水平下，观察到统计显著差异 "
                f"({test_name}, 统计量={test_stat:.3f}, p={p_value:.6f})"
            )
            lines.append(
                f"实验组相对对照组的变化为 {lift_pct:+.2f}%，"
                f"效果量={effect_size:.3f}（{self._classify_effect_size_label(effect_size)}）"
            )
            if lift_pct > 0:
                lines.append("数据支持实验组优于对照组的结论。建议结合业务成本与收益评估是否全量上线。")
            else:
                lines.append("数据支持对照组优于实验组的结论。建议检查实验组设计是否存在缺陷。")
        else:
            lines.append(
                f"在 {sig_level}% 置信水平下，未观察到统计显著差异 "
                f"({test_name}, 统计量={test_stat:.3f}, p={p_value:.4f})"
            )
            lines.append(
                f"实验组相对对照组变化为 {lift_pct:+.2f}%，"
                f"效果量={effect_size:.3f}（{self._classify_effect_size_label(effect_size)}）"
            )
            if effect_size < 0.1:
                lines.append("效果量极小，即使增加样本量也不太可能达到商业上有意义的差异。可以结束实验。")
            else:
                lines.append(f"存在一定效果量，但未达统计显著。考虑增加样本量或延长实验周期。")

        return lines
