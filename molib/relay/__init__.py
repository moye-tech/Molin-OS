"""墨麟OS — 接力数据包（relay协议实现）

子公司间数据接力标准实现。
每个 cron 作业执行后写入接力文件，下游 cron 读取。

使用方式（在 cron prompt 中通过 script 调用）：
    python3 -m molib.relay write --origin 墨思 --summary "今日趋势..."
    python3 -m molib.relay read intelligence --days-ago 0
"""

from .relay_core import (
    RelayWriter,
    RelayReader,
    RELAY_DIR,
    write_relay,
    read_relay,
    list_todays_relays,
    list_recent_relays,
)
