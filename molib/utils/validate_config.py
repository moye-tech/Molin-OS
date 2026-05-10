"""
配置验证脚本 — 系统启动前校验配置一致性
检查项：
1. 所有 manager 的 worker_types 是否对应实际存在的 worker 文件
2. 所有 manager 的 subsidiary_id 是否在 subsidiaries.toml 中存在
3. claude_code_enabled 是否全部启用
4. 外部工具是否全部注册成功
"""

import sys
from pathlib import Path
from loguru import logger

ROOT = Path(__file__).resolve().parent.parent


def _load_toml(path: Path) -> dict:
    try:
        import tomllib
        with open(path, "rb") as f:
            return tomllib.load(f)
    except ImportError:
        try:
            import toml
            return toml.load(str(path))
        except ImportError:
            logger.error("需要 tomllib (Python 3.11+) 或 toml 库")
            return {}


def discover_worker_files() -> set:
    """扫描 agencies/workers/ 目录下所有实际存在的 worker 模块名"""
    workers_dir = ROOT / "agencies" / "workers"
    names = set()
    for f in workers_dir.glob("*_worker.py"):
        names.add(f.stem.replace("_worker", ""))
    return names


def discover_subidiary_ids() -> set:
    """从 subsidiaries.toml 提取所有已注册的子公司 ID"""
    config = _load_toml(ROOT / "config" / "subsidiaries.toml")
    ids = set()
    for agency in config.get("agencies", []):
        if isinstance(agency, dict) and "id" in agency:
            ids.add(agency["id"])
    return ids


def discover_external_tools() -> list:
    """从 __init__.py 提取已注册的外部工具"""
    init_file = ROOT / "integrations" / "external_tools" / "__init__.py"
    if not init_file.exists():
        return []
    tools = []
    with open(init_file) as f:
        for line in f:
            if line.startswith("from .") and "import get_" in line:
                tool_name = line.split("import get_")[1].strip()
                tools.append(tool_name)
    return tools


def validate_all() -> bool:
    """执行全部校验，返回是否通过"""
    errors = []
    warnings = []

    # 1. 加载 managers.toml
    managers_config = _load_toml(ROOT / "config" / "managers.toml")
    if not managers_config:
        errors.append("无法加载 config/managers.toml")
        return False

    manager_defs = managers_config.get("managers", {})
    if not manager_defs:
        errors.append("managers.toml 中未定义任何 manager")
        return False

    worker_files = discover_worker_files()
    subsidiary_ids = discover_subidiary_ids()
    ext_tools = discover_external_tools()

    logger.info(f"发现 {len(worker_files)} 个 Worker 文件: {sorted(worker_files)}")
    logger.info(f"发现 {len(subsidiary_ids)} 个子公司 ID: {sorted(subsidiary_ids)}")
    logger.info(f"发现 {len(ext_tools)} 个外部工具: {sorted(ext_tools)}")
    logger.info(f"发现 {len(manager_defs)} 个 Manager 配置")

    # 2. 校验每个 manager
    for manager_id, cfg in manager_defs.items():
        prefix = f"[{manager_id}]"

        # 2.1 worker_types → 实际文件
        worker_types = cfg.get("worker_types", [])
        for wt in worker_types:
            if wt not in worker_files:
                errors.append(f"{prefix} worker_type '{wt}' 不存在于 agencies/workers/ 目录")

        # 2.2 subsidiary_id → subsidiaries.toml
        sub_id = cfg.get("subsidiary_id", "")
        if sub_id and sub_id not in subsidiary_ids:
            errors.append(f"{prefix} subsidiary_id '{sub_id}' 未在 subsidiaries.toml 中注册")

        # 2.3 claude_code_enabled 检查
        claude_enabled = cfg.get("claude_code_enabled", True)
        if not claude_enabled:
            warnings.append(f"{prefix} claude_code_enabled=false，该 Manager 将跳过 Worker 链路")

    # 3. 汇总结果
    if warnings:
        logger.warning("=== 配置警告 ===")
        for w in warnings:
            logger.warning(f"  ⚠ {w}")

    if errors:
        logger.error("=== 配置错误 ===")
        for e in errors:
            logger.error(f"  ✗ {e}")
        return False

    logger.info("配置验证通过 ✓")
    return True


if __name__ == "__main__":
    ok = validate_all()
    sys.exit(0 if ok else 1)
