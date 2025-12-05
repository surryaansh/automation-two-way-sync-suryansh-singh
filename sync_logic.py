# sync_logic.py
"""
Final, interview-ready sync logic (compact, timestamp arbitration).
Keeps the same behavior you tested: idempotent two-way sync between Notion and Trello.
"""

import os
from dateutil.parser import isoparse
from notion_client import parse_leads, set_trello_card_id, update_lead_status
from trello_client import create_card, move_card, get_cards

# Read Trello list IDs from env (you already have these in your .env)
LIST_TODO = os.getenv("TRELLO_LIST_TODO")
LIST_INPROGRESS = os.getenv("TRELLO_LIST_INPROGRESS")
LIST_DONE = os.getenv("TRELLO_LIST_DONE")
LIST_LOST = os.getenv("TRELLO_LIST_LOST")

# Build mapping (list_id -> notion status) dynamically from env values
LIST_TO_STATUS = {
    LIST_TODO: "New",
    LIST_INPROGRESS: "Contacted",
    LIST_DONE: "Qualified",
    LIST_LOST: "Lost",
}
# Reverse mapping for convenience (notion status -> list id)
STATUS_TO_LIST = {v: k for k, v in LIST_TO_STATUS.items()}


def parse_time_iso(s):
    """Parse ISO timestamp to datetime (timezone-aware). Return None on failure."""
    if not s:
        return None
    try:
        return isoparse(s)
    except Exception:
        return None


def choose_and_sync_decision(lead, card):
    """
    Decide which system (Notion or Trello) should be treated as the source of truth
    based on last edit times.

    Returns:
        "notion" → Notion is newer → update Trello
        "trello" → Trello is newer → update Notion
    """
    notion_time = parse_time_iso(lead.get("last_edited_time"))
    trello_time = parse_time_iso(card.get("dateLastActivity"))

    # If both timestamps exist, compare normally
    if notion_time and trello_time:
        return "notion" if notion_time > trello_time else "trello"

    # Only Notion time exists → use Notion
    if notion_time and not trello_time:
        return "notion"

    # Only Trello time exists → use Trello
    if trello_time and not notion_time:
        return "trello"

    # Neither exists → default to Trello as source (deterministic fallback)
    return "trello"


def sync_notion_to_trello():
    """
    Create Trello cards for new Notion leads and move existing cards to match Notion,
    but only when Notion is the newer source (by timestamp).
    """
    leads = parse_leads()
    cards = get_cards()
    trello_by_id = {c["id"]: c for c in cards}

    print(f"Notion leads: {len(leads)}, Trello cards: {len(cards)}")

    for lead in leads:
        lead_id = lead.get("id")
        name = lead.get("name") or "(No Name)"
        status = lead.get("status")
        card_id = lead.get("trello_card_id")

        if not status:
            # nothing to map
            continue

        # create card if missing
        if not card_id:
            new_id = create_card(name, lead_id)
            if new_id:
                set_trello_card_id(lead_id, new_id)
                print(f"Created Trello card for lead: {name}")
            continue

        # card exists — find it
        card = trello_by_id.get(card_id)
        if not card:
            # card not found on board (maybe deleted) — skip for simplicity
            print(f"Card {card_id} for lead {name} not found in Trello; skipping")
            continue

        trello_status = LIST_TO_STATUS.get(card.get("idList"))
        if trello_status == status:
            # already in sync
            continue

        # decide which side is newer
        if choose_and_sync_decision(lead, card) == "notion":
            move_card(card_id, status)
            print(f"Moved card '{name}' to list '{status}'")
        else:
            # Trello is newer; skip Notion->Trello move
            # Let sync_trello_to_notion handle updating Notion if needed
            continue


def sync_trello_to_notion():
    """
    Update Notion lead statuses when Trello is the newer source (by timestamp).
    """
    cards = get_cards()
    leads = parse_leads()
    lead_by_card = {lead["trello_card_id"]: lead for lead in leads if lead.get("trello_card_id")}

    print(f"Found {len(cards)} trello cards, {len(lead_by_card)} linked to Notion leads")

    for card in cards:
        cid = card.get("id")
        if cid not in lead_by_card:
            continue

        lead = lead_by_card[cid]
        desired_status = LIST_TO_STATUS.get(card.get("idList"))
        if not desired_status:
            # unmapped list
            continue

        if desired_status == lead.get("status"):
            # already in sync
            continue

        if choose_and_sync_decision(lead, card) == "trello":
            update_lead_status(lead["id"], desired_status)
            print(f"Updated Notion lead '{lead.get('name')}' → {desired_status}")
        else:
            # Notion is newer; skip
            continue


def run_sync():
    """Run both directions (Trello->Notion first; final changes decided by timestamps)."""
    print("Running sync...")
    sync_trello_to_notion()
    sync_notion_to_trello()
    print("Sync done.")
