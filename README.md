# LearnTinuum

A personal Telegram bot for tracking learning progress accross sources like YouTube videos, reddit, blogposts, medium articles etc.

## Features (Phase 1)

- Paste a YouTube URL with timestamp
- Extract video metadata using yt-dlp
- Assign video to a topic
- Resume videos later from saved timestamp
- Persistent storage using SQLite

## Architecture

The project is structured into clear layers:

learning_bot/
│
├── main.py               # Entry point
├── config.py             # Configuration values
│
├── bot/                  # Telegram interaction layer
│   ├── handlers.py
│   ├── keyboards.py
│
├── db/                   # Persistence layer
│   ├── database.py
│   ├── crud.py
│   ├── models.py
│
├── services/             # Business logic layer
│   ├── youtube.py
│   ├── scheduler.py
│
├── utils/                # Utility helpers
│   ├── url_parser.py
│
└── requirements.txt

## Tech Stack

- python-telegram-bot (async v20+)
- yt-dlp
- SQLite
- APScheduler (future use)

## Setup

1. Create virtual environment:

   python -m venv venv
   source venv/bin/activate

2. Install dependencies:

   pip install -r requirements.txt

3. Create config.py and add your Telegram token:

   TELEGRAM_TOKEN = "YOUR_TOKEN_HERE"

4. Run the bot:

   python main.py

## Future Phases

- Quiz module
- Smart answer validation
- Learning nudges
- REST API backend
- MCP-compatible tool interface