# Product.py
import json
from typing import List, Any, Optional
from Queue import CircularQueue

def _coerce_float(x: Any) -> Optional[float]:
    try:
        if x is None:
            return None
        return float(x)
    except (TypeError, ValueError):
        return None

class Product:
    def __init__(self, name: str, url: str, data: Optional[CircularQueue] = None, selector: Optional[str] = None):
        self.name = name
        self.url = url
        self.selector = selector
        self.data = data or CircularQueue(30)

    # ------- getters used by GUI -------
    def get_name(self): return self.name
    def get_url(self): return self.url

    def get_current(self):
        v = self.data.get_last()
        return v if v is not None else ""

    def get_change(self):
        # same convention as your queue: int(100 - curr*100/prev)
        return self.data.find_daily_diff()

    def get_max_change(self):
        return self.data.find_max_diff()

    # ------- JSON (de)serialization -------
    def to_dict(self) -> dict:
        # serialize only primitive fields; values oldest -> newest
        values = []
        # we assume your CircularQueue exposes .size, .count, .front, .queue (as in your file)
        for i in range(self.data.count):
            idx = (self.data.front + i) % self.data.size
            values.append(self.data.queue[idx])
        return {
            "name": self.name,
            "url": self.url,
            "selector": self.selector,
            "values": values,  # <- canonical field
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Product":
        name = d.get("name", "")
        url = d.get("url", "")
        selector = d.get("selector")

        # Accept new format: "values": [..]  OR legacy: "data": [..] / {"values":[..]} / etc.
        raw_values = None

        if "values" in d:
            raw_values = d.get("values")
        elif "data" in d:
            # Try a few legacy shapes
            data_field = d.get("data")
            if isinstance(data_field, list):
                raw_values = data_field
            elif isinstance(data_field, dict):
                # sometimes people stored {"values": [...]}
                raw_values = data_field.get("values")
            else:
                raw_values = None

        q = CircularQueue(30)
        if isinstance(raw_values, list):
            for x in raw_values:
                fx = _coerce_float(x)
                if fx is not None:
                    q.enqueue(fx)

        return cls(name=name, url=url, data=q, selector=selector)

# ------- file helpers (used by GUI) -------
def save_products(products: List[Product], path: str = "data.json"):
    # Do nothing if products is None (prevents wiping accidentally)
    if products is None:
        return
    data = [p.to_dict() for p in products]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_products(path: str = "data.json") -> List[Product]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            return []
        return [Product.from_dict(item) for item in data if isinstance(item, dict)]
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        # Corrupt file -> don't crash GUI
        return []
