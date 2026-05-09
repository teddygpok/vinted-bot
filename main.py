import os, time, json, requests, logging
from datetime import datetime, timezone, timedelta

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
CHECK_INTERVAL = 120

VINTED_URL = "https://www.vinted.fr/api/v2/catalog/items"
PARAMS = {"search_text": "rayquaza", "order": "newest_first", "per_page": 20}
HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0)",
    "Accept": "application/json",
    "Accept-Language": "fr-FR,fr;q=0.9",
}

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
    return "rayquaza" in title

def is_recent(item):
    # Essayer différents champs de date
    created_at = item.get("created_at_ts") or item.get("created_at") or item.get("photo", {}).get("created_at_ts")
    logging.info(f"Champs dispo: {[k for k in item.keys()]}")
    if not created_at:
        return True  # si pas de date, on notifie quand même
    if isinstance(created_at, str):
        from datetime import datetime
        created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00")).timestamp()
    age = datetime.now(timezone.utc) - datetime.fromtimestamp(created_at, tz=timezone.utc)
    return age < timedelta(hours=1, minutes=10)
    
def notify(item):
    title = item.get("title", "?")
    price = item.get("price", {}).get("amount", "?")
    url = f"https://www.vinted.fr/items/{item['id']}"
    text = f"🟢 Nouvelle carte Rayquaza !\n\n{title}\nPrix : {price} EUR\n\n{url}"
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
