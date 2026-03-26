from __future__ import annotations

import json
import time
import re
from collections import deque
from typing import Optional, Tuple, List, Dict
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from Product import Product, load_products, save_products

JSON_PATH = "data.json"
HISTORY_LEN = 30
REQUEST_TIMEOUT = 15
RETRY_COUNT = 2
RETRY_DELAY_S = 1.0
ROW_DELAY_S = 0.4

# These are checked if no custom selector is provided
TRENDYOL_SELECTORS = [
    "span.prc-dsc",   # discounted/current price (most common)
    "span.prc-slg",   # current price when there is no discount
    "span.prc-org",   # original crossed-out price (fallback only)
]

COMMON_PRICE_SELECTORS = [
    "span.price",
    "span.current-price",
    "[data-test='price']",
    ".price .amount",
    "meta[itemprop='price']",
]

def parse_price(text: str) -> Optional[float]:
    if not text:
        return None
    # Remove everything except digits, comma, and dot
    cleaned = re.sub(r"[^\d.,]", "", text)
    if not cleaned:
        return None
        
    # Handle different decimal/thousands separators
    # If both , and . are present
    if "," in cleaned and "." in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            # 1.234,56 -> 1234.56
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            # 1,234.56 -> 1234.56
            cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        # 1234,56 -> 1234.56
        cleaned = cleaned.replace(",", ".")
    
    try:
        return float(cleaned)
    except ValueError:
        return None

def _get_element_text(el) -> Optional[str]:
    if not el:
        return None
    if getattr(el, "get", None) and el.get("content"):
        return el["content"].strip()
    return el.get_text(strip=True)

def fetch_price(session: requests.Session, url: str, selector: Optional[str] = None) -> Tuple[Optional[str], Optional[float]]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }

    for attempt in range(RETRY_COUNT + 1):
        try:
            resp = session.get(url, timeout=REQUEST_TIMEOUT, headers=headers, allow_redirects=True)
            resp.raise_for_status()

            if len(resp.text) < 2000 and attempt < RETRY_COUNT:
                time.sleep(RETRY_DELAY_S)
                continue

            soup = BeautifulSoup(resp.text, "lxml")

            # 1) User-provided selector wins
            if selector:
                try:
                    el = soup.select_one(selector)
                    raw = _get_element_text(el)
                    if raw:
                        price = parse_price(raw)
                        if price is not None:
                            return raw, price
                except Exception:
                    pass

            # 2) Domain-aware selectors
            domain = urlparse(url).netloc
            site_selectors = TRENDYOL_SELECTORS if "trendyol.com" in domain else []
            for sel in site_selectors:
                el = soup.select_one(sel)
                raw = _get_element_text(el)
                if raw:
                    price = parse_price(raw)
                    if price is not None:
                        return raw, price

            # 3) JSON-LD fallback
            for script in soup.find_all("script", {"type": "application/ld+json"}):
                try:
                    data = json.loads(script.string or "")
                except (json.JSONDecodeError, TypeError):
                    continue
                
                blocks = data if isinstance(data, list) else [data]
                for obj in blocks:
                    offers = obj.get("offers")
                    if not offers:
                        continue
                    
                    offer_list = offers if isinstance(offers, list) else [offers]
                    for off in offer_list:
                        if isinstance(off, dict):
                            price_val = off.get("price")
                            if price_val:
                                price = parse_price(str(price_val))
                                if price is not None:
                                    return str(price_val), price

            # 4) Generic fallbacks
            for sel in COMMON_PRICE_SELECTORS:
                el = soup.select_one(sel)
                raw = _get_element_text(el)
                if raw:
                    price = parse_price(raw)
                    if price is not None:
                        return raw, price

            return None, None

        except Exception:
            if attempt < RETRY_COUNT:
                time.sleep(RETRY_DELAY_S)
            else:
                return None, None

    return None, None

def update_all_products(path: str = JSON_PATH, callback=None) -> None:
    """
    Updates all products from the JSON file.
    :param path: Path to data.json
    :param callback: Optional function to call after each product update (for progress reporting)
    """
    products = load_products(path)
    if not products:
        return

    with requests.Session() as session:
        total = len(products)
        for i, p in enumerate(products):
            url = p.url.strip()
            if not url:
                if callback: callback(i + 1, total, p.name, None)
                continue

            raw, numeric = fetch_price(session, url, p.selector)
            if numeric is not None:
                p.data.enqueue(numeric)
            
            if callback:
                callback(i + 1, total, p.name, numeric)

            if ROW_DELAY_S and i < total - 1:
                time.sleep(ROW_DELAY_S)

    save_products(products, path)

if __name__ == "__main__":
    def console_callback(current, total, name, price):
        status = f"{price}" if price is not None else "failed"
        print(f"[{current}/{total}] {name}: {status}")

    print("Updating prices...")
    update_all_products(JSON_PATH, callback=console_callback)
    print("Done.")

