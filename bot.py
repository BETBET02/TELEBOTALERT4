import os
import requests
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import Update

from dotenv import load_dotenv
load_dotenv()

SPORTRADAR_API_KEY = os.getenv("SPORTRADAR_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Kaikki avaimet pienillä kirjaimilla!
TOURNAMENT_IDS = {
    ("seriea", "brazil"): "sr:tournament:26",        # Brasil Serie A
    ("veikkausliiga", "finland"): "sr:tournament:67",
    ("premierleague", "england"): "sr:tournament:17",
    ("laliga", "spain"): "sr:tournament:8",
    # Lisää tarvittaessa!
}

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

    # Muutetaan syöte pieniksi, jotta mapping toimii aina.
    sarja = context.args[0].strip().lower()
    maa = context.args[1].strip().lower()
    paiva = context.args[2]

    key = (sarja, maa)
    tournament_id = TOURNAMENT_IDS.get(key)
    if not tournament_id:
        await update.message.reply_text(f"Tuntematon sarja/maa ({sarja}/{maa}), lisää mapping TOURNAMENT_IDS")
        return

    try:
        day, month, year = paiva.split('.')
        date_iso = f"{year}-{month}-{day}"
    except Exception:
        date_iso = paiva  # fallback jos käyttäjä syötti valmiiksi oikein

    url = f"https://api.sportradar.com/soccer/trial/v4/en/tournaments/{tournament_id}/schedule.json?api_key={SPORTRADAR_API_KEY}"
    print("Kutsu URL:", url)
    resp = requests.get(url)
    print("Status code:", resp.status_code)
    print("Vastaus:", resp.text[:300])

    if resp.status_code != 200:
        await update.message.reply_text(f"Virhe haettaessa otteluita!\nStatus code: {resp.status_code}\nVastaus: {resp.text}")
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
