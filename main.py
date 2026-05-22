import os, time, requests, logging, re
from datetime import datetime, timezone, timedelta

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
CHECK_INTERVAL = 30

VINTED_URL = "https://www.vinted.fr/api/v2/catalog/items"
PARAMS = {"search_text": "rayquaza", "order": "newest_first", "per_page": 20}
HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0)",
    "Accept": "application/json",
    "Accept-Language": "fr-FR,fr;q=0.9",
}

PATTERNS = [
    r"\bdp\s*47\b",
    r"\b0?18\b",
    r"\b232\b",
    r"\b102\b",
    r"\b97\b",
    r"\b0?39\b",
    r"\b107\b",
    r"\b0{0,2}3\b",
    r"\b218\b",
    r"\b87\b",
    r"\b105\b",
    r"64\b",
    r"69\b",
    r"\b128\b",
    r"\b10\b",
    r"\bsl\b",
    r"\b16\b",
    r"\b26\b",
    r"\b9\b",
    r"star",
    r"étoile",
    r"★",
]

def get_session():
    s = requests.Session()
    s.get("https://www.vinted.fr", headers=HEADERS, timeout=10)
    return s

def fetch_items(session):
    try:
        r = session.get(VINTED_URL, params=PARAMS, headers=HEADERS, timeout=10)
        return r.json().get("items", []) if r.status_code == 200 else []
    except Exception as e:
        logging.error(e); return []

def is_valid(item):
    title = item.get("title", "").lower()
    if "rayquaza" not in title:
        return False
    return any(re.search(p, title) for p in PATTERNS)

def is_recent(item):
    try:
        photo = item.get("photo", {})
        ts = photo.get("created_at_ts") or photo.get("updated_at_ts")
        if ts:
            age = datetime.now(timezone.utc) - datetime.fromtimestamp(ts, tz=timezone.utc)
            return age < timedelta(hours=1, minutes=10)
    except:
        pass
    return True

def notify(item):
    title = item.get("title", "?")
    price = item.get("price", {}).get("amount", "?")
    url = f"https://www.vinted.fr/items/{item['id']}"
    photos = item.get("photos", [])
    photo_url = photos[0].get("url") if photos else None

    text = f"{title}\nPrix : {price} EUR\n\n{url}"
    if photo_url:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto",
            json={"chat_id": TELEGRAM_CHAT_ID, "photo": photo_url, "caption": text},
            timeout=10
        )
    else:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text},
            timeout=10
        )

def main():
    logging.info("Bot démarré !")
    session = get_session()
    notified = set()

    while True:
        try:
            items = fetch_items(session)
            if not items:
                session = get_session()
                time.sleep(300)
                continue

            for item in items:
                item_id = str(item["id"])
                if is_valid(item) and is_recent(item) and item_id not in notified:
                    notify(item)
                    notified.add(item_id)
                    logging.info(f"Notifié : {item.get('title')}")

        except Exception as e:
            logging.error(f"Erreur : {e}")
            session = get_session()

        time.sleep(CHECK_INTERVAL)

main()
