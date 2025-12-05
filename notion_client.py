import os
import requests
import time
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

def safe_request(method, url, **kwargs):
    """Tiny wrapper around requests.request:
    - retries once on server error
    - logs minimal info
    - returns requests.Response or None on failure"""
    try:
        r = requests.request(method, url, **kwargs)
        if r is None:
            return None
        if r.status_code >= 500:
            print(f"[safe_request] Server error {r.status_code} for {url}, retrying in 1s...")
            time.sleep(1)
            r = requests.request(method, url, **kwargs)
        r.raise_for_status()
        return r
    except Exception as e:
        print(f"[safe_request] ERROR calling {url}: {e}")
        return None


# Basic API operations 

def get_leads():
    """Query notion and return raw JSON response"""
    url = f"{BASE}/databases/{DATABASE_ID}/query"
    r = safe_request("POST", url, headers=HEADERS, json={})
    if not r:
        return {}
    return r.json()


# Parsing for convenience
def parse_leads():
    """Convert Notion query results into a list of simple dicts:
    {
      id, name, email, status, source, trello_card_id, last_edited_time
    }
    """
    data = get_leads()
    results = data.get("results", []) if isinstance(data, dict) else []
    leads = []

    for item in results:
        props = item.get("properties", {})

        # Name
        name = ""
        title_prop = props.get("Name", {}).get("title", [])
        if title_prop and isinstance(title_prop, list) and title_prop:
            first = title_prop[0]
            name = first.get("plain_text", "") if first else ""

        # Email
        email = props.get("Email", {}).get("email")

        # Status
        status = None
        status_prop = props.get("Status", {})
        sel = status_prop.get("select") or status_prop.get("status")
        if sel and isinstance(sel, dict):
            status = sel.get("name")

        # Source (rich_text)
        source = None
        rt = props.get("Source", {}).get("rich_text", [])
        if rt and isinstance(rt, list) and rt:
            source = rt[0].get("plain_text", "")

        # TrelloCardID (rich_text or text)
        trello_card_id = None
        tc = props.get("TrelloCardID", {}).get("rich_text", [])
        if tc and isinstance(tc, list) and tc:
            trello_card_id = tc[0].get("plain_text", "")
        else:
            tc_text = props.get("TrelloCardID", {}).get("text")
            if tc_text:
                trello_card_id = tc_text

        # Page last edited time
        last_edited = item.get("last_edited_time")

        leads.append({
            "id": item.get("id"),
            "name": name,
            "email": email,
            "status": status,
            "source": source,
            "trello_card_id": trello_card_id,
            "last_edited_time": last_edited
        })

    return leads


# Mutations
def set_trello_card_id(page_id, card_id):
    """Store Trello card ID inside the TrelloCardID rich_text property."""
    """Overwrites previous value. Returns JSON response or None."""
    url = f"{BASE}/pages/{page_id}"
    body = {
        "properties": {
            "TrelloCardID": {
                "rich_text": [
                    {"text": {"content": card_id}}
                ]
            }
        }
    }
    r = safe_request("PATCH", url, headers=HEADERS, json=body)
    if not r:
        return None
    return r.json()


def update_lead_status(page_id, new_status):
    """Update the Status property of a Notion page."""
    """Tries 'select' first, then 'status' if select fails (resilient)."""
    """Returns JSON response or None."""
    url = f"{BASE}/pages/{page_id}"
    body_select = {"properties": {"Status": {"select": {"name": new_status}}}}
    body_status = {"properties": {"Status": {"status": {"name": new_status}}}}

    # Try select style first
    r = safe_request("PATCH", url, headers=HEADERS, json=body_select)
    if r and r.status_code < 400:
        return r.json()

    # Fallback to status style
    r2 = safe_request("PATCH", url, headers=HEADERS, json=body_status)
    if not r2:
        return None
    return r2.json()


def create_lead(name, email=None, status="New", source=None):
    """Create a new lead (page) in the Notion database."""
    url = f"{BASE}/pages"
    properties = {
        "Name": {"title": [{"text": {"content": name}}]},
        "Status": {"select": {"name": status}}
    }
    if email:
        properties["Email"] = {"email": email}
    if source:
        properties["Source"] = {"rich_text": [{"text": {"content": source}}]}

    body = {
        "parent": {"database_id": DATABASE_ID},
        "properties": properties
    }

    r = safe_request("POST", url, headers=HEADERS, json=body)
    if not r:
        return None
    page = r.json()

    return {
        "id": page.get("id"),
        "name": name,
        "email": email,
        "status": status,
        "source": source,
        "trello_card_id": None,
        "last_edited_time": page.get("last_edited_time")
    }
