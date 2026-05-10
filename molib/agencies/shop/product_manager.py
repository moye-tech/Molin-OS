"""墨链电商 — 商品管理系统

Product CRUD, inventory tracking, low-stock alerts.
Storage: JSON at ~/.molin/shop/products.json
Stdlib-only, zero external dependencies.
"""

from __future__ import annotations

import json
import os
import shutil
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ── Data Model ───────────────────────────────────────────────────────


@dataclass
class Product:
    id: str
    name: str
    description: str = ""
    price: float = 0.0
    images: list[str] = field(default_factory=list)
    category: str = ""
    status: str = "draft"  # draft, active, sold, archived
    stock: int = 0
    low_stock_threshold: int = 5
    platform: str = ""  # e.g., 闲鱼, 淘宝, 拼多多
    platform_listing_id: str = ""
    created_at: float = 0.0
    updated_at: float = 0.0

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]
        if not self.created_at:
            self.created_at = time.time()
        if not self.updated_at:
            self.updated_at = self.created_at

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "images": self.images,
            "category": self.category,
            "status": self.status,
            "stock": self.stock,
            "low_stock_threshold": self.low_stock_threshold,
            "platform": self.platform,
            "platform_listing_id": self.platform_listing_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Product:
        return cls(
            id=d.get("id", ""),
            name=d.get("name", ""),
            description=d.get("description", ""),
            price=d.get("price", 0.0),
            images=d.get("images", []),
            category=d.get("category", ""),
            status=d.get("status", "draft"),
            stock=d.get("stock", 0),
            low_stock_threshold=d.get("low_stock_threshold", 5),
            platform=d.get("platform", ""),
            platform_listing_id=d.get("platform_listing_id", ""),
            created_at=d.get("created_at", 0.0),
            updated_at=d.get("updated_at", 0.0),
        )

    @property
    def is_low_stock(self) -> bool:
        return self.stock <= self.low_stock_threshold and self.status == "active"

    @property
    def summary(self) -> str:
        return (
            f"[{self.id}] {self.name} | ¥{self.price:.0f} | "
            f"库存:{self.stock} | {self.status} | {self.category}"
        )


# ── Storage Layer ─────────────────────────────────────────────────────


