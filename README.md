# Learntinuum

> *Because "I'll find it later" is how learning dies.*

You're 40 minutes into a great YouTube video on your laptop. Life happens. You pick up your phone later and spend the next 10 minutes scrubbing through trying to find where you left off. By that point, the momentum is gone.

Learntinuum is a personal Telegram bot that solves exactly this. Paste a YouTube URL with a timestamp, and it remembers where you are — across every device, forever.

---

## Features

### Topic-based organisation
Group your learning into topics — *MCP*, *Linear Algebra*, *System Design*, whatever you're working through. Videos and playlists live under topics, not in one flat chaotic list.

### Video tracking
Paste any YouTube URL. The bot extracts the video ID and timestamp, fetches the title via `yt-dlp`, and saves it under your chosen topic. Send the same URL later with a new timestamp and it updates in place — no duplicates, no friction.

### Playlist tracking
Paste a YouTube playlist URL (the kind with `list=` in it). The bot fetches the full playlist metadata, stores every video ID, and tracks exactly which video you're on and where within it. Update your position by pasting the URL again with the current video and timestamp.

**On Android?** The YouTube app's share button strips playlist context from the URL. Learntinuum handles this — if you send a bare video URL, it checks whether that video belongs to any of your tracked playlists and updates the position automatically. One-time setup per playlist, then it just works.

### Resume anywhere
Hit Resume from the main menu and get a deep link straight to your last position — correct video, correct timestamp, playlist context intact. Open it on any device and YouTube drops you exactly where you left off.

### Mark complete / Remove
Keep your active list clean. Mark a video or playlist as done, or remove it entirely. Removing a topic cascades — everything under it goes with it.

### Persistent across restarts
The bot remembers its last UI message and cleans it up on restart, so you always have one clean interface rather than a chat full of orphaned keyboards.

---

## How it works

Everything is inline keyboard driven after `/start` — no commands to memorise.

```
/start
  ├── Resume
  │     └── deep link to most recently accessed video or playlist
  │
  ├── Add Topic
  │     └── type a name → topic created
  │
  └── View Topics
        └── topic list → pick a topic
              ├── Videos
              │     └── [Title] → Resume  Complete  Remove
              └── Playlists
                    └── [Title (video X/Y)] → Resume  Complete  Remove
```

**Sending a YouTube URL:**
```
URL received
  ├── has list= param → playlist flow
  │     ├── already tracked → update video index + timestamp, confirm
  │     └── new → fetch metadata → pick topic (or create one from playlist title)
  │
  └── no list= param → video flow
        ├── matches a tracked playlist video → update playlist position (Android flow)
        ├── already tracked as standalone → update timestamp, confirm
        └── new → pick topic → fetch title → save
```

URLs without a timestamp default to `0:00`.

---

## Tech Stack

| Layer | Tool |
|---|---|
| Bot framework | `python-telegram-bot` v20+ (async) |
| Video & playlist metadata | `yt-dlp` |
| Database | SQLite |
| Config | `python-dotenv` |
| Scheduler *(future)* | `APScheduler` |

---

## Project Structure

```
learntinuum/
│
├── main.py                  # Entry point, startup hook
├── config.py                # Loads env vars
│
├── bot/
│   ├── handlers.py          # All update handlers and flow logic
│   └── keyboards.py         # Inline keyboard builders
│
├── db/
│   ├── database.py          # Schema init and connection helper
│   └── crud.py              # All DB read/write operations
│
├── services/
│   ├── youtube.py           # yt-dlp video + playlist metadata fetching
│   └── scheduler.py         # Reserved for future learning nudges
│
├── utils/
│   └── url_parser.py        # YouTube URL, video ID, playlist ID, timestamp extraction
│
└── requirements.txt
```

---

## Setup

### 1. Clone and create a virtual environment
```bash
git clone <your-repo-url>
cd learntinuum
python -m venv env
source env/bin/activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

`yt-dlp` requires a JavaScript runtime for YouTube extraction. Install Node.js if you don't have it:
```bash
# via nvm
nvm install --lts && nvm use --lts

# or directly
sudo apt install nodejs
```

### 3. Create your Telegram bot

1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow the prompts
3. BotFather will return a **bot token** — looks like `123456789:ABCdefGHI...` — save this

### 4. Get your Chat ID

The bot only responds to one chat ID, keeping it private to you.

1. Search for [@userinfobot](https://t.me/userinfobot) on Telegram
2. Send it any message — it replies with your **Chat ID** (a number like `987654321`)

### 5. Create a `.env` file

```env
BOT_TOKEN=your_bot_token_here
CHAT_ID=your_chat_id_here
```

### 6. Run

```bash
python main.py
```

Send `/start` to your bot in Telegram. The main menu will appear.

---

## Running as a service

To run the bot in the background with automatic restarts (e.g. on a Raspberry Pi or VPS), create a systemd service:

`/etc/systemd/system/learntinuum.service`
```ini
[Unit]
Description=Learntinuum bot
After=network.target

[Service]
Type=simple
WorkingDirectory=/path/to/learntinuum
ExecStart=/path/to/env/bin/python3 /path/to/learntinuum/main.py
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable learntinuum
sudo systemctl start learntinuum
```

`WorkingDirectory` must point to the project root — the database path is relative to it.

---

## Database

Learntinuum uses a local SQLite file (`learning.db`).

| Table | Purpose |
|---|---|
| `topics` | User-defined topic groups |
| `videos` | Standalone tracked videos |
| `playlists` | Tracked playlists with current position |
| `playlist_videos` | All video IDs per playlist, used for Android reverse lookup |
| `settings` | Internal key-value store (e.g. last UI message ID) |

**Migrating to a new device** — stop the bot first, then:
```bash
# Export
sqlite3 learning.db .dump > backup.sql

# Import on the new machine
sqlite3 learning.db < backup.sql
```

---

## Roadmap

- [x] YouTube video tracking with timestamps
- [x] YouTube playlist tracking with per-video position
- [x] Android reverse lookup — bare video URLs matched to tracked playlists
- [x] Topic-based organisation with cascade delete
- [x] Resume from any device
- [x] Persistent UI across bot restarts
- [ ] Support for blog posts, Reddit threads, Medium articles
- [ ] Quiz module — turn watched content into active recall
- [ ] Learning nudges — reminders for content you haven't touched in a while
- [ ] REST API backend
- [ ] MCP-compatible tool interface

---

*Built for personal use. Turns out the problem was common enough to make it worth building properly.*