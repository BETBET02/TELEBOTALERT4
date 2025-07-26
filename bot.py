import os
import requests
from dotenv import load_dotenv
load_dotenv()
import telebot


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
    league_info = get_league_id_and_season(league)
    if not league_info:
        bot.reply_to(message, "Tuntematon liiga. Tarkista kirjoitusasu.")
        return

    league_id, season_id = league_info
    fixtures = get_fixtures(league_id, season_id, date)
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

def get_fixtures(league_id, season_id, date):
    url = "https://v3.football.api-sports.io/fixtures"
    params = {
        "league": league_id,
        "season": season_id,
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
    try:
        for event in r.json():
            teams = [t.lower() for t in event["teams"]]
            if home.lower() in teams and away.lower() in teams:
                outcomes = event["bookmakers"][0]["markets"][0]["outcomes"]
                close = "-".join([f"{o['price']:.2f}" for o in outcomes])
                launch = "-".join([f"{o['price'] + 0.1:.2f}" for o in outcomes])  # Simuloitu launch
                return launch, close
    except Exception:
        pass
    return "–", "–"

def get_league_id_and_season(name):
    leagues = {
        "EPL": (39, 7293),
        "LaLiga": (140, 7351),
        "SerieB": (71, 7079),
        "SerieA": (135, 7286),
        "Argentina": (128, 7000),
        "Ligue1": (61, 7335),
        "Eliteserien": (103, 7042),
        "Allsvenskan": (113, 7041),
        "OBOS": (104, 7043),
        "Superettan": (114, 7040),
        "Superliga": (119, 7294),
        "1LigTurkey": (204, 7395),
        "Veikkausliiga": (244, 7044),
        "Eredivisie": (88, 7304),
        "ChampionsLeague": (2, 7318),
        "EuropaLeague": (3, 7320),
        "ConferenceLeague": (848, 7319)
    }
    return leagues.get(name)
