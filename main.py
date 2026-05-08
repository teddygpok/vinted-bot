import os, time, json, requests, logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
CHECK_INTERVAL = 120  # vérification toutes les 2 minutes

VINTED_URL = "https://www.vinted.fr/api/v2/catalog/items"
PARAMS = {"search_text": "carte rayquaza", "order": "newest_first", "per_page": 20}
HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0)",
    "Accept": "application/json",
    "Accept-Language": "fr-FR,fr;q=0.9",
}

SEEN_FILE = "seen_ids.json"

def load_seen():
    try:
        with open(SEEN_FILE) as f: return set(json.load(f))
    except: return set()

def save_seen(ids):
    with open(SEEN_FILE, "w") as f: json.dump(list(ids), f)

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
    seen = load_seen()
    session = get_session()
    first_run = not seen

    while True:
        items = fetch_items(session)
        if not items:
            session = get_session()
            time.sleep(300)
            continue

        if first_run:
            seen = {str(i["id"]) for i in items}
            save_seen(seen)
            first_run = False
            logging.info("Premier lancement : annonces existantes ignorées.")
        else:
            new = [i for i in items if str(i["id"]) not in seen]
            for item in new:
                notify(item)
                seen.add(str(item["id"]))
            if new: save_seen(seen)

        time.sleep(CHECK_INTERVAL)

main()
