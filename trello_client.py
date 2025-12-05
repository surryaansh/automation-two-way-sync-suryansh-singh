# trello_client.py (updated with safe_request)
import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()

TRELLO_KEY = os.getenv("TRELLO_KEY")
TRELLO_TOKEN = os.getenv("TRELLO_TOKEN")
TRELLO_BOARD_ID = os.getenv("TRELLO_BOARD_ID", "0G2ETi3B")

LIST_TODO = os.getenv("TRELLO_LIST_TODO")
LIST_INPROGRESS = os.getenv("TRELLO_LIST_INPROGRESS")
LIST_DONE = os.getenv("TRELLO_LIST_DONE")
LIST_LOST = os.getenv("TRELLO_LIST_LOST")

BASE = "https://api.trello.com/1"


def safe_request(method, url, **kwargs):
    """Simple wrapper around requests with one retry for server errors. Returns requests.Response or None on failure."""
    try:
        r = requests.request(method, url, **kwargs)
        if r is None:
            return None
        if r.status_code >= 500:
            print(f"[safe_request] Trello server error {r.status_code} for {url}, retrying in 1s...")
            time.sleep(1)
            r = requests.request(method, url, **kwargs)
        r.raise_for_status()
        return r
    except Exception as e:
        print(f"[safe_request] ERROR calling {url}: {e}")
        return None


def _auth_params(extra=None):
    p = {"key": TRELLO_KEY, "token": TRELLO_TOKEN}
    if extra:
        p.update(extra)
    return p


def get_cards():
    """Return cards"""
    url = f"{BASE}/boards/{TRELLO_BOARD_ID}/cards"
    r = safe_request("GET", url, params=_auth_params())
    if not r:
        return []
    return r.json()


def create_card(name, lead_id):
    """Create a card in the TODO list. Returns card id string or None."""
    url = f"{BASE}/cards"
    params = _auth_params({
        "idList": LIST_TODO,
        "name": name or "(No Name)",
        "desc": f"Lead ID: {lead_id}"
    })
    r = safe_request("POST", url, params=params)
    if not r:
        return None
    return r.json().get("id")


def move_card(card_id, new_status):
    """Move a card based on Notion status."""
    """Accepts: "New", "Contacted", "Qualified", "Lost" """
    status_map = {
        "New": LIST_TODO,
        "Contacted": LIST_INPROGRESS,
        "Qualified": LIST_DONE,
        "Lost": LIST_LOST
    }
    target = status_map.get(new_status)
    if not target:
        return None
    url = f"{BASE}/cards/{card_id}"
    params = _auth_params({"idList": target})
    r = safe_request("PUT", url, params=params)
    if not r:
        return None
    return r.json()
