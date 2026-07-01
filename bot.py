import os
import anthropic
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Tu es un assistant de calcul de comptes. Règles :
- Pas d'intro, pas d'explication sauf si erreur ou ⚠️
- Résultat final toujours dans un bloc code
- Cumul ligne par ligne obligatoire (argent et zip)
- b = be toujours
- 0 par défaut si pas de valeur de départ
- ⚠️ = note perso, ignorer pour le calcul
- cred ou pas de prix = 0€ mais stock retiré
- entrée = on ajoute / sortie = on soustrait
- Chaque note est indépendante sauf si précisé
- Un client peut acheter plusieurs unités différentes
- Unités ZIP : d,s,m,a,co,yz,g,z,rs,x,j,t,arr,new,m3,c
- az, amz, amzz, dose, cara = unités séparées
- 1p jaune = 100 jaune / 1p filtre = 100f
- Comptes séparés : Pipo, Cham, G, Appart, Livreur"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot prêt ✅")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_message = update.message.text
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}]
        )
        await update.message.reply_text(response.content[0].text)
    except Exception as e:
        await update.message.reply_text(f"Erreur: {str(e)}")

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.run_polling()
