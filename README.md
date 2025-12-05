🚀 Notion ↔ Trello Two-Way Sync

A lightweight automation system that keeps Notion leads and Trello tasks in continuous two-way sync.
Built in Python using real REST APIs. Created as part of the DeepLogic AI Automation & Integrations assignment.

📌 Overview

Lead Tracker: Notion database

Work Tracker: Trello board

When a Notion lead is created → a Trello task is created

When lead status changes → Trello card moves to correct list

When Trello card moves → Notion lead status updates

No duplicates (idempotent)

Uses timestamp comparison + small grace window

Includes error handling, retry logic, logging
