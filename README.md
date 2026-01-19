# 🔥 Vinted Deal Finder - GitHub Actions

Bot automatico che trova deal su Vinted e ti notifica su Discord. Ottimizzato per GitHub Actions (100% gratuito, sempre attivo).

## ✨ Caratteristiche

- 🔍 Ricerca automatica ogni 5 minuti
- 📱 Notifiche Discord con rich embeds
- 💰 Filtri prezzo personalizzabili
- 🚀 100% gratuito su GitHub Actions
- 💾 Tracking automatico deal già notificati
- 📊 Statistiche dettagliate
- 🏷️ **Filtro taglie rigoroso** (solo S, M, L, XL adulto)
- 📸 **Verifica foto con AI** (OpenAI GPT-4o Vision)
- ⚽ **Squadre specifiche** (11 club + 3 nazionali)
- ⏱️ **Solo ultimi 20 minuti** (articoli recenti)

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

### 6. (Opzionale) Abilita Verifica Foto AI

Per attivare la verifica automatica delle foto con AI:

1. Crea account OpenAI: https://platform.openai.com/
2. Genera API Key: https://platform.openai.com/api-keys
3. Aggiungi secret **`OPENAI_API_KEY`** con la tua chiave
4. Il bot verificherà automaticamente:
   - ✅ Tuta completa (felpa + pantalone visibili)
   - ✅ Squadra corretta
   - ✅ Taglia adulto (non bambino)

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
| `DISCORD_WEBHOOK_URL` | - | **Obbligatorio** - URL webhook Discord |
| `OPENAI_API_KEY` | - | Opzionale - Abilita verifica foto AI |
| `SEARCH_QUERY` | `tuta calcio completa` | Cosa cercare |
| `MAX_PRICE` | `20` | Prezzo massimo € |
| `MIN_PRICE` | `1` | Prezzo minimo € |
| `ENABLE_IMAGE_CHECK` | `true` | Attiva/disattiva verifica foto |
| `IMAGE_CHECK_CONFIDENCE` | `70` | Soglia confidenza AI (0-100) |

## 🏷️ Filtro Taglie

Il bot accetta **SOLO** taglie adulto:
- ✅ **Accettate:** S, M, L, XL
- ❌ **Escluse:** 
  - Bambino: XS, 2-3, 3-4, 4-5, 104cm, 110cm, etc.
  - Troppo grandi: XXL, XXXL, 2XL, 3XL
  - Parole chiave bambino: enfant, kids, bambino, junior, etc.

## ⚽ Squadre Monitorate

**CLUB (11):**
- Liverpool, Barcelona, Real Madrid, Arsenal
- PSG, Marsiglia, Lione
- Bayern Monaco, Manchester City, Manchester United
- Borussia Dortmund

**NAZIONALI (3):**
- Argentina 🇦🇷
- Spagna 🇪🇸
- Francia 🇫🇷

## 📸 Verifica Foto con AI

Se configurata `OPENAI_API_KEY`, il bot analizza le foto per verificare:

1. **Completezza:** Entrambi i pezzi visibili (felpa + pantalone)
2. **Squadra:** Stemmi, loghi, colori corrispondono
3. **Taglia:** Sembra adulto, non bambino
4. **Confidenza:** Quanto è sicuro (min 70%)

L'articolo viene notificato **SOLO** se passa tutti i controlli.

### Costi AI
- ~$0.01 ogni 10-20 articoli verificati
- Consigliato: budget iniziale $5/mese

## 📱 Notifiche Discord

Esempio notifica:

> **🔥🔥🔥 TUTA CALCIO LIVERPOOL NIKE**
> 
> **💰 Prezzo: €12.50**
> **⚽ Liverpool**
> **✅ Tuta COMPLETA senza difetti**
> **🆕 Pubblicato da pochi minuti!**
> **✅ Foto verificata AI (85%)**
> 
> 🏷️ Brand: Nike
> 📏 Taglia: M
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

**❌ Verifica foto non funziona**
- Controlla OPENAI_API_KEY sia configurata correttamente
- Verifica credito OpenAI disponibile
- Controlla log per errori API
- Riduci IMAGE_CHECK_CONFIDENCE se troppi articoli vengono rifiutati

**❌ "Invalid size" o troppi rifiuti**
- Il filtro taglie è rigoroso (solo S, M, L, XL)
- Verifica che gli articoli abbiano taglia specificata
- Cerca articoli con taglia adulto esplicita

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

Per GitHub Actions servono SOLO questi file:

1. `vinted_scraper.py` - Logica scraping
2. `vinted_bot.py` - Bot principale + ImageAnalyzer
3. `requirements.txt` - Dipendenze (requests, openai)
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
