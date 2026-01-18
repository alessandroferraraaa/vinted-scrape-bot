"""
🔥 Vinted Deal Finder - Versione GitHub Actions Ottimizzata
"""
import os
import time
import json
import requests
from datetime import datetime
from typing import List, Dict
from vinted_scraper import VintedScraper

# ============================================
# CONFIGURAZIONE
# ============================================

CONFIG = {
    "search_query": os.getenv("SEARCH_QUERY", "tuta calcio"),
    "max_price": float(os.getenv("MAX_PRICE", "20")),
    "min_price": float(os.getenv("MIN_PRICE", "1")),
    "max_items": int(os.getenv("MAX_ITEMS", "50")),
    "discord_webhook_url": os.getenv("DISCORD_WEBHOOK_URL", ""),
    "notified_deals_file": "notified_deals.json",
    "stats_file": "bot_stats.json"
}


class DealManager:
    """Gestisce tracking deal notificati"""

    def __init__(self, deals_file: str):
        self.deals_file = deals_file
        self.notified_deals = self._load_deals()
        self.new_deals_count = 0

    def _load_deals(self) -> set:
        """Carica deal già notificati"""
        try:
            if os.path.exists(self.deals_file):
                with open(self.deals_file, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return set(data[-1000:])
                    return set(data.get('deals', [])[-1000:])
        except Exception as e:
            print(f"⚠️ Errore caricamento deals: {e}")
        return set()

    def save_deals(self):
        """Salva deal notificati"""
        try:
            data = {
                'deals': list(self.notified_deals)[-1000:],
                'last_update': datetime.now().isoformat(),
                'total': len(self.notified_deals)
            }
            with open(self.deals_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠️ Errore salvataggio: {e}")

    def is_new_deal(self, item_id: str) -> bool:
        return item_id not in self.notified_deals

    def mark_as_notified(self, item_id: str):
        self.notified_deals.add(item_id)
        self.new_deals_count += 1
        self.save_deals()


class NotificationManager:
    """Gestisce notifiche Discord"""

    @staticmethod
    def send_discord(webhook_url: str, item: Dict) -> bool:
        """Invia notifica Discord con rich embed"""
        if not webhook_url:
            return False

        try:
            # Emoji basati sul prezzo
            if item['price'] <= 10:
                emoji = "🔥🔥🔥"
                color = 0xFF4500
            elif item['price'] <= 15:
                emoji = "🔥🔥"
                color = 0xFF8C00
            else:
                emoji = "🔥"
                color = 0x00FF00

            embed = {
                "embeds": [{
                    "title": f"{emoji} {item.get('title', 'Deal Vinted')[:100]}",
                    "description": f"**💰 Prezzo: €{item.get('price', 'N/A')}**",
                    "url": item.get("url", ""),
                    "color": color,
                    "fields": [
                        {"name": "🆔 ID", "value": item.get("id", "N/D"), "inline": True},
                        {"name": "🔗 Link", "value": "[Vedi su Vinted](" + item.get("url", "") + ")", "inline": False}
                    ],
                    "footer": {"text": f"Vinted Bot • {datetime.now().strftime('%d/%m/%Y %H:%M')}"},
                    "timestamp": datetime.utcnow().isoformat()
                }]
            }

            response = requests.post(webhook_url, json=embed, timeout=10)
            return response.status_code in [200, 204]

        except Exception as e:
            print(f"❌ Discord error: {e}")
            return False


class VintedBot:
    """Bot principale per GitHub Actions"""

    def __init__(self):
        self.config = CONFIG
        self.deal_manager = DealManager(CONFIG["notified_deals_file"])
        self.scraper = VintedScraper()
        self.stats = {
            'timestamp': datetime.now().isoformat(),
            'items_found': 0,
            'new_deals': 0,
            'notifications_sent': 0
        }

    def run(self):
        """Esegue singolo controllo per GitHub Actions"""
        print("\n" + "="*60)
        print("🔥 VINTED DEAL FINDER")
        print("="*60)
        print(f"⏰ {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"🔍 Ricerca: '{self.config['search_query']}'")
        print(f"💰 Prezzo: €{self.config['min_price']}-€{self.config['max_price']}")

        if not self.config['discord_webhook_url']:
            print("⚠️ WARNING: Discord webhook non configurato!")
            print("   Configura DISCORD_WEBHOOK_URL nei GitHub Secrets")

        print("="*60)

        # Cerca articoli
        items = self.scraper.search_items(
            query=self.config['search_query'],
            max_price=self.config['max_price'],
            min_price=self.config['min_price'],
            max_items=self.config['max_items']
        )

        self.stats['items_found'] = len(items)

        if not items:
            print("\n📭 Nessun articolo trovato")
        else:
            # Processa deal
            new_deals = self._process_deals(items)
            self.stats['new_deals'] = new_deals

            if new_deals == 0:
                print("\n✨ Nessun nuovo deal")

        # Stampa statistiche
        self._print_stats()

        # Salva statistiche
        self._save_stats()

        print("\n✅ Controllo completato!")
        print("="*60)

    def _process_deals(self, items: List[Dict]) -> int:
        """Processa nuovi deal e invia notifiche"""
        new_deals = 0

        for item in items:
            if self.deal_manager.is_new_deal(item["id"]):
                new_deals += 1

                print(f"\n🔥 NUOVO DEAL #{new_deals}!")
                print(f"   📦 {item.get('title', 'N/D')[:60]}")
                print(f"   💰 €{item.get('price', 'N/A')}")
                print(f"   🔗 {item.get('url', '')}")

                # Invia notifica Discord
                if self.config['discord_webhook_url']:
                    if NotificationManager.send_discord(self.config['discord_webhook_url'], item):
                        print(f"   ✅ Discord notificato")
                        self.stats['notifications_sent'] += 1
                    else:
                        print(f"   ❌ Errore notifica Discord")

                # Marca come notificato
                self.deal_manager.mark_as_notified(item["id"])

                time.sleep(1)  # Pausa tra notifiche

        return new_deals

    def _print_stats(self):
        """Stampa statistiche"""
        scraper_stats = self.scraper.get_stats()

        print(f"\n📊 Statistiche:")
        print(f"   📦 Articoli trovati: {self.stats['items_found']}")
        print(f"   🔥 Nuovi deal: {self.stats['new_deals']}")
        print(f"   📨 Notifiche inviate: {self.stats['notifications_sent']}")
        print(f"   🌐 Richieste HTTP: {scraper_stats['requests']}")
        print(f"   ✅ Success rate: {scraper_stats['success_rate']}%")
        print(f"   💾 Deal tracciati: {len(self.deal_manager.notified_deals)}")

    def _save_stats(self):
        """Salva statistiche"""
        try:
            stats_data = {
                **self.stats,
                'scraper_stats': self.scraper.get_stats(),
                'total_deals_tracked': len(self.deal_manager.notified_deals)
            }

            with open(self.config['stats_file'], 'w') as f:
                json.dump(stats_data, f, indent=2)

        except Exception as e:
            print(f"⚠️ Errore salvataggio stats: {e}")


def main():
    """Funzione principale"""
    try:
        bot = VintedBot()
        bot.run()
    except KeyboardInterrupt:
        print("\n\n🛑 Interrotto")
    except Exception as e:
        print(f"\n❌ Errore: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()
