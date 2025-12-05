# trello_client.py (minimal + clean)

import os, requests
from dotenv import load_dotenv

load_dotenv()

TRELLO_KEY = os.getenv("TRELLO_KEY")
TRELLO_TOKEN = os.getenv("TRELLO_TOKEN")
TRELLO_BOARD_ID = os.getenv("TRELLO_BOARD_ID")

LIST_TODO = os.getenv("TRELLO_LIST_TODO")
LIST_INPROGRESS = os.getenv("TRELLO_LIST_INPROGRESS")
LIST_DONE = os.getenv("TRELLO_LIST_DONE")
LIST_LOST = os.getenv("TRELLO_LIST_LOST")

BASE = "https://api.trello.com/1"

def get_cards():
    url = f"{BASE}/boards/{TRELLO_BOARD_ID}/cards"
    params = {"key": TRELLO_KEY, "token": TRELLO_TOKEN}
    r = requests.get(url, params=params)
    r.raise_for_status()
    return r.json()

def create_card(name, lead_id):
    url = f"{BASE}/cards"
    params = {
        "key": TRELLO_KEY,
        "token": TRELLO_TOKEN,
        "idList": LIST_TODO,
        "name": name or "(No Name)",
        "desc": f"Lead ID: {lead_id}"
    }
    r = requests.post(url, params=params)
    r.raise_for_status()
    return r.json().get("id")

def move_card(card_id, new_status):
    status_map = {
        "New": LIST_TODO,
        "Contacted": LIST_INPROGRESS,
        "Qualified": LIST_DONE,
        "Lost": LIST_LOST
    }
    target_list = status_map.get(new_status)
    if not target_list:
        return None

    url = f"{BASE}/cards/{card_id}"
    params = {
        "key": TRELLO_KEY,
        "token": TRELLO_TOKEN,
        "idList": target_list
    }
    r = requests.put(url, params=params)
    r.raise_for_status()
    return r.json()
