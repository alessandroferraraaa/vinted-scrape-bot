"""
🔥 Vinted Deal Finder - BOT DEFINITIVO
Ricerca MASSIVA con 20+ query multi-lingua ottimizzate
"""
import os
import time
import json
import re
import requests
from datetime import datetime
from typing import List, Dict
from vinted_scraper import VintedScraper

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# ============================================
# CONFIGURAZIONE
# ============================================

# Costanti ImageAnalyzer
MAX_PHOTOS_PER_ITEM = 3
OPENAI_MODEL = "gpt-4o"
OPENAI_MAX_TOKENS = 300
OPENAI_TEMPERATURE = 0.3

def get_float_env(key: str, default: float) -> float:
    value = os.getenv(key, "")
    if not value or value.strip() == "":
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def get_int_env(key: str, default: int) -> int:
    value = os.getenv(key, "")
    if not value or value.strip() == "":
        return default
    try:
        return int(value)
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
    "max_age_minutes": 20,
    "openai_api_key": os.getenv("OPENAI_API_KEY", "").strip(),
    "enable_image_check": os.getenv("ENABLE_IMAGE_CHECK", "true").lower() == "true",
    "image_check_confidence": get_int_env("IMAGE_CHECK_CONFIDENCE", 70)
}

# ============================================
# QUERY DI RICERCA OTTIMIZZATE (20 query selezionate)
# ============================================
SEARCH_QUERIES = [
    # ITALIANO - Generiche
    "tuta calcio completa",
    "tuta allenamento calcio",
    "tuta rappresentanza calcio",

    # ITALIANO - Brand
    "nike tuta calcio",
    "adidas tuta calcio",

    # FRANCESE - Generiche
    "survetement football complet",
    "ensemble football complet",
    "survetement equipe football",

    # FRANCESE - Brand
    "ensemble football nike",
    "ensemble football adidas",

    # INGLESE - Generiche
    "football tracksuit complete",
    "soccer tracksuit full",
    "training tracksuit football",

    # INGLESE - Specifiche
    "official football tracksuit",
    "team football tracksuit",

    # INGLESE - Brand
    "nike football tracksuit",
    "adidas football tracksuit",

    # COMBO Brand + Specifiche
    "nike academy tracksuit",
    "adidas tiro tracksuit",

    # Ultra specifiche per club
    "barcelona tracksuit",
    "psg tracksuit"
]

# Squadre + Nazionali (SOLO QUESTE)
SQUADRE_NAZIONALI = {
    # CLUB
    "liverpool": ["liverpool", "lfc"],
    "barcelona": ["barcellona", "barcelona", "barça", "barca", "fcb"],
    "real_madrid": ["real madrid", "madrid", "real"],
    "arsenal": ["arsenal", "afc", "gunners"],
    "psg": ["psg", "paris saint germain", "paris sg"],
    "marsiglia": ["marseille", "olympique marseille", "om"],
    "lione": ["lyon", "olympique lyonnais", "ol"],
    "bayern": ["bayern", "bayern monaco", "bayern munich", "fc bayern"],
    "man_city": ["manchester city", "man city", "mcfc", "city"],
    "man_united": ["manchester united", "man united", "mufc", "united"],
    "dortmund": ["borussia dortmund", "dortmund", "bvb"],

    # NAZIONALI
    "argentina": ["argentina", "argentine", "albiceleste", "afa"],
    "francia": ["francia", "france", "bleus", "les bleus", "equipe de france", "fff"],
    "spagna": ["spagna", "spain", "españa", "espagne", "la roja", "rfef"]
}

# Taglie ACCETTATE (solo queste - adulto)
TAGLIE_ACCETTATE = ["s", "m", "l", "xl"]

# Taglie ESCLUSE - bambino
TAGLIE_BAMBINO_NUMERICHE = [
    "2-3", "3-4", "4-5", "5-6", "6-7", "7-8", "8-9", "9-10", 
    "10-11", "11-12", "12-13", "13-14"
]

TAGLIE_BAMBINO_CM = [
    "104", "110", "116", "122", "128", "134", "140", "146", "152", "158", "164"
]

# Taglie troppo piccole/grandi
TAGLIE_FUORI_RANGE = [
    "xs", "xxs", "xxxs", "xxl", "xxxl", "2xl", "3xl"
]

