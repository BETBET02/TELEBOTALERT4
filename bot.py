import asyncio
import asyncpg
import os
from datetime import datetime, timezone
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import tweepy

# --- Lue tiedot ympäristömuuttujista ---
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TWITTER_BEARER_TOKEN = os.environ["TWITTER_BEARER_TOKEN"]
DATABASE_URL = os.environ["DATABASE_URL"]

# --- Cachein kesto sekunteina ---
CACHE_TTL_SECONDS = 3600  # 1 tunti

# --- Twitter API client ---
client = tweepy.Client(bearer_token=TWITTER_BEARER_TOKEN, wait_on_rate_limit=True)

# --- PostgreSQL yhteys ---
db_pool = None

async def init_db_pool():
    global db_pool
    db_pool = await asyncpg.create_pool(DATABASE_URL)
    async with db_pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS tweet_cache (
                key TEXT PRIMARY KEY,
                fetched_at TIMESTAMP,
                data JSONB
            );
        """)

# --- Täydellinen Twitter-kanavien user ID ja nimet sisältävä rakenne ---

USER_IDS = {
    "kiekko": {
        "NHL": {
            "loukkaantumiset": [
                "1200045509",  # EP Transfers
                "16188237",    # Squawka (myös futis, mutta tässä mukana)
                "1305433894694223872", # MoneyPuckdotcom (analyysi)
                "17464681",    # NHL
                "18838464",    # NHL.com
                "34796001",    # NHLPR
            ],
            "kokoonpanot": [
                "1200045509",
                "16188237",
                "17464681",
                "18838464",
            ],
            "siirrot": [
                "1305433894694223872",
                "16188237",
                "17464681",
                "18838464",
            ],
            "analyysi": [
                "2468469096",  # MoneyPuckdotcom (oikea ID)
                "17464681",
            ],
            "uutiset": [
                "1200045509",
                "16188237",
                "1305433894694223872",
                "2468469096",
                "17464681",
                "18838464",
                "34796001",
            ],
        },
        "SHL": {
            "loukkaantumiset": [
                "SwissHockeyNews",  # Twitter handle, muutetaan ID:ksi haussa erikseen
            ],
            "kokoonpanot": [
                "SwissHockeyNews",
            ],
            "siirrot": [
                "SwissHockeyNews",
            ],
            "analyysi": [
                "SwissHockeyNews",
            ],
            "uutiset": [
                "SwissHockeyNews",
                "jatkoaika",
            ],
        },
        "NLA": {
            "loukkaantumiset": ["SwissHockeyNews"],
            "kokoonpanot": ["SwissHockeyNews"],
            "siirrot": ["SwissHockeyNews"],
            "analyysi": ["SwissHockeyNews"],
            "uutiset": ["SwissHockeyNews"],
        },
        "Liiga": {
            "loukkaantumiset": [
                "jatkoaika",
            ],
            "kokoonpanot": [
                "jatkoaika",
            ],
            "siirrot": [
                "jatkoaika",
            ],
            "analyysi": [
                "jatkoaika",
            ],
            "uutiset": [
                "jatkoaika",
            ],
        },
    },
    "futis": {
        "LaLiga": {
            "loukkaantumiset": [
                "LaLigaLowdown",
                "LaLigaEN",
            ],
            "kokoonpanot": [
                "LaLigaLowdown",
                "LaLigaEN",
            ],
            "siirrot": [
                "LaLigaLowdown",
                "LaLigaEN",
            ],
            "analyysi": [
                "LaLigaLowdown",
                "Squawka",
            ],
            "uutiset": [
                "LaLigaLowdown",
                "LaLigaEN",
                "Squawka",
                "FabrizioRomano",
                "OptaJoe",
            ],
        },
        "SerieA": {
            "loukkaantumiset": [
                "SerieA_EN",
                "IFTVofficial",
            ],
            "kokoonpanot": [
                "SerieA_EN",
                "IFTVofficial",
            ],
            "siirrot": [
                "SerieA_EN",
                "IFTVofficial",
                "FabrizioRomano",
            ],
            "analyysi": [
                "SerieA_EN",
                "OptaJoe",
                "FabrizioRomano",
            ],
            "uutiset": [
                "SerieA_EN",
                "IFTVofficial",
                "FabrizioRomano",
                "OptaJoe",
            ],
        },
        "Ligue1": {
            "loukkaantumiset": [
                "GFFN",
                "Ligue1_ENG",
            ],
            "kokoonpanot": [
                "GFFN",
                "Ligue1_ENG",
            ],
            "siirrot": [
                "GFFN",
                "Ligue1_ENG",
                "FabrizioRomano",
            ],
            "analyysi": [
                "GFFN",
                "WhoScored",
                "OptaJoe",
            ],
            "uutiset": [
                "GFFN",
                "Ligue1_ENG",
                "FabrizioRomano",
                "OptaJoe",
            ],
        },
        "EPL": {
            "loukkaantumiset": [
                "premierleague",
                "OptaJoe",
            ],
            "kokoonpanot": [
                "premierleague",
                "OptaJoe",
            ],
            "siirrot": [
                "premierleague",
                "FabrizioRomano",
                "OptaJoe",
            ],
            "analyysi": [
                "WhoScored",
                "OptaJoe",
            ],
            "uutiset": [
                "premierleague",
                "FabrizioRomano",
                "OptaJoe",
                "WhoScored",
            ],
        },
        "Bundesliga": {
            "loukkaantumiset": [
                "Bundesliga_EN",
            ],
            "kokoonpanot": [
                "Bundesliga_EN",
            ],
            "siirrot": [
                "Bundesliga_EN",
                "FabrizioRomano",
            ],
            "analyysi": [
                "OptaJoe",
            ],
            "uutiset": [
                "Bundesliga_EN",
                "FabrizioRomano",
                "OptaJoe",
            ],
        },
    },
    "tennis": {
        "ATP": {
            "loukkaantumiset": [
                "atptour",
            ],
            "kokoonpanot": [
                "atptour",
            ],
            "siirrot": [
                "atptour",
            ],
            "analyysi": [
                "atptour",
                "MoneyPuckdotcom",  # Käytetään analyysiin myös jääkiekkokanavaa, jos halutaan
            ],
            "uutiset": [
                "atptour",
                "BenRothenberg",
            ],
        },
        "WTA": {
            "loukkaantumiset": [
                "WTA",
            ],
            "kokoonpanot": [
                "WTA",
            ],
            "siirrot": [
                "WTA",
            ],
            "analyysi": [
                "WTA",
            ],
            "uutiset": [
                "WTA",
                "BenRothenberg",
            ],
        },
    }
}

# Huom! Tässä kanavissa on sekaisin user ID:t ja Twitter-nimet (screen name)
# Pitäisi muuttaa kaikki ID:ksi yhdellä funktiolla, joka hakee käyttäjätunnuksen ID:n Twitteristä

# --- Apufunktio usernamen -> user_id selvitykseen (kerralla monta) ---
async def resolve_usernames(usernames):
    # Palauttaa dict username -> user_id
    user_ids = {}
    chunks = [usernames[i:i+100] for i in range(0, len(usernames), 100)]
    for chunk in chunks:
        try:
            users = client.get_users(usernames=chunk)
            if users.data:
                for u in users.data:
                    user_ids[u.username] = u.id
        except Exception as e:
            print(f"Virhe käyttäjien hakemisessa: {e}")
    return user_ids

# --- Cache DB - funktiot ---

async def get_cached_tweets(key):
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("SELECT fetched_at, data FROM tweet_cache WHERE key=$1", key)
        if row:
            fetched_at = row["fetched_at"]
            if (datetime.now(timezone.utc) - fetched_at).total_seconds() < CACHE_TTL_SECONDS:
                return row["data"]
        return None

async def set_cached_tweets(key, data):
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO tweet_cache (key, fetched_at, data)
            VALUES ($1, $2, $3)
            ON CONFLICT (key) DO UPDATE SET fetched_at = EXCLUDED.fetched_at, data = EXCLUDED.data;
        """, key, datetime.now(timezone.utc), data)

