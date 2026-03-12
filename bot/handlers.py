from telegram import Update
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
import re
from db.crud import *
from config import CHAT_ID
from bot.keyboards import *
from utils.url_parser import *
from services.youtube import *

YOUTUBE_REGEX = r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+"


def is_authorized(update: Update) -> bool:
    return str(update.effective_chat.id) == str(CHAT_ID)


def format_duration(seconds: int) -> str:
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def make_resume_url(video_id: str, position: int) -> str:
    return f"https://www.youtube.com/watch?v={video_id}&t={position}s"


def make_playlist_resume_url(video_id: str, playlist_id: str, index: int, position: int) -> str:
    return f"https://www.youtube.com/watch?v={video_id}&list={playlist_id}&index={index + 1}&t={position}s"


def escape_md(text: str) -> str:
    special = r'\_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{c}' if c in special else c for c in str(text))


# ========================
# HELPERS
# ========================

async def _edit_ui(context, chat_id, text, reply_markup, parse_mode="MarkdownV2"):
    msg_id = context.user_data.get("ui_message_id") or context.bot_data.get("ui_message_id")
    
    if not msg_id:
        print(f"[_edit_ui] No msg_id found, sending new message")
    
    if msg_id:
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=msg_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
            )
            print(f"[_edit_ui] ✅ Edited message {msg_id} successfully")
            return
        except Exception as e:
            print(f"[_edit_ui] ❌ Edit failed for msg {msg_id}: {e}")
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
                print(f"[_edit_ui] 🗑 Deleted old message {msg_id}")
            except Exception as e2:
                print(f"[_edit_ui] ❌ Delete also failed: {e2}")

    msg = await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=reply_markup,
        parse_mode=parse_mode,
    )
    print(f"[_edit_ui] 📨 Sent new message {msg.message_id}")
    context.user_data["ui_message_id"] = msg.message_id
    context.bot_data["ui_message_id"] = msg.message_id
    set_setting("ui_message_id", str(msg.message_id))

# ========================
# START
# ========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return

    old_msg_id = context.user_data.get("ui_message_id") or context.bot_data.get("ui_message_id")
    if old_msg_id:
        try:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=old_msg_id,
            )
        except Exception:
            pass

    msg = await update.effective_message.reply_text(
        "📚 *Welcome to Learntinuum*\n\nTrack your learning progress across devices\.",
        reply_markup=build_main_menu(),
        parse_mode="MarkdownV2",
    )

    context.user_data["ui_message_id"] = msg.message_id
    context.bot_data["ui_message_id"] = msg.message_id
    set_setting("ui_message_id", str(msg.message_id))
    context.user_data["state"] = None


# ========================
# MENU CALLBACKS
# ========================

