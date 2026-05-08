"""
molib.feishu_ext — 飞书扩展模块
Bitable数据同步 + 云空间文件管理 + 官方审批API
"""
from molib.feishu_ext.bitable_sync import sync_task_execution, build_dashboard_summary_card
from molib.feishu_ext.drive_manager import FeishuDriveManager, archive_execution_results
from molib.feishu_ext.official_approval import (
    create_approval_instance, get_approval_status,
    approve_instance, reject_instance, push_official_approval,
)

__all__ = [
    "sync_task_execution", "build_dashboard_summary_card",
    "FeishuDriveManager", "archive_execution_results",
    "create_approval_instance", "get_approval_status",
    "approve_instance", "reject_instance", "push_official_approval",
]
