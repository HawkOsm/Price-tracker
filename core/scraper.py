import asyncio
import re
import logging
from typing import Optional, Tuple, List
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from utils.helpers import setup_logger

logger = setup_logger(__name__)

# Constants
REQUEST_TIMEOUT = 20.0
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9,tr;q=0.8",
}

# Selectors from legacy Tracker.py
TRENDYOL_SELECTORS = [
    "span.prc-dsc",
    "span.prc-slg",
    "span.prc-org",
]

COMMON_PRICE_SELECTORS = [
    "span.price",
    "span.current-price",
    "[data-test='price']",
    ".price .amount",
    "meta[itemprop='price']",
]

def parse_price(text: str) -> Optional[float]:
    """
    Robust price parsing for various international formats.
    
    Examples:
    - 1,234.56 -> 1234.56
    - 1.234,56 -> 1234.56
    - 1 234,56 -> 1234.56
    - $12.34 -> 12.34
    """
    if not text:
        return None
        
    # Remove symbols like currency and spaces
    cleaned = re.sub(r"[^\d.,]", "", text)
    if not cleaned:
        return None
        
    # Handle cases with multiple commas/dots
    # If both , and . are present, assume the last one is the decimal separator
    if "," in cleaned and "." in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            # 1.234,56 -> 1234.56
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            # 1,234.56 -> 1234.56
            cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        # 1234,56 -> 1234.56
        # But wait, what if it's 1,234 (thousands)?
        # For simplicity, if only one comma exists, we can't be sure, 
        # but in many regions it's the decimal separator.
        # Let's count them. If more than one comma, it's a thousand separator.
        if cleaned.count(",") > 1:
            cleaned = cleaned.replace(",", "")
        else:
            # 12,34 -> 12.34
            cleaned = cleaned.replace(",", ".")
            
    try:
        return float(cleaned)
    except ValueError:
        logger.error(f"Failed to parse price from: {text}")
        return None

async def fetch_price(url: str, selector: Optional[str] = None) -> Tuple[Optional[str], Optional[float]]:
    """
    Fetches the price from the given URL using optional CSS selector.
    """
    async with httpx.AsyncClient(headers=DEFAULT_HEADERS, follow_redirects=True, timeout=REQUEST_TIMEOUT) as client:
        try:
            logger.info(f"Fetching: {url}")
            response = await client.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "lxml")
            
            # 1) Try user-provided selector
            if selector:
                el = soup.select_one(selector)
                if el:
                    text = el.get_text(strip=True)
                    price = parse_price(text)
                    if price is not None:
                        return text, price
            
            # 2) Domain-specific logic
            domain = urlparse(url).netloc
            if "trendyol.com" in domain:
                for sel in TRENDYOL_SELECTORS:
                    el = soup.select_one(sel)
                    if el:
                        text = el.get_text(strip=True)
                        price = parse_price(text)
                        if price is not None:
                            return text, price
                            
            # 3) Common selectors
            for sel in COMMON_PRICE_SELECTORS:
                el = soup.select_one(sel)
                if el:
                    text = el.get_text(strip=True)
                    price = parse_price(text)
                    if price is not None:
                        return text, price
                        
            logger.warning(f"No price found for {url}")
            return None, None
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP Error fetching {url}: {e}")
            return None, None
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None, None

async def scrape_multiple(urls_with_selectors: List[Tuple[int, str, Optional[str]]]) -> List[Tuple[int, Optional[float]]]:
    """
    Scrapes multiple URLs asynchronously.
    """
    tasks = []
    for product_id, url, selector in urls_with_selectors:
        tasks.append(fetch_with_id(product_id, url, selector))
    
    return await asyncio.gather(*tasks)

async def fetch_with_id(product_id: int, url: str, selector: Optional[str]) -> Tuple[int, Optional[float]]:
    _, price = await fetch_price(url, selector)
    return product_id, price

if __name__ == "__main__":
    # Simple test
    async def main():
        url = "https://www.google.com"  # Replace with a real price URL for testing
        raw, price = await fetch_price(url)
        print(f"Price: {price}")

    asyncio.run(main())