async def handle_menu_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return

    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = update.effective_user.id

    # -------- ADD TOPIC --------
    if data == "menu_add_topic":
        context.user_data["state"] = "awaiting_topic_name"
        await query.edit_message_text("📝 Send me the topic name:")

    # -------- VIEW TOPICS --------
    elif data == "menu_view_topics":
        topics = sorted(get_topics(user_id), key=lambda t: t["name"].lower())
        if not topics:
            await query.edit_message_text(
                "📭 No topics yet. Add one first!",
                reply_markup=build_main_menu(),
            )
            return
        await query.edit_message_text(
            "📚 *Your Topics* — pick one to see its videos:",
            reply_markup=build_topics_keyboard(topics),
            parse_mode="MarkdownV2",
        )

    # -------- RESUME --------
    elif data == "menu_resume":
        video = get_latest_active_video(user_id)
        playlist = get_latest_active_playlist(user_id)

        if video and playlist:
            use_playlist = playlist["last_accessed"] > video["last_accessed"]
        elif playlist:
            use_playlist = True
        else:
            use_playlist = False

        if not video and not playlist:
            await query.edit_message_text(
                "📭 No active videos or playlists found\\. Add some first\\!",
                reply_markup=build_main_menu(),
                parse_mode="MarkdownV2",
            )
            return

        if use_playlist:
            pl = playlist
            url = make_playlist_resume_url(
                pl["current_video_id"], pl["playlist_id"],
                pl["current_index"], pl["current_position"],
            )
            pos_str = format_duration(pl["current_position"])
            index_display = f"{pl['current_index'] + 1}/{pl['total_videos']}"

            await query.edit_message_text(
                f"▶️ *Resume where you left off*\n\n"
                f"📋 *{escape_md(pl['title'])}*\n"
                f"📂 Topic: {escape_md(pl['topic_name'])}\n"
                f"🎬 Video: {escape_md(index_display)}\n"
                f"⏱ Position: {escape_md(pos_str)}\n\n"
                f"🔗 {escape_md(url)}",
                reply_markup=build_main_menu(),
                parse_mode="MarkdownV2",
                disable_web_page_preview=True,
            )
        else:
            v = video
            url = make_resume_url(v["video_id"], v["last_position"])
            pos_str = format_duration(v["last_position"])

            await query.edit_message_text(
                f"▶️ *Resume where you left off*\n\n"
                f"📌 *{escape_md(v['title'])}*\n"
                f"📂 Topic: {escape_md(v['topic_name'])}\n"
                f"⏱ Position: {escape_md(pos_str)}\n\n"
                f"🔗 {escape_md(url)}",
                reply_markup=build_main_menu(),
                parse_mode="MarkdownV2",
                disable_web_page_preview=True,
            )

    # -------- USE PLAYLIST TITLE AS TOPIC --------
    elif data == "menu_use_playlist_title_as_topic":
        playlist_id = context.user_data.get("pending_playlist_id")
        playlist_title = context.user_data.get("pending_playlist_title")

        if not playlist_id or not playlist_title:
            await query.edit_message_text(
                "❌ Something went wrong\\. Please send the URL again\\.",
                reply_markup=build_main_menu(),
                parse_mode="MarkdownV2",
            )
            return

        create_topic(user_id, playlist_title)
        topics = get_topics(user_id)
        match = next((t for t in topics if t["name"] == playlist_title.strip()), None)
        topic_id = match["id"] if match else None

        if not topic_id:
            await query.edit_message_text(
                "❌ Could not create topic\\. Please try again\\.",
                reply_markup=build_main_menu(),
                parse_mode="MarkdownV2",
            )
            return

        context.user_data["active_topic_id"] = topic_id
        context.user_data["state"] = None

        video_id = context.user_data.pop("pending_video_id", None)
        timestamp = context.user_data.pop("pending_timestamp", 0)
        index = context.user_data.pop("pending_playlist_index", 0)
        context.user_data.pop("pending_playlist_id", None)
        context.user_data.pop("pending_playlist_title", None)

        await _save_new_playlist(
            context, query.message.chat_id,
            topic_id, playlist_id, video_id, index, timestamp,
            query=query,
        )

    # -------- NEW TOPIC FOR VIDEO/PLAYLIST --------
    elif data == "menu_new_topic_for_video":
        context.user_data["state"] = "awaiting_topic_name_for_video"
        await query.edit_message_text("📝 Send me the new topic name:")

    # -------- BACK TO MENU --------
    elif data == "menu_back":
        context.user_data["state"] = None
        context.user_data.pop("pending_video_id", None)
        context.user_data.pop("pending_timestamp", None)
        context.user_data.pop("pending_playlist_id", None)
        context.user_data.pop("pending_playlist_index", None)
        context.user_data.pop("pending_playlist_title", None)
        context.user_data.pop("pending_playlist_meta", None)

        await query.edit_message_text(
            "📚 *Main Menu*\n\nChoose an action:",
            reply_markup=build_main_menu(),
            parse_mode="MarkdownV2",
        )


# ========================
# TOPIC SELECTION → show videos + playlists
# ========================

async def handle_topic_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return

    query = update.callback_query
    await query.answer()

    topic_id = int(query.data.split("_")[1])
    context.user_data["active_topic_id"] = topic_id

    videos = get_active_videos(topic_id)
    playlists = get_active_playlists(topic_id)

    if not videos and not playlists:
        await query.edit_message_text(
            "📂 No active videos or playlists in this topic yet\.\n\nSend a YouTube URL to add one\\!",
            reply_markup=build_main_menu(),
            parse_mode="MarkdownV2",
        )
        return

    await query.edit_message_text(
        "🎬 *Active content in this topic:*",
        reply_markup=build_videos_keyboard(videos, playlists),
        parse_mode="MarkdownV2",
    )


