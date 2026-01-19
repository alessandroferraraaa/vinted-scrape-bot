"""
🔥 Vinted Deal Finder - Bot con Filtri Intelligenti per Tute Calcio
"""
import os
import time
import json
import requests
from datetime import datetime
from typing import List, Dict
from vinted_scraper import VintedScraper

# ============================================
# CONFIGURAZIONE AVANZATA
# ============================================

def get_float_env(key: str, default: float) -> float:
    value = os.getenv(key, "")
    if not value or value.strip() == "":
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

CONFIG = {
    "search_query": os.getenv("SEARCH_QUERY", "").strip() or "tuta calcio completa",
    "max_price": get_float_env("MAX_PRICE", 20.0),
    "min_price": get_float_env("MIN_PRICE", 1.0),
    "max_items": 96,
    "discord_webhook_url": os.getenv("DISCORD_WEBHOOK_URL", "").strip(),
    "notified_deals_file": "notified_deals.json",
    "stats_file": "bot_stats.json"
}

# Squadre accettate (case-insensitive)
SQUADRE_ACCETTATE = [
    "liverpool", "barcellona", "barcelona", "barça",
    "real madrid", "madrid",
    "arsenal",
    "psg", "paris saint germain", "paris",
    "marsiglia", "marseille", "om",
    "lione", "lyon", "ol",
    "bayern", "bayern monaco", "bayern munich",
    "manchester city", "man city", "city",
    "manchester united", "man united", "united",
    "borussia dortmund", "dortmund", "bvb"
]

# Parole che indicano difetti (case-insensitive)
PAROLE_DIFETTI = [
    "difetto", "difetti", "rovinato", "rovinata", "rotto", "rotta",
    "bucato", "buco", "buchi", "macchiato", "macchia", "macchie",
    "strappo", "strappato", "consumato", "usurato", "sbiadito",
    "danneggiato", "danneggiata", "difettoso", "difettosa",
    "scucito", "scucitura", "pelucchi", "scolorito", "scolorita"
]

# Parole che indicano NON è completa
PAROLE_NON_COMPLETA = [
    "solo maglia", "solo pantalone", "solo pantaloni", "solo giacca",
    "maglia singola", "pantalone singolo", "giacca singola",
    "senza pantalone", "senza pantaloni", "senza maglia", "senza giacca"
]


class ItemFilter:
    """Filtro intelligente per articoli"""
    
    @staticmethod
    def is_squadra_accettata(text: str) -> bool:
        """Verifica se l'articolo è di una squadra accettata"""
        text_lower = text.lower()
        for squadra in SQUADRE_ACCETTATE:
            if squadra in text_lower:
                return True
        return False
    
    @staticmethod
    def ha_difetti(text: str) -> bool:
        """Verifica se la descrizione menziona difetti"""
        text_lower = text.lower()
        for parola in PAROLE_DIFETTI:
            if parola in text_lower:
                return True
        return False
    
    @staticmethod
    def is_completa(text: str) -> bool:
        """Verifica se è una tuta COMPLETA"""
        text_lower = text.lower()
        
        # Controlla se dice esplicitamente che NON è completa
        for parola in PAROLE_NON_COMPLETA:
            if parola in text_lower:
                return False
        
        # Cerca indicatori di tuta completa
        indicatori_completa = [
            "completa", "complete", "set", "divisa completa",
            "felpa + pantalone", "felpa e pantalone",
            "giacca + pantalone", "giacca e pantalone",
            "top + pantalone", "top e pantalone"
        ]
        
        for indicatore in indicatori_completa:
            if indicatore in text_lower:
                return True
        
        # Se nel titolo c'è "tuta" è probabile sia completa
        if "tuta" in text_lower:
            return True
        
        return False
    
    @staticmethod
    def filtra_articolo(item: Dict) -> Dict:
        """
        Filtra un articolo secondo i criteri
        Ritorna: {"valido": bool, "motivo": str, "squadra": str}
        """
        title = item.get("title", "").lower()
        description = item.get("description", "").lower()
        brand = item.get("brand", "").lower()
        
        text_completo = f"{title} {description} {brand}"
        
        # 1. Verifica se è di una squadra accettata
        if not ItemFilter.is_squadra_accettata(text_completo):
            return {
                "valido": False,
                "motivo": "❌ Non è di una squadra della lista",
                "squadra": None
            }
        
        # Identifica quale squadra
        squadra_trovata = None
        for squadra in SQUADRE_ACCETTATE:
            if squadra in text_completo:
                squadra_trovata = squadra.title()
                break
        
        # 2. Verifica se è completa
        if not ItemFilter.is_completa(text_completo):
            return {
                "valido": False,
                "motivo": "❌ Non è una tuta completa (manca felpa o pantalone)",
                "squadra": squadra_trovata
            }
        
        # 3. Verifica se ha difetti
        if ItemFilter.ha_difetti(description):
            return {
                "valido": False,
                "motivo": "❌ Ha difetti menzionati nella descrizione",
                "squadra": squadra_trovata
            }
        
        return {
            "valido": True,
            "motivo": "✅ Tuta completa senza difetti",
            "squadra": squadra_trovata
        }


