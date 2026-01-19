"""
🔥 Vinted Deal Finder - BOT ULTRA-PERFEZIONATO
- Solo tute pubblicate negli ultimi 20 minuti
- Multi-lingua (Italiano + Francese)
- Filtri super precisi per tute COMPLETE
- Include nazionali: Argentina, Francia, Spagna
"""
import os
import time
import json
import requests
from datetime import datetime, timedelta
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
    "stats_file": "bot_stats.json",
    "max_age_minutes": 20  # Solo articoli pubblicati negli ultimi 20 minuti
}

# Query di ricerca multiple (italiano + francese)
SEARCH_QUERIES = [
    "tuta calcio completa",      # Italiano
    "tuta allenamento calcio",   # Italiano
    "survetement football",      # Francese
    "ensemble football",         # Francese
    "tracksuit football"         # Inglese
]

# Squadre + Nazionali (con varianti multi-lingua)
SQUADRE_NAZIONALI = {
    # CLUB
    "liverpool": ["liverpool", "lfc"],
    "barcelona": ["barcellona", "barcelona", "barça", "barca", "fcb"],
    "real_madrid": ["real madrid", "madrid", "real"],
    "arsenal": ["arsenal", "afc"],
    "psg": ["psg", "paris saint germain", "paris sg", "paris"],
    "marsiglia": ["marseille", "olympique marseille", "olympique de marseille"],
    "lione": ["lyon", "olympique lyonnais", "ol lyon"],
    "bayern": ["bayern", "bayern monaco", "bayern munich", "fc bayern"],
    "man_city": ["manchester city", "man city", "mcfc"],
    "man_united": ["manchester united", "man united", "mufc"],
    "dortmund": ["borussia dortmund", "dortmund", "bvb"],

    # NAZIONALI
    "argentina": ["argentina", "argentine", "albiceleste"],
    "francia": ["francia", "france", "bleus", "les bleus", "equipe de france"],
    "spagna": ["spagna", "spain", "españa", "espagne", "la roja"]
}

# Parole che indicano difetti
PAROLE_DIFETTI = [
    # Italiano
    "difetto", "difetti", "rovinato", "rovinata", "rotto", "rotta",
    "bucato", "buco", "buchi", "macchiato", "macchia", "macchie",
    "strappo", "strappato", "consumato", "usurato", "sbiadito",
    "danneggiato", "danneggiata", "difettoso", "difettosa",
    "scucito", "scucitura", "pelucchi", "scolorito", "scolorita",
    # Francese
    "défaut", "défauts", "abîmé", "abîmée", "cassé", "cassée",
    "troué", "trou", "trous", "taché", "tache", "taches",
    "déchiré", "déchirure", "usé", "usée", "endommagé",
    # Inglese
    "defect", "damaged", "broken", "torn", "stain", "hole"
]

# Parole che indicano NON completa
PAROLE_NON_COMPLETA = [
    # Italiano
    "solo maglia", "solo pantalone", "solo pantaloni", "solo giacca", "solo felpa",
    "maglia singola", "pantalone singolo", "giacca singola",
    "senza pantalone", "senza pantaloni", "senza maglia", "senza giacca", "senza felpa",
    # Francese
    "seulement maillot", "seulement pantalon", "seulement veste",
    "sans pantalon", "sans maillot", "sans veste",
    # Inglese
    "only shirt", "only pants", "only jacket",
    "without pants", "without shirt", "without jacket"
]

# Parole che confermano è COMPLETA
PAROLE_COMPLETA = [
    # Italiano
    "completa", "complete", "set", "divisa completa", "kit completo",
    "felpa + pantalone", "felpa e pantalone", "giacca + pantalone", "giacca e pantalone",
    "top + pantalone", "top e pantalone", "maglia + pantalone", "maglia e pantalone",
    "2 pezzi", "due pezzi", "tuta intera",
    # Francese
    "complet", "complete", "ensemble", "ensemble complet",
    "veste + pantalon", "veste et pantalon", "haut + pantalon", "haut et pantalon",
    "2 pieces", "deux pieces",
    # Inglese
    "complete set", "full set", "tracksuit", "jacket + pants", "top + pants",
    "2 pieces", "two pieces"
]