# --- Hae twiitit yhdeltä käyttäjältä ---
async def fetch_tweets_from_user(user_id: str, max_results=5):
    try:
        resp = client.get_users_tweets(id=user_id, max_results=max_results, tweet_fields=["created_at", "text"])
        if resp.data:
            return [{"created_at": str(tweet.created_at), "text": tweet.text, "id": tweet.id} for tweet in resp.data]
    except Exception as e:
        print(f"Virhe haettaessa twiittejä käyttäjältä {user_id}: {e}")
    return []

# --- Pääfunktio tiedon hakemiseen useilta kanavilta yhdellä pyynnöllä ---

async def fetch_tweets_for_command(sport, league, command):
    # Avataan kanavien ID:t (muutetaan nimistä ID:ksi, jos nimi)
    channels = USER_IDS.get(sport, {}).get(league, {}).get(command, [])
    if not channels:
        return f"Ei löytynyt kanavia laji/ liiga/ komento-yhdistelmällä: {sport}/{league}/{command}"

    # Selvitä nimistä ID:t (käyttäjätilin ID:t ovat numeroita, muuten hae)
    usernames_to_resolve = [ch for ch in channels if not ch.isdigit()]
    resolved_ids = {}
    if usernames_to_resolve:
        resolved_ids = await resolve_usernames(usernames_to_resolve)

    # Korvataan käyttäjänimet id:llä
    user_ids = []
    for ch in channels:
        if ch.isdigit():
            user_ids.append(ch)
        else:
            user_ids.append(str(resolved_ids.get(ch, "")))
    user_ids = [uid for uid in user_ids if uid]

    # Tarkista cache
    cache_key = f"{sport}_{league}_{command}"
    cached = await get_cached_tweets(cache_key)
    if cached:
        return cached

    # Hae twiitit kaikilta kanavilta ja yhdistä tulokset
    all_tweets = []
    for uid in user_ids:
        tweets = await fetch_tweets_from_user(uid)
        all_tweets.extend(tweets)

    # Järjestä twiitit aikajärjestykseen (uusin ensin)
    all_tweets.sort(key=lambda x: x["created_at"], reverse=True)

    # Rajataan max 10 twiittiin
    all_tweets = all_tweets[:10]

    # Muodosta vastaus (voit muokata tekstiksi mieleisesi)
    response = f"🔎 {sport.upper()} / {league.upper()} / {command}\n\n"
    for t in all_tweets:
        text = t["text"].replace("\n", " ")
        created = t["created_at"]
        tweet_url = f"https://twitter.com/i/web/status/{t['id']}"
        response += f"- [{created}] {text}\n{tweet_url}\n\n"

    # Cachetus
    await set_cached_tweets(cache_key, response)
    return response

# --- Telegram-komentojen käsittelijät ---

async def handle_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text(
            "Käyttö: /komento laji liiga komento\n"
            "Esim. /komento kiekko NHL loukkaantumiset\n"
            "Komennot: loukkaantumiset, kokoonpanot, siirrot, analyysi, uutiset\n"
            "Lajit esim: kiekko, futis, tennis\n"
            "Liigat esim: NHL, SHL, LaLiga, ATP, WTA"
        )
        return

    sport = context.args[0].lower()
    league = context.args[1]
    command = context.args[2].lower()

    response = await fetch_tweets_for_command(sport, league, command)
    await update.message.reply_text(response)

# --- Käynnistys ---

async def main():
    await init_db_pool()

    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("komento", handle_command))

    print("Bot käynnistyy...")
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
