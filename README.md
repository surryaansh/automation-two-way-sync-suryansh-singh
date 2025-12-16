# 🚀 Notion ↔ Trello Two-Way Sync

A lightweight automation system that keeps Notion leads and Trello tasks in a continuous two-way sync.
Built in Python using real REST APIs. Created as part of the DeepLogic AI's "Software Engineer: Automation & Integrations" assignment.

# 📌 Overview

- Lead Tracker: Notion database
- Work Tracker: Trello board
- When a Notion lead is created → a Trello task is created
- When lead status changes → Trello card moves to correct list
- When Trello card moves → Notion lead status updates
- No duplicates (idempotent)
- Uses timestamp comparison + small grace window
- Includes error handling, retry logic, logging

# 🏗 Architecture

Notion Leads  <------>  sync_logic.py  <------>  Trello Tasks
   (API)                     |                      (API)

| Notion Status | Trello List |
| ------------- | ----------- |
| New           | To Do       |
| Contacted     | In Progress |
| Qualified     | Done        |
| Lost          | Lost        |


# 📁 Project Structure

- notion_client.py
- trello_client.py
- sync_logic.py (Two-way sync logic + decisions)
- main.py
- .env.example
- requirements.txt

# 🔧 Setup

## 1️⃣ Clone
git clone https://github.com/surryaansh/automation-two-way-sync-suryansh-singh

## 2️⃣ Notion Setup
- Create an Internal Integration at https://www.notion.so/my-integrations
- Copy token → share your database with it
- Copy Notion database ID from the URL

## 3️⃣ Trello Setup
- Create Power-up and get API key: https://trello.com/power-ups/admin
- Generate token on same page (from the hyperlink “Token” on the right side of API Key)
- Get list IDs by opening board JSON (simply add “.json” at the end of the url on boards webpage

## 4️⃣ Create .env
- NOTION_TOKEN=xxx
- NOTION_DATABASE_ID=xxx
- TRELLO_KEY=xxx
- TRELLO_TOKEN=xxx
- TRELLO_BOARD_ID=xxx
- TRELLO_LIST_TODO=xxx
- TRELLO_LIST_INPROGRESS=xxx
- TRELLO_LIST_DONE=xxx
- TRELLO_LIST_LOST=xxx

## 5️⃣ Install deps
pip install -r requirements.txt

# ▶️ Running the Sync
## python3 main.py

### Example Output:

Running sync...
[Decision] Trello Update is newer for 'Test_Name'
Moved card 'Test_Name' to list 'Qualified'
Sync done.

### You can test by:
- Creating a lead in Notion -> Trello card appears
- Changing status in Notion -> Trello card moves
- Dragging card in Trello -> Notion status updates

### Idempotent: running sync repeatedly does not duplicate cards.

# ⚙️ Error Handling & Idempotency

- safe_request() retry wrapper prevents crashes
- Duplicate prevention using TrelloCardID stored in Notion
- Grace window avoids false conflicts
- Timestamp comparison decides which system is newer

# 🧪 Assumptions & Limitations

- Polling-based (no webhooks)
- Limited to main statuses
- Small timestamp differences possible between tools

# 🤖 AI Usage Notes
Used ChatGPT for:

- Mostly used for understanding how and where to find API + secret + token keys for Trello (I'm new to Trello)
- To find List IDs by adding .json at the URL end
- Creating API Error Handling wrapper for notion and trello client
- Understanding timestamp loopholes and fixing errors
- Drafting README structure

One suggestion I rejected: AI proposed using a webhook architecture; I simplified to polling to keep the implementation clear and aligned with assignment scope.

