"""墨麟OS — 子公司Worker注册表"""
from .base import SubsidiaryWorker, WorkerRegistry, Task, WorkerResult

from .content_writer import ContentWriter
from .ip_manager import IpManager
from .designer import Designer
from .short_video import ShortVideo
from .voice_actor import VoiceActor
from .crm import TwentyClient, segment_users, build_touch_sequence, get_twenty_status
from .customer_service import CustomerService
from .ecommerce import Ecommerce
from .education import Education
from .developer import Developer
from .ops import Ops
from .security import Security
from .auto_dream import AutoDream
from .finance import Finance
from .bd import Bd
from .global_marketing import GlobalMarketing
from .research import Research
from .legal import Legal
from .knowledge import Knowledge
from .data_analyst import DataAnalyst
from .cocoindex_sync import CocoIndexSync
from .trading import Trading
from .scrapling_worker import ScraplingWorker

def register_all():
    WorkerRegistry.register(ContentWriter)
    WorkerRegistry.register(IpManager)
    WorkerRegistry.register(Designer)
    WorkerRegistry.register(ShortVideo)
    WorkerRegistry.register(VoiceActor)
    # Crm: Twenty API模式（非Worker子类）
    WorkerRegistry.register(CustomerService)
    WorkerRegistry.register(Ecommerce)
    WorkerRegistry.register(Education)
    WorkerRegistry.register(Developer)
    WorkerRegistry.register(Ops)
    WorkerRegistry.register(Security)
    WorkerRegistry.register(AutoDream)
    WorkerRegistry.register(Finance)
    WorkerRegistry.register(Bd)
    WorkerRegistry.register(GlobalMarketing)
    WorkerRegistry.register(Research)
    WorkerRegistry.register(Legal)
    WorkerRegistry.register(Knowledge)
    WorkerRegistry.register(DataAnalyst)
    WorkerRegistry.register(CocoIndexSync)
    WorkerRegistry.register(Trading)
    WorkerRegistry.register(ScraplingWorker)

def get_worker(name: str) -> SubsidiaryWorker | None:
    cls = WorkerRegistry.get(name)
    if cls:
        return cls()
    for wid, wcls in WorkerRegistry._workers.items():
        if name in wid or name in wcls.worker_name:
            return wcls()
    return None

def list_workers() -> list[dict]:
    return [
        {"id": wid, "name": wcls.worker_name, "desc": wcls.description, "line": getattr(wcls, "oneliner", "")}
        for wid, wcls in WorkerRegistry._workers.items()
    ]
