import os
import requests
from dotenv import load_dotenv
import telebot

load_dotenv()

bot = telebot.TeleBot(os.getenv("TELEGRAM_BOT_TOKEN"))
API_KEY = os.getenv("API_FOOTBALL_KEY")
ODDS_KEY = os.getenv("ODDS_API_KEY")

# Kartta liigoista API Footballissa (league_id, season_id)
leagues = {
    "epl": (39, 2025),
    "laliga": (140, 2025),
    "serieb": (71, 2025),
    "seriea": (135, 2025),
    "argentina": (128, 2025),
    "ligue1": (61, 2025),
    "eliteserien": (103, 2025),
    "allsvenskan": (113, 2025),
    "obos": (104, 2025),
    "superettan": (114, 2025),
    "superliga": (119, 2025),
    "1ligturkey": (204, 2025),
    "veikkausliiga": (244, 2025),
    "eredivisie": (88, 2025),
    "championsleague": (2, 2025),
    "europaleague": (3, 2025),
    "conferenceleague": (848, 2025)
}

@bot.message_handler(commands=['ottelut'])
def handle_matches(message):
    args = message.text.split()
    if len(args) < 3:
        bot.reply_to(message, "Käyttö: /ottelut <LIIGA> <YYYY-MM-DD>")
        return

    league_key, date = args[1].lower(), args[2]
    league_info = leagues.get(league_key)
    if not league_info:
        bot.reply_to(message, "Tuntematon liiga. Tarkista kirjoitusasu.")
        return

    league_id, season_id = league_info
    fixtures = get_fixtures(league_id, season_id, date)
    if not fixtures:
        bot.reply_to(message, "Ei otteluita kyseiselle päivälle.")
        return

    results = []
    for match in fixtures:
        home = match['home']
        away = match['away']
        launch_odds, close_odds = get_odds(home, away)
        results.append(f"{home} - {away} {close_odds} ({launch_odds})")

    bot.reply_to(message, "\n".join(results))

def get_fixtures(league_id, season_id, date):
    url = "https://v3.football.api-sports.io/fixtures"
    params = {
        "league": league_id,
        "season": season_id,
        "date": date
    }
    headers = {"x-apisports-key": API_KEY}
    r = requests.get(url, headers=headers, params=params)
    if r.status_code != 200:
        return None
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
        "markets": "h2h",
        "oddsFormat": "decimal"
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

# /kertoimet komento ja liiga -> odds api mapping
league_map = {
    "valio": "soccer_epl",
    "epl": "soccer_epl",
    "laliga": "soccer_spain_la_liga",
    "seriea": "soccer_italy_serie_a",
    "ligue1": "soccer_france_ligue_one",
    "seriea_brasil": "soccer_brazil_campeonato_brasileiro",
}

@bot.message_handler(commands=['kertoimet'])
def kertoimet(message):
    args = message.text.split()
    if len(args) < 3:
        bot.reply_to(message, "Käyttö: /kertoimet <LIIGA> <YYYY-MM-DD>")
        return

    league = args[1].lower()
    date = args[2]
    sport_key = league_map.get(league)
    if not sport_key:
        bot.reply_to(message, "Tuntematon liiga.")
        return

    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    params = {
        "apiKey": ODDS_KEY,
        "regions": "uk",
        "markets": "h2h",
        "dateFormat": "iso",
        "oddsFormat": "decimal",
    }

    r = requests.get(url, params=params)
    if r.status_code != 200:
        bot.reply_to(message, f"Virhe kertoimia haettaessa: {r.status_code}")
        return

    events = r.json()
    if not events:
        bot.reply_to(message, "Ei kertoimia kyseiselle päivälle.")
        return

    results = []
    for event in events:
        home, away = event["teams"]
        commence_time = event.get("commence_time", "")
        if not commence_time.startswith(date):
            continue
        try:
            outcomes = event["bookmakers"][0]["markets"][0]["outcomes"]
            close_odds = "-".join(f"{o['price']:.2f}" for o in outcomes)
            launch_odds = "-".join(f"{o['price'] + 0.1:.2f}" for o in outcomes)  # Simuloitu alku
            results.append(f"{home} - {away} {close_odds} ({launch_odds})")
        except Exception:
            continue

    if results:
        bot.reply_to(message, "\n".join(results))
    else:
        bot.reply_to(message, "Ei kertoimia saatavilla.")

if __name__ == "__main__":
    print("Bot käynnistyy...")
    bot.polling()
