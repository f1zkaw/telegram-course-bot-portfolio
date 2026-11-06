# Telegram Course Bot — Portfolio Edition

**Python Telegram bot for educational content delivery and automated user interactions.**

A portfolio-safe adaptation of a bot developed for a client project. The public version uses fictional course content, a local SQLite database and a free demo-access flow. It does **not** contain client data, real credentials or paid educational materials.

## Features

- **Interactive conversations:** `/start`, `/cancel`, reply keyboards and inline buttons.
- **Course access management:** three sample lessons, access checks and saved lesson progress.
- **Demo payment flow:** free course unlock by default (`PAYMENT_MODE=demo`), without charging users.
- **Optional invoice example:** Telegram payment handlers with order validation. Live payments are not configured or tested in this portfolio edition.
- **SQLite persistence:** user records, consultation requests, lesson progress and payment records.
- **Daily content:** a 24-hour cooldown that persists across bot restarts.
- **Admin notifications:** optional notification when a consultation request arrives.
- **Media support:** optional local demo videos, without distributing client media.

## Tech stack

| Technology | Purpose |
| --- | --- |
| Python 3.11+ | Core application |
| python-telegram-bot 20.8 | Asynchronous Telegram bot handlers |
| SQLite | Local data persistence |
| python-dotenv | Environment-based configuration |
| unittest | Unit testing |

## Project structure

```text
telegram-course-bot-portfolio/
├── bot.py                 # Telegram commands, menus and conversations
├── config.py              # Configuration loaded from environment variables
├── content.py             # Fictional demo lessons and messages
├── storage.py             # SQLite tables and database operations
├── services.py            # Reusable business rules
├── test_storage.py        # Storage and logic unit tests
├── requirements.txt       # Python dependencies
├── .env.example           # Template for local configuration
├── .gitignore             # Excludes secrets, databases and media
└── README.md
```

## Getting started

**Requirements:** Python 3.11 or newer and your own test bot created through [@BotFather](https://t.me/BotFather).

### Windows (PowerShell)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit the new `.env` file and set `BOT_TOKEN` to the token of **your own test bot**. Keep `PAYMENT_MODE=demo`.

Start the bot:

```powershell
python bot.py
```

Open your bot in Telegram, send `/start`, then select **Курс → Продолжить**. Demo access is granted for free, and you can open the sample lessons.

**Never commit `.env`, tokens, user databases or actual client assets.**

## Testing

Run the unit tests from the repository root:

```bash
python -m unittest test_storage -v
```

The suite currently contains **7 unit tests** covering database state, course access and progress, duplicate payment records, daily cooldown and checkout parameter validation. These are local unit tests; they are **not** end-to-end Telegram or live payment tests.

## Key engineering decisions

- Separate Telegram handlers (`bot.py`) from persistence (`storage.py`) and reusable rules (`services.py`).
- Use parameterized SQL queries when writing user-supplied data.
- Read secrets from environment variables rather than hard-coding credentials.
- Keep payments in a non-charging demo mode unless explicitly configured and separately tested.
- Use a unique payment provider charge ID to avoid recording the same payment twice.

## Project status and privacy

**Status:** portfolio demonstration, not a production deployment.

This repository contains anonymized demonstration content. The client's original database, media, course texts, identifiers and credentials are not included. The demo does not claim production-grade payment reconciliation, consent workflows, data-retention controls or deployment hardening.

The public repository is provided to demonstrate Python backend and Telegram automation patterns developed in a client-work context. It is not the client's deployed bot.
