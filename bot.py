import os
import requests
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import Update

SPORTRADAR_API_KEY = os.getenv("SPORTRADAR_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

def get_odds_arrow(opening_odds, current_odds):
    if current_odds > opening_odds:
        return "🔼"
    elif current_odds < opening_odds:
        return "🔽"
    else:
        return "➡️"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Tervetuloa TeleBotAlert4-urheilubottiin!\nKokeile komentoa: /ottelut SerieA Brazil 27.07.2025"
    )

async def ottelut(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text("Käytä muotoa: /ottelut <sarja> <maa> <pp.kk.vvvv>\nEsim: /ottelut SerieA Brazil 27.07.2025")
        return

    sarja = context.args[0]
    maa = context.args[1]
    paiva = context.args[2]

    # DEMO: Hardkodattu tournament_id. Lisää mapping oikeisiin sarjoihin!
    tournament_id = "brazil-serie-a-id"

    # Päivämäärän muunto vvvv-kk-pp (esim. 27.07.2025 -> 2025-07-27)
    try:
        day, month, year = paiva.split('.')
        date_iso = f"{year}-{month}-{day}"
    except Exception:
        date_iso = paiva  # fallback jos käyttäjä syötti valmiiksi oikein

    url = f"https://api.sportradar.com/soccer/trial/v4/en/tournaments/{tournament_id}/schedule.json?api_key={SPORTRADAR_API_KEY}"
    resp = requests.get(url)
    if resp.status_code != 200:
        await update.message.reply_text("Virhe haettaessa otteluita.")
        return

    data = resp.json()
    matches = []
    for match in data.get("sport_events", []):
        if match["start_time"].startswith(date_iso):
            home = match["competitors"][0]["name"]
            away = match["competitors"][1]["name"]
            # DEMO: Kertoimet kovakoodattu, lisää oikea API-kutsu tähän
            opening_odds = 2.00
            current_odds = 2.10
            arrow = get_odds_arrow(opening_odds, current_odds)
            matches.append(f"{home} vs {away}\nKerroin: {current_odds:.2f} {arrow} (Avaus: {opening_odds:.2f})")

    if not matches:
        await update.message.reply_text("Ei otteluita löytynyt tälle päivälle.")
    else:
        await update.message.reply_text("\n\n".join(matches))

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ottelut", ottelut))
    application.run_polling()

if __name__ == "__main__":
    main()
