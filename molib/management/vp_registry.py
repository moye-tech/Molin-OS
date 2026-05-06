"""
墨域OS — VP注册表
====================
暴露 get_all_vps() 返回所有5位VP实例。

用法:
    from molib.management.vp_registry import get_all_vps

    vps = get_all_vps()
    for vp in vps:
        print(vp.name, vp.subsidiaries)
"""

from molib.management.vp_agents import (
    VPMarketing,
    VPOps,
    VPTech,
    VPFinance,
    VPStrategy,
    ManagerAgent,
)

# 全局缓存（单例模式）
_vp_instances: dict[str, ManagerAgent] = {}


def get_all_vps() -> list[ManagerAgent]:
    """返回所有5位VP实例（懒加载 + 缓存）"""
    if not _vp_instances:
        _vp_instances["marketing"] = VPMarketing()
        _vp_instances["ops"] = VPOps()
        _vp_instances["tech"] = VPTech()
        _vp_instances["finance"] = VPFinance()
        _vp_instances["strategy"] = VPStrategy()
    return list(_vp_instances.values())


def get_vp(name: str) -> ManagerAgent:
    """按名称获取单个VP实例（支持中文/英文名）"""
    mapping = {
        "vp营销": "marketing",
        "vp运营": "ops",
        "vp技术": "tech",
        "vp财务": "finance",
        "vp战略": "strategy",
        "marketing": "marketing",
        "ops": "ops",
        "tech": "tech",
        "finance": "finance",
        "strategy": "strategy",
    }
    key = mapping.get(name.lower())
    if key is None:
        raise ValueError(f"Unknown VP: {name!r}")
    # 触发初始化
    get_all_vps()
    return _vp_instances[key]


def reset():
    """重置缓存（测试用）"""
    _vp_instances.clear()
