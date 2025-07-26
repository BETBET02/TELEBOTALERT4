import os
import requests
from dotenv import load_dotenv
import telebot

load_dotenv()
bot = telebot.TeleBot(os.getenv("TELEGRAM_BOT_TOKEN"))
API_KEY = os.getenv("API_FOOTBALL_KEY")
ODDS_KEY = os.getenv("ODDS_API_KEY")

@bot.message_handler(commands=['ottelut'])
def handle_matches(message):
    args = message.text.split()
    if len(args) < 3:
        bot.reply_to(message, "Käyttö: /ottelut <LIIGA> <YYYY-MM-DD>")
        return

    league, date = args[1], args[2]
    fixtures = get_fixtures(league, date)
    if not fixtures:
        bot.reply_to(message, "Ei otteluita.")
        return

    results = []
    for match in fixtures:
        home = match['home']
        away = match['away']
        launch_odds, close_odds = get_odds(home, away)
        results.append(f"{home}-{away} {close_odds} ({launch_odds})")
    
    bot.reply_to(message, "\n".join(results))

def get_fixtures(league_name, date):
    url = "https://v3.football.api-sports.io/fixtures"
    params = {
        "league": get_league_id(league_name),
        "season": "2025",
        "date": date
    }
    headers = {
        "x-apisports-key": API_KEY
    }
    r = requests.get(url, headers=headers, params=params)
    data = r.json()
    fixtures = []
    for m in data.get("response", []):
        home = m["teams"]["home"]["name"]
        away = m["teams"]["away"]["name"]
        fixtures.append({"home": home, "away": away})
    return fixtures

def get_odds(home, away):
    url = "https://api.the-odds-api.com/v4/sports/soccer_epl/odds"
    params = {
        "apiKey": ODDS_KEY,
        "regions": "uk",
        "markets": "h2h"
    }
    r = requests.get(url, params=params)
    for event in r.json():
        teams = [t.lower() for t in event["teams"]]
        if home.lower() in teams and away.lower() in teams:
            outcomes = event["bookmakers"][0]["markets"][0]["outcomes"]
            close = "-".join([f"{o['price']:.2f}" for o in outcomes])
            launch = "-".join([f"{o['price'] + 0.1:.2f}" for o in outcomes])  # simuloitu launch
            return launch, close
    return "–", "–"

def get_league_id(name):
    leagues = {
        "EPL": 39,
        "LaLiga": 140,
        "SerieA": 135,
    }
    return leagues.get(name, 39)  # default EPL