class DealManager:
    """Gestisce tracking deal notificati"""
    
    def __init__(self, deals_file: str):
        self.deals_file = deals_file
        self.notified_deals = self._load_deals()
        self.new_deals_count = 0
    
    def _load_deals(self) -> set:
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
    def send_discord(webhook_url: str, item: Dict, squadra: str) -> bool:
        """Invia notifica Discord con info squadra"""
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
            
            # Costruisci descrizione
            desc_parts = [f"**💰 Prezzo: €{item.get('price', 'N/A')}**"]
            if squadra:
                desc_parts.append(f"**⚽ Squadra: {squadra}**")
            desc_parts.append("**✅ Tuta COMPLETA senza difetti**")
            
            fields = []
            if item.get("brand"):
                fields.append({"name": "🏷️ Brand", "value": item["brand"], "inline": True})
            if item.get("size"):
                fields.append({"name": "📏 Taglia", "value": item["size"], "inline": True})
            fields.append({"name": "🆔 ID", "value": item.get("id", "N/D"), "inline": True})
            
            embed = {
                "embeds": [{
                    "title": f"{emoji} {item.get('title', 'Tuta Calcio')[:100]}",
                    "description": "\n".join(desc_parts),
                    "url": item.get("url", ""),
                    "color": color,
                    "fields": fields,
                    "thumbnail": {"url": item.get("photo", "")} if item.get("photo") else None,
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
    """Bot con filtri intelligenti per tute calcio"""
    
    def __init__(self):
        self.config = CONFIG
        self.deal_manager = DealManager(CONFIG["notified_deals_file"])
        self.scraper = VintedScraper()
        self.stats = {
            'timestamp': datetime.now().isoformat(),
            'items_found': 0,
            'items_filtered': 0,
            'new_deals': 0,
            'notifications_sent': 0,
            'filtri': {
                'squadra_sbagliata': 0,
                'non_completa': 0,
                'con_difetti': 0
            }
        }
    
    def run(self):
        """Esegue singolo controllo"""
        print("\n" + "="*60)
        print("🔥 VINTED DEAL FINDER - TUTE CALCIO FILTRATE")
        print("="*60)
        print(f"⏰ {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"🔍 Ricerca: '{self.config['search_query']}'")
        print(f"💰 Prezzo: €{self.config['min_price']}-€{self.config['max_price']}")
        print(f"⚽ Squadre: {len(SQUADRE_ACCETTATE)} squadre monitorate")
        
        if not self.config['discord_webhook_url']:
            print("⚠️ WARNING: Discord webhook non configurato!")
        
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
            # Filtra e processa
            filtered_items = self._filter_items(items)
            
            if filtered_items:
                new_deals = self._process_deals(filtered_items)
                self.stats['new_deals'] = new_deals
                
                if new_deals == 0:
                    print("\n✨ Nessun nuovo deal (già notificati)")
            else:
                print("\n❌ Nessun articolo ha superato i filtri")
        
        self._print_stats()
        self._save_stats()
        
        print("\n✅ Controllo completato!")
        print("="*60)
    
    def _filter_items(self, items: List[Dict]) -> List[Dict]:
        """Filtra articoli secondo criteri"""
        print(f"\n🔍 Applicazione filtri a {len(items)} articoli...")
        
        filtered = []
        
        for item in items:
            result = ItemFilter.filtra_articolo(item)
            
            if result["valido"]:
                item["squadra"] = result["squadra"]
                filtered.append(item)
                print(f"   ✅ {item['title'][:50]} - {result['squadra']}")
            else:
                # Conta motivi filtro
                if "squadra" in result["motivo"].lower():
                    self.stats['filtri']['squadra_sbagliata'] += 1
                elif "completa" in result["motivo"].lower():
                    self.stats['filtri']['non_completa'] += 1
                elif "difetti" in result["motivo"].lower():
                    self.stats['filtri']['con_difetti'] += 1
        
        self.stats['items_filtered'] = len(filtered)
        
        print(f"\n📊 Filtri applicati:")
        print(f"   ✅ Articoli validi: {len(filtered)}")
        print(f"   ❌ Squadra non in lista: {self.stats['filtri']['squadra_sbagliata']}")
        print(f"   ❌ Non completa: {self.stats['filtri']['non_completa']}")
        print(f"   ❌ Con difetti: {self.stats['filtri']['con_difetti']}")
        
        return filtered
    
    def _process_deals(self, items: List[Dict]) -> int:
        """Processa deal validi"""
        new_deals = 0
        
        for item in items:
            if self.deal_manager.is_new_deal(item["id"]):
                new_deals += 1
                
                print(f"\n🔥 NUOVO DEAL #{new_deals}!")
                print(f"   📦 {item.get('title', 'N/D')[:60]}")
                print(f"   ⚽ {item.get('squadra', 'N/D')}")
                print(f"   💰 €{item.get('price', 'N/A')}")
                print(f"   🔗 {item.get('url', '')}")
                
                if self.config['discord_webhook_url']:
                    if NotificationManager.send_discord(
                        self.config['discord_webhook_url'],
                        item,
                        item.get('squadra')
                    ):
                        print(f"   ✅ Discord notificato")
                        self.stats['notifications_sent'] += 1
                    else:
                        print(f"   ❌ Errore notifica Discord")
                
                self.deal_manager.mark_as_notified(item["id"])
                time.sleep(1)
        
        return new_deals
    
    def _print_stats(self):
        """Stampa statistiche"""
        scraper_stats = self.scraper.get_stats()
        
        print(f"\n📊 Statistiche finali:")
        print(f"   📦 Articoli trovati: {self.stats['items_found']}")
        print(f"   ✅ Passati filtri: {self.stats['items_filtered']}")
        print(f"   🔥 Nuovi deal: {self.stats['new_deals']}")
        print(f"   📨 Notifiche inviate: {self.stats['notifications_sent']}")
        print(f"   🌐 Success rate: {scraper_stats['success_rate']}%")
    
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
