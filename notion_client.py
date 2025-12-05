# notion_client.py (minimal + clean)

import os, requests
from dotenv import load_dotenv

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

BASE = "https://api.notion.com/v1"
HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

def get_leads():
    """Query the Notion database."""
    r = requests.post(f"{BASE}/databases/{DATABASE_ID}/query",
                      headers=HEADERS, json={})
    r.raise_for_status()
    return r.json()

def parse_leads():
    """Extract useful fields from raw Notion pages."""
    out = []
    for item in get_leads().get("results", []):
        p = item.get("properties", {})

        # Name
        title = p.get("Name", {}).get("title", [])
        name = title[0].get("plain_text", "") if title else ""

        # Email
        email = p.get("Email", {}).get("email")

        # Status
        status_prop = p.get("Status", {})
        sel = status_prop.get("select") or status_prop.get("status")
        status = sel.get("name") if isinstance(sel, dict) else None

        # Source
        rt = p.get("Source", {}).get("rich_text", [])
        source = rt[0].get("plain_text", "") if rt else None

        # Trello Card ID
        tc = p.get("TrelloCardID", {}).get("rich_text", [])
        trello_card_id = tc[0].get("plain_text", "") if tc else None

        out.append({
            "id": item.get("id"),
            "name": name,
            "email": email,
            "status": status,
            "source": source,
            "trello_card_id": trello_card_id,
            "last_edited_time": item.get("last_edited_time")
        })
    return out

def set_trello_card_id(page_id, card_id):
    """Write TrelloCardID to Notion."""
    body = {
        "properties": {
            "TrelloCardID": {
                "rich_text": [{"text": {"content": card_id}}]
            }
        }
    }
    r = requests.patch(f"{BASE}/pages/{page_id}",
                       headers=HEADERS, json=body)
    r.raise_for_status()
    return r.json()

def update_lead_status(page_id, new_status):
    """Update Notion status (supports both select and status types)."""
    url = f"{BASE}/pages/{page_id}"

    # Try select
    b1 = {"properties": {"Status": {"select": {"name": new_status}}}}
    r = requests.patch(url, headers=HEADERS, json=b1)
    if r.status_code < 400:
        return r.json()

    # Fallback: status type
    b2 = {"properties": {"Status": {"status": {"name": new_status}}}}
    r2 = requests.patch(url, headers=HEADERS, json=b2)
    r2.raise_for_status()
    return r2.json()
