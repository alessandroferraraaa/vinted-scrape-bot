"""
🔥 Vinted Deal Finder - Versione Single Check per GitHub Actions
Esegue un singolo controllo e termina (per schedulazione cron)
"""

import os
import time
import json
import requests
from datetime import datetime
from typing import List, Dict, Optional

# ============================================
# CONFIGURAZIONE
# ============================================

CONFIG = {
    "search_query": "tuta calcio",
    "max_price": 20,
    "min_price": 1,
    "discord_webhook_url": os.getenv("DISCORD_WEBHOOK_URL", ""),
    "twilio_account_sid": os.getenv("TWILIO_ACCOUNT_SID", ""),
    "twilio_auth_token": os.getenv("TWILIO_AUTH_TOKEN", ""),
    "twilio_whatsapp_from": os.getenv("TWILIO_WHATSAPP_FROM", ""),
    "twilio_whatsapp_to": os.getenv("TWILIO_WHATSAPP_TO", ""),
}

NOTIFIED_DEALS_FILE = "notified_deals.json"


class VintedDealFinder:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://www.vinted.it"
        self.notified_deals = self.load_notified_deals()
        
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "it-IT,it;q=0.9",
            "Referer": "https://www.vinted.it/",
        })
    
    def load_notified_deals(self) -> set:
        try:
            if os.path.exists(NOTIFIED_DEALS_FILE):
                with open(NOTIFIED_DEALS_FILE, "r") as f:
                    return set(json.load(f))
        except:
            pass
        return set()
    
    def save_notified_deals(self):
        try:
            with open(NOTIFIED_DEALS_FILE, "w") as f:
                json.dump(list(self.notified_deals), f)
        except Exception as e:
            print(f"⚠️ Errore salvataggio: {e}")
    
    def search_items(self, query: str, max_price: float, min_price: float = 1) -> List[Dict]:
        items = []
        
        try:
            self.session.get(self.base_url, timeout=10)
            time.sleep(1)
            
            search_url = f"{self.base_url}/catalog"
            params = {
                "search_text": query,
                "price_to": max_price,
                "price_from": min_price,
                "order": "newest_first",
                "currency": "EUR",
            }
            
            response = self.session.get(search_url, params=params, timeout=15)
            
            if response.status_code == 200:
                items = self.parse_html_items(response.text)
                
        except Exception as e:
            print(f"❌ Errore ricerca: {e}")
        
        return items
    
    def parse_html_items(self, html: str) -> List[Dict]:
        items = []
        
        try:
            import re
            
            item_links = re.findall(r'href="(/items/\d+-[^"]+)"', html)
            price_pattern = r'(\d+[.,]?\d*)\s*€'
            
            seen_ids = set()
            for link in item_links[:20]:
                try:
                    item_id = link.split("/items/")[1].split("-")[0]
                    
                    if item_id in seen_ids:
                        continue
                    seen_ids.add(item_id)
                    
                    idx = html.find(link)
                    if idx > 0:
                        snippet = html[idx:idx+500]
                        prices = re.findall(price_pattern, snippet)
                        if prices:
                            price = float(prices[0].replace(",", "."))
                            if price <= CONFIG["max_price"]:
                                title_match = link.split("-", 1)
                                title = title_match[1].replace("-", " ").title() if len(title_match) > 1 else f"Articolo {item_id}"
                                
                                items.append({
                                    "id": item_id,
                                    "title": title[:80],
                                    "price": price,
                                    "url": f"https://www.vinted.it{link}",
                                    "brand": "",
                                    "size": "",
                                    "photo": "",
                                })
                except:
                    continue
                    
        except Exception as e:
            print(f"⚠️ Errore parsing: {e}")
        
        return items
    
    def is_new_deal(self, item_id: str) -> bool:
        return item_id not in self.notified_deals
    
    def mark_as_notified(self, item_id: str):
        self.notified_deals.add(item_id)
        self.save_notified_deals()


def send_discord(webhook_url: str, item: Dict) -> bool:
    if not webhook_url:
        return False
    
    try:
        embed = {
            "embeds": [{
                "title": f"🔥 {item.get('title', 'Tuta Calcio')[:100]}",
                "description": f"**💰 Prezzo: €{item.get('price', 'N/A')}**",
                "url": item.get("url", ""),
                "color": 0x00FF00,
                "footer": {"text": f"Vinted Deal | {datetime.now().strftime('%d/%m %H:%M')}"},
            }]
        }
        
        response = requests.post(webhook_url, json=embed, timeout=10)
        return response.status_code in [200, 204]
        
    except Exception as e:
        print(f"❌ Discord error: {e}")
        return False


def send_whatsapp(item: Dict) -> bool:
    if not all([CONFIG["twilio_account_sid"], CONFIG["twilio_auth_token"], 
                CONFIG["twilio_whatsapp_from"], CONFIG["twilio_whatsapp_to"]]):
        return False
    
    try:
        url = f"https://api.twilio.com/2010-04-01/Accounts/{CONFIG['twilio_account_sid']}/Messages.json"
        
        message = f"""🔥 DEAL VINTED

📦 {item.get('title', 'Tuta Calcio')[:100]}
💰 €{item.get('price', 'N/A')}

🔗 {item.get('url', '')}"""
        
        response = requests.post(
            url,
            data={
                "From": CONFIG["twilio_whatsapp_from"],
                "To": CONFIG["twilio_whatsapp_to"],
                "Body": message,
            },
            auth=(CONFIG["twilio_account_sid"], CONFIG["twilio_auth_token"]),
            timeout=10
        )
        
        return response.status_code in [200, 201]
        
    except Exception as e:
        print(f"❌ WhatsApp error: {e}")
        return False


def main():
    print(f"\n🔥 Vinted Deal Finder - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"🔍 Cerco: '{CONFIG['search_query']}' (max €{CONFIG['max_price']})")
    print("=" * 50)
    
    finder = VintedDealFinder()
    
    items = finder.search_items(
        query=CONFIG["search_query"],
        max_price=CONFIG["max_price"],
        min_price=CONFIG["min_price"]
    )
    
    if not items:
        print("📭 Nessun risultato trovato")
        return
    
    print(f"📦 Trovati {len(items)} articoli")
    
    new_deals = 0
    for item in items:
        if finder.is_new_deal(item["id"]):
            new_deals += 1
            print(f"\n🔥 NUOVO: {item['title'][:50]} - €{item['price']}")
            print(f"   🔗 {item['url']}")
            
            # Notifica
            discord_ok = send_discord(CONFIG["discord_webhook_url"], item)
            whatsapp_ok = send_whatsapp(item)
            
            if discord_ok:
                print("   ✅ Discord notificato")
            if whatsapp_ok:
                print("   ✅ WhatsApp notificato")
            
            finder.mark_as_notified(item["id"])
            time.sleep(1)
    
    if new_deals == 0:
        print("✨ Nessun nuovo deal")
    else:
        print(f"\n📨 {new_deals} nuovi deal trovati e notificati!")


if __name__ == "__main__":
    main()
