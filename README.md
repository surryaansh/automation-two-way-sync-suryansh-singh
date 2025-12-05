🚀 Notion ↔ Trello Two-Way Sync

A lightweight automation system that keeps Notion leads and Trello tasks in continuous two-way sync.
Built in Python using real REST APIs. Created as part of the DeepLogic AI Automation & Integrations assignment.

📌 Overview

- Lead Tracker: Notion database
- Work Tracker: Trello board
- When a Notion lead is created → a Trello task is created
- When lead status changes → Trello card moves to correct list
- When Trello card moves → Notion lead status updates
- No duplicates (idempotent)
- Uses timestamp comparison + small grace window
- Includes error handling, retry logic, logging

🏗 Architecture

Notion Leads  <------>  sync_logic.py  <------>  Trello Tasks
   (API)                     |                      (API)

| Notion Status | Trello List |
| ------------- | ----------- |
| New           | To Do       |
| Contacted     | In Progress |
| Qualified     | Done        |
| Lost          | Lost        |

📁 Project Structure

notion_client.py     # Notion API wrapper
trello_client.py     # Trello API wrapper
sync_logic.py        # Two-way sync logic + decisions
main.py              # Entry point
.env.example         # Sample env file
requirements.txt