# Parole chiave bambino (multi-lingua)
PAROLE_BAMBINO = [
    "enfant", "kids", "bambino", "bambini", "child", "children", 
    "junior", "jr", "ragazzo", "ragazza", "garcon", "fille", 
    "boy", "girl", "youth", "jeune"
]

# Parole che indicano difetti (multi-lingua)
PAROLE_DIFETTI = [
    "difetto", "difetti", "rovinato", "rovinata", "rotto", "rotta",
    "bucato", "buco", "buchi", "macchiato", "macchia", "macchie",
    "strappo", "strappato", "consumato", "usurato", "sbiadito",
    "danneggiato", "danneggiata", "difettoso", "difettosa",
    "scucito", "scucitura", "pelucchi", "scolorito", "scolorita",
    "défaut", "défauts", "abîmé", "abîmée", "cassé", "cassée",
    "troué", "trou", "trous", "taché", "tache", "taches",
    "déchiré", "déchirure", "usé", "usée", "endommagé",
    "defect", "damaged", "broken", "torn", "stain", "hole"
]

# Parole che indicano NON completa
PAROLE_NON_COMPLETA = [
    "solo maglia", "solo pantalone", "solo pantaloni", "solo giacca", "solo felpa",
    "maglia singola", "pantalone singolo", "giacca singola",
    "senza pantalone", "senza pantaloni", "senza maglia", "senza giacca", "senza felpa",
    "seulement maillot", "seulement pantalon", "seulement veste",
    "sans pantalon", "sans maillot", "sans veste",
    "only shirt", "only pants", "only jacket", "only top",
    "without pants", "without shirt", "without jacket"
]

# Parole che confermano COMPLETA
PAROLE_COMPLETA = [
    # Italiano
    "completa", "complete", "set", "divisa completa", "kit completo",
    "felpa + pantalone", "felpa e pantalone", "giacca + pantalone", "giacca e pantalone",
    "top + pantalone", "top e pantalone", "maglia + pantalone", "maglia e pantalone",
    "2 pezzi", "due pezzi", "tuta intera", "set completo",
    # Francese
    "complet", "complete", "ensemble", "ensemble complet",
    "veste + pantalon", "veste et pantalon", "haut + pantalon", "haut et pantalon",
    "2 pieces", "deux pieces", "2 pièces", "deux pièces",
    # Inglese
    "complete set", "full set", "tracksuit", "jacket + pants", "top + pants",
    "2 pieces", "two pieces", "full tracksuit", "complete tracksuit"
]


