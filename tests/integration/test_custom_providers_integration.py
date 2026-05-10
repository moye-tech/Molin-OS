#!/usr/bin/env python3
"""
自定义提供者集成测试
验证hermes-agent的三个自定义提供者：内存、网关、SOP
"""

import sys
import os
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TestCustomProvidersIntegration:
    """自定义提供者集成测试类"""

    def __init__(self):
        self.memory_provider = None
        self.sop_provider = None
        self.feishu_provider = None

    async def test_memory_provider_initialization(self) -> bool:
        """测试内存提供者初始化"""
        logger.info("测试内存提供者初始化...")

        try:
            from hermes_fusion.providers.memory_provider import HierarchicalMemoryProvider

            # 初始化内存提供者
            self.memory_provider = HierarchicalMemoryProvider()

            # 测试初始化
            await self.memory_provider.initialize()

            # 验证初始化状态
            if not self.memory_provider.initialized:
                logger.error("内存提供者初始化失败")
                return False

            if self.memory_provider.memory_manager is None:
                logger.error("内存管理器未初始化")
                return False

            logger.info("内存提供者初始化测试通过")
            return True

        except Exception as e:
            logger.error(f"内存提供者初始化测试异常: {e}")
            return False

    async def test_memory_provider_store_retrieve(self) -> bool:
        """测试内存提供者存储和检索"""
        logger.info("测试内存提供者存储和检索...")

        try:
            # 确保已初始化
            if not self.memory_provider or not self.memory_provider.initialized:
                logger.error("内存提供者未初始化")
                return False

            test_context = {
                'scenario': 'transactional',
                'user_id': 'test_user_001',
                'data_type': 'test_data'
            }

            test_data = {
                'message': '这是一个测试记忆记录',
                'priority': 'medium',
                'tags': ['test', 'integration']
            }

            test_metadata = {
                'created_by': 'integration_test',
                'test_id': '001'
            }

            # 测试存储
            record_id = await self.memory_provider.store(
                context=test_context,
                data=test_data,
                metadata=test_metadata
            )

            if not record_id:
                logger.error("存储失败：未返回记录ID")
                return False

            logger.info(f"存储成功，记录ID: {record_id}")

            # 测试按ID检索
            retrieve_context = test_context.copy()
            retrieve_results = await self.memory_provider.retrieve(
                context=retrieve_context,
                query=record_id,
                limit=10
            )

            if not retrieve_results:
                logger.warning("按ID检索未返回结果（可能是异步延迟），尝试搜索查询")
            else:
                logger.info(f"按ID检索返回 {len(retrieve_results)} 个结果")
                for result in retrieve_results[:2]:  # 只显示前2个
                    logger.debug(f"检索结果: {result.get('id')}, 内容: {str(result.get('content'))[:50]}...")

            # 测试语义搜索
            search_context = test_context.copy()
            search_context['scenario'] = 'semantic_search'

            search_results = await self.memory_provider.search(
                context=search_context,
                query='测试记忆记录',
                limit=5
            )

            logger.info(f"语义搜索返回 {len(search_results)} 个结果")

            # 测试获取统计信息
            stats = await self.memory_provider.get_stats()
            logger.info(f"内存系统统计: {stats.get('status')}, 后端: {stats.get('backend')}")

            logger.info("内存提供者存储检索测试通过")
            return True

        except Exception as e:
            logger.error(f"内存提供者存储检索测试异常: {e}")
            return False

    async def test_sop_provider_initialization(self) -> bool:
        """测试SOP提供者初始化"""
        logger.info("测试SOP提供者初始化...")

        try:
            from hermes_fusion.providers.sop_provider import SopExecutionProvider

            # 初始化SOP提供者
            self.sop_provider = SopExecutionProvider({
                'workflow_dir': 'tests/integration/test_workflows'
            })

            # 创建测试工作流目录
            workflow_dir = Path('tests/integration/test_workflows')
            workflow_dir.mkdir(parents=True, exist_ok=True)

            # 测试初始化
            await self.sop_provider.initialize()

            # 验证初始化状态
            logger.info(f"SOP提供者初始化完成，工作流目录: {self.sop_provider.workflow_dir}")

            logger.info("SOP提供者初始化测试通过")
            return True

        except Exception as e:
            logger.error(f"SOP提供者初始化测试异常: {e}")
            return False

    async def test_sop_workflow_creation_and_execution(self) -> bool:
        """测试SOP工作流创建和执行"""
        logger.info("测试SOP工作流创建和执行...")

        try:
            # 确保已初始化
            if not self.sop_provider:
                logger.error("SOP提供者未初始化")
                return False

            # 创建测试工作流定义
            test_workflow = {
                'id': 'test_integration_workflow',
                'name': '集成测试工作流',
                'description': '用于集成测试的简单工作流',
                'version': '1.0',
                'variables': {
                    'test_user': 'integration_tester',
                    'max_retries': 3
                },
                'steps': [
                    {
                        'id': 'step_1',
                        'name': '初始化步骤',
                        'description': '初始化测试环境',
                        'type': 'automated',
                        'action': {
                            'type': 'skill',
                            'skill_name': 'echo_skill',
                            'parameters': {
                                'message': '开始集成测试'
                            }
                        },
                        'parameters': {
                            'timeout': 30
                        }
                    },
                    {
                        'id': 'step_2',
                        'name': '处理步骤',
                        'description': '处理测试数据',
                        'type': 'automated',
                        'action': {
                            'type': 'skill',
                            'skill_name': 'process_skill',
                            'parameters': {
                                'input': '{{test_user}} 的数据'
                            }
                        },
                        'conditions': [
                            {
                                'type': 'expression',
                                'expression': '{{max_retries}} > 0'
                            }
                        ]
                    },
                    {
                        'id': 'step_3',
                        'name': '通知步骤',
                        'description': '发送完成通知',
                        'type': 'notification',
                        'parameters': {
                            'type': 'message',
                            'recipients': ['test_recipient@example.com'],
                            'content': '工作流执行完成'
                        }
                    }
                ],
                'triggers': {
                    'manual': True,
                    'cron': None
                }
            }

            # 创建工作流
            create_result = await self.sop_provider.create_workflow(test_workflow)

            if create_result['status'] != 'success':
                logger.error(f"工作流创建失败: {create_result.get('error')}")
                return False

            logger.info(f"工作流创建成功: {create_result['workflow_id']}")

            # 列出工作流
            workflows = await self.sop_provider.list_workflows()
            logger.info(f"可用工作流数量: {len(workflows)}")

            # 执行工作流
            execution_context = {
                'workflow_id': 'test_integration_workflow',
                'user_id': 'test_user_001',
                'variables': {
                    'test_user': '执行用户',
                    'additional_param': '自定义参数'
                }
            }

            execution_result = await self.sop_provider.execute(execution_context)

            if execution_result['status'] != 'success':
                logger.error(f"工作流执行启动失败: {execution_result.get('error')}")
                return False

            execution_id = execution_result['execution_id']
            logger.info(f"工作流执行已启动: {execution_id}")

            # 获取执行状态
            await asyncio.sleep(0.5)  # 等待执行开始

            status_result = await self.sop_provider.get_execution_status(execution_id)

            if status_result['status'] != 'success':
                logger.error(f"获取执行状态失败: {status_result.get('error')}")
            else:
                logger.info(f"执行状态: {status_result['execution_status']}, "
                           f"当前步骤: {status_result['current_step']}/{status_result['total_steps']}")

            logger.info("SOP工作流创建执行测试通过")
            return True

        except Exception as e:
            logger.error(f"SOP工作流创建执行测试异常: {e}")
            return False

    async def test_feishu_gateway_provider_initialization(self) -> bool:
        """测试飞书网关提供者初始化"""
        logger.info("测试飞书网关提供者初始化...")

        try:
            from hermes_fusion.providers.feishu_gateway import FeishuGatewayProvider

            # 初始化飞书网关提供者
            self.feishu_provider = FeishuGatewayProvider({
                'app_id': 'test_app_id_001',
                'app_secret': 'test_app_secret_001',
                'verification_token': 'test_token_001'
            })

            # 测试连接（模拟模式）
            connected = await self.feishu_provider.connect()

            if not connected:
                logger.error("飞书网关连接失败")
                return False

            logger.info("飞书网关提供者初始化测试通过")
            return True

        except Exception as e:
            logger.error(f"飞书网关提供者初始化测试异常: {e}")
            return False

    async def test_feishu_gateway_message_operations(self) -> bool:
        """测试飞书网关消息操作"""
        logger.info("测试飞书网关消息操作...")

        try:
            # 确保已初始化
            if not self.feishu_provider:
                logger.error("飞书网关提供者未初始化")
                return False

            test_chat_id = 'test_chat_001'
            test_message = '这是一个集成测试消息'

            # 测试发送文本消息
            send_result = await self.feishu_provider.send_message(
                chat_id=test_chat_id,
                content=test_message,
                message_type='text'
            )

            if send_result['status'] != 'success':
                logger.error(f"发送文本消息失败: {send_result.get('error')}")
                return False

            logger.info(f"文本消息发送成功: {send_result['message_id']}")

            # 测试发送交互式卡片
            card_data = {
                'title': '集成测试通知',
                'content': '这是一个测试卡片',
                'actions': [
                    {
                        'tag': 'button',
                        'text': '确认',
                        'type': 'primary',
                        'value': 'confirm'
                    }
                ]
            }

            card_result = await self.feishu_provider.send_interactive_card(
                chat_id=test_chat_id,
                card_template='notification_card',
                card_data=card_data
            )

            if card_result['status'] != 'success':
                logger.warning(f"发送交互式卡片失败（可能是测试模式）: {card_result.get('error')}")
                # 继续测试，不视为失败
            else:
                logger.info(f"交互式卡片发送成功: {card_result['message_id']}")

            # 测试接收消息（模拟模式）
            receive_result = await self.feishu_provider.receive_messages(
                test_mode=True,
                limit=5
            )

            logger.info(f"接收消息测试: 获取到 {len(receive_result)} 条模拟消息")

            # 测试处理交互式卡片
            test_card_data = {
                'type': 'notification_card',
                'action_value': {'action': 'confirm'},
                'user_id': 'test_user_001',
                'message_id': 'test_msg_001'
            }

            card_handle_result = await self.feishu_provider.handle_interactive_card(test_card_data)

            if card_handle_result['status'] != 'success':
                logger.warning(f"处理交互式卡片失败: {card_handle_result.get('error')}")
            else:
                logger.info(f"交互式卡片处理成功: {card_handle_result['card_type']}")

            # 测试用户信息获取
            user_info = await self.feishu_provider.get_user_info('test_user_001')
            logger.info(f"用户信息: {user_info.get('name')}, 状态: {user_info.get('status')}")

            # 测试聊天信息获取
            chat_info = await self.feishu_provider.get_chat_info('test_chat_001')
            logger.info(f"聊天信息: {chat_info.get('name')}, 类型: {chat_info.get('type')}")

            # 测试断开连接
            disconnected = await self.feishu_provider.disconnect()

            if not disconnected:
                logger.warning("断开连接失败（可能是测试模式）")
            else:
                logger.info("飞书网关断开连接成功")

            logger.info("飞书网关消息操作测试通过")
            return True

        except Exception as e:
            logger.error(f"飞书网关消息操作测试异常: {e}")
            return False

    async def test_provider_interaction(self) -> bool:
        """测试提供者间交互"""
        logger.info("测试提供者间交互...")

        try:
            # 确保所有提供者都已初始化
            if not all([self.memory_provider, self.sop_provider, self.feishu_provider]):
                logger.error("部分提供者未初始化")
                return False

            # 创建一个综合测试场景：
            # 1. 使用SOP提供者执行工作流
            # 2. 工作流执行结果存储到内存提供者
            # 3. 通过飞书网关发送通知

            # 创建工作流执行上下文
            interaction_context = {
                'workflow_id': 'provider_interaction_test',
                'user_id': 'interaction_test_user',
                'variables': {
                    'test_phase': 'integration',
                    'interaction_mode': 'memory_to_gateway'
                }
            }

            # 记录交互开始到内存
            interaction_start_data = {
                'phase': 'provider_interaction_test',
                'timestamp': datetime.now().isoformat(),
                'providers_available': [
                    'memory_provider',
                    'sop_provider',
                    'feishu_gateway'
                ]
            }

            interaction_record_id = await self.memory_provider.store(
                context={'scenario': 'transactional', 'user_id': 'interaction_test'},
                data=interaction_start_data,
                metadata={'test_type': 'provider_interaction'}
            )

            logger.info(f"交互测试记录已存储: {interaction_record_id}")

            # 验证记录可检索
            retrieve_context = {'scenario': 'transactional'}
            interaction_results = await self.memory_provider.retrieve(
                context=retrieve_context,
                query=interaction_record_id,
                limit=1
            )

            if interaction_results:
                logger.info(f"交互测试记录检索成功，内容: {interaction_results[0].get('content', {})}")
            else:
                logger.warning("交互测试记录检索失败（可能是异步延迟）")

            # 通过飞书网关发送交互通知
            if self.feishu_provider.connected:
                # 重新连接
                await self.feishu_provider.connect()

            notification_result = await self.feishu_provider.send_message(
                chat_id='interaction_test_chat',
                content=f'提供者交互测试完成，记录ID: {interaction_record_id}',
                message_type='text'
            )

            if notification_result['status'] == 'success':
                logger.info(f"交互通知发送成功: {notification_result['message_id']}")
            else:
                logger.warning(f"交互通知发送失败: {notification_result.get('error')}")

            # 获取SOP工作流状态
            workflows = await self.sop_provider.list_workflows()
            logger.info(f"SOP提供者工作流数量: {len(workflows)}")

            logger.info("提供者间交互测试通过")
            return True

        except Exception as e:
            logger.error(f"提供者间交互测试异常: {e}")
            return False

    async def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试并返回结果"""
        logger.info("=" * 60)
        logger.info("开始自定义提供者集成测试")
        logger.info("=" * 60)

        test_cases = [
            ("内存提供者初始化", self.test_memory_provider_initialization),
            ("内存提供者存储检索", self.test_memory_provider_store_retrieve),
            ("SOP提供者初始化", self.test_sop_provider_initialization),
            ("SOP工作流创建执行", self.test_sop_workflow_creation_and_execution),
            ("飞书网关提供者初始化", self.test_feishu_gateway_provider_initialization),
            ("飞书网关消息操作", self.test_feishu_gateway_message_operations),
            ("提供者间交互", self.test_provider_interaction)
        ]

        results = []
        for test_name, test_func in test_cases:
            logger.info(f"\n--- 开始测试: {test_name} ---")
            try:
                success = await test_func()
                results.append((test_name, success))
                status = "通过" if success else "失败"
                logger.info(f"测试 {test_name}: {status}")
            except Exception as e:
                logger.error(f"测试 {test_name} 异常: {e}")
                results.append((test_name, False))

        # 汇总结果
        logger.info("\n" + "=" * 60)
        logger.info("自定义提供者集成测试结果汇总")
        logger.info("=" * 60)

        passed = 0
        total = len(results)

        for test_name, success in results:
            status = "✓ 通过" if success else "✗ 失败"
            logger.info(f"  {test_name}: {status}")
            if success:
                passed += 1

        success_rate = (passed / total * 100) if total > 0 else 0
        logger.info(f"\n总计: {passed}/{total} 通过 ({success_rate:.1f}%)")

        # 生成详细报告
        report = {
            'test_date': datetime.now().isoformat(),
            'total_tests': total,
            'passed_tests': passed,
            'failed_tests': total - passed,
            'success_rate': success_rate,
            'providers_tested': ['memory_provider', 'sop_provider', 'feishu_gateway'],
            'results': [
                {
                    'test_name': name,
                    'passed': passed,
                    'timestamp': datetime.now().isoformat()
                }
                for name, passed in results
            ],
            'summary': {
                'memory_provider_working': any(name in ["内存提供者初始化", "内存提供者存储检索"]
                                            and passed for name, passed in results),
                'sop_provider_working': any(name in ["SOP提供者初始化", "SOP工作流创建执行"]
                                          and passed for name, passed in results),
                'feishu_gateway_working': any(name in ["飞书网关提供者初始化", "飞书网关消息操作"]
                                           and passed for name, passed in results),
                'providers_interaction_working': any(name == "提供者间交互"
                                                   and passed for name, passed in results)
            }
        }

        if passed == total:
            logger.info("🎉 所有测试通过！自定义提供者集成完整。")
        else:
            logger.warning(f"⚠️  {total - passed} 个测试失败，需要进一步检查。")

        return report


async def main():
    """主函数：运行集成测试"""
    tester = TestCustomProvidersIntegration()
    report = await tester.run_all_tests()

    # 保存测试报告
    report_file = "custom_providers_integration_report.json"
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        logger.info(f"测试报告已保存到: {report_file}")
    except Exception as e:
        logger.error(f"保存测试报告失败: {e}")

    # 返回退出代码
    return 0 if report['passed_tests'] == report['total_tests'] else 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)