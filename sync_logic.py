import os
from dateutil.parser import isoparse
from notion_client import parse_leads, set_trello_card_id, update_lead_status
from trello_client import create_card, move_card, get_cards

GRACE_SECONDS = int(os.getenv("SYNC_GRACE_SECONDS", "30"))

# Read Trello list IDs from .env
LIST_TODO = os.getenv("TRELLO_LIST_TODO")
LIST_INPROGRESS = os.getenv("TRELLO_LIST_INPROGRESS")
LIST_DONE = os.getenv("TRELLO_LIST_DONE")
LIST_LOST = os.getenv("TRELLO_LIST_LOST")

# Map ID to Status
LIST_TO_STATUS = {
    LIST_TODO: "New",
    LIST_INPROGRESS: "Contacted",
    LIST_DONE: "Qualified",
    LIST_LOST: "Lost",
}
# Reverse mapping for convenience (notion status to list id)
STATUS_TO_LIST = {v: k for k, v in LIST_TO_STATUS.items()}


def parse_time_iso(s):
    """Parse ISO timestamp to datetime (aware of timezone). Return None on failure."""
    if not s:
        return None
    try:
        return isoparse(s)
    except Exception:
        return None


def choose_and_sync_decision(lead, card):
    """Decide which system (Notion or Trello) should be treated as the source of truth. Returns "notion" or "trello"."""
    notion_time = parse_time_iso(lead.get("last_edited_time"))
    trello_time = parse_time_iso(card.get("dateLastActivity"))

    if notion_time and trello_time:
        if notion_time > trello_time:
            return "notion"
        # If Trello is only slightly newer, prefer Notion
        if (trello_time - notion_time).total_seconds() <= GRACE_SECONDS:
            return "notion"
        return "trello"

    if notion_time and not trello_time:
        return "notion"
    if trello_time and not notion_time:
        return "trello"

    # fallback
    return "trello"

def sync_notion_to_trello():
    """Create Trello cards for new Notion leads and move existing cards to match Notion"""
    """But only when Notion is determined to be the newer source."""
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
            continue

        # create card if missing
        if not card_id:
            new_id = create_card(name, lead_id)
            if new_id:
                set_trello_card_id(lead_id, new_id)
                print(f"Created Trello card for lead: {name}")
            continue

        # card exists: find it on board
        card = trello_by_id.get(card_id)
        if not card:
            print(f"Card {card_id} for lead {name} not found in Trello; skipping")
            continue

        trello_status = LIST_TO_STATUS.get(card.get("idList"))
        if trello_status == status:
            # already in sync
            continue

        # decide and act only if notion is winner
        decision = choose_and_sync_decision(lead, card)
        if decision == "notion":
            # Print the minimal decision message then act
            print(f"[Decision] Notion Update is newer for '{name}'")
            move_card(card_id, status)
            print(f"Moved card '{name}' to list '{status}'")
        else:
            # Trello is newer so do not override here
            continue

def sync_trello_to_notion():
    """Update Notion lead statuses when Trello is the newer source."""
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
            continue

        if desired_status == lead.get("status"):
            continue

        decision = choose_and_sync_decision(lead, card)
        if decision == "trello":
            # Print decision message then act
            print(f"[Decision] Trello Update is newer for '{lead.get('name')}'")
            update_lead_status(lead["id"], desired_status)
            print(f"Updated Notion lead '{lead.get('name')}' to {desired_status}")
        else:
            # Notion newer, so skip
            continue


def run_sync():
    """Run both directions (Trello to Notion first. Final changes decided by timestamps)."""
    print("Running sync...")
    sync_trello_to_notion()
    sync_notion_to_trello()
    print("Sync done.")
