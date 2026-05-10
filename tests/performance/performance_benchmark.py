#!/usr/bin/env python3
"""
性能基准测试
验证系统响应时间和并发处理能力
"""

import sys
import os
import time
import asyncio
import statistics
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PerformanceBenchmark:
    """性能基准测试类"""

    def __init__(self):
        self.results = {}
        self.test_data = self._prepare_test_data()

    def _prepare_test_data(self) -> Dict[str, Any]:
        """准备测试数据"""
        return {
            'ceo_decision_requests': [
                {
                    'user_id': f'user_{i:03d}',
                    'query': f'测试决策请求 {i}',
                    'budget': 1000 + i * 100,
                    'timeline': f'{i+1}个月',
                    'target_revenue': 5000 + i * 500,
                    'industry': '科技' if i % 3 == 0 else '教育' if i % 3 == 1 else '电商'
                }
                for i in range(50)  # 准备50个测试请求
            ],
            'memory_operations': [
                {
                    'context': {'scenario': 'transactional', 'user_id': f'test_user_{i}'},
                    'data': {'message': f'测试消息 {i}', 'index': i, 'timestamp': time.time()},
                    'metadata': {'test': True, 'iteration': i}
                }
                for i in range(100)  # 准备100个内存操作
            ]
        }

    async def benchmark_ceo_decision_response_time(self, num_requests: int = 10) -> Dict[str, Any]:
        """基准测试CEO决策响应时间"""
        logger.info(f"基准测试CEO决策响应时间 ({num_requests}个请求)...")

        try:
            from hermes_fusion.skills.ceo_decision.skill import CeoDecisionSkill

            skill = CeoDecisionSkill()
            response_times = []

            # 使用前N个请求
            requests = self.test_data['ceo_decision_requests'][:num_requests]

            for i, request_data in enumerate(requests):
                start_time = time.time()

                try:
                    # 创建测试上下文
                    context = {
                        'user_id': request_data['user_id'],
                        'query': request_data['query'],
                        'budget': request_data['budget'],
                        'timeline': request_data['timeline'],
                        'target_revenue': request_data['target_revenue'],
                        'industry': request_data['industry'],
                        'platform': 'performance_test',
                        'timestamp': datetime.now().isoformat()
                    }

                    # 开始执行
                    if skill.start_execution():
                        try:
                            # 执行决策
                            result = skill.execute(context)
                            response_times.append(time.time() - start_time)

                            logger.debug(f"请求 {i+1}/{num_requests}: {result.get('decision', 'unknown')}, "
                                        f"响应时间: {response_times[-1]:.3f}s")
                        finally:
                            skill.finish_execution(success=True)
                    else:
                        logger.warning(f"请求 {i+1} 无法开始执行（并发限制）")
                        response_times.append(None)

                except Exception as e:
                    logger.error(f"请求 {i+1} 执行异常: {e}")
                    response_times.append(None)

            # 过滤掉None值
            valid_times = [t for t in response_times if t is not None]

            if not valid_times:
                logger.error("没有有效的响应时间数据")
                return {'success': False, 'error': '没有有效的响应时间数据'}

            # 计算统计信息
            stats = {
                'total_requests': num_requests,
                'successful_requests': len(valid_times),
                'failed_requests': num_requests - len(valid_times),
                'min_time': min(valid_times),
                'max_time': max(valid_times),
                'avg_time': statistics.mean(valid_times),
                'median_time': statistics.median(valid_times),
                'std_dev': statistics.stdev(valid_times) if len(valid_times) > 1 else 0,
                'p95_time': statistics.quantiles(valid_times, n=20)[18] if len(valid_times) >= 20 else valid_times[-1],
                'throughput': len(valid_times) / sum(valid_times) if sum(valid_times) > 0 else 0
            }

            logger.info(f"CEO决策响应时间统计:")
            logger.info(f"  成功请求: {stats['successful_requests']}/{stats['total_requests']}")
            logger.info(f"  最小: {stats['min_time']:.3f}s, 最大: {stats['max_time']:.3f}s, 平均: {stats['avg_time']:.3f}s")
            logger.info(f"  中位数: {stats['median_time']:.3f}s, 标准差: {stats['std_dev']:.3f}s")
            logger.info(f"  P95: {stats['p95_time']:.3f}s, 吞吐量: {stats['throughput']:.2f} 请求/秒")

            return {'success': True, 'stats': stats, 'response_times': valid_times}

        except Exception as e:
            logger.error(f"CEO决策响应时间基准测试异常: {e}")
            return {'success': False, 'error': str(e)}

    async def benchmark_concurrent_ceo_decisions(self, concurrency_levels: List[int] = None) -> Dict[str, Any]:
        """基准测试并发CEO决策处理能力"""
        if concurrency_levels is None:
            concurrency_levels = [1, 3, 5, 10]

        logger.info(f"基准测试并发CEO决策处理能力 (并发级别: {concurrency_levels})...")

        try:
            from hermes_fusion.skills.ceo_decision.skill import CeoDecisionSkill

            results = {}

            for concurrency in concurrency_levels:
                logger.info(f"测试并发级别 {concurrency}...")

                # 准备并发请求
                requests = self.test_data['ceo_decision_requests'][:concurrency * 5]  # 每个级别5倍请求
                total_requests = len(requests)

                # 创建技能实例池
                skills = [CeoDecisionSkill() for _ in range(concurrency)]

                start_time = time.time()
                successful_requests = 0
                failed_requests = 0
                response_times = []

                # 使用线程池模拟并发请求
                with ThreadPoolExecutor(max_workers=concurrency) as executor:
                    futures = []
                    for i, request_data in enumerate(requests):
                        skill_idx = i % concurrency
                        future = executor.submit(
                            self._execute_ceo_decision_sync,
                            skills[skill_idx],
                            request_data,
                            i
                        )
                        futures.append(future)

                    # 收集结果
                    for i, future in enumerate(futures):
                        try:
                            result, exec_time = future.result(timeout=30)  # 30秒超时
                            if result.get('success', False):
                                successful_requests += 1
                                response_times.append(exec_time)
                            else:
                                failed_requests += 1
                                logger.debug(f"请求 {i} 失败: {result.get('error', 'unknown')}")
                        except Exception as e:
                            failed_requests += 1
                            logger.warning(f"请求 {i} 执行异常: {e}")

                total_time = time.time() - start_time

                if not response_times:
                    logger.warning(f"并发级别 {concurrency}: 没有成功的请求")
                    continue

                # 计算统计信息
                stats = {
                    'concurrency_level': concurrency,
                    'total_requests': total_requests,
                    'successful_requests': successful_requests,
                    'failed_requests': failed_requests,
                    'total_time': total_time,
                    'avg_response_time': statistics.mean(response_times) if response_times else 0,
                    'throughput': successful_requests / total_time if total_time > 0 else 0,
                    'error_rate': failed_requests / total_requests if total_requests > 0 else 0
                }

                results[concurrency] = stats

                logger.info(f"并发级别 {concurrency} 结果:")
                logger.info(f"  总请求: {stats['total_requests']}, 成功: {stats['successful_requests']}, "
                           f"失败: {stats['failed_requests']}")
                logger.info(f"  总时间: {stats['total_time']:.2f}s, 平均响应: {stats['avg_response_time']:.3f}s")
                logger.info(f"  吞吐量: {stats['throughput']:.2f} 请求/秒, 错误率: {stats['error_rate']:.2%}")

            return {'success': True, 'results': results}

        except Exception as e:
            logger.error(f"并发CEO决策基准测试异常: {e}")
            return {'success': False, 'error': str(e)}

    def _execute_ceo_decision_sync(self, skill, request_data: Dict[str, Any], request_id: int) -> Tuple[Dict[str, Any], float]:
        """同步执行CEO决策（用于线程池）"""
        try:
            start_time = time.time()

            context = {
                'user_id': request_data['user_id'],
                'query': request_data['query'],
                'budget': request_data['budget'],
                'timeline': request_data['timeline'],
                'target_revenue': request_data['target_revenue'],
                'industry': request_data['industry'],
                'platform': 'concurrency_test',
                'timestamp': datetime.now().isoformat()
            }

            # 开始执行
            if skill.start_execution():
                try:
                    result = skill.execute(context)
                    exec_time = time.time() - start_time
                    return {'success': True, 'decision': result.get('decision')}, exec_time
                finally:
                    skill.finish_execution(success=True)
            else:
                exec_time = time.time() - start_time
                return {'success': False, 'error': '无法开始执行（并发限制）'}, exec_time

        except Exception as e:
            exec_time = time.time() - start_time
            return {'success': False, 'error': str(e)}, exec_time

    async def benchmark_memory_provider_operations(self, num_operations: int = 50) -> Dict[str, Any]:
        """基准测试内存提供者操作性能"""
        logger.info(f"基准测试内存提供者操作性能 ({num_operations}个操作)...")

        try:
            from hermes_fusion.providers.memory_provider import HierarchicalMemoryProvider

            memory_provider = HierarchicalMemoryProvider()
            await memory_provider.initialize()

            operations = self.test_data['memory_operations'][:num_operations]
            store_times = []
            retrieve_times = []
            successful_operations = 0

            for i, operation in enumerate(operations):
                # 测试存储性能
                store_start = time.time()
                try:
                    record_id = await memory_provider.store(
                        context=operation['context'],
                        data=operation['data'],
                        metadata=operation['metadata']
                    )
                    store_time = time.time() - store_start
                    store_times.append(store_time)

                    # 测试检索性能
                    retrieve_start = time.time()
                    results = await memory_provider.retrieve(
                        context=operation['context'],
                        query=record_id,
                        limit=1
                    )
                    retrieve_time = time.time() - retrieve_start
                    retrieve_times.append(retrieve_time)

                    if results:
                        successful_operations += 1

                    if i % 10 == 0:  # 每10个操作记录一次
                        logger.debug(f"内存操作 {i+1}/{num_operations}: "
                                    f"存储 {store_time:.3f}s, 检索 {retrieve_time:.3f}s")

                except Exception as e:
                    logger.warning(f"内存操作 {i+1} 失败: {e}")

            if not store_times or not retrieve_times:
                logger.error("没有成功的内存操作数据")
                return {'success': False, 'error': '没有成功的内存操作数据'}

            # 计算统计信息
            store_stats = {
                'count': len(store_times),
                'min': min(store_times),
                'max': max(store_times),
                'avg': statistics.mean(store_times),
                'median': statistics.median(store_times),
                'p95': statistics.quantiles(store_times, n=20)[18] if len(store_times) >= 20 else store_times[-1]
            }

            retrieve_stats = {
                'count': len(retrieve_times),
                'min': min(retrieve_times),
                'max': max(retrieve_times),
                'avg': statistics.mean(retrieve_times),
                'median': statistics.median(retrieve_times),
                'p95': statistics.quantiles(retrieve_times, n=20)[18] if len(retrieve_times) >= 20 else retrieve_times[-1]
            }

            logger.info(f"内存提供者性能统计:")
            logger.info(f"  成功操作: {successful_operations}/{num_operations}")
            logger.info(f"  存储: 平均 {store_stats['avg']:.3f}s, P95 {store_stats['p95']:.3f}s")
            logger.info(f"  检索: 平均 {retrieve_stats['avg']:.3f}s, P95 {retrieve_stats['p95']:.3f}s")

            return {
                'success': True,
                'successful_operations': successful_operations,
                'total_operations': num_operations,
                'store_stats': store_stats,
                'retrieve_stats': retrieve_stats
            }

        except Exception as e:
            logger.error(f"内存提供者基准测试异常: {e}")
            return {'success': False, 'error': str(e)}

    async def benchmark_system_load(self, duration_seconds: int = 30) -> Dict[str, Any]:
        """基准测试系统负载能力"""
        logger.info(f"基准测试系统负载能力 ({duration_seconds}秒)...")

        try:
            import psutil
            import threading

            # 监控系统资源
            cpu_percentages = []
            memory_usages = []
            io_counters = []

            stop_monitoring = threading.Event()

            def monitor_resources():
                """监控系统资源使用情况"""
                while not stop_monitoring.is_set():
                    cpu_percentages.append(psutil.cpu_percent(interval=0.1))
                    memory_usages.append(psutil.virtual_memory().percent)

                    # 获取IO统计（如果有）
                    try:
                        io = psutil.disk_io_counters()
                        io_counters.append({
                            'read_bytes': io.read_bytes,
                            'write_bytes': io.write_bytes
                        })
                    except:
                        pass

            # 启动监控线程
            monitor_thread = threading.Thread(target=monitor_resources)
            monitor_thread.start()

            # 在监控期间执行一些负载
            start_time = time.time()
            operations_completed = 0

            from hermes_fusion.skills.ceo_decision.skill import CeoDecisionSkill
            skill = CeoDecisionSkill()

            while time.time() - start_time < duration_seconds:
                try:
                    # 执行简单的决策操作
                    if skill.start_execution():
                        try:
                            context = {
                                'user_id': f'load_test_user_{operations_completed}',
                                'query': f'负载测试请求 {operations_completed}',
                                'budget': 1000,
                                'timeline': '1个月',
                                'target_revenue': 5000,
                                'platform': 'load_test',
                                'timestamp': datetime.now().isoformat()
                            }
                            skill.execute(context)
                            operations_completed += 1
                        finally:
                            skill.finish_execution(success=True)
                except Exception as e:
                    logger.debug(f"负载测试操作异常: {e}")

                # 短暂延迟
                await asyncio.sleep(0.01)

            # 停止监控
            stop_monitoring.set()
            monitor_thread.join()

            # 计算统计信息
            if cpu_percentages:
                cpu_avg = statistics.mean(cpu_percentages)
                cpu_max = max(cpu_percentages)
            else:
                cpu_avg = cpu_max = 0

            if memory_usages:
                memory_avg = statistics.mean(memory_usages)
                memory_max = max(memory_usages)
            else:
                memory_avg = memory_max = 0

            ops_per_second = operations_completed / duration_seconds if duration_seconds > 0 else 0

            stats = {
                'duration_seconds': duration_seconds,
                'operations_completed': operations_completed,
                'ops_per_second': ops_per_second,
                'cpu_avg_percent': cpu_avg,
                'cpu_max_percent': cpu_max,
                'memory_avg_percent': memory_avg,
                'memory_max_percent': memory_max
            }

            logger.info(f"系统负载测试结果:")
            logger.info(f"  持续时间: {duration_seconds}秒, 完成操作: {operations_completed}")
            logger.info(f"  操作/秒: {ops_per_second:.2f}")
            logger.info(f"  CPU: 平均 {cpu_avg:.1f}%, 最大 {cpu_max:.1f}%")
            logger.info(f"  内存: 平均 {memory_avg:.1f}%, 最大 {memory_max:.1f}%")

            return {'success': True, 'stats': stats}

        except ImportError:
            logger.warning("psutil未安装，跳过系统负载测试")
            return {'success': False, 'error': 'psutil未安装'}
        except Exception as e:
            logger.error(f"系统负载基准测试异常: {e}")
            return {'success': False, 'error': str(e)}

    async def run_all_benchmarks(self) -> Dict[str, Any]:
        """运行所有基准测试"""
        logger.info("=" * 60)
        logger.info("开始性能基准测试")
        logger.info("=" * 60)

        benchmarks = [
            ("CEO决策响应时间", lambda: self.benchmark_ceo_decision_response_time(20)),
            ("并发CEO决策处理", lambda: self.benchmark_concurrent_ceo_decisions([1, 3, 5])),
            ("内存提供者操作性能", lambda: self.benchmark_memory_provider_operations(30)),
            ("系统负载能力", lambda: self.benchmark_system_load(15))
        ]

        results = {}
        for benchmark_name, benchmark_func in benchmarks:
            logger.info(f"\n--- 开始基准测试: {benchmark_name} ---")
            try:
                result = await benchmark_func()
                results[benchmark_name] = result

                if result.get('success', False):
                    logger.info(f"基准测试 {benchmark_name}: ✓ 成功")
                else:
                    logger.warning(f"基准测试 {benchmark_name}: ✗ 失败 - {result.get('error', '未知错误')}")
            except Exception as e:
                logger.error(f"基准测试 {benchmark_name} 异常: {e}")
                results[benchmark_name] = {'success': False, 'error': str(e)}

        # 汇总结果
        logger.info("\n" + "=" * 60)
        logger.info("性能基准测试结果汇总")
        logger.info("=" * 60)

        passed = 0
        total = len(results)

        for benchmark_name, result in results.items():
            status = "✓ 通过" if result.get('success', False) else "✗ 失败"
            logger.info(f"  {benchmark_name}: {status}")

            if result.get('success', False):
                passed += 1

        success_rate = (passed / total * 100) if total > 0 else 0
        logger.info(f"\n总计: {passed}/{total} 通过 ({success_rate:.1f}%)")

        # 生成详细报告
        report = {
            'test_date': datetime.now().isoformat(),
            'total_benchmarks': total,
            'passed_benchmarks': passed,
            'failed_benchmarks': total - passed,
            'success_rate': success_rate,
            'results': results,
            'summary': self._generate_summary(results)
        }

        if passed == total:
            logger.info("🎉 所有基准测试通过！系统性能符合预期。")
        else:
            logger.warning(f"⚠️  {total - passed} 个基准测试失败，需要性能优化。")

        return report

    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """生成性能摘要"""
        summary = {}

        # CEO决策响应时间
        ceo_result = results.get('CEO决策响应时间', {})
        if ceo_result.get('success', False):
            stats = ceo_result.get('stats', {})
            summary['ceo_response_time'] = {
                'avg_ms': stats.get('avg_time', 0) * 1000,
                'p95_ms': stats.get('p95_time', 0) * 1000,
                'throughput_per_second': stats.get('throughput', 0)
            }

        # 并发处理
        concurrent_result = results.get('并发CEO决策处理', {})
        if concurrent_result.get('success', False):
            concurrent_results = concurrent_result.get('results', {})
            if concurrent_results:
                # 获取最高并发级别的结果
                max_concurrency = max(concurrent_results.keys())
                max_stats = concurrent_results[max_concurrency]
                summary['concurrent_processing'] = {
                    'max_concurrency_tested': max_concurrency,
                    'throughput_at_max': max_stats.get('throughput', 0),
                    'error_rate_at_max': max_stats.get('error_rate', 0)
                }

        # 内存操作性能
        memory_result = results.get('内存提供者操作性能', {})
        if memory_result.get('success', False):
            store_stats = memory_result.get('store_stats', {})
            retrieve_stats = memory_result.get('retrieve_stats', {})
            summary['memory_operations'] = {
                'store_avg_ms': store_stats.get('avg', 0) * 1000,
                'retrieve_avg_ms': retrieve_stats.get('avg', 0) * 1000
            }

        # 系统负载
        system_result = results.get('系统负载能力', {})
        if system_result.get('success', False):
            system_stats = system_result.get('stats', {})
            summary['system_load'] = {
                'ops_per_second': system_stats.get('ops_per_second', 0),
                'cpu_avg_percent': system_stats.get('cpu_avg_percent', 0),
                'memory_avg_percent': system_stats.get('memory_avg_percent', 0)
            }

        return summary


