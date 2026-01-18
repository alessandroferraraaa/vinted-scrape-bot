# 🔥 Vinted Deal Finder - Tute da Calcio

Bot automatico che cerca le migliori offerte su tute da calcio su Vinted e ti notifica via Discord o WhatsApp.

## ⚡ Funzionalità

- 🔍 Cerca automaticamente tute da calcio con prezzo max €20
- ⏰ Controllo ogni 5 minuti (configurabile)
- 📱 Notifiche Discord e/o WhatsApp
- 🚀 Funziona su GitHub Actions (gratuito!)
- 💾 Memorizza i deal già notificati

## 🚀 Setup Rapido

### Opzione 1: GitHub Actions (Consigliato - Gratuito e sempre attivo)

1. **Fork questa repo** o crea una nuova repo con questi file

2. **Configura i Secrets** in Settings → Secrets → Actions:
   - `DISCORD_WEBHOOK_URL` - Il tuo webhook Discord

3. **Attiva GitHub Actions** nella tab Actions

4. **Fatto!** Il bot controllerà ogni 5 minuti automaticamente

### Opzione 2: Esecuzione Locale

```bash
# Installa dipendenze
pip install requests

# Imposta variabili d'ambiente (opzionale)
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."

# Esegui
python vinted_deals.py
```

## 📱 Configurare le Notifiche

### Discord (Consigliato - Gratuito)

1. Vai nel tuo server Discord
2. Modifica un canale → Integrazioni → Webhook
3. Crea un nuovo webhook
4. Copia l'URL del webhook
5. Aggiungi come secret `DISCORD_WEBHOOK_URL`

### WhatsApp (Opzionale - via Twilio)

1. Crea account su [Twilio](https://www.twilio.com)
2. Attiva il WhatsApp Sandbox
3. Configura questi secrets:
   - `TWILIO_ACCOUNT_SID`
   - `TWILIO_AUTH_TOKEN`
   - `TWILIO_WHATSAPP_FROM` (es: `whatsapp:+14155238886`)
   - `TWILIO_WHATSAPP_TO` (es: `whatsapp:+39XXXXXXXXXX`)

## ⚙️ Personalizzazione

Modifica `CONFIG` in `vinted_deals.py`:

```python
CONFIG = {
    "search_query": "tuta calcio",  # Cosa cercare
    "max_price": 20,                 # Prezzo massimo
    "min_price": 1,                  # Prezzo minimo
    "check_interval_minutes": 5,     # Intervallo controllo
}
```

## 📁 File

- `vinted_deals.py` - Bot principale (loop continuo)
- `vinted_deals_single.py` - Versione per GitHub Actions (singolo check)
- `requirements.txt` - Dipendenze Python
- `.github/workflows/vinted-deals.yml` - Workflow GitHub Actions
- `notified_deals.json` - Cache dei deal già notificati

## 🔒 Note sulla Privacy

- Non richiede login Vinted
- Non salva credenziali
- Solo ricerca pubblica
- I webhook/token restano nei secrets di GitHub

## 📝 Licenza

MIT - Usa come vuoi!