class ImageAnalyzer:
    """Analizzatore foto con OpenAI GPT-4o Vision"""
    
    def __init__(self, api_key: str = ""):
        self.enabled = False
        self.client = None
        
        if api_key and OPENAI_AVAILABLE:
            try:
                self.client = openai.OpenAI(api_key=api_key)
                self.enabled = True
                print("✅ ImageAnalyzer abilitato (OpenAI Vision)")
            except Exception as e:
                print(f"⚠️ Errore inizializzazione OpenAI: {e}")
        elif api_key and not OPENAI_AVAILABLE:
            print("⚠️ OpenAI non installato - pip install openai>=1.0.0")
        else:
            print("⚠️ OPENAI_API_KEY non configurata - verifica foto disabilitata")
    
    def verifica_tuta(self, photo_urls: List[str], squadra_attesa: str, confidence_threshold: int = 70) -> Dict:
        """
        Analizza le foto per verificare:
        1. È una tuta COMPLETA (felpa/giacca + pantalone visibili)?
        2. È della squadra corretta?
        3. È taglia adulto (non bambino)?
        
        Returns:
            {
                "completa": True/False,
                "squadra_corretta": True/False,
                "taglia_adulto": True/False,
                "confidenza": 0-100,
                "note": "descrizione"
            }
        """
        if not self.enabled:
            return {
                "completa": True,
                "squadra_corretta": True,
                "taglia_adulto": True,
                "confidenza": 0,
                "note": "Verifica foto disabilitata"
            }
        
        try:
            # Limita a max N foto per risparmiare token
            urls_to_check = photo_urls[:MAX_PHOTOS_PER_ITEM]
            
            if not urls_to_check:
                return {
                    "completa": False,
                    "squadra_corretta": False,
                    "taglia_adulto": False,
                    "confidenza": 0,
                    "note": "Nessuna foto disponibile"
                }
            
            # Costruisci prompt
            prompt = f"""Analizza queste foto di un articolo Vinted. Devi verificare se è una TUTA DA CALCIO.

Rispondi SOLO in formato JSON con questi campi:
{{
    "completa": true/false,  // TRUE solo se vedi ENTRAMBI: felpa/giacca E pantalone
    "squadra_corretta": true/false,  // TRUE se la tuta è della squadra: {squadra_attesa}
    "taglia_adulto": true/false,  // TRUE se sembra taglia adulto, FALSE se bambino
    "confidenza": 0-100,  // quanto sei sicuro della risposta
    "note": "breve descrizione di cosa vedi"
}}

IMPORTANTE:
- "completa" = TRUE solo se nelle foto si vedono ENTRAMBI i pezzi (sopra + sotto)
- Cerca stemmi, loghi, colori della squadra per verificare
- Se vedi solo la maglia o solo il pantalone = FALSE
- Se non riesci a determinare la squadra = FALSE"""
            
            # Prepara messaggi per API
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt}
                    ]
                }
            ]
            
            # Aggiungi immagini
            for url in urls_to_check:
                messages[0]["content"].append({
                    "type": "image_url",
                    "image_url": {"url": url}
                })
            
            # Chiamata API OpenAI
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                max_tokens=OPENAI_MAX_TOKENS,
                temperature=OPENAI_TEMPERATURE
            )
            
            # Parse risposta
            content = response.choices[0].message.content
            
            # Estrai JSON dalla risposta (cerca il primo oggetto JSON valido)
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content)
            if json_match:
                result = json.loads(json_match.group())
                
                # Valida campi
                required_fields = ["completa", "squadra_corretta", "taglia_adulto", "confidenza", "note"]
                if all(field in result for field in required_fields):
                    # Verifica soglia confidenza
                    if result["confidenza"] < confidence_threshold:
                        result["completa"] = False
                        result["note"] = f"Confidenza troppo bassa ({result['confidenza']}%)"
                    
                    return result
            
            # Se non riesce a parsare
            return {
                "completa": False,
                "squadra_corretta": False,
                "taglia_adulto": False,
                "confidenza": 0,
                "note": "Errore parsing risposta AI"
            }
            
        except Exception as e:
            print(f"⚠️ Errore verifica foto: {e}")
            return {
                "completa": False,
                "squadra_corretta": False,
                "taglia_adulto": False,
                "confidenza": 0,
                "note": f"Errore API: {str(e)[:100]}"
            }