async def main():
    """主函数：运行性能基准测试"""
    benchmark = PerformanceBenchmark()
    report = await benchmark.run_all_benchmarks()

    # 保存测试报告
    report_file = "performance_benchmark_report.json"
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        logger.info(f"性能基准测试报告已保存到: {report_file}")
    except Exception as e:
        logger.error(f"保存性能基准测试报告失败: {e}")

    # 检查是否满足性能要求
    performance_requirements_met = check_performance_requirements(report)

    if performance_requirements_met:
        logger.info("✅ 系统性能满足要求")
        return 0
    else:
        logger.warning("⚠️ 系统性能未完全满足要求，需要优化")
        return 1


def check_performance_requirements(report: Dict[str, Any]) -> bool:
    """检查性能是否满足要求"""
    requirements = {
        'ceo_response_time_max_ms': 2000,  # CEO决策响应时间 < 2秒
        'memory_operation_max_ms': 1000,   # 内存操作 < 1秒
        'concurrent_throughput_min': 1.0,  # 并发吞吐量 > 1请求/秒
        'system_cpu_max_percent': 80.0     # 系统CPU使用率 < 80%
    }

    summary = report.get('summary', {})
    all_requirements_met = True

    # 检查CEO决策响应时间
    ceo_response = summary.get('ceo_response_time', {})
    if ceo_response:
        avg_ms = ceo_response.get('avg_ms', float('inf'))
        if avg_ms > requirements['ceo_response_time_max_ms']:
            logger.warning(f"CEO决策响应时间 ({avg_ms:.0f}ms) 超过限制 ({requirements['ceo_response_time_max_ms']}ms)")
            all_requirements_met = False
        else:
            logger.info(f"✅ CEO决策响应时间: {avg_ms:.0f}ms (< {requirements['ceo_response_time_max_ms']}ms)")
    else:
        logger.warning("CEO决策响应时间数据缺失")

    # 检查内存操作性能
    memory_ops = summary.get('memory_operations', {})
    if memory_ops:
        store_ms = memory_ops.get('store_avg_ms', float('inf'))
        retrieve_ms = memory_ops.get('retrieve_avg_ms', float('inf'))

        if store_ms > requirements['memory_operation_max_ms']:
            logger.warning(f"内存存储时间 ({store_ms:.0f}ms) 超过限制 ({requirements['memory_operation_max_ms']}ms)")
            all_requirements_met = False
        else:
            logger.info(f"✅ 内存存储时间: {store_ms:.0f}ms (< {requirements['memory_operation_max_ms']}ms)")

        if retrieve_ms > requirements['memory_operation_max_ms']:
            logger.warning(f"内存检索时间 ({retrieve_ms:.0f}ms) 超过限制 ({requirements['memory_operation_max_ms']}ms)")
            all_requirements_met = False
        else:
            logger.info(f"✅ 内存检索时间: {retrieve_ms:.0f}ms (< {requirements['memory_operation_max_ms']}ms)")
    else:
        logger.warning("内存操作性能数据缺失")

    # 检查并发吞吐量
    concurrent = summary.get('concurrent_processing', {})
    if concurrent:
        throughput = concurrent.get('throughput_at_max', 0)
        if throughput < requirements['concurrent_throughput_min']:
            logger.warning(f"并发吞吐量 ({throughput:.2f} 请求/秒) 低于要求 ({requirements['concurrent_throughput_min']} 请求/秒)")
            all_requirements_met = False
        else:
            logger.info(f"✅ 并发吞吐量: {throughput:.2f} 请求/秒 (> {requirements['concurrent_throughput_min']} 请求/秒)")
    else:
        logger.warning("并发处理性能数据缺失")

    # 检查系统CPU使用率
    system_load = summary.get('system_load', {})
    if system_load:
        cpu_avg = system_load.get('cpu_avg_percent', 0)
        if cpu_avg > requirements['system_cpu_max_percent']:
            logger.warning(f"系统CPU使用率 ({cpu_avg:.1f}%) 超过限制 ({requirements['system_cpu_max_percent']}%)")
            all_requirements_met = False
        else:
            logger.info(f"✅ 系统CPU使用率: {cpu_avg:.1f}% (< {requirements['system_cpu_max_percent']}%)")
    else:
        logger.warning("系统负载数据缺失")

    return all_requirements_met


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)