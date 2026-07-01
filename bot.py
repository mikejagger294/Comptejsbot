import os
import io
import contextlib
import anthropic
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

conversation_history = {}

SYSTEM_PROMPT = """Tu es un assistant de calcul de comptes de stock et d'argent. Tu suis ces regles EXACTEMENT.

=== OUTIL PYTHON OBLIGATOIRE ===
Pour TOUT calcul, tu DOIS utiliser l'outil python_calc. Ne calcule JAMAIS de tete.
Ecris le code Python qui calcule chaque categorie (argent cumul, zip, jaune, etc.) et affiche les resultats avec print.
Utilise le resultat de l'outil pour construire ta reponse finale.

=== FORMAT DE REPONSE ===
- AUCUN detail de calcul dans la reponse finale
- Uniquement le resultat final dans un bloc code
- Pas d'intro, pas d'explication
- Unites en minuscules
- Afficher warning si un stock est negatif

Exemple de reponse finale (bloc code):
390 argent
27 zip
8 jaune

Si l'utilisateur demande detail, verifie ou detail zip, montrer le calcul ligne par ligne (toujours calcule via python_calc).

=== QUESTIONS AVANT CALCUL ===
Si probleme detecte, poser les questions AVANT de calculer (jamais apres):
- Unite inconnue
- Prix manquant et pas clairement cred
- Ligne ambigue ou nombre sans contexte

=== UNITES ZIP (tout regrouper) ===
d, s, m, a, co, yz, g, z, rs, x, j, t, arr, new, m3, c
5x0,5 = 2,5 zip / 10x0,5g = 5 zip / 1z = 1 zip / 2rs = 2 zip

=== UNITES SEPAREES ===
az, amz, amzz, dose, cara

=== CORRESPONDANCES ===
- b = be
- rs = zip
- 1p jaune = 100 jaune / 1p filtre = 100f
- 1 dose = unite separee

=== REGLES ===
1. entree = ajoute / sortie = soustrait
2. coche = vente confirmee
3. warning = note perso, IGNORER, compter normalement
4. cred ou pas de prix = 0 euro mais retirer le stock
5. -X euro = deduire de l'argent
6. kdo = stock vendu mais pas d'argent
7. Pas de valeur de depart = 0
8. Un client peut acheter plusieurs unites (prix = argent uniquement)
9. Chaque message independant sauf si precise

=== COMPTES SEPARES ===
Pipo, Cham, G, Appart, Livreur

=== ORDRE FINAL ===
Argent, Zip, Jaune, F, Cali, Amz/Amzz/Az, Kt, Md, Taz, Dose, Oliv, Kdo, Autres"""

TOOLS = [
    {
        "name": "python_calc",
        "description": "Execute du code Python pour faire des calculs precis. Utilise print() pour afficher les resultats.",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Le code Python a executer"
                }
            },
            "required": ["code"]
        }
    }
]

def run_python(code):
    output = io.StringIO()
    try:
        with contextlib.redirect_stdout(output):
            exec(code, {})
        return output.getvalue()
    except Exception as e:
        return f"Erreur Python: {str(e)}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    conversation_history[chat_id] = []
    await update.message.reply_text("Bot pret")

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    conversation_history[chat_id] = []
    await update.message.reply_text("Conversation reinitialisee")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.message.chat_id
        user_message = update.message.text

        if chat_id not in conversation_history:
            conversation_history[chat_id] = []

        conversation_history[chat_id].append({
            "role": "user",
            "content": user_message
        })

        while True:
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=3000,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=conversation_history[chat_id]
            )

            conversation_history[chat_id].append({
                "role": "assistant",
                "content": response.content
            })

            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = run_python(block.input["code"])
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result
                        })
                conversation_history[chat_id].append({
                    "role": "user",
                    "content": tool_results
                })
            else:
                final_text = ""
                for block in response.content:
                    if block.type == "text":
                        final_text += block.text
                await update.message.reply_text(final_text)
                break

        if len(conversation_history[chat_id]) > 60:
            conversation_history[chat_id] = conversation_history[chat_id][-60:]

    except Exception as e:
        await update.message.reply_text(f"Erreur: {str(e)}")

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("reset", reset))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.run_polling()