class ItemFilter:
    """Filtro ULTRA-PRECISO"""

    @staticmethod
    def is_taglia_valida(size: str, text: str) -> tuple:
        """
        Verifica che la taglia sia adulto (S, M, L, XL) e NON bambino
        Returns: (valido: bool, motivo: str)
        """
        if not size:
            return False, "Taglia non specificata"
        
        size_lower = size.lower().strip()
        text_lower = text.lower()
        
        # 1. Verifica parole chiave bambino nel testo
        for parola in PAROLE_BAMBINO:
            if parola in text_lower:
                return False, f"Contiene parola bambino: '{parola}'"
        
        # 2. Verifica taglie bambino numeriche
        for taglia in TAGLIE_BAMBINO_NUMERICHE:
            if taglia in size_lower or taglia in text_lower:
                return False, f"Taglia bambino numerica: {taglia}"
        
        # 3. Verifica taglie bambino in cm
        for taglia in TAGLIE_BAMBINO_CM:
            if taglia in size_lower or f"{taglia}cm" in text_lower or f"{taglia} cm" in text_lower:
                return False, f"Taglia bambino cm: {taglia}"
        
        # 4. Verifica taglie fuori range (XS, XXL, etc.)
        for taglia in TAGLIE_FUORI_RANGE:
            if size_lower == taglia or f" {taglia} " in f" {text_lower} ":
                return False, f"Taglia fuori range: {taglia.upper()}"
        
        # 5. Verifica che sia ESATTAMENTE una delle taglie accettate
        if size_lower not in TAGLIE_ACCETTATE:
            return False, f"Taglia non valida: {size} (solo S, M, L, XL)"
        
        return True, f"Taglia valida: {size.upper()}"

    @staticmethod
    def is_squadra_accettata(text: str) -> tuple:
        """Match PRECISO con word boundaries"""
        text_lower = text.lower()

        for squadra_key, varianti in SQUADRE_NAZIONALI.items():
            for variante in varianti:
                # Cerca con spazi per evitare false match
                pattern = f" {variante} "
                text_padded = f" {text_lower} "

                if pattern in text_padded or                    text_lower.startswith(f"{variante} ") or                    text_lower.endswith(f" {variante}"):
                    nome_display = squadra_key.replace("_", " ").title()
                    return True, nome_display

        return False, None

    @staticmethod
    def ha_difetti(text: str) -> bool:
        text_lower = text.lower()
        for parola in PAROLE_DIFETTI:
            if parola in text_lower:
                return True
        return False

    @staticmethod
    def is_completa(text: str) -> tuple:
        text_lower = text.lower()

        # 1. Escludi se dice NON completa
        for parola in PAROLE_NON_COMPLETA:
            if parola in text_lower:
                return False, f"Contiene: '{parola}'"

        # 2. Cerca indicatori FORTI
        for indicatore in PAROLE_COMPLETA:
            if indicatore in text_lower:
                return True, f"Indicatore: '{indicatore}'"

        # 3. Verifica TOP + BOTTOM
        parole_top = ["felpa", "giacca", "top", "maglia", "veste", "haut", "jacket", "hoodie", "sweat"]
        parole_bottom = ["pantalone", "pantaloni", "pants", "pantalon", "bas", "jogger"]

        ha_top = any(p in text_lower for p in parole_top)
        ha_bottom = any(p in text_lower for p in parole_bottom)

        if ha_top and ha_bottom:
            return True, "Ha top + bottom"

        # 4. Keywords tuta
        if "tuta" in text_lower or "survetement" in text_lower or "tracksuit" in text_lower or "ensemble" in text_lower:
            return True, "Keyword tuta"

        return False, "Nessun indicatore"

    @staticmethod
    def filtra_articolo(item: Dict, max_age_minutes: int = 20) -> Dict:
        title = item.get("title", "").lower()
        description = item.get("description", "").lower()
        brand = item.get("brand", "").lower()
        size = item.get("size", "")

        text_completo = f"{title} {description} {brand}"

        # 1. Verifica squadra/nazionale
        is_valid_team, squadra_nome = ItemFilter.is_squadra_accettata(text_completo)
        if not is_valid_team:
            return {
                "valido": False,
                "motivo": "❌ Non è squadra/nazionale",
                "squadra": None
            }

        # 2. Verifica completezza
        is_complete, motivo_completezza = ItemFilter.is_completa(text_completo)
        if not is_complete:
            return {
                "valido": False,
                "motivo": f"❌ Non completa: {motivo_completezza}",
                "squadra": squadra_nome
            }

        # 3. Verifica difetti
        if ItemFilter.ha_difetti(description):
            return {
                "valido": False,
                "motivo": "❌ Ha difetti",
                "squadra": squadra_nome
            }

        # 4. Verifica taglia (NUOVO)
        is_valid_size, motivo_taglia = ItemFilter.is_taglia_valida(size, text_completo)
        if not is_valid_size:
            return {
                "valido": False,
                "motivo": f"❌ Taglia: {motivo_taglia}",
                "squadra": squadra_nome
            }

        return {
            "valido": True,
            "motivo": f"✅ {motivo_completezza}",
            "squadra": squadra_nome,
            "taglia": size
        }


