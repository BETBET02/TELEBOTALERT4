import requests

MASTER_API_KEY = "YOUR_MASTER_API_KEY"
SEASON_ID = "sr:season:128461"  # Vaihda haluamasi sarjan season_id tähän!
TARGET_DATE = "2025-07-27"

def fetch_matches(season_id, target_date):
    url = f"https://api.sportradar.com/soccer/trial/v4/en/seasons/{season_id}/schedules.json?api_key={MASTER_API_KEY}"
    resp = requests.get(url)
    schedules = resp.json()
    matches = []

    for event in schedules.get("sport_events", []):
        if event["start_time"].startswith(target_date):
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

            matches.append({
                "home": home,
                "away": away,
                "1": kerroin_1,
                "X": kerroin_x,
                "2": kerroin_2
            })

    return matches

if __name__ == "__main__":
    results = fetch_matches(SEASON_ID, TARGET_DATE)
    for match in results:
        print(f"{match['home']} - {match['away']}: 1 {match['1']} X {match['X']} 2 {match['2']}")
