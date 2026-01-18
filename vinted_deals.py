"""
🔥 Vinted Deal Finder - Cerca le migliori offerte su tute da calcio
Funziona da GitHub Actions o localmente
Notifiche via Discord o WhatsApp (Twilio)
"""

import os
import time
import json
import requests
from datetime import datetime
from typing import List, Dict, Optional
import hashlib

# ============================================
# CONFIGURAZIONE - Modifica questi valori
# ============================================

CONFIG = {
    # Ricerca
    "search_query": "tuta calcio",  # Cosa cercare
    "max_price": 20,  # Prezzo massimo in euro
    "min_price": 1,  # Prezzo minimo (evita errori)
    
    # Intervallo
    "check_interval_minutes": 5,
    
    # Notifiche Discord (preferito - gratuito e facile)
    "discord_webhook_url": os.getenv("DISCORD_WEBHOOK_URL", ""),
    
    # Notifiche WhatsApp via Twilio (opzionale)
    "twilio_account_sid": os.getenv("TWILIO_ACCOUNT_SID", ""),
    "twilio_auth_token": os.getenv("TWILIO_AUTH_TOKEN", ""),
    "twilio_whatsapp_from": os.getenv("TWILIO_WHATSAPP_FROM", ""),  # es: whatsapp:+14155238886
    "twilio_whatsapp_to": os.getenv("TWILIO_WHATSAPP_TO", ""),  # es: whatsapp:+39XXXXXXXXXX
}

# File per tracciare i deal già notificati
NOTIFIED_DEALS_FILE = "notified_deals.json"