# ========================
# VIDEO ACTION CALLBACKS
# ========================

async def handle_topic_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return

    query = update.callback_query
    await query.answer()

    topic_id = int(query.data.split("_")[1])
    user_id = update.effective_user.id

    delete_topic(topic_id)

    # If the removed topic was the active one, clear it
    if context.user_data.get("active_topic_id") == topic_id:
        context.user_data.pop("active_topic_id", None)

    # Refresh the topics list
    topics = sorted(get_topics(user_id), key=lambda t: t["name"].lower())
    if not topics:
        await query.edit_message_text(
            "🗑 Topic removed\\.\n\n📭 No topics left\\. Add one first\\!",
            reply_markup=build_main_menu(),
            parse_mode="MarkdownV2",
        )
        return

    await query.edit_message_text(
        "🗑 Topic removed\\.\n\n📚 *Your Topics:*",
        reply_markup=build_topics_keyboard(topics),
        parse_mode="MarkdownV2",
    )

async def handle_video_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return

    query = update.callback_query
    await query.answer()

    data = query.data
    action, vid_id_str = data.split("_", 1)
    vid_db_id = int(vid_id_str)

    if action == "vresume":
        video = get_video_by_db_id(vid_db_id)
        if not video:
            await query.edit_message_text("❌ Video not found\\.", reply_markup=build_main_menu(), parse_mode="MarkdownV2")
            return

        url = make_resume_url(video["video_id"], video["last_position"])
        pos_str = format_duration(video["last_position"])

        await query.edit_message_text(
            f"▶️ *Resume*\n\n"
            f"📌 *{escape_md(video['title'])}*\n"
            f"⏱ Position: {escape_md(pos_str)}\n\n"
            f"🔗 {escape_md(url)}",
            reply_markup=build_main_menu(),
            parse_mode="MarkdownV2",
            disable_web_page_preview=True,
        )

    elif action == "vcomplete":
        mark_video_completed(vid_db_id)
        await query.edit_message_text("✅ Video marked as completed\\!", reply_markup=build_main_menu(), parse_mode="MarkdownV2")

    elif action == "vremove":
        delete_video(vid_db_id)
        await query.edit_message_text("🗑 Video removed\\.", reply_markup=build_main_menu(), parse_mode="MarkdownV2")


# ========================
# PLAYLIST ACTION CALLBACKS
# ========================

async def handle_playlist_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return

    query = update.callback_query
    await query.answer()

    data = query.data
    action, pl_id_str = data.split("_", 1)
    pl_db_id = int(pl_id_str)

    if action == "presume":
        pl = get_playlist_by_db_id(pl_db_id)
        if not pl:
            await query.edit_message_text("❌ Playlist not found\\.", reply_markup=build_main_menu(), parse_mode="MarkdownV2")
            return

        url = make_playlist_resume_url(
            pl["current_video_id"], pl["playlist_id"],
            pl["current_index"], pl["current_position"],
        )
        pos_str = format_duration(pl["current_position"])
        index_display = f"{pl['current_index'] + 1}/{pl['total_videos']}"

        await query.edit_message_text(
            f"▶️ *Resume Playlist*\n\n"
            f"📋 *{escape_md(pl['title'])}*\n"
            f"📺 Channel: {escape_md(pl['channel'] or 'Unknown')}\n"
            f"🎬 Video: {escape_md(index_display)}\n"
            f"⏱ Position: {escape_md(pos_str)}\n\n"
            f"🔗 {escape_md(url)}",
            reply_markup=build_main_menu(),
            parse_mode="MarkdownV2",
            disable_web_page_preview=True,
        )

    elif action == "pcomplete":
        mark_playlist_completed(pl_db_id)
        await query.edit_message_text("✅ Playlist marked as completed\\!", reply_markup=build_main_menu(), parse_mode="MarkdownV2")

    elif action == "premove":
        delete_playlist(pl_db_id)
        await query.edit_message_text("🗑 Playlist removed\\.", reply_markup=build_main_menu(), parse_mode="MarkdownV2")