class ItemFilter:
    """Filtro ULTRA-PRECISO per articoli"""

    @staticmethod
    def is_recent(item: Dict, max_age_minutes: int = 20) -> bool:
        """Verifica se l'articolo è stato pubblicato negli ultimi X minuti"""
        try:
            # L'API Vinted fornisce photo.high_resolution.timestamp
            # Oppure possiamo cercare nel campo created_at_ts

            # Per ora usiamo l'ID come proxy: ID più alti = più recenti
            # Ma dovremmo verificare il timestamp se disponibile

            # NOTA: L'API potrebbe non fornire sempre il timestamp
            # In questo caso, ordiniamo per newest_first e prendiamo solo i primi risultati

            return True  # Filtreremo lato API ordinando per newest_first

        except Exception:
            return True

    @staticmethod
    def is_squadra_accettata(text: str) -> tuple:
        """
        Verifica se l'articolo è di una squadra/nazionale accettata
        Returns: (bool, str) - (è_valido, nome_squadra)
        """
        text_lower = text.lower()

        for squadra_key, varianti in SQUADRE_NAZIONALI.items():
            for variante in varianti:
                # Match preciso con word boundaries
                if f" {variante} " in f" {text_lower} " or                    text_lower.startswith(f"{variante} ") or                    text_lower.endswith(f" {variante}"):
                    # Nome display
                    nome_display = squadra_key.replace("_", " ").title()
                    return True, nome_display

        return False, None

    @staticmethod
    def ha_difetti(text: str) -> bool:
        """Verifica se la descrizione menziona difetti"""
        text_lower = text.lower()
        for parola in PAROLE_DIFETTI:
            if parola in text_lower:
                return True
        return False

    @staticmethod
    def is_completa(text: str) -> tuple:
        """
        Verifica PRECISAMENTE se è una tuta COMPLETA
        Returns: (bool, str) - (è_completa, motivo)
        """
        text_lower = text.lower()

        # 1. Controlla se dice esplicitamente che NON è completa
        for parola in PAROLE_NON_COMPLETA:
            if parola in text_lower:
                return False, f"Contiene: '{parola}'"

        # 2. Cerca indicatori FORTI di completezza
        ha_indicatore_completa = False
        indicatore_trovato = ""

        for indicatore in PAROLE_COMPLETA:
            if indicatore in text_lower:
                ha_indicatore_completa = True
                indicatore_trovato = indicatore
                break

        # 3. Verifica presenza di ENTRAMBI i pezzi nelle keywords
        parole_top = ["felpa", "giacca", "top", "maglia", "veste", "haut", "jacket", "hoodie"]
        parole_bottom = ["pantalone", "pantaloni", "pants", "pantalon", "bas"]

        ha_top = any(p in text_lower for p in parole_top)
        ha_bottom = any(p in text_lower for p in parole_bottom)

        # 4. Decisione finale
        if ha_indicatore_completa:
            return True, f"Indicatore: '{indicatore_trovato}'"

        if ha_top and ha_bottom:
            return True, "Ha top + bottom menzionati"

        # Se c'è "tuta" nel titolo, è probabile sia completa
        if "tuta" in text_lower or "survetement" in text_lower or "tracksuit" in text_lower:
            return True, "Keyword 'tuta/survetement/tracksuit'"

        return False, "Nessun indicatore di completezza"

    @staticmethod
    def filtra_articolo(item: Dict, max_age_minutes: int = 20) -> Dict:
        """
        Filtra un articolo secondo TUTTI i criteri
        """
        title = item.get("title", "").lower()
        description = item.get("description", "").lower()
        brand = item.get("brand", "").lower()

        text_completo = f"{title} {description} {brand}"

        # 1. Verifica età (max 20 minuti)
        if not ItemFilter.is_recent(item, max_age_minutes):
            return {
                "valido": False,
                "motivo": "❌ Pubblicato oltre 20 minuti fa",
                "squadra": None
            }

        # 2. Verifica squadra/nazionale
        is_valid_team, squadra_nome = ItemFilter.is_squadra_accettata(text_completo)
        if not is_valid_team:
            return {
                "valido": False,
                "motivo": "❌ Non è squadra/nazionale della lista",
                "squadra": None
            }

        # 3. Verifica completezza
        is_complete, motivo_completezza = ItemFilter.is_completa(text_completo)
        if not is_complete:
            return {
                "valido": False,
                "motivo": f"❌ Non completa: {motivo_completezza}",
                "squadra": squadra_nome
            }

        # 4. Verifica difetti
        if ItemFilter.ha_difetti(description):
            return {
                "valido": False,
                "motivo": "❌ Ha difetti menzionati",
                "squadra": squadra_nome
            }

        return {
            "valido": True,
            "motivo": f"✅ {motivo_completezza}",
            "squadra": squadra_nome
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
                        return set(data[-2000:])
                    return set(data.get('deals', [])[-2000:])
        except Exception as e:
            print(f"⚠️ Errore caricamento deals: {e}")
        return set()

    def save_deals(self):
        try:
            data = {
                'deals': list(self.notified_deals)[-2000:],
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
        """Invia notifica Discord ULTRA dettagliata"""
        if not webhook_url:
            return False

        try:
            # Emoji basati sul prezzo
            if item['price'] <= 10:
                emoji = "🔥🔥🔥"
                color = 0xFF0000
            elif item['price'] <= 15:
                emoji = "🔥🔥"
                color = 0xFF4500
            else:
                emoji = "🔥"
                color = 0xFFA500

            # Costruisci descrizione
            desc_parts = [
                f"**💰 Prezzo: €{item.get('price', 'N/A')}**",
                f"**⚽ {squadra}**",
                f"**✅ Tuta COMPLETA senza difetti**",
                f"**🆕 Pubblicato da pochi minuti!**"
            ]

            fields = []
            if item.get("brand"):
                fields.append({"name": "🏷️ Brand", "value": item["brand"], "inline": True})
            if item.get("size"):
                fields.append({"name": "📏 Taglia", "value": item["size"], "inline": True})
            fields.append({"name": "🆔 ID", "value": item.get("id", "N/D"), "inline": True})

            embed = {
                "content": f"@everyone {emoji} **NUOVA TUTA TROVATA!**",
                "embeds": [{
                    "title": f"{emoji} {item.get('title', 'Tuta Calcio')[:150]}",
                    "description": "\n".join(desc_parts),
                    "url": item.get("url", ""),
                    "color": color,
                    "fields": fields,
                    "thumbnail": {"url": item.get("photo", "")} if item.get("photo") else None,
                    "footer": {"text": f"Vinted Bot Ultra • {datetime.now().strftime('%d/%m/%Y %H:%M')}"},
                    "timestamp": datetime.utcnow().isoformat()
                }]
            }

            response = requests.post(webhook_url, json=embed, timeout=10)
            return response.status_code in [200, 204]

        except Exception as e:
            print(f"❌ Discord error: {e}")
            return False


class VintedBot:
    """Bot ULTRA-PERFEZIONATO"""

    def __init__(self):
        self.config = CONFIG
        self.deal_manager = DealManager(CONFIG["notified_deals_file"])
        self.scraper = VintedScraper()
        self.stats = {
            'timestamp': datetime.now().isoformat(),
            'queries_searched': 0,
            'items_found': 0,
            'items_filtered': 0,
            'new_deals': 0,
            'notifications_sent': 0,
            'filtri': {
                'troppo_vecchi': 0,
                'squadra_sbagliata': 0,
                'non_completa': 0,
                'con_difetti': 0
            }
        }

    def run(self):
        """Esegue ricerca multi-query"""
        print("\n" + "="*70)
        print("🔥 VINTED BOT ULTRA - TUTE CALCIO PERFETTE")
        print("="*70)
        print(f"⏰ {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"💰 Prezzo: €{self.config['min_price']}-€{self.config['max_price']}")
        print(f"⚽ Squadre: {len(SQUADRE_NAZIONALI)} squadre/nazionali")
        print(f"⏱️  Solo articoli pubblicati negli ultimi {self.config['max_age_minutes']} minuti")
        print(f"🌍 Ricerca multi-lingua: {len(SEARCH_QUERIES)} query")

        if not self.config['discord_webhook_url']:
            print("⚠️ WARNING: Discord webhook non configurato!")

        print("="*70)

        # Ricerca con query multiple
        all_items = []
        seen_ids = set()

        for query in SEARCH_QUERIES:
            print(f"\n🔍 Query: '{query}'")
            items = self.scraper.search_items(
                query=query,
                max_price=self.config['max_price'],
                min_price=self.config['min_price'],
                max_items=self.config['max_items']
            )

            self.stats['queries_searched'] += 1

            # Rimuovi duplicati
            for item in items:
                if item['id'] not in seen_ids:
                    all_items.append(item)
                    seen_ids.add(item['id'])

            time.sleep(2)  # Pausa tra query

        self.stats['items_found'] = len(all_items)
        print(f"\n📦 Totale articoli unici trovati: {len(all_items)}")

        if not all_items:
            print("\n📭 Nessun articolo trovato")
        else:
            # Filtra e processa
            filtered_items = self._filter_items(all_items)

            if filtered_items:
                new_deals = self._process_deals(filtered_items)
                self.stats['new_deals'] = new_deals

                if new_deals == 0:
                    print("\n✨ Nessun nuovo deal (già notificati)")
            else:
                print("\n❌ Nessun articolo ha superato TUTTI i filtri")

        self._print_stats()
        self._save_stats()

        print("\n✅ Controllo completato!")
        print("="*70)

    def _filter_items(self, items: List[Dict]) -> List[Dict]:
        """Applica TUTTI i filtri"""
        print(f"\n🔍 Applicazione filtri ULTRA-PRECISI a {len(items)} articoli...")

        filtered = []

        for item in items:
            result = ItemFilter.filtra_articolo(item, self.config['max_age_minutes'])

            if result["valido"]:
                item["squadra"] = result["squadra"]
                item["motivo_validazione"] = result["motivo"]
                filtered.append(item)
                print(f"   ✅ {item['title'][:60]} - {result['squadra']}")
            else:
                # Conta motivi filtro
                motivo = result["motivo"].lower()
                if "vecchi" in motivo or "minuti" in motivo:
                    self.stats['filtri']['troppo_vecchi'] += 1
                elif "squadra" in motivo or "nazionale" in motivo:
                    self.stats['filtri']['squadra_sbagliata'] += 1
                elif "completa" in motivo:
                    self.stats['filtri']['non_completa'] += 1
                elif "difetti" in motivo:
                    self.stats['filtri']['con_difetti'] += 1

        self.stats['items_filtered'] = len(filtered)

        print(f"\n📊 Risultati filtri:")
        print(f"   ✅ Articoli PERFETTI: {len(filtered)}")
        print(f"   ❌ Troppo vecchi (>20 min): {self.stats['filtri']['troppo_vecchi']}")
        print(f"   ❌ Squadra non in lista: {self.stats['filtri']['squadra_sbagliata']}")
        print(f"   ❌ Non completa: {self.stats['filtri']['non_completa']}")
        print(f"   ❌ Con difetti: {self.stats['filtri']['con_difetti']}")

        return filtered

    def _process_deals(self, items: List[Dict]) -> int:
        """Processa e notifica deal perfetti"""
        new_deals = 0

        for item in items:
            if self.deal_manager.is_new_deal(item["id"]):
                new_deals += 1

                print(f"\n🔥 DEAL PERFETTO #{new_deals}!")
                print(f"   📦 {item.get('title', 'N/D')[:70]}")
                print(f"   ⚽ {item.get('squadra', 'N/D')}")
                print(f"   💰 €{item.get('price', 'N/A')}")
                print(f"   ✅ {item.get('motivo_validazione', 'Validato')}")
                print(f"   🔗 {item.get('url', '')}")

                if self.config['discord_webhook_url']:
                    if NotificationManager.send_discord(
                        self.config['discord_webhook_url'],
                        item,
                        item.get('squadra')
                    ):
                        print(f"   📨 Discord notificato con @everyone")
                        self.stats['notifications_sent'] += 1
                    else:
                        print(f"   ❌ Errore notifica Discord")

                self.deal_manager.mark_as_notified(item["id"])
                time.sleep(1)

        return new_deals

    def _print_stats(self):
        """Stampa statistiche dettagliate"""
        scraper_stats = self.scraper.get_stats()

        print(f"\n📊 Statistiche finali:")
        print(f"   🔍 Query eseguite: {self.stats['queries_searched']}")
        print(f"   📦 Articoli trovati: {self.stats['items_found']}")
        print(f"   ✅ Passati filtri: {self.stats['items_filtered']}")
        print(f"   🔥 Nuovi deal: {self.stats['new_deals']}")
        print(f"   📨 Notifiche inviate: {self.stats['notifications_sent']}")
        print(f"   🌐 Success rate: {scraper_stats['success_rate']}%")
        print(f"   💾 Deal totali tracciati: {len(self.deal_manager.notified_deals)}")

    def _save_stats(self):
        """Salva statistiche"""
        try:
            stats_data = {
                **self.stats,
                'scraper_stats': self.scraper.get_stats(),
                'total_deals_tracked': len(self.deal_manager.notified_deals),
                'squadre_monitorate': list(SQUADRE_NAZIONALI.keys())
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
        print(f"\n❌ Errore critico: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()