class VintedDealFinder:
    """Cerca deal su Vinted senza Selenium - usa le API pubbliche"""
    
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://www.vinted.it"
        self.api_url = "https://www.vinted.it/api/v2"
        self.notified_deals = self.load_notified_deals()
        
        # Headers per sembrare un browser normale
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://www.vinted.it/",
            "Origin": "https://www.vinted.it",
        })
    
    def load_notified_deals(self) -> set:
        """Carica i deal già notificati"""
        try:
            if os.path.exists(NOTIFIED_DEALS_FILE):
                with open(NOTIFIED_DEALS_FILE, "r") as f:
                    return set(json.load(f))
        except Exception as e:
            print(f"⚠️ Errore caricamento deals salvati: {e}")
        return set()
    
    def save_notified_deals(self):
        """Salva i deal notificati"""
        try:
            with open(NOTIFIED_DEALS_FILE, "w") as f:
                json.dump(list(self.notified_deals), f)
        except Exception as e:
            print(f"⚠️ Errore salvataggio deals: {e}")
    
    def get_csrf_token(self) -> Optional[str]:
        """Ottiene il CSRF token dalla pagina principale"""
        try:
            response = self.session.get(self.base_url, timeout=10)
            # Il token è nei cookies dopo la prima visita
            return self.session.cookies.get("_csrf_token")
        except Exception as e:
            print(f"⚠️ Errore CSRF: {e}")
            return None
    
    def search_items(self, query: str, max_price: float, min_price: float = 1) -> List[Dict]:
        """Cerca articoli su Vinted"""
        items = []
        
        try:
            # Prima visita per ottenere cookies
            self.session.get(self.base_url, timeout=10)
            time.sleep(1)
            
            # URL di ricerca con parametri
            search_url = f"{self.base_url}/catalog"
            params = {
                "search_text": query,
                "price_to": max_price,
                "price_from": min_price,
                "order": "newest_first",  # I più recenti prima
                "currency": "EUR",
            }
            
            # Prova con web scraping della pagina
            response = self.session.get(search_url, params=params, timeout=15)
            
            if response.status_code == 200:
                # Cerca i dati JSON nella pagina
                items = self.parse_search_results(response.text)
                
            # Se non funziona, prova l'API alternativa
            if not items:
                items = self.search_via_api(query, max_price, min_price)
                
        except Exception as e:
            print(f"❌ Errore ricerca: {e}")
        
        return items
    
    def parse_search_results(self, html: str) -> List[Dict]:
        """Estrae i risultati dalla pagina HTML"""
        items = []
        
        try:
            # Cerca il JSON embedded nella pagina
            import re
            
            # Pattern per trovare i dati degli item
            patterns = [
                r'"items":\s*(\[.*?\])',
                r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\});',
                r'"catalogItems":\s*(\{.*?\})',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, html, re.DOTALL)
                if matches:
                    try:
                        data = json.loads(matches[0])
                        if isinstance(data, list):
                            items = self.extract_items_from_data(data)
                        elif isinstance(data, dict):
                            items = self.extract_items_from_data(data)
                        if items:
                            break
                    except json.JSONDecodeError:
                        continue
            
            # Fallback: parsing HTML semplice
            if not items:
                items = self.parse_html_items(html)
                
        except Exception as e:
            print(f"⚠️ Errore parsing: {e}")
        
        return items
    
    def parse_html_items(self, html: str) -> List[Dict]:
        """Parsing HTML semplificato per estrarre gli item"""
        items = []
        
        try:
            import re
            
            # Pattern per trovare link agli articoli
            item_pattern = r'href="(/items/(\d+)[^"]*)"[^>]*>.*?'
            price_pattern = r'(\d+[.,]?\d*)\s*€'
            
            # Cerca tutti i link agli articoli
            item_links = re.findall(r'href="(/items/\d+-[^"]+)"', html)
            
            for link in item_links[:20]:  # Limita a 20 risultati
                try:
                    item_id = link.split("/items/")[1].split("-")[0]
                    
                    # Cerca il prezzo nelle vicinanze
                    idx = html.find(link)
                    if idx > 0:
                        snippet = html[idx:idx+500]
                        prices = re.findall(price_pattern, snippet)
                        if prices:
                            price = float(prices[0].replace(",", "."))
                            if price <= CONFIG["max_price"]:
                                # Estrai il titolo dal link
                                title_match = link.split("-", 1)
                                title = title_match[1].replace("-", " ") if len(title_match) > 1 else f"Articolo {item_id}"
                                
                                items.append({
                                    "id": item_id,
                                    "title": title[:50],
                                    "price": price,
                                    "url": f"https://www.vinted.it{link}",
                                })
                except:
                    continue
                    
        except Exception as e:
            print(f"⚠️ Errore HTML parsing: {e}")
        
        return items
    
    def search_via_api(self, query: str, max_price: float, min_price: float) -> List[Dict]:
        """Cerca usando l'API di Vinted"""
        items = []
        
        try:
            # Endpoint API pubblico
            api_url = f"{self.api_url}/catalog/items"
            params = {
                "search_text": query,
                "price_to": max_price,
                "price_from": min_price,
                "order": "newest_first",
                "per_page": 20,
            }
            
            response = self.session.get(api_url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if "items" in data:
                    for item in data["items"]:
                        items.append({
                            "id": str(item.get("id", "")),
                            "title": item.get("title", ""),
                            "price": float(item.get("price", {}).get("amount", 0)),
                            "url": item.get("url", f"{self.base_url}/items/{item.get('id')}"),
                            "photo": item.get("photo", {}).get("url", ""),
                            "brand": item.get("brand_title", ""),
                            "size": item.get("size_title", ""),
                        })
                        
        except Exception as e:
            print(f"⚠️ API error: {e}")
        
        return items
    
    def extract_items_from_data(self, data) -> List[Dict]:
        """Estrae gli item dai dati JSON"""
        items = []
        
        try:
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and "id" in item:
                        items.append({
                            "id": str(item.get("id", "")),
                            "title": item.get("title", ""),
                            "price": float(item.get("price", {}).get("amount", 0) if isinstance(item.get("price"), dict) else item.get("price", 0)),
                            "url": item.get("url", f"{self.base_url}/items/{item.get('id')}"),
                        })
            elif isinstance(data, dict):
                if "items" in data:
                    return self.extract_items_from_data(data["items"])
                    
        except Exception as e:
            print(f"⚠️ Errore estrazione: {e}")
        
        return items
    
    def is_new_deal(self, item_id: str) -> bool:
        """Controlla se è un nuovo deal"""
        return item_id not in self.notified_deals
    
    def mark_as_notified(self, item_id: str):
        """Segna un deal come notificato"""
        self.notified_deals.add(item_id)
        self.save_notified_deals()


class NotificationManager:
    """Gestisce le notifiche Discord e WhatsApp"""
    
    @staticmethod
    def send_discord(webhook_url: str, item: Dict) -> bool:
        """Invia notifica su Discord"""
        if not webhook_url:
            return False
        
        try:
            embed = {
                "embeds": [{
                    "title": f"🔥 DEAL TROVATO: {item.get('title', 'Articolo')[:100]}",
                    "description": f"**Prezzo:** €{item.get('price', 'N/A')}",
                    "url": item.get("url", ""),
                    "color": 0x00FF00,  # Verde
                    "fields": [
                        {"name": "🏷️ Brand", "value": item.get("brand", "N/D"), "inline": True},
                        {"name": "📏 Taglia", "value": item.get("size", "N/D"), "inline": True},
                    ],
                    "thumbnail": {"url": item.get("photo", "")},
                    "footer": {"text": f"Vinted Deal Finder | {datetime.now().strftime('%H:%M:%S')}"},
                }]
            }
            
            response = requests.post(webhook_url, json=embed, timeout=10)
            
            if response.status_code in [200, 204]:
                print(f"✅ Discord: Notifica inviata per {item.get('title', '')[:30]}")
                return True
            else:
                print(f"⚠️ Discord error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Discord error: {e}")
            return False
    
    @staticmethod
    def send_whatsapp(item: Dict) -> bool:
        """Invia notifica su WhatsApp via Twilio"""
        if not all([CONFIG["twilio_account_sid"], CONFIG["twilio_auth_token"], 
                    CONFIG["twilio_whatsapp_from"], CONFIG["twilio_whatsapp_to"]]):
            return False
        
        try:
            url = f"https://api.twilio.com/2010-04-01/Accounts/{CONFIG['twilio_account_sid']}/Messages.json"
            
            message = f"""🔥 *DEAL VINTED*
            
📦 *{item.get('title', 'Articolo')[:100]}*
💰 Prezzo: €{item.get('price', 'N/A')}
🏷️ Brand: {item.get('brand', 'N/D')}
📏 Taglia: {item.get('size', 'N/D')}

🔗 {item.get('url', '')}"""
            
            data = {
                "From": CONFIG["twilio_whatsapp_from"],
                "To": CONFIG["twilio_whatsapp_to"],
                "Body": message,
            }
            
            response = requests.post(
                url,
                data=data,
                auth=(CONFIG["twilio_account_sid"], CONFIG["twilio_auth_token"]),
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                print(f"✅ WhatsApp: Notifica inviata per {item.get('title', '')[:30]}")
                return True
            else:
                print(f"⚠️ WhatsApp error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ WhatsApp error: {e}")
            return False
    
    @staticmethod
    def notify(item: Dict):
        """Invia notifica su tutti i canali configurati"""
        discord_sent = False
        whatsapp_sent = False
        
        # Prova Discord
        if CONFIG["discord_webhook_url"]:
            discord_sent = NotificationManager.send_discord(CONFIG["discord_webhook_url"], item)
        
        # Prova WhatsApp
        if CONFIG["twilio_account_sid"]:
            whatsapp_sent = NotificationManager.send_whatsapp(item)
        
        if not discord_sent and not whatsapp_sent:
            print(f"⚠️ Nessun canale di notifica configurato!")
            print(f"   Deal trovato: {item.get('title', '')} - €{item.get('price', '')}")
            print(f"   URL: {item.get('url', '')}")
        
        return discord_sent or whatsapp_sent


def print_banner():
    """Stampa il banner di avvio"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║        🔥 VINTED DEAL FINDER - Tute da Calcio 🔥             ║
║                                                              ║
║  ⚽ Cerca: tute da calcio                                    ║
║  💰 Prezzo max: 20€                                          ║
║  ⏰ Refresh: ogni 5 minuti                                   ║
║  📱 Notifiche: Discord / WhatsApp                            ║
║                                                              ║
║  🚀 Pronto per GitHub Actions - No Selenium!                 ║
╚══════════════════════════════════════════════════════════════╝
    """)


def check_configuration():
    """Verifica la configurazione"""
    print("\n🔧 Verifica configurazione...")
    
    has_discord = bool(CONFIG["discord_webhook_url"])
    has_whatsapp = bool(CONFIG["twilio_account_sid"] and CONFIG["twilio_whatsapp_to"])
    
    print(f"   Discord Webhook: {'✅ Configurato' if has_discord else '❌ Non configurato'}")
    print(f"   WhatsApp Twilio: {'✅ Configurato' if has_whatsapp else '❌ Non configurato'}")
    
    if not has_discord and not has_whatsapp:
        print("\n⚠️  ATTENZIONE: Nessun canale di notifica configurato!")
        print("   I deal saranno solo stampati nella console.\n")
        print("   Per configurare Discord:")
        print("   1. Crea un webhook nel tuo server Discord")
        print("   2. Imposta DISCORD_WEBHOOK_URL come variabile d'ambiente")
        print("   3. Oppure modifica CONFIG['discord_webhook_url'] nel codice\n")
    
    return has_discord or has_whatsapp


def main():
    """Funzione principale"""
    print_banner()
    check_configuration()
    
    finder = VintedDealFinder()
    
    print(f"\n🔍 Inizio ricerca: '{CONFIG['search_query']}' (max €{CONFIG['max_price']})")
    print(f"⏰ Controllo ogni {CONFIG['check_interval_minutes']} minuti")
    print("=" * 60)
    
    check_count = 0
    
    while True:
        check_count += 1
        current_time = datetime.now().strftime("%H:%M:%S")
        print(f"\n[{current_time}] 🔄 Controllo #{check_count}...")
        
        try:
            # Cerca gli articoli
            items = finder.search_items(
                query=CONFIG["search_query"],
                max_price=CONFIG["max_price"],
                min_price=CONFIG["min_price"]
            )
            
            if not items:
                print("   📭 Nessun risultato trovato")
            else:
                print(f"   📦 Trovati {len(items)} articoli")
                
                new_deals = 0
                for item in items:
                    if finder.is_new_deal(item["id"]):
                        new_deals += 1
                        print(f"\n   🔥 NUOVO DEAL!")
                        print(f"      📦 {item.get('title', 'N/D')[:50]}")
                        print(f"      💰 €{item.get('price', 'N/D')}")
                        print(f"      🔗 {item.get('url', '')}")
                        
                        # Invia notifica
                        NotificationManager.notify(item)
                        
                        # Segna come notificato
                        finder.mark_as_notified(item["id"])
                        
                        # Piccola pausa tra le notifiche
                        time.sleep(1)
                
                if new_deals == 0:
                    print("   ✨ Nessun nuovo deal")
                else:
                    print(f"\n   📨 {new_deals} nuovi deal notificati!")
                    
        except Exception as e:
            print(f"   ❌ Errore: {e}")
        
        # Attendi prima del prossimo controllo
        wait_seconds = CONFIG["check_interval_minutes"] * 60
        print(f"\n⏳ Prossimo controllo tra {CONFIG['check_interval_minutes']} minuti...")
        
        try:
            time.sleep(wait_seconds)
        except KeyboardInterrupt:
            print("\n\n🛑 Bot fermato dall'utente")
            break
    
    print("\n👋 Arrivederci!")


if __name__ == "__main__":
    main()