class DealManager:
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
            print(f"⚠️ Errore caricamento: {e}")
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
    @staticmethod
    def send_discord(webhook_url: str, item: Dict, squadra: str) -> bool:
        if not webhook_url:
            return False

        try:
            if item['price'] <= 10:
                emoji = "🔥🔥🔥"
                color = 0xFF0000
            elif item['price'] <= 15:
                emoji = "🔥🔥"
                color = 0xFF4500
            else:
                emoji = "🔥"
                color = 0xFFA500

            desc_parts = [
                f"**💰 Prezzo: €{item.get('price', 'N/A')}**",
                f"**⚽ {squadra}**",
                f"**✅ Tuta COMPLETA senza difetti**",
                f"**🆕 Pubblicato da pochi minuti!**"
            ]
            
            # Aggiungi info verifica foto
            verifica_foto = item.get("verifica_foto")
            if verifica_foto and verifica_foto.get("confidenza", 0) > 0:
                desc_parts.append(f"**✅ Foto verificata AI ({verifica_foto['confidenza']}%)**")
            elif verifica_foto is None:
                desc_parts.append(f"**⚠️ Verifica foto disabilitata**")

            fields = []
            if item.get("brand"):
                fields.append({"name": "🏷️ Brand", "value": item["brand"], "inline": True})
            if item.get("size") or item.get("taglia"):
                taglia = item.get("size") or item.get("taglia", "N/D")
                fields.append({"name": "📏 Taglia", "value": taglia.upper(), "inline": True})
            fields.append({"name": "🆔 ID", "value": item.get("id", "N/D"), "inline": True})

            embed = {
                "content": f"@everyone {emoji} **NUOVA TUTA PERFETTA!**",
                "embeds": [{
                    "title": f"{emoji} {item.get('title', 'Tuta')[:150]}",
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
    def __init__(self):
        self.config = CONFIG
        self.deal_manager = DealManager(CONFIG["notified_deals_file"])
        self.scraper = VintedScraper()
        self.image_analyzer = ImageAnalyzer(CONFIG["openai_api_key"]) if CONFIG["enable_image_check"] else None
        self.stats = {
            'timestamp': datetime.now().isoformat(),
            'queries_searched': 0,
            'items_found': 0,
            'items_filtered': 0,
            'new_deals': 0,
            'notifications_sent': 0,
            'filtri': {
                'squadra_sbagliata': 0,
                'non_completa': 0,
                'con_difetti': 0,
                'taglia_invalida': 0,
                'foto_non_valida': 0
            }
        }

    def run(self):
        print("\n" + "="*70)
        print("🔥 VINTED BOT DEFINITIVO - RICERCA MASSIVA")
        print("="*70)
        print(f"⏰ {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"💰 Range: €{self.config['min_price']}-€{self.config['max_price']}")
        print(f"⚽ {len(SQUADRE_NAZIONALI)} squadre/nazionali monitorate")
        print(f"🔍 {len(SEARCH_QUERIES)} query di ricerca")
        print(f"⏱️  Solo ultimi {self.config['max_age_minutes']} minuti")
        
        if self.image_analyzer and self.image_analyzer.enabled:
            print(f"📸 Verifica foto AI: ABILITATA (confidenza min: {self.config['image_check_confidence']}%)")
        else:
            print(f"📸 Verifica foto AI: DISABILITATA")

        if not self.config['discord_webhook_url']:
            print("⚠️ WARNING: Discord webhook non configurato!")

        print("="*70)

        # Ricerca con tutte le query
        all_items = []
        seen_ids = set()

        for i, query in enumerate(SEARCH_QUERIES, 1):
            print(f"\n[{i}/{len(SEARCH_QUERIES)}] 🔍 '{query}'")

            items = self.scraper.search_items(
                query=query,
                max_price=self.config['max_price'],
                min_price=self.config['min_price'],
                max_items=50  # Limita a 50 per query per velocità
            )

            self.stats['queries_searched'] += 1

            # Rimuovi duplicati
            new_items = 0
            for item in items:
                if item['id'] not in seen_ids:
                    all_items.append(item)
                    seen_ids.add(item['id'])
                    new_items += 1

            if new_items > 0:
                print(f"   ➕ {new_items} nuovi articoli")

            time.sleep(1.5)  # Pausa tra query

        self.stats['items_found'] = len(all_items)
        print(f"\n📦 TOTALE articoli unici: {len(all_items)}")

        if not all_items:
            print("\n📭 Nessun articolo trovato")
        else:
            filtered_items = self._filter_items(all_items)

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
        print("="*70)

    def _filter_items(self, items: List[Dict]) -> List[Dict]:
        print(f"\n🔍 Applicazione filtri a {len(items)} articoli...")

        filtered = []

        for item in items:
            result = ItemFilter.filtra_articolo(item, self.config['max_age_minutes'])

            if result["valido"]:
                item["squadra"] = result["squadra"]
                item["motivo_validazione"] = result["motivo"]
                item["taglia"] = result.get("taglia", "")
                
                # Verifica foto con AI (se abilitata)
                if self.image_analyzer and self.image_analyzer.enabled:
                    photo_urls = item.get("photo_urls", [])
                    if not photo_urls and item.get("photo"):
                        photo_urls = [item["photo"]]
                    photo_urls = [url for url in photo_urls if url]  # Rimuovi URL vuoti
                    
                    verifica = self.image_analyzer.verifica_tuta(
                        photo_urls, 
                        result["squadra"],
                        self.config["image_check_confidence"]
                    )
                    
                    item["verifica_foto"] = verifica
                    
                    # Articolo valido SOLO se passa tutti i controlli foto
                    if not (verifica["completa"] and verifica["squadra_corretta"] and verifica["taglia_adulto"]):
                        print(f"   ❌ {item['title'][:60]} - FOTO: {verifica['note']}")
                        self.stats['filtri']['foto_non_valida'] += 1
                        continue
                    
                    print(f"   ✅ {item['title'][:60]} - {result['squadra']} (AI: {verifica['confidenza']}%)")
                else:
                    item["verifica_foto"] = None
                    print(f"   ✅ {item['title'][:60]} - {result['squadra']}")
                
                filtered.append(item)
            else:
                motivo = result["motivo"].lower()
                if "squadra" in motivo or "nazionale" in motivo:
                    self.stats['filtri']['squadra_sbagliata'] += 1
                elif "completa" in motivo:
                    self.stats['filtri']['non_completa'] += 1
                elif "difetti" in motivo:
                    self.stats['filtri']['con_difetti'] += 1
                elif "taglia" in motivo:
                    self.stats['filtri']['taglia_invalida'] += 1

        self.stats['items_filtered'] = len(filtered)

        print(f"\n📊 Risultati:")
        print(f"   ✅ PERFETTI: {len(filtered)}")
        print(f"   ❌ Squadra errata: {self.stats['filtri']['squadra_sbagliata']}")
        print(f"   ❌ Non completa: {self.stats['filtri']['non_completa']}")
        print(f"   ❌ Con difetti: {self.stats['filtri']['con_difetti']}")
        print(f"   ❌ Taglia invalida: {self.stats['filtri']['taglia_invalida']}")
        if self.image_analyzer and self.image_analyzer.enabled:
            print(f"   ❌ Foto non valida: {self.stats['filtri']['foto_non_valida']}")

        return filtered

    def _process_deals(self, items: List[Dict]) -> int:
        new_deals = 0

        for item in items:
            if self.deal_manager.is_new_deal(item["id"]):
                new_deals += 1

                print(f"\n🔥 DEAL #{new_deals}!")
                print(f"   📦 {item.get('title', 'N/D')[:70]}")
                print(f"   ⚽ {item.get('squadra', 'N/D')}")
                print(f"   💰 €{item.get('price', 'N/A')}")
                print(f"   🔗 {item.get('url', '')}")

                if self.config['discord_webhook_url']:
                    if NotificationManager.send_discord(
                        self.config['discord_webhook_url'],
                        item,
                        item.get('squadra')
                    ):
                        print(f"   📨 Discord ✅")
                        self.stats['notifications_sent'] += 1
                    else:
                        print(f"   ❌ Discord fallito")

                self.deal_manager.mark_as_notified(item["id"])
                time.sleep(1)

        return new_deals

    def _print_stats(self):
        scraper_stats = self.scraper.get_stats()

        print(f"\n📊 Statistiche:")
        print(f"   🔍 Query: {self.stats['queries_searched']}")
        print(f"   📦 Trovati: {self.stats['items_found']}")
        print(f"   ✅ Validati: {self.stats['items_filtered']}")
        print(f"   🔥 Nuovi: {self.stats['new_deals']}")
        print(f"   📨 Notificati: {self.stats['notifications_sent']}")
        print(f"   🌐 Success: {scraper_stats['success_rate']}%")

    def _save_stats(self):
        try:
            stats_data = {
                **self.stats,
                'scraper_stats': self.scraper.get_stats(),
                'total_tracked': len(self.deal_manager.notified_deals)
            }
            with open(self.config['stats_file'], 'w') as f:
                json.dump(stats_data, f, indent=2)
        except Exception as e:
            print(f"⚠️ Errore stats: {e}")


def main():
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
