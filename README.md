# 🔥 Vinted Deal Finder - GitHub Actions

Bot automatico che trova deal su Vinted e ti notifica su Discord. Ottimizzato per GitHub Actions (100% gratuito, sempre attivo).

## ✨ Caratteristiche

- 🔍 Ricerca automatica ogni 5 minuti
- 📱 Notifiche Discord con rich embeds
- 💰 Filtri prezzo personalizzabili
- 🚀 100% gratuito su GitHub Actions
- 💾 Tracking automatico deal già notificati
- 📊 Statistiche dettagliate

## 🚀 Setup (5 minuti)

### 1. Crea Discord Webhook

1. Discord → Server → Canale
2. Impostazioni → Integrazioni → Webhook
3. Nuovo Webhook → Copia URL
4. URL sarà tipo: `https://discord.com/api/webhooks/123456789/abc...`

### 2. Crea Repository

1. Vai su https://github.com/new
2. Nome: `vinted-deal-finder`
3. Pubblico o Privato
4. Create repository

### 3. Upload Files

Nel repository:
- Click "Add file" → "Upload files"
- Trascina questi 4 file:
  - `vinted_scraper.py`
  - `vinted_bot.py`
  - `requirements.txt`
  - `README.md`
- Commit changes

### 4. Crea Workflow

1. "Add file" → "Create new file"
2. Nome: `.github/workflows/vinted-bot.yml`
3. Copia il contenuto dal file workflow qui sotto
4. Commit new file

### 5. Configura Secret

1. Settings → Secrets and variables → Actions
2. New repository secret
3. **Name:** `DISCORD_WEBHOOK_URL`
4. **Value:** (il tuo webhook)
5. Add secret

### ✅ Fatto!

Il bot parte automaticamente ogni 5 minuti!

## 🎯 Test Immediato

1. Tab Actions
2. "Vinted Deal Finder" → Run workflow
3. Aspetta 1 minuto
4. Controlla i log
5. Verifica Discord!

## ⚙️ Personalizzazione

Aggiungi altri secrets per personalizzare:

| Secret | Default | Descrizione |
|--------|---------|-------------|
| `SEARCH_QUERY` | `tuta calcio` | Cosa cercare |
| `MAX_PRICE` | `20` | Prezzo massimo € |
| `MIN_PRICE` | `1` | Prezzo minimo € |

## 🔑 Configurazione Verifica Foto (GRATIS con Gemini!)

La verifica foto usa **Google Gemini** che è **GRATUITO** (60 richieste/minuto).

### Ottenere API Key Gemini (gratis):
1. Vai su https://makersuite.google.com/app/apikey
2. Clicca "Create API Key"
3. Copia la chiave

### Configurazione:
| Variabile | Obbligatoria | Valore | Descrizione |
|-----------|-------------|--------|-------------|
| `GEMINI_API_KEY` | ❌ No | `AIza...` | Chiave API Gemini (gratis!) |
| `ENABLE_IMAGE_CHECK` | ❌ No | `true`/`false` | Attiva verifica foto |
| `IMAGE_CHECK_CONFIDENCE` | ❌ No | `70` | Soglia confidenza 0-100 |

### Note:
- Se `GEMINI_API_KEY` non è configurata, il bot funziona comunque senza verifica foto
- Google Gemini è GRATIS fino a 60 richieste/minuto
- Il modello usato è `gemini-1.5-flash` (veloce e gratuito)
- La verifica foto controlla:
  - ✅ Tuta COMPLETA (felpa/giacca + pantalone)
  - ✅ Squadra corretta
  - ✅ Taglia adulto (non bambino)

## 📱 Notifiche Discord

Esempio notifica:

> **🔥🔥🔥 TUTA CALCIO INTER NIKE**
> 
> **💰 Prezzo: €12.50**
> 
> 🆔 ID: 123456789  
> 🔗 [Vedi su Vinted]
> 
> *Vinted Bot • 18/01/2026 23:55*

**Emoji per prezzo:**
- 🔥🔥🔥 = Sotto €10 (ottimo deal!)
- 🔥🔥 = €10-15 (buon deal)
- 🔥 = €15-20 (deal interessante)

## 📊 Monitoraggio

### Visualizza log:
Actions → Ultima esecuzione → find-deals

### File generati:
- `notified_deals.json` - Deal già notificati (ultimi 1000)
- `bot_stats.json` - Statistiche esecuzione

## 🔧 Troubleshooting

**❌ Notifiche non arrivano**
- Verifica webhook sia corretto
- Controlla canale Discord esista
- Test webhook con curl

**❌ "No module named vinted_scraper"**
- Assicurati tutti i file .py siano nella root del repo

**❌ Workflow non parte**
- Verifica file sia in `.github/workflows/vinted-bot.yml`
- Controlla Actions sia abilitato

## 📈 Prestazioni

- **Frequenza:** Ogni 5 minuti (288 check/giorno)
- **Consumo:** ~5 minuti GitHub Actions/giorno
- **Limite gratuito:** 2000 minuti/mese (abbondante!)
- **Costo:** €0.00

## 🎯 Best Practices

✅ Intervallo minimo: 5 minuti  
✅ Query generiche trovano più deal  
✅ Range prezzo ampio (€1-30)  
✅ Monitora log prime ore  

❌ NON usare intervalli <3 minuti  
❌ NON condividere webhook pubblicamente  

## 💡 Consigli Ricerca

**Query efficaci:**
- `tuta calcio` - Specifica
- `scarpe nike` - Brand specifico
- `giacca` - Generica (molti risultati)
- `sneakers jordan` - Modello specifico

**Prezzi:**
- `MAX_PRICE=20` - Budget basso
- `MAX_PRICE=50` - Abbigliamento medio
- `MAX_PRICE=100` - Articoli premium

## 📝 File Necessari

Per GitHub Actions servono SOLO 4 file:

1. `vinted_scraper.py` - Logica scraping
2. `vinted_bot.py` - Bot principale
3. `requirements.txt` - Dipendenze (solo requests)
4. `.github/workflows/vinted-bot.yml` - Workflow Actions

## 🆘 Supporto

Problemi? Controlla:
1. Tutti i file sono nella root del repo?
2. Webhook Discord configurato nei Secrets?
3. Actions abilitato?
4. Workflow file nella cartella corretta?

## 📜 Licenza

MIT - Usa liberamente

---

**🔥 Buona caccia ai deal! 🔥**

*Bot creato per automatizzare la ricerca su Vinted*
