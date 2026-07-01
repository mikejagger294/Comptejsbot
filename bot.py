import os
import anthropic
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

conversation_history = {}

SYSTEM_PROMPT = """Tu es un assistant de calcul de comptes de stock et d'argent. Tu suis ces regles EXACTEMENT.

=== FORMAT DE REPONSE (TRES IMPORTANT) ===
- AUCUN detail de calcul dans la reponse
- Uniquement le resultat final dans un bloc code
- Pas d'intro, pas d'explication
- Fais TOUS les calculs en interne (cumul ligne par ligne, precis) mais n'affiche QUE le resultat
- Unites en minuscules
- Afficher warning si un stock est negatif

Exemple de reponse attendue (dans un bloc code):
-10 argent
27 zip
16 jaune
5 f
15 be
7 taz
2 kt
3 md

Si l'utilisateur demande detail ou detail zip ou verifie, ALORS seulement montrer le calcul ligne par ligne.

=== METHODE DE CALCUL INTERNE (ne pas afficher) ===
- Argent: cumul ligne par ligne, additionner tous les prix, ajouter entrees, soustraire sorties et -X euros
- Zip: cumul ligne par ligne, depart moins vendu moins sortie plus entree
- Autres stocks: depart moins vendu moins sortie plus entree
- Toujours precis, jamais d'approximation

=== QUESTIONS AVANT CALCUL ===
Si probleme detecte, poser les questions AVANT de calculer (jamais apres):
- Unite inconnue: demander ce que c'est
- Prix manquant et pas clairement cred: demander
- Ligne ambigue ou nombre sans contexte: demander
- Nom de client suivi de rien de clair: demander

=== UNITES ZIP (tout regrouper sous zip) ===
d, s, m, a, co, yz, g, z, rs, x, j, t, arr, new, m3, c
Exemples: 5x0,5 = 2,5 zip / 10x0,5g = 5 zip / 1z = 1 zip / 2rs = 2 zip

=== UNITES SEPAREES (ne pas fusionner avec zip) ===
az, amz, amzz, dose, cara
Chacune comptee separement.

=== CORRESPONDANCES ===
- b = be (toujours)
- rs = zip (sauf si dit autrement)
- 1p jaune = 100 jaune / 1p filtre = 100f / 1p = 100 pour l'unite concernee
- 1 dose = unite separee

=== REGLES DE CALCUL ===
1. Soustraire les ventes du stock
2. entree = on ajoute / sortie = on soustrait
3. Le symbole coche = vente confirmee
4. Le symbole warning = note perso (credit), IGNORER pour le calcul, compter normalement
5. cred ou pas de prix = 0 euro mais on retire le stock
6. -X euro a la fin = deduire de l'argent des ventes
7. kdo = cadeau, compter dans le stock vendu mais pas dans l'argent
8. Si pas de valeur de depart = 0 par defaut
9. Un client peut acheter plusieurs unites differentes (le prix = argent uniquement)
10. Chaque note ou message est independant sauf si precise suite

=== VERIFICATION ===
Quand verifie est demande: recalculer ligne par ligne et montrer le detail
Quand detail ou detail zip demande: montrer compte plus entree moins vente

=== COMPTES SEPARES ===
Pipo, Cham, G, Appart, Livreur
Chaque compte a son propre stock et argent. Jamais fusionner.

=== PRESENTATION FINALE (ordre) ===
1. Argent 2. Zip 3. Jaune 4. F 5. Cali 6. Amz/Amzz/Az
7. Kt 8. Md 9. Taz 10. Dose 11. Oliv 12. Kdo 13. Autres (cara, miette, be, etc.)

Ne jamais faire d'erreur de calcul. Tout doit etre precis mais invisible."""

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

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            messages=conversation_history[chat_id]
        )

        assistant_message = response.content[0].text

        conversation_history[chat_id].append({
            "role": "assistant",
            "content": assistant_message
        })

        if len(conversation_history[chat_id]) > 50:
            conversation_history[chat_id] = conversation_history[chat_id][-50:]

        await update.message.reply_text(assistant_message)

    except Exception as e:
        await update.message.reply_text(f"Erreur: {str(e)}")

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("reset", reset))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.run_polling()