# ========================
# TOPIC PICKER FOR NEW VIDEO/PLAYLIST
# ========================

async def handle_pick_topic_for_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return

    query = update.callback_query
    await query.answer()

    topic_id = int(query.data.split("_")[1])
    context.user_data["active_topic_id"] = topic_id
    context.user_data["state"] = None

    playlist_id = context.user_data.pop("pending_playlist_id", None)
    if playlist_id:
        video_id = context.user_data.pop("pending_video_id", None)
        timestamp = context.user_data.pop("pending_timestamp", 0)
        index = context.user_data.pop("pending_playlist_index", 0)
        context.user_data.pop("pending_playlist_title", None)
        await _save_new_playlist(
            context, query.message.chat_id,
            topic_id, playlist_id, video_id, index, timestamp,
            query=query,
        )
        return

    video_id = context.user_data.pop("pending_video_id", None)
    timestamp = context.user_data.pop("pending_timestamp", 0)

    if not video_id:
        await query.edit_message_text(
            "❌ Something went wrong\\. Please send the URL again\\.",
            reply_markup=build_main_menu(),
            parse_mode="MarkdownV2",
        )
        return

    await _save_new_video(context, query.message.chat_id, topic_id, video_id, timestamp, query=query)


# ========================
# SAVE HELPERS
# ========================

async def _save_new_video(context, chat_id, topic_id, video_id, timestamp, query=None):
    try:
        meta = fetch_video_metadata(video_id)
        title = meta.get("title") or video_id
    except Exception:
        title = video_id

    try:
        add_video(topic_id, video_id, title, timestamp)
    except Exception:
        text = "⚠️ This video already exists in the selected topic\\."
        if query:
            await query.edit_message_text(text, reply_markup=build_main_menu(), parse_mode="MarkdownV2")
        else:
            await _edit_ui(context, chat_id, text, build_main_menu())
        return

    pos_str = format_duration(timestamp)
    text = (
        f"✅ *Video added\\!*\n\n"
        f"📌 *{escape_md(title)}*\n"
        f"⏱ Starting position: *{escape_md(pos_str)}*"
    )

    if query:
        await query.edit_message_text(text, reply_markup=build_main_menu(), parse_mode="MarkdownV2")
    else:
        await _edit_ui(context, chat_id, text, build_main_menu())


async def _save_new_playlist(context, chat_id, topic_id, playlist_id, current_video_id, current_index, current_position, query=None):
    # Use stashed metadata if available to avoid double fetch
    meta = context.user_data.pop("pending_playlist_meta", None)

    if not meta:
        await _edit_ui(context, chat_id, "🔍 Fetching playlist info\.\.\.", None)
        try:
            meta = fetch_playlist_metadata(playlist_id)
        except Exception as e:
            text = f"❌ Could not fetch playlist info: {escape_md(str(e))}"
            if query:
                await query.edit_message_text(text, reply_markup=build_main_menu(), parse_mode="MarkdownV2")
            else:
                await _edit_ui(context, chat_id, text, build_main_menu())
            return

    try:
        add_playlist(
            topic_id=topic_id,
            playlist_id=playlist_id,
            title=meta["title"],
            channel=meta["channel"],
            total_videos=meta["total_videos"],
            current_video_id=current_video_id,
            current_index=current_index,
            current_position=current_position,
        )
        add_playlist_videos(playlist_id, meta["videos"])
    except Exception:
        text = "⚠️ This playlist already exists in the selected topic\\."
        if query:
            await query.edit_message_text(text, reply_markup=build_main_menu(), parse_mode="MarkdownV2")
        else:
            await _edit_ui(context, chat_id, text, build_main_menu())
        return

    pos_str = format_duration(current_position)
    index_display = f"{current_index + 1}/{meta['total_videos']}"
    text = (
        f"✅ *Playlist added\\!*\n\n"
        f"📋 *{escape_md(meta['title'])}*\n"
        f"📺 Channel: {escape_md(meta['channel'])}\n"
        f"🎬 {escape_md(str(meta['total_videos']))} videos\n"
        f"📍 Starting at video {escape_md(index_display)}, position {escape_md(pos_str)}"
    )

    if query:
        await query.edit_message_text(text, reply_markup=build_main_menu(), parse_mode="MarkdownV2")
    else:
        await _edit_ui(context, chat_id, text, build_main_menu())


