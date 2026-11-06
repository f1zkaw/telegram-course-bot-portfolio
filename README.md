# Telegram Course Bot — Portfolio Edition

A public **demonstration** of a Python Telegram bot architecture based on a commissioned educational automation project. The demo includes **no original client content, tokens, user database, customer media, brand names or private links**.

> **Publication rights:** Anonymization does not transfer copyright. Publish this adapted implementation only if your agreement/permissions allow you to share the work. Otherwise use a separately authored sample project and describe the commissioned work without publishing its source.

## Stack

- Python 3.11+
- [`python-telegram-bot`](https://github.com/python-telegram-bot/python-telegram-bot) 20.8 (asyncio)
- SQLite (`sqlite3` from Python standard library)
- `python-dotenv` for local configuration
- `unittest` for offline logic/storage tests

## Features

- Commands `/start` and `/cancel`; guided menus and conversation states
- Three placeholder lessons, progress persistence, gated access
- **No-charge demo unlock** (default, `PAYMENT_MODE=demo`)
- Optional Telegram invoice integration (`PAYMENT_MODE=telegram`) with payload, amount and currency validation; requires **your own** configured payment provider and independent compliance/testing
- Daily message with a **persistent** 24-hour cooldown
- Consultation request stored in SQLite; optional admin notice
- Optional local demo media under `assets/` (not included)
- SQL parameters, environment-only credentials, local data excluded from Git

## Quick start (Windows PowerShell)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Create **your own test bot** using Telegram BotFather and set `BOT_TOKEN` in `.env`. Keep `PAYMENT_MODE=demo` for initial tests. Then run:

```powershell
python bot.py
```

Open your own Telegram bot, send `/start`, choose `Курс` → `Продолжить`. The sample lessons unlock **without charging money**.

## Testing

Unit tests do not require Telegram credentials or the third-party package:

```bash
python -m unittest discover -s tests -v
```

## Project structure

```text
telegram-bot-portfolio/
├── bot.py              # Telegram handlers and navigation
├── config.py           # Environment-based configuration
├── content.py          # Fictional lessons and tips
├── storage.py          # SQLite schema and queries
├── services.py         # Testable pure business rules
├── tests/              # Unit tests
├── .env.example        # Empty, safe configuration example
├── .gitignore          # Secret, database and media exclusions
├── requirements.txt
└── README.md
```

## Data and privacy

The local `bot_data.db` file contains user IDs and user-entered consultation requests. **Never upload it to GitHub.** This educational demo does not implement production-grade retention periods, deletion workflows, payments reconciliation, consent/notice, concurrency or administrative security. Do not treat it as a production-ready payment application.

## What was intentionally removed

- Any actual Telegram bot token or billing provider credential
- Administrator IDs, customer identity, specific services and commercial prices
- Lesson scripts, video URLs, copyrighted media and mind-map links
- Offensive/client-specific humor and branding
- Production payment database, log files, user messages and identifiers

## Disclosure

**Unofficial educational portfolio demo.** Not a deployed version of the client's system. It demonstrates similar engineering patterns; no claim of permission to publish the original project or of tested production payments.
