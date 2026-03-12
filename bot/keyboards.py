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
    if callback_prefix == "picktopic":
        keyboard.append([InlineKeyboardButton("➕ Create New Topic", callback_data="menu_new_topic_for_video")])
    keyboard.append([InlineKeyboardButton("« Back", callback_data="menu_back")])
    return InlineKeyboardMarkup(keyboard)


def build_videos_keyboard(videos, playlists) -> InlineKeyboardMarkup:
    """
    Renders two sections:
      🎬 Videos — each with Resume / Complete / Remove
      📋 Playlists — each with Resume / Complete / Remove
    """
    keyboard = []

    if videos:
        keyboard.append([InlineKeyboardButton("── 🎬 Videos ──", callback_data="noop_section")])
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

    if playlists:
        keyboard.append([InlineKeyboardButton("── 📋 Playlists ──", callback_data="noop_section")])
        for pl in playlists:
            title = pl["title"]
            short_title = title if len(title) <= 35 else title[:32] + "…"
            index_display = f"video {pl['current_index'] + 1}/{pl['total_videos']}"
            keyboard.append([
                InlineKeyboardButton(
                    text=f"📋 {short_title} ({index_display})",
                    callback_data=f"noop_{pl['id']}",
                )
            ])
            keyboard.append([
                InlineKeyboardButton("▶️ Resume",   callback_data=f"presume_{pl['id']}"),
                InlineKeyboardButton("✅ Complete", callback_data=f"pcomplete_{pl['id']}"),
                InlineKeyboardButton("🗑 Remove",   callback_data=f"premove_{pl['id']}"),
            ])

    keyboard.append([InlineKeyboardButton("« Back to Topics", callback_data="menu_view_topics")])
    keyboard.append([InlineKeyboardButton("« Main Menu",      callback_data="menu_back")])
    return InlineKeyboardMarkup(keyboard)


def build_save_video_keyboard(active_topic, all_topics) -> InlineKeyboardMarkup:
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
    keyboard.append([InlineKeyboardButton("➕ Create New Topic", callback_data="menu_new_topic_for_video")])
    keyboard.append([InlineKeyboardButton("« Cancel", callback_data="menu_back")])
    return InlineKeyboardMarkup(keyboard)

def build_save_playlist_keyboard(active_topic, all_topics, playlist_title) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(
            f"📋 Create topic '{playlist_title[:30]}'",
            callback_data="menu_use_playlist_title_as_topic",
        )],
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
    keyboard.append([InlineKeyboardButton("➕ Create New Topic", callback_data="menu_new_topic_for_video")])
    keyboard.append([InlineKeyboardButton("« Cancel", callback_data="menu_back")])
    return InlineKeyboardMarkup(keyboard)


def build_pick_playlist_topic_keyboard(all_topics, playlist_title) -> InlineKeyboardMarkup:
    """Used when there's no active topic — still offer the playlist title option."""
    keyboard = [
        [InlineKeyboardButton(
            f"📋 Create topic '{playlist_title[:30]}'",
            callback_data="menu_use_playlist_title_as_topic",
        )]
    ]
    for topic in all_topics:
        keyboard.append([
            InlineKeyboardButton(
                f"📂 {topic['name']}",
                callback_data=f"picktopic_{topic['id']}",
            )
        ])
    keyboard.append([InlineKeyboardButton("➕ Create New Topic", callback_data="menu_new_topic_for_video")])
    keyboard.append([InlineKeyboardButton("« Cancel", callback_data="menu_back")])
    return InlineKeyboardMarkup(keyboard)

def build_topics_keyboard(topics, callback_prefix: str = "topic") -> InlineKeyboardMarkup:
    keyboard = []
    for topic in topics:
        row = [
            InlineKeyboardButton(
                text=f"📂 {topic['name']}",
                callback_data=f"{callback_prefix}_{topic['id']}",
            )
        ]
        # Only show remove button in normal view, not when picking a topic for a video
        if callback_prefix == "topic":
            row.append(InlineKeyboardButton("🗑", callback_data=f"topicremove_{topic['id']}"))
        keyboard.append(row)
    if callback_prefix == "picktopic":
        keyboard.append([InlineKeyboardButton("➕ Create New Topic", callback_data="menu_new_topic_for_video")])
    keyboard.append([InlineKeyboardButton("« Back", callback_data="menu_back")])
    return InlineKeyboardMarkup(keyboard)