# ========================
# TEXT INPUT HANDLER
# ========================

async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return

    text_input = update.message.text.strip()
    state = context.user_data.get("state")
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    # ---- Topic creation flow ----
    if state == "awaiting_topic_name":
        topic_name = text_input
        created = create_topic(user_id, topic_name)
        context.user_data["state"] = None

        result_text = (
            f"✅ Topic *'{escape_md(topic_name)}'* added\\!"
            if created
            else f"⚠️ Topic *'{escape_md(topic_name)}'* already exists\\."
        )

        await update.message.delete()
        await _edit_ui(
            context, chat_id,
            result_text + "\n\nChoose next action:",
            build_main_menu(),
        )
        return

    if state == "awaiting_topic_name_for_video":
        topic_name = text_input
        created = create_topic(user_id, topic_name)
        context.user_data["state"] = None

        topics = get_topics(user_id)
        match = next((t for t in topics if t["name"] == topic_name.strip()), None)
        topic_id = match["id"] if match else None

        video_id = context.user_data.pop("pending_video_id", None)
        timestamp = context.user_data.pop("pending_timestamp", 0)
        playlist_id = context.user_data.pop("pending_playlist_id", None)
        playlist_index = context.user_data.pop("pending_playlist_index", 0)
        context.user_data.pop("pending_playlist_title", None)

        await update.message.delete()

        if not topic_id:
            await _edit_ui(context, chat_id, "❌ Something went wrong\\. Please send the URL again\\.", build_main_menu())
            return

        context.user_data["active_topic_id"] = topic_id

        if playlist_id:
            await _save_new_playlist(context, chat_id, topic_id, playlist_id, video_id, playlist_index, timestamp)
        elif video_id:
            await _save_new_video(context, chat_id, topic_id, video_id, timestamp)
        return

    # ---- YouTube URL flow ----
    if re.match(YOUTUBE_REGEX, text_input):
        await update.message.delete()

        video_id = extract_video_id(text_input)
        playlist_id = extract_playlist_id(text_input)
        timestamp = extract_timestamp_seconds(text_input)
        playlist_index = extract_playlist_index(text_input) if playlist_id else 0

        if not video_id and not playlist_id:
            await _edit_ui(context, chat_id, "❌ Could not extract video or playlist ID\\.", build_main_menu())
            return

        # ── PLAYLIST URL ──
        if playlist_id:
            existing_playlist = get_playlist_by_playlist_id(playlist_id)

            if existing_playlist:
                update_playlist_position(
                    existing_playlist["id"],
                    video_id,
                    playlist_index,
                    timestamp,
                )
                pos_str = format_duration(timestamp)
                index_display = f"{playlist_index + 1}/{existing_playlist['total_videos']}"
                await _edit_ui(
                    context, chat_id,
                    f"📋 Playlist already tracked in topic *'{escape_md(existing_playlist['topic_name'])}'*\.\n\n"
                    f"🎬 Position updated to video {escape_md(index_display)} at {escape_md(pos_str)}\.",
                    build_main_menu(),
                )
                return

            # New playlist — fetch metadata upfront for the "use as topic" option
            await _edit_ui(context, chat_id, "🔍 Fetching playlist info\.\.\.", None)
            try:
                meta = fetch_playlist_metadata(playlist_id)
                playlist_title = meta["title"]
            except Exception:
                meta = None
                playlist_title = None

            # Stash everything including metadata to avoid double fetch later
            context.user_data["pending_playlist_id"] = playlist_id
            context.user_data["pending_video_id"] = video_id
            context.user_data["pending_timestamp"] = timestamp
            context.user_data["pending_playlist_index"] = playlist_index
            context.user_data["pending_playlist_title"] = playlist_title
            context.user_data["pending_playlist_meta"] = meta

            topics = sorted(get_topics(user_id), key=lambda t: t["name"].lower())
            if not topics and not playlist_title:
                await _edit_ui(
                    context, chat_id,
                    "⚠️ No topics exist yet\\.\n\nAdd a topic first, then send the URL again\\.",
                    build_main_menu(),
                )
                return

            active_topic_id = context.user_data.get("active_topic_id")
            if active_topic_id:
                active_topic = get_topic_by_id(active_topic_id)
                if active_topic:
                    keyboard = build_save_playlist_keyboard(active_topic, topics, playlist_title or playlist_id)
                    await _edit_ui(
                        context, chat_id,
                        f"📂 Save playlist to *'{escape_md(active_topic['name'])}'* or pick a different topic?",
                        keyboard,
                    )
                    return

            keyboard = (
                build_pick_playlist_topic_keyboard(topics, playlist_title)
                if playlist_title
                else build_topics_keyboard(topics, callback_prefix="picktopic")
            )
            await _edit_ui(context, chat_id, "📂 Pick a topic to save this playlist into:", keyboard)
            return

        # ── STANDALONE VIDEO URL ──

        # Android reverse lookup — check if video belongs to a tracked playlist
        playlist_match = find_video_in_playlists(video_id)
        if playlist_match:
            index = get_playlist_video_index(playlist_match["playlist_id"], video_id)
            update_playlist_position(playlist_match["id"], video_id, index, timestamp)
            pos_str = format_duration(timestamp)
            index_display = f"{index + 1}/{playlist_match['total_videos']}"
            await _edit_ui(
                context, chat_id,
                f"📋 Video is part of tracked playlist *'{escape_md(playlist_match['title'])}'*\.\n\n"
                f"🎬 Position updated to video {escape_md(index_display)} at {escape_md(pos_str)}\.",
                build_main_menu(),
            )
            return

        # Check standalone videos
        existing_video = get_video_by_video_id(video_id)
        if existing_video:
            update_video_position(existing_video["id"], timestamp)
            pos_str = format_duration(timestamp)
            await _edit_ui(
                context, chat_id,
                f"📌 Video already tracked in topic *'{escape_md(existing_video['topic_name'])}'*\.\n\n"
                f"⏱ Resume position updated to *{escape_md(pos_str)}*\.",
                build_main_menu(),
            )
            return

        # New standalone video
        topics = sorted(get_topics(user_id), key=lambda t: t["name"].lower())
        if not topics:
            await _edit_ui(
                context, chat_id,
                "⚠️ No topics exist yet\\.\n\nAdd a topic first, then send the URL again\\.",
                build_main_menu(),
            )
            return

        context.user_data["pending_video_id"] = video_id
        context.user_data["pending_timestamp"] = timestamp

        active_topic_id = context.user_data.get("active_topic_id")
        if active_topic_id:
            active_topic = get_topic_by_id(active_topic_id)
            if active_topic:
                keyboard = build_save_video_keyboard(active_topic, topics)
                await _edit_ui(
                    context, chat_id,
                    f"📂 Save to *'{escape_md(active_topic['name'])}'* or pick a different topic?",
                    keyboard,
                )
                return

        context.user_data["state"] = "awaiting_topic_for_video"
        keyboard = build_topics_keyboard(topics, callback_prefix="picktopic")
        await _edit_ui(context, chat_id, "📂 Pick a topic to save this video into:", keyboard)
        return

    # ---- Unknown text — silently delete ----
    await update.message.delete()


# ========================
# REGISTER
# ========================

def register_handlers(app):
    app.add_handler(CommandHandler("start", start))

    app.add_handler(CallbackQueryHandler(handle_menu_callbacks, pattern="^menu_"))
    app.add_handler(CallbackQueryHandler(handle_topic_selection, pattern="^topic_"))
    app.add_handler(CallbackQueryHandler(handle_video_callbacks, pattern="^v(resume|complete|remove)_"))
    app.add_handler(CallbackQueryHandler(handle_playlist_callbacks, pattern="^p(resume|complete|remove)_"))
    app.add_handler(CallbackQueryHandler(handle_pick_topic_for_video, pattern="^picktopic_"))
    app.add_handler(CallbackQueryHandler(handle_topic_remove, pattern="^topicremove_"))
    app.add_handler(CallbackQueryHandler(lambda u, c: u.callback_query.answer(), pattern="^noop_"))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))