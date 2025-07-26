import os
import requests
import telebot  # tai "from telebot.async_telebot import AsyncTeleBot" jos async

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

SPORTDATA_KEY = os.getenv("SPORTDATA_API_KEY")
ODDS_KEY = os.getenv("ODDS_API_KEY")

@bot.message_handler(commands=['ottelut'])
def handle_ottelut(message):
    # Esimerkki: viesti = "EPL 2025-08-15"
    args = message.text.split()[1:]  # ['EPL', '2025-08-15']
    if len(args) != 2:
        bot.reply_to(message, "Käyttö: /ottelut <liiga> <YYYY‑MM‑DD>")
        return
    
    league, date = args
    matches = get_matches(league, date)
    if not matches:
        bot.reply_to(message, "Ei otteluita annettuna päivänä/liigassa.")
        return

    texts = []
    for m in matches:
        home = m['home_team']; away = m['away_team']
        launch_odds, closing_odds = get_odds(m['match_id'])
        texts.append(f"{home}-{away} {launch_odds} ({closing_odds})")
    bot.reply_to(message, "\n".join(texts))

def get_matches(league, date):
    url = f"https://api.sportdataapi.com/v1/soccer/matches"
    params = {"api_token": SPORTDATA_KEY, "date": date, "league": league}
    r = requests.get(url, params=params)
    data = r.json().get('data', [])
    return [{"match_id": ev['id'], "home_team": ev['localteam_name'], "away_team": ev['visitorteam_name']} for ev in data]

def get_odds(match_id):
    url = "https://api.the-odds-api.com/v4/sports/soccer_epl/odds"  # muokkaa lajiin
    params = {"apiKey": ODDS_KEY, "regions": "uk", "markets": "h2h"}
    r = requests.get(url, params=params)
    best = r.json()
    # etsi oikea ottelu esim. event_timestamp tai joukkueet
    for ev in best:
        if ev.get('id') == str(match_id):
            prices = ev['bookmakers'][0]['markets'][0]['outcomes']
            closing = ev.get('started') and prices  # esimerkki
            launch = ev.get('commence_time') and prices
            launch_str = "-".join([f"{o['price']:.2f}" for o in launch])
            close_str = "-".join([f"{o['price']:.2f}" for o in prices])
            return launch_str, close_str
    return "–", "–"
