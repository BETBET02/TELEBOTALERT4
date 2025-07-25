import requests

MASTER_API_KEY = "YOUR_MASTER_API_KEY"
TARGET_DATE = "2025-07-27"
# Season ID:t, jotka mainitsit:
SEASON_IDS = [
    "sr:season:128461",  # Brasilia Serie A
    "sr:season:129540",  # Veikkausliiga
    "sr:season:128840",  # Premier League
    "sr:season:129229",  # La Liga
]

def hae_liigan_ottelut_ja_kertoimet(season_id):
    url = f"https://api.sportradar.com/soccer/trial/v4/en/seasons/{season_id}/schedules.json?api_key={MASTER_API_KEY}"
    resp = requests.get(url)
    schedules = resp.json()
    tulokset = []

    for event in schedules.get("sport_events", []):
        if event["start_time"].startswith(TARGET_DATE):
            home = event["competitors"][0]["name"]
            away = event["competitors"][1]["name"]
            event_id = event["id"]

            kerroin_1 = kerroin_x = kerroin_2 = "-"

            odds_url = f"https://api.sportradar.com/odds/trial/v4/en/sport_events/{event_id}/odds.json?api_key={MASTER_API_KEY}"
            odds_resp = requests.get(odds_url)
            odds_data = odds_resp.json()

            for market in odds_data.get("markets", []):
                if market.get("name") in ["Match Winner", "1X2"]:
                    for outcome in market.get("outcomes", []):
                        if outcome["type"] == "home":
                            kerroin_1 = outcome["odds"]
                        elif outcome["type"] == "draw":
                            kerroin_x = outcome["odds"]
                        elif outcome["type"] == "away":
                            kerroin_2 = outcome["odds"]

            tulokset.append(f"{home} - {away}: 1 {kerroin_1} X {kerroin_x} 2 {kerroin_2}")

    return tulokset

if __name__ == "__main__":
    for season_id in SEASON_IDS:
        print(f"\nLiiga: {season_id}")
        tulokset = hae_liigan_ottelut_ja_kertoimet(season_id)
        for rivi in tulokset:
            print(rivi)
