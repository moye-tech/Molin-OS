#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.expanduser("/home/ubuntu/hermes-os"))
from molib.shared.analysis import DataCollector, DataProcessor
print("ok: import")

dc = DataCollector(storage_path="/tmp/test_hermes_data")
dp = DataProcessor()
print("ok: init")

col = dc.create_collector("test", {"site": "xiaoHongShu"})
print("ok: create_collector", col['id'])

t = dc.add_target("https://x.com/a", "content_feed")
print("ok: add_target", t['target_id'])

r = dc.run(parallelism=2)
print("ok: run", r['succeeded'], r['items_collected'], r['skipped_dedup'])

d = dc.get_data(col['id'])
print("ok: get_data", len(d), "items")

s = dc.stats()
print("ok: stats", s['total_collectors'], s['total_items_collected'])

raw = [{"a": "1", "b": None}, {"a": "1", "b": None}]
cl = dp.clean(raw)
print("ok: clean", len(raw), "->", len(cl), "dedup", dp._clean_stats['dedup_removed'])

schema = {"va": {"source": "a", "transform": "int"}}
tr = dp.transform(cl, schema)
print("ok: transform", len(tr), "items")

ag = dp.aggregate([{"g":"x","v":10},{"g":"x","v":20}],"g",{"sv":{"field":"v","op":"sum"}})
print("ok: aggregate", ag['totals']['group_count'], "groups")

ex = dp.export(cl, "json")
print("ok: export json", len(ex), "chars")

import shutil; shutil.rmtree("/tmp/test_hermes_data", ignore_errors=True)
print("ALL TESTS PASSED")
