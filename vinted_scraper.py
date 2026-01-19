"""
Vinted Scraper - Versione API DIRETTA (funziona SEMPRE!)
Usa l'API ufficiale di Vinted per ottenere risultati affidabili
"""
import requests
import time
import random
from typing import List, Dict, Optional


class VintedScraper:
    """Scraper Vinted usando API ufficiale"""

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ]

    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://www.vinted.it"
        self.api_url = "https://www.vinted.it/api/v2/catalog/items"
        self.stats = {"requests": 0, "successes": 0, "failures": 0}
        self._get_session_cookie()

    def _get_session_cookie(self):
        """Ottiene cookie di sessione da Vinted"""
        try:
            headers = {
                "User-Agent": random.choice(self.USER_AGENTS),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
                "Connection": "keep-alive"
            }

            response = self.session.get(self.base_url, headers=headers, timeout=10)

            # Aggiorna headers per le richieste API
            self.session.headers.update({
                "User-Agent": random.choice(self.USER_AGENTS),
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "it-IT,it;q=0.9",
                "Referer": self.base_url + "/",
                "Origin": self.base_url
            })

            return True

        except Exception as e:
            print(f"⚠️ Errore sessione: {e}")
            return False

    def search_items(self, query: str, max_price: float, 
                    min_price: float = 1, max_items: int = 50) -> List[Dict]:
        """Cerca articoli usando API Vinted"""
        items = []

        try:
            print("🔄 Connessione a Vinted...")

            # Parametri per API Vinted
            params = {
                "search_text": query,
                "price_to": int(max_price),
                "price_from": int(min_price),
                "currency": "EUR",
                "order": "newest_first",
                "per_page": min(max_items, 96)
            }

            print(f"🔍 Ricerca API: '{query}' (€{min_price}-€{max_price})")

            self.stats["requests"] += 1

            # Chiamata API
            response = self.session.get(
                self.api_url,
                params=params,
                timeout=15
            )

            if response.status_code == 200:
                self.stats["successes"] += 1
                data = response.json()

                # Estrai items dalla risposta
                vinted_items = data.get("items", [])

                print(f"✅ API ha restituito {len(vinted_items)} articoli")

                for item in vinted_items[:max_items]:
                    try:
                        # Estrai dati
                        item_id = str(item.get("id", ""))
                        title = item.get("title", "Articolo")

                        # Prezzo
                        price_data = item.get("price", {})
                        if isinstance(price_data, dict):
                            price = float(price_data.get("amount", 0))
                        else:
                            price = float(price_data) if price_data else 0

                        # URL
                        url = item.get("url")
                        if not url or not url.startswith("http"):
                            url = f"{self.base_url}/items/{item_id}"

                        # Foto (tutte, non solo la prima)
                        photo = ""
                        photo_urls = []
                        photos = item.get("photos", [])
                        if photos and len(photos) > 0:
                            photo = photos[0].get("url", "")
                            # Estrai tutte le foto (max 5 per efficienza)
                            for p in photos[:5]:
                                url_foto = p.get("url", "")
                                if url_foto:
                                    photo_urls.append(url_foto)

                        # Brand e taglia
                        brand = item.get("brand_title", "")
                        size = item.get("size_title", "")

                        # Descrizione (importante per i filtri!)
                        description = item.get("description", "")
                        
                        # Timestamp creazione (per filtro tempo)
                        created_at_ts = item.get("created_at_ts")

                        items.append({
                            "id": item_id,
                            "title": title[:100],
                            "description": description,
                            "price": price,
                            "url": url,
                            "photo": photo,
                            "photo_urls": photo_urls,
                            "brand": brand,
                            "size": size,
                            "created_at_ts": created_at_ts
                        })

                    except Exception as e:
                        print(f"⚠️ Errore parsing item: {e}")
                        continue

                if items:
                    print(f"✅ {len(items)} articoli processati con successo")
                else:
                    print("⚠️ Nessun articolo valido trovato")

            elif response.status_code == 403:
                print("❌ Accesso bloccato (403) - Riprova tra qualche minuto")
                self.stats["failures"] += 1

            elif response.status_code == 429:
                print("❌ Troppi richieste (429) - Attendi 30 secondi")
                self.stats["failures"] += 1

            else:
                print(f"❌ Errore API: status {response.status_code}")
                self.stats["failures"] += 1

        except requests.exceptions.Timeout:
            print("❌ Timeout connessione")
            self.stats["failures"] += 1

        except requests.exceptions.RequestException as e:
            print(f"❌ Errore rete: {e}")
            self.stats["failures"] += 1

        except Exception as e:
            print(f"❌ Errore imprevisto: {e}")
            self.stats["failures"] += 1

        return items

    def get_stats(self) -> Dict:
        """Statistiche scraper"""
        stats = self.stats.copy()
        if stats["requests"] > 0:
            stats["success_rate"] = round(stats["successes"] / stats["requests"] * 100, 2)
        else:
            stats["success_rate"] = 0
        return stats
