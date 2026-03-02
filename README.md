# 📚 Learntinuum

> *Because "I'll find it later" is how learning dies.*

You're 40 minutes into a great YouTube video on your laptop. Life happens. You pick up your phone an hour later and spend the next 10 minutes scrubbing through the video trying to find where you were. By that point, the momentum is gone.

**Learntinuum** is a personal Telegram bot that solves exactly this. Paste a YouTube URL with a timestamp, and it remembers where you are. Pick it back up from any device, any time.

---

## ✨ What it does

- 📌 **Tracks YouTube videos by topic** — organise what you're learning, not just a flat list of links
- ⏱ **Saves your exact position** — paste a URL with a timestamp and it stores it; paste it again later and it updates
- ▶️ **One-tap resume** — get a deep link straight to your last position, ready to open on any device
- ✅ **Mark complete / 🗑 Remove** — keep your active list clean
- 🤖 **Fully inline keyboard UI** — no commands to remember after `/start`

---

## 🔁 How it works

```
/start
  ├── ▶️ Resume          → sends you a deep link to your most recently active video
  ├── ➕ Add Topic       → type a topic name to organise your videos under
  └── 📚 View Topics     → browse topics → see active videos → Resume / Complete / Remove
```

**Sending a YouTube URL:**
- If the video is already tracked → timestamp gets updated, bot confirms
- If it's new → bot asks which topic to file it under (or confirms your last-used topic)
- No timestamp in the URL? Defaults to `0:00`

---

## 🛠 Tech Stack

| Layer | Tool |
|---|---|
| Bot framework | `python-telegram-bot` v20+ (async) |
| Video metadata | `yt-dlp` |
| Database | SQLite via `sqlite3` |
| Config | `python-dotenv` |
| Scheduler *(future)* | `APScheduler` |

---

## 🗂 Project Structure

```
learntinuum/
│
├── main.py                  # Entry point
├── config.py                # Loads env vars
│
├── bot/
│   ├── handlers.py          # All update handlers and conversation logic
│   └── keyboards.py         # Inline keyboard builders
│
├── db/
│   ├── database.py          # Schema init and connection helper
│   └── crud.py              # All DB read/write operations
│
├── services/
│   ├── youtube.py           # yt-dlp metadata fetching
│   └── scheduler.py         # Reserved for future learning nudges
│
├── utils/
│   └── url_parser.py        # YouTube URL and timestamp extraction
│
└── requirements.txt
```

---

## ⚙️ Setup

**1. Clone and create a virtual environment**
```bash
git clone <your-repo-url>
cd learntinuum
python -m venv env
source env/bin/activate
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Create a `.env` file in the project root**
```env
BOT_TOKEN=your_telegram_bot_token_here
CHAT_ID=your_telegram_chat_id_here
```

> `BOT_TOKEN` — get this from [@BotFather](https://t.me/BotFather)  
> `CHAT_ID` — the bot only responds to this chat ID, keeping it private to you. You can get yours from [@userinfobot](https://t.me/userinfobot)

**4. Run**
```bash
python main.py
```

---

## 🗺 Roadmap

- [x] YouTube video tracking with timestamps
- [x] Topic-based organisation
- [x] Resume from any device
- [ ] Support for blog posts, Reddit threads, Medium articles
- [ ] Quiz module — turn your watched content into active recall
- [ ] Learning nudges — scheduled reminders for videos you haven't touched in a while
- [ ] REST API backend
- [ ] MCP-compatible tool interface

---

*Built for personal use. Works best when you actually use it.*