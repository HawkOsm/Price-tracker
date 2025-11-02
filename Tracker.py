from __future__ import annotations

import json
import time
import re
from collections import deque
from typing import Optional, Tuple, List, Dict

import requests
from bs4 import BeautifulSoup

JSON_PATH = "data.json"
HISTORY_LEN = 30
REQUEST_TIMEOUT = 15
RETRY_COUNT = 2
RETRY_DELAY_S = 1.0
ROW_DELAY_S = 0.4

COMMON_PRICE_SELECTORS = [
    "span.prc-dsc",
    "span.prc-slg",
    "span.prc-org",

    "span.price",
    "span.current-price",
    "[data-test='price']",
    ".price .amount",
    "meta[itemprop='price']",
]

def load_products(path: str = JSON_PATH) -> List[Dict]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("data.json root must be a list")
        # normalize minimal fields
        out = []
        for item in data:
            if not isinstance(item, dict):
                continue
            out.append({
                "name": item.get("name") or "",
                "url": item.get("url") or "",
                "selector": item.get("selector") or None,
                "values": item.get("values") or [],  # oldest -> newest
            })
        return out
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        print("ERROR: data.json is not valid JSON.")
        return []

def save_products(products: List[Dict], path: str = JSON_PATH) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

import json
import re
import time
from urllib.parse import urlparse
from bs4 import BeautifulSoup

REQUEST_TIMEOUT = 15
RETRY_COUNT = 2
RETRY_DELAY_S = 1.0

COMMON_PRICE_SELECTORS = [
    "span.price",
    "span.current-price",
    "[data-test='price']",
    ".price .amount",
    "meta[itemprop='price']",
]

TRENDYOL_SELECTORS = [
    "span.prc-dsc",   # discounted/current price (most common)
    "span.prc-slg",   # current price when there is no discount
    "span.prc-org",   # original crossed-out price (fallback only)
]

def parse_price(text: str):
    if not text:
        return None
    cleaned = re.sub(r"[^\d.,\-+]", "", text)
    if "," in cleaned and "." in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            cleaned = cleaned.replace(".", "")
            cleaned = cleaned.replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    else:
        if "," in cleaned and "." not in cleaned:
            cleaned = cleaned.replace(".", "")
            cleaned = cleaned.replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    try:
        return float(cleaned)
    except ValueError:
        return None

def _first_text_or_content(el):
    if not el:
        return None
    if getattr(el, "get", None) and el.get("content"):
        return el["content"].strip()
    return el.get_text(strip=True)

def fetch_price(session, url, selector=None):
    headers = {
        # desktop UA is fine, but language matters a lot on Turkish sites
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }

    last_exc = None
    for _ in range(RETRY_COUNT + 1):
        try:
            resp = session.get(url, timeout=REQUEST_TIMEOUT, headers=headers, allow_redirects=True)
            resp.raise_for_status()

            # Sometimes you get a consent/captcha or empty SSR shell.
            # Quick guard: if body is suspiciously small, retry.
            if len(resp.text) < 2000 and _ < RETRY_COUNT:
                time.sleep(RETRY_DELAY_S)
                continue

            soup = BeautifulSoup(resp.text, "lxml")

            # 1) User-provided selector wins
            if selector:
                try:
                    el = soup.select_one(selector)
                    raw = _first_text_or_content(el)
                    if raw:
                        return raw, parse_price(raw)
                except Exception:
                    pass  # invalid CSS; continue

            # 2) Domain-aware selectors
            domain = urlparse(url).netloc
            site_selectors = TRENDYOL_SELECTORS if "trendyol.com" in domain else []
            for sel in site_selectors:
                el = soup.select_one(sel)
                raw = _first_text_or_content(el)
                if raw:
                    return raw, parse_price(raw)

            # 3) JSON-LD fallback (very reliable if present)
            # Look for application/ld+json blocks and check offers.price / offers[0].price
            for script in soup.find_all("script", {"type": "application/ld+json"}):
                try:
                    data = json.loads(script.string or "")
                except Exception:
                    continue
                # Normalize to list to handle single/multiple objects
                blocks = data if isinstance(data, list) else [data]
                for obj in blocks:
                    offers = obj.get("offers")
                    if not offers:
                        continue
                    # offers can be dict or list
                    if isinstance(offers, dict):
                        price = offers.get("price")
                        if price:
                            return str(price), parse_price(str(price))
                    elif isinstance(offers, list):
                        for off in offers:
                            price = isinstance(off, dict) and off.get("price")
                            if price:
                                return str(price), parse_price(str(price))

            # 4) Generic fallbacks
            for sel in COMMON_PRICE_SELECTORS:
                el = soup.select_one(sel)
                raw = _first_text_or_content(el)
                if raw:
                    return raw, parse_price(raw)

            # 5) Nothing found → return None with a small diagnostic hint
            # (Tip: if you hit this often, you likely need Playwright/puppeteer because the price is client-side.)
            return None, None

        except Exception as e:
            last_exc = e
            time.sleep(RETRY_DELAY_S)

    return None, None


def bounded_history(values: List[float]) -> deque:
    dq = deque(maxlen=HISTORY_LEN)
    for v in values:
        if isinstance(v, (int, float)):
            dq.append(float(v))
    return dq

def compute_stats(history: deque) -> Tuple[Optional[float], int, Optional[float]]:
    latest = history[-1] if history else None
    if len(history) >= 2 and history[-2]:
        prev = history[-2]
        curr = latest
        daily = int(100 - (curr * 100 / prev)) if curr is not None else 0
    else:
        daily = 0
    max_diff = (max(history) - min(history)) if len(history) >= 1 else None
    return latest, daily, max_diff

def update_all_products(path: str = JSON_PATH) -> None:
    products = load_products(path)
    if not products:
        print("No products in data.json")
        return

    with requests.Session() as session:
        summaries = []
        for p in products:
            url = p.get("url", "").strip()
            if not url:
                summaries.append((p.get("name") or url or "?", None, None, "no URL"))
                continue

            selector = (p.get("selector") or None)
            raw, numeric = fetch_price(session, url, selector)

            hist = bounded_history(p.get("values", []))
            if numeric is not None:
                hist.append(numeric)

            latest, daily_pct, max_diff = compute_stats(hist)
            p["values"] = list(hist)  # write back (oldest -> newest)

            summaries.append((p.get("name") or url, latest, daily_pct, max_diff))

            if ROW_DELAY_S:
                time.sleep(ROW_DELAY_S)

    save_products(products, path)

    # console summary
    print("\nUpdated:")
    for name, latest, daily, mdiff in summaries:
        print(f"- {name}: latest={latest}  daily%={daily}  max_diff={mdiff}")
    print("\nDone.")

if __name__ == "__main__":
    update_all_products(JSON_PATH)

