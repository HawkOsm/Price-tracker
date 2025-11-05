# pytest tests for your change-detection utilities

import math
import types

# ---- copy/import the functions you want to test ----
# If these live in on_open.py, change the imports accordingly:
# from on_open import find_changed_products, _effective_threshold_for

# Paste minimal copies here for isolated testing if you prefer:
def _effective_threshold_for(p, default_threshold: float = 10.0) -> float:
    candidates = []
    for attr in ("on_change", "on_max_change"):
        if hasattr(p, attr):
            v = getattr(p, attr)
            if isinstance(v, (int, float)) and v >= 0:
                candidates.append(float(v))
    return max(candidates) if candidates else float(default_threshold)

def find_changed_products(products, default_threshold: float = 10.0):
    changed = []
    for p in products:
        try:
            name = p.get_name()
            url = p.get_url()
            pct_change = p.get_change()
            if pct_change is None or pct_change == "":
                continue
            pct = abs(float(pct_change))
            threshold = _effective_threshold_for(p, default_threshold)
            if pct >= threshold:
                changed.append((name, url, pct, threshold))
        except Exception:
            continue
    return changed


# ---- a tiny stub Product for testing ----
class StubProduct:
    def __init__(self, name, url, change, on_change=None, on_max_change=None):
        self._name = name
        self._url = url
        self._change = change          # percent change number (can be str/float/None)
        self.on_change = on_change     # optional custom threshold
        self.on_max_change = on_max_change

    def get_name(self):
        return self._name

    def get_url(self):
        return self._url

    def get_change(self):
        return self._change


# ------------------- tests -------------------

def test_effective_threshold_default_when_none_set():
    p = StubProduct("A", "http://a", 5, on_change=None, on_max_change=None)
    assert _effective_threshold_for(p, default_threshold=12.5) == 12.5

def test_effective_threshold_uses_max_of_two():
    p = StubProduct("A", "http://a", 5, on_change=7.0, on_max_change=12.0)
    assert _effective_threshold_for(p, default_threshold=1.0) == 12.0

def test_effective_threshold_ignores_negative_or_non_numeric():
    p = StubProduct("A", "http://a", 5, on_change=-3, on_max_change="x")
    assert _effective_threshold_for(p, default_threshold=9.0) == 9.0

def test_find_changed_products_includes_item_when_change_meets_threshold():
    p = StubProduct("P1", "http://p1", 10.0, on_change=10.0)  # exactly meets
    results = find_changed_products([p], default_threshold=5.0)
    assert len(results) == 1
    name, url, pct, threshold = results[0]
    assert name == "P1"
    assert url == "http://p1"
    assert math.isclose(pct, 10.0)
    assert math.isclose(threshold, 10.0)  # picked per-product threshold

def test_find_changed_products_excludes_item_below_threshold():
    p = StubProduct("P2", "http://p2", 9.9, on_change=10.0)
    results = find_changed_products([p], default_threshold=1.0)
    assert results == []

def test_find_changed_products_uses_default_threshold_when_not_set():
    p = StubProduct("P3", "http://p3", 12.0)  # no per-product thresholds
    results = find_changed_products([p], default_threshold=10.0)
    assert len(results) == 1
    assert results[0][0] == "P3"

def test_find_changed_products_handles_missing_change_gracefully():
    p_none = StubProduct("None", "http://none", None, on_change=0)
    p_empty = StubProduct("Empty", "http://empty", "", on_change=0)
    results = find_changed_products([p_none, p_empty], default_threshold=0.0)
    assert results == []

def test_find_changed_products_abs_value_for_drop_and_rise():
    rising = StubProduct("Up", "http://up", +15.0, on_change=10.0)
    falling = StubProduct("Down", "http://down", -15.0, on_change=10.0)
    results = find_changed_products([rising, falling], default_threshold=0.0)
    names = {r[0] for r in results}
    assert names == {"Up", "Down"}
