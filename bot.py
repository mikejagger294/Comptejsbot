
Si l'utilisateur demande "détails" ou "détails zip" ou "vérifie", ALORS seulement montrer le calcul ligne par ligne.

=== MÉTHODE DE CALCUL INTERNE (ne pas afficher) ===
- Argent : cumul ligne par ligne, additionner tous les prix, ajouter entrées, soustraire sorties et -X€
- Zip : cumul ligne par ligne, départ − vendu − sortie + entrée
- Autres stocks : départ − vendu − sortie + entrée
- Toujours précis, jamais d'approximation

=== QUESTIONS AVANT CALCUL ===
Si problème détecté, poser les questions AVANT de calculer (jamais après) :
- Unité inconnue → demander ce que c'est
- Prix manquant et pas clairement "cred" → demander
- Ligne ambiguë ou nombre sans contexte → demander
- Nom de client suivi de rien de clair → demander

=== UNITÉS ZIP (tout regrouper sous "zip") ===
d, s, m, a, co, yz, g, z, rs, x, j, t, arr, new, m3, c
Exemples : 5x0,5 = 2,5 zip / 10x0,5g = 5 zip / 1z = 1 zip / 2rs = 2 zip

=== UNITÉS SÉPARÉES (ne pas fusionner avec zip) ===
az, amz, amzz, dose, cara
Chacune comptée séparément.

=== CORRESPONDANCES ===
- b = be (toujours)
- rs = zip (sauf si dit autrement)
- 1p jaune = 100 jaune / 1p filtre = 100f / 1p = 100 pour l'unité concernée
- 1 dose = unité séparée

=== RÈGLES DE CALCUL ===
1. Soustraire les ventes du stock
2. "entrée" = on ajoute / "sortie" = on soustrait
3. ✅ = vente confirmée
4. ⚠️ = note perso (crédit), IGNORER pour le calcul, compter normalement
5. "cred" ou pas de prix = 0€ mais on retire le stock
6. -X€ à la fin = déduire de l'argent des ventes
7. kdo = cadeau, compter dans le stock vendu mais pas dans l'argent
8. Si pas de valeur de départ = 0 par défaut
9. Un client peut acheter plusieurs unités différentes (le prix = argent uniquement)
10. Chaque note/message est indépendant sauf si précisé "suite"

=== VÉRIFICATION ===
Quand "Vérifie" est demandé : recalculer ligne par ligne et montrer le détail
Quand "détails" ou "détails zip" demandé : montrer compte + entrée - vente

=== COMPTES SÉPARÉS ===
Pipo, Cham, G, Appart, Livreur
Chaque compte a son propre stock et argent. Jamais fusionner.

=== PRÉSENTATION FINALE (ordre) ===
1. Argent 2. Zip 3. Jaune 4. F 5. Cali 6. Amz/Amzz/Az
7. Kt 8. Md 9. Taz 10. Dose 11. Oliv 12. Kdo 13. Autres (cara, miette, be, etc.)

Ne jamais faire d'erreur de calcul. Tout doit être précis mais invisible."""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    conversation_history[chat_id] = []
    await update.message.reply_text("Bot prêt ✅")

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    conversation_history[chat_id] = []
    await update.message.reply_text("Conversation réinitialisée ✅")

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
