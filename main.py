import os, time, requests, logging

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
    import re
    title = item.get("title", "").lower()
    if "rayquaza" not in title:
        return False
    patterns = [
        r"dp\s*47",
        r"0?18",
        r"232",
        r"102",
        r"97",
        r"0?39",
        r"107",
    ]
    return any(re.search(p, title) for p in patterns)
    
def get_photo_url(item):
    try:
        photos = item.get("photos", [])
        if photos:
            return photos[0].get("url", "") or photos[0].get("full_size_url", "")
        photo = item.get("photo", {})
        return photo.get("url", "") or photo.get("full_size_url", "")
    except:
        return ""

def notify(item):
    title = item.get("title", "?")
    price = item.get("price", {}).get("amount", "?")
    url = f"https://www.vinted.fr/items/{item['id']}"
    photo_url = get_photo_url(item)

    if photo_url:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto",
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "photo": photo_url,
                "caption": f"{title}\nPrix : {price} EUR\n\n{url}"
            },
            timeout=10
        )
    else:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": f"{title}\nPrix : {price} EUR\n\n{url}"
            },
            timeout=10
        )

def main():
    logging.info("Bot démarré !")
    session = get_session()
    notified = set()
    first_run = True

    while True:
        try:
            items = fetch_items(session)
            if not items:
                session = get_session()
                time.sleep(300)
                continue

            valid_items = [i for i in items if is_valid(i)]

            if first_run:
                for item in valid_items:
                    notified.add(str(item["id"]))
                first_run = False
                logging.info(f"{len(notified)} annonces existantes ignorées.")
            else:
                for item in valid_items:
                    item_id = str(item["id"])
                    if item_id not in notified:
                        notify(item)
                        notified.add(item_id)
                        logging.info(f"Notifié : {item.get('title')}")

        except Exception as e:
            logging.error(f"Erreur : {e}")
            session = get_session()

        time.sleep(CHECK_INTERVAL)

main()
