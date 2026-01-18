"""
Vinted Scraper - Versione ottimizzata per GitHub Actions (NO PROXY)
"""
import requests
import time
import json
import random
import re
from datetime import datetime
from typing import List, Dict, Optional


class VintedScraper:
    """Scraper Vinted ottimizzato per GitHub Actions"""

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
    ]

    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://www.vinted.it"
        self.stats = {"requests": 0, "successes": 0, "failures": 0}
        self._update_headers()

    def _update_headers(self):
        """Aggiorna headers con user agent random"""
        self.session.headers.update({
            "User-Agent": random.choice(self.USER_AGENTS),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://www.vinted.it/",
            "DNT": "1",
            "Connection": "keep-alive"
        })

    def make_request(self, url: str, params: Optional[Dict] = None, 
                    timeout: int = 15, max_retries: int = 3) -> Optional[requests.Response]:
        """Esegue richiesta con retry logic"""
        self.stats["requests"] += 1

        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    self._update_headers()
                    time.sleep(2 ** attempt)  # Exponential backoff

                response = self.session.get(url, params=params, timeout=timeout)

                if response.status_code == 200:
                    self.stats["successes"] += 1
                    return response
                elif response.status_code == 429:
                    print(f"⚠️ Rate limited - Pausa 30s")
                    time.sleep(30)
                    continue
                else:
                    print(f"⚠️ Status {response.status_code}")

            except Exception as e:
                print(f"⚠️ Errore tentativo {attempt + 1}: {type(e).__name__}")
                if attempt == max_retries - 1:
                    self.stats["failures"] += 1
                    return None

        self.stats["failures"] += 1
        return None

    def search_items(self, query: str, max_price: float, 
                    min_price: float = 1, max_items: int = 50) -> List[Dict]:
        """Cerca articoli su Vinted"""
        items = []

        try:
            print("🔄 Connessione a Vinted...")
            response = self.make_request(self.base_url, timeout=10)

            if not response:
                print("❌ Impossibile connettersi")
                return items

            time.sleep(random.uniform(1, 2))

            print(f"🔍 Ricerca: '{query}' (€{min_price}-€{max_price})")

            search_url = f"{self.base_url}/catalog"
            params = {
                "search_text": query,
                "price_to": max_price,
                "price_from": min_price,
                "order": "newest_first",
                "currency": "EUR"
            }

            response = self.make_request(search_url, params=params, timeout=20)

            if response and response.status_code == 200:
                items = self._parse_items(response.text, max_items)

        except Exception as e:
            print(f"❌ Errore ricerca: {e}")

        return items

    def _parse_items(self, html: str, max_items: int = 50) -> List[Dict]:
        """Estrae items dal HTML"""
        items = []

        try:
            item_pattern = r'href="(/items/\d+-[^"]+)"'
            price_pattern = r'(\d+[.,]?\d*)\s*€'

            item_links = re.findall(item_pattern, html)
            seen_ids = set()

            for link in item_links[:max_items]:
                try:
                    item_id = link.split("/items/")[1].split("-")[0]

                    if item_id in seen_ids:
                        continue
                    seen_ids.add(item_id)

                    idx = html.find(link)
                    if idx > 0:
                        snippet = html[idx:idx+600]
                        prices = re.findall(price_pattern, snippet)

                        if prices:
                            price = float(prices[0].replace(",", "."))

                            title_parts = link.split("-", 1)
                            if len(title_parts) > 1:
                                title = title_parts[1].replace("-", " ").title()
                            else:
                                title = f"Articolo {item_id}"

                            items.append({
                                "id": item_id,
                                "title": title[:100],
                                "price": price,
                                "url": f"https://www.vinted.it{link}",
                                "brand": "",
                                "size": "",
                                "photo": ""
                            })

                except Exception:
                    continue

            if items:
                print(f"✅ Trovati {len(items)} articoli")

        except Exception as e:
            print(f"⚠️ Errore parsing: {e}")

        return items

    def get_stats(self) -> Dict:
        """Statistiche scraper"""
        stats = self.stats.copy()
        if stats["requests"] > 0:
            stats["success_rate"] = round(stats["successes"] / stats["requests"] * 100, 2)
        else:
            stats["success_rate"] = 0
        return stats