class ProductStore:
    """JSON-file-backed product storage."""

    def __init__(self, storage_dir: str = ""):
        if storage_dir:
            self._dir = Path(storage_dir)
        else:
            self._dir = Path.home() / ".molin" / "shop"
        self._dir.mkdir(parents=True, exist_ok=True)
        self._file = self._dir / "products.json"
        self._backup_dir = self._dir / "backups"
        self._backup_dir.mkdir(parents=True, exist_ok=True)

    def _load(self) -> dict[str, dict]:
        if not self._file.exists():
            return {}
        try:
            return json.loads(self._file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def _save(self, data: dict[str, dict]) -> None:
        # atomic write via temp file
        tmp = self._file.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        tmp.replace(self._file)

    def _backup(self) -> None:
        if not self._file.exists():
            return
        stamp = time.strftime("%Y%m%d_%H%M%S")
        backup_path = self._backup_dir / f"products_{stamp}.json"
        shutil.copy2(self._file, backup_path)
        # keep only last 10 backups
        backups = sorted(self._backup_dir.glob("products_*.json"))
        for old in backups[:-10]:
            old.unlink(missing_ok=True)


# ── Product Manager ───────────────────────────────────────────────────


class ProductManager:
    """Full CRUD for products with inventory tracking and low-stock alerts."""

    def __init__(self, storage_dir: str = ""):
        self._store = ProductStore(storage_dir)

    # ── CRUD ──────────────────────────────────────────────────────

    def create(self, product: Product) -> Product:
        data = self._store._load()
        if product.id in data:
            raise ValueError(f"Product {product.id} already exists")
        data[product.id] = product.to_dict()
        self._store._backup()
        self._store._save(data)
        return product

    def get(self, product_id: str) -> Optional[Product]:
        data = self._store._load()
        d = data.get(product_id)
        return Product.from_dict(d) if d else None

    def update(self, product_id: str, **kwargs) -> Optional[Product]:
        data = self._store._load()
        d = data.get(product_id)
        if not d:
            return None
        allowed = {
            "name", "description", "price", "images", "category",
            "status", "stock", "low_stock_threshold", "platform",
            "platform_listing_id",
        }
        for k, v in kwargs.items():
            if k in allowed:
                d[k] = v
        d["updated_at"] = time.time()
        data[product_id] = d
        self._store._backup()
        self._store._save(data)
        return Product.from_dict(d)

    def delete(self, product_id: str) -> bool:
        data = self._store._load()
        if product_id not in data:
            return False
        self._store._backup()
        del data[product_id]
        self._store._save(data)
        return True

    def list_all(self, status: str = "") -> list[Product]:
        data = self._store._load()
        products = [Product.from_dict(d) for d in data.values()]
        if status:
            products = [p for p in products if p.status == status]
        products.sort(key=lambda p: p.updated_at, reverse=True)
        return products

    def search(self, query: str) -> list[Product]:
        q = query.lower()
        data = self._store._load()
        results = []
        for d in data.values():
            p = Product.from_dict(d)
            if (
                q in p.name.lower()
                or q in p.description.lower()
                or q in p.category.lower()
                or q in p.id
            ):
                results.append(p)
        results.sort(key=lambda p: p.updated_at, reverse=True)
        return results

    # ── Inventory ─────────────────────────────────────────────────

    def adjust_stock(self, product_id: str, delta: int) -> Optional[Product]:
        """Add or remove stock. Returns updated product or None."""
        p = self.get(product_id)
        if not p:
            return None
        new_stock = max(0, p.stock + delta)
        return self.update(product_id, stock=new_stock)

    def check_low_stock(self) -> list[Product]:
        """Return all active products with stock <= threshold."""
        return [p for p in self.list_all("active") if p.is_low_stock]

    def get_inventory_report(self) -> dict:
        products = self.list_all()
        total_products = len(products)
        active = [p for p in products if p.status == "active"]
        low = [p for p in active if p.is_low_stock]
        out = [p for p in active if p.stock == 0]
        total_value = sum(p.price * p.stock for p in active)
        return {
            "total_products": total_products,
            "active_products": len(active),
            "low_stock_items": len(low),
            "out_of_stock_items": len(out),
            "total_inventory_value": round(total_value, 2),
            "low_stock_details": [p.summary for p in low],
            "out_of_stock_details": [p.summary for p in out],
            "reported_at": time.time(),
        }

    def count(self) -> int:
        return len(self._store._load())


# ── Quick CLI helpers ─────────────────────────────────────────────────


def _parse_args(args: list[str]) -> dict:
    """Simple --key value parser."""
    opts = {}
    i = 0
    while i < len(args):
        if args[i].startswith("--"):
            key = args[i][2:]
            if i + 1 < len(args) and not args[i + 1].startswith("--"):
                opts[key] = args[i + 1]
                i += 2
            else:
                opts[key] = True
                i += 1
        else:
            i += 1
    return opts


def cmd_product(args: list[str]) -> dict:
    """CLI handler for product commands."""
    if not args:
        return {"error": "子命令: add | list | search | update | delete | inventory | low-stock"}

    subcmd = args[0]
    rest = args[1:]
    opts = _parse_args(rest)
    pm = ProductManager()

    if subcmd == "add":
        name = opts.get("name", "")
        if not name:
            return {"error": "--name is required"}
        p = Product(
            name=name,
            description=opts.get("description", ""),
            price=float(opts.get("price", 0)),
            category=opts.get("category", ""),
            stock=int(opts.get("stock", 0)),
            status=opts.get("status", "active"),
            platform=opts.get("platform", "闲鱼"),
            images=[u.strip() for u in opts.get("images", "").split(",") if u.strip()],
        )
        pm.create(p)
        return {"status": "created", "product": p.to_dict()}

    elif subcmd == "list":
        status = opts.get("status", "")
        products = pm.list_all(status)
        return {
            "count": len(products),
            "products": [p.to_dict() for p in products],
            "summaries": [p.summary for p in products],
        }

    elif subcmd == "search":
        query = opts.get("query", rest[0] if rest else "")
        if not query:
            return {"error": "--query is required"}
        results = pm.search(query)
        return {"query": query, "count": len(results), "results": [p.to_dict() for p in results]}

    elif subcmd == "update":
        pid = opts.get("id", rest[0] if rest else "")
        if not pid:
            return {"error": "--id is required"}
        update_opts = {k: v for k, v in opts.items() if k != "id"}
        if "price" in update_opts:
            update_opts["price"] = float(update_opts["price"])
        if "stock" in update_opts:
            update_opts["stock"] = int(update_opts["stock"])
        updated = pm.update(pid, **update_opts)
        if not updated:
            return {"error": f"Product {pid} not found"}
        return {"status": "updated", "product": updated.to_dict()}

    elif subcmd == "delete":
        pid = opts.get("id", rest[0] if rest else "")
        if not pid:
            return {"error": "--id is required"}
        ok = pm.delete(pid)
        return {"status": "deleted" if ok else "not_found", "id": pid}

    elif subcmd == "inventory":
        return pm.get_inventory_report()

    elif subcmd == "low-stock":
        low = pm.check_low_stock()
        return {"count": len(low), "items": [p.to_dict() for p in low]}

    return {"error": f"未知子命令: {subcmd}"}
