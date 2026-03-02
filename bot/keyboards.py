from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def build_main_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("▶️ Resume", callback_data="menu_resume")],
        [
            InlineKeyboardButton("➕ Add Topic", callback_data="menu_add_topic"),
            InlineKeyboardButton("📚 View Topics", callback_data="menu_view_topics"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_topics_keyboard(topics, callback_prefix: str = "topic") -> InlineKeyboardMarkup:
    keyboard = []
    for topic in topics:
        keyboard.append([
            InlineKeyboardButton(
                text=f"📂 {topic['name']}",
                callback_data=f"{callback_prefix}_{topic['id']}",
            )
        ])
    keyboard.append([InlineKeyboardButton("« Back", callback_data="menu_back")])
    return InlineKeyboardMarkup(keyboard)


def build_videos_keyboard(videos) -> InlineKeyboardMarkup:
    """
    For each active video renders:
      [ 🎬 Video Title ]
      [ ▶️ Resume   ✅ Complete   🗑 Remove ]
    """
    keyboard = []
    for video in videos:
        title = video["title"]
        short_title = title if len(title) <= 35 else title[:32] + "…"
        keyboard.append([
            InlineKeyboardButton(
                text=f"🎬 {short_title}",
                callback_data=f"noop_{video['id']}",
            )
        ])
        keyboard.append([
            InlineKeyboardButton("▶️ Resume",   callback_data=f"vresume_{video['id']}"),
            InlineKeyboardButton("✅ Complete", callback_data=f"vcomplete_{video['id']}"),
            InlineKeyboardButton("🗑 Remove",   callback_data=f"vremove_{video['id']}"),
        ])

    keyboard.append([InlineKeyboardButton("« Back to Topics", callback_data="menu_view_topics")])
    keyboard.append([InlineKeyboardButton("« Main Menu",      callback_data="menu_back")])
    return InlineKeyboardMarkup(keyboard)


def build_save_video_keyboard(active_topic, all_topics) -> InlineKeyboardMarkup:
    """
    Shown when user sends a URL and a topic is already active.
    Top button = confirm current topic. Rest = switch to another. Bottom = cancel.
    """
    keyboard = [
        [InlineKeyboardButton(
            f"✅ Save to '{active_topic['name']}'",
            callback_data=f"picktopic_{active_topic['id']}",
        )]
    ]
    for topic in all_topics:
        if topic["id"] == active_topic["id"]:
            continue
        keyboard.append([
            InlineKeyboardButton(
                f"📂 {topic['name']}",
                callback_data=f"picktopic_{topic['id']}",
            )
        ])
    keyboard.append([InlineKeyboardButton("« Cancel", callback_data="menu_back")])
    return InlineKeyboardMarkup(keyboard)