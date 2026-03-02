from telegram import Update
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from db.crud import (
    create_topic,
    get_topics,
    get_topic_by_id,
    get_video_by_video_id,
    get_video_by_db_id,
    update_video_position,
    add_video,
    get_active_videos,
    get_latest_active_video,
    mark_video_completed,
    delete_video,
)
from config import CHAT_ID
from bot.keyboards import (
    build_main_menu,
    build_topics_keyboard,
    build_videos_keyboard,
    build_save_video_keyboard,
)
from utils.url_parser import extract_video_id, extract_timestamp_seconds
from services.youtube import fetch_video_metadata
import re

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


# ========================
# HELPERS
# ========================

async def _edit_ui(context, chat_id, text, reply_markup, parse_mode="Markdown"):
    msg_id = context.user_data.get("ui_message_id")
    if msg_id:
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=msg_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
            )
            return
        except Exception:
            pass
    msg = await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=reply_markup,
        parse_mode=parse_mode,
    )
    context.user_data["ui_message_id"] = msg.message_id


# ========================
# START
# ========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return

    msg = await update.effective_message.reply_text(
        "📚 *Welcome to Learntinuum*\n\nTrack your learning progress across devices.",
        reply_markup=build_main_menu(),
        parse_mode="Markdown",
    )

    context.user_data["ui_message_id"] = msg.message_id
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
            parse_mode="Markdown",
        )

    # -------- RESUME (latest active video globally) --------
    elif data == "menu_resume":
        video = get_latest_active_video(user_id)
        if not video:
            await query.edit_message_text(
                "📭 No active videos found. Add some first!",
                reply_markup=build_main_menu(),
            )
            return

        url = make_resume_url(video["video_id"], video["last_position"])
        pos_str = format_duration(video["last_position"])

        await query.edit_message_text(
            f"▶️ *Resume where you left off*\n\n"
            f"📌 *{video['title']}*\n"
            f"📂 Topic: {video['topic_name']}\n"
            f"⏱ Position: {pos_str}\n\n"
            f"🔗 {url}",
            reply_markup=build_main_menu(),
            parse_mode="Markdown",
        )

    # -------- BACK TO MENU --------
    elif data == "menu_new_topic_for_video":
            context.user_data["state"] = "awaiting_topic_name_for_video"
            await query.edit_message_text("📝 Send me the new topic name:")

    elif data == "menu_back":
        context.user_data["state"] = None
        context.user_data.pop("pending_video_id", None)
        context.user_data.pop("pending_timestamp", None)

        await query.edit_message_text(
            "📚 *Main Menu*\n\nChoose an action:",
            reply_markup=build_main_menu(),
            parse_mode="Markdown",
        )

# ========================
# TOPIC SELECTION → show videos
# ========================

async def handle_topic_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return

    query = update.callback_query
    await query.answer()

    topic_id = int(query.data.split("_")[1])
    context.user_data["active_topic_id"] = topic_id

    videos = get_active_videos(topic_id)

    if not videos:
        await query.edit_message_text(
            "📂 No active videos in this topic yet.\n\nSend a YouTube URL to add one!",
            reply_markup=build_main_menu(),
        )
        return

    await query.edit_message_text(
        "🎬 *Active videos in this topic:*",
        reply_markup=build_videos_keyboard(videos),
        parse_mode="Markdown",
    )


# ========================
# VIDEO ACTION CALLBACKS
# ========================

async def handle_video_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return

    query = update.callback_query
    await query.answer()

    data = query.data  # vresume_42 / vcomplete_42 / vremove_42
    action, vid_id_str = data.split("_", 1)
    vid_db_id = int(vid_id_str)

    if action == "vresume":
        video = get_video_by_db_id(vid_db_id)
        if not video:
            await query.edit_message_text("❌ Video not found.", reply_markup=build_main_menu())
            return

        url = make_resume_url(video["video_id"], video["last_position"])
        pos_str = format_duration(video["last_position"])

        await query.edit_message_text(
            f"▶️ *Resume*\n\n"
            f"📌 *{video['title']}*\n"
            f"⏱ Position: {pos_str}\n\n"
            f"🔗 {url}",
            reply_markup=build_main_menu(),
            parse_mode="Markdown",
        )

    elif action == "vcomplete":
        mark_video_completed(vid_db_id)
        await query.edit_message_text(
            "✅ Video marked as completed!",
            reply_markup=build_main_menu(),
        )

    elif action == "vremove":
        delete_video(vid_db_id)
        await query.edit_message_text(
            "🗑 Video removed.",
            reply_markup=build_main_menu(),
        )


# ========================
# TOPIC PICKER FOR NEW VIDEO
# ========================

async def handle_pick_topic_for_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return

    query = update.callback_query
    await query.answer()

    topic_id = int(query.data.split("_")[1])
    context.user_data["active_topic_id"] = topic_id
    context.user_data["state"] = None

    video_id = context.user_data.pop("pending_video_id", None)
    timestamp = context.user_data.pop("pending_timestamp", 0)

    if not video_id:
        await query.edit_message_text(
            "❌ Something went wrong. Please send the URL again.",
            reply_markup=build_main_menu(),
        )
        return

    await _save_new_video(context, query.message.chat_id, topic_id, video_id, timestamp, query=query)


# ========================
# SAVE VIDEO HELPER
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
        text = "⚠️ This video already exists in the selected topic."
        if query:
            await query.edit_message_text(text, reply_markup=build_main_menu())
        else:
            await _edit_ui(context, chat_id, text, build_main_menu())
        return

    pos_str = format_duration(timestamp)
    text = (
        f"✅ *Video added!*\n\n"
        f"📌 *{title}*\n"
        f"⏱ Starting position: *{pos_str}*"
    )

    if query:
        await query.edit_message_text(text, reply_markup=build_main_menu(), parse_mode="Markdown")
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
                f"✅ Topic *'{topic_name}'* added!"
                if created
                else f"⚠️ Topic *'{topic_name}'* already exists."
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

        if created:
            # freshest topic = the one just created
            topics = sorted(get_topics(user_id), key=lambda t: t["name"].lower())
            topic_id = topics[0]["id"]
        else:
            # topic already existed — find it by name
            topics = sorted(get_topics(user_id), key=lambda t: t["name"].lower())
            match = next((t for t in topics if t["name"] == topic_name.strip()), None)
            topic_id = match["id"] if match else None

        video_id = context.user_data.pop("pending_video_id", None)
        timestamp = context.user_data.pop("pending_timestamp", 0)

        await update.message.delete()

        if not video_id or not topic_id:
            await _edit_ui(context, chat_id, "❌ Something went wrong. Please send the URL again.", build_main_menu())
            return

        context.user_data["active_topic_id"] = topic_id
        await _save_new_video(context, chat_id, topic_id, video_id, timestamp)
        return

    # ---- YouTube URL flow ----
    if re.match(YOUTUBE_REGEX, text_input):
        await update.message.delete()

        video_id = extract_video_id(text_input)
        timestamp = extract_timestamp_seconds(text_input)

        if not video_id:
            await _edit_ui(context, chat_id, "❌ Could not extract video ID.", build_main_menu())
            return

        # Case 1: Video already tracked → update timestamp
        existing_video = get_video_by_video_id(video_id)
        if existing_video:
            update_video_position(existing_video["id"], timestamp)
            pos_str = format_duration(timestamp)
            await _edit_ui(
                context, chat_id,
                f"📌 Video already tracked in topic *'{existing_video['topic_name']}'*.\n\n"
                f"⏱ Resume position updated to *{pos_str}*.",
                build_main_menu(),
            )
            return

        # Case 2: New video — need at least one topic
        topics = sorted(get_topics(user_id), key=lambda t: t["name"].lower())
        if not topics:
            await _edit_ui(
                context, chat_id,
                "⚠️ No topics exist yet.\n\nAdd a topic first, then send the URL again.",
                build_main_menu(),
            )
            return

        # Stash pending video info
        context.user_data["pending_video_id"] = video_id
        context.user_data["pending_timestamp"] = timestamp

        active_topic_id = context.user_data.get("active_topic_id")

        if active_topic_id:
            # A topic was previously selected — ask to confirm or pick another
            active_topic = get_topic_by_id(active_topic_id)
            if active_topic:
                keyboard = build_save_video_keyboard(active_topic, topics)
                await _edit_ui(
                    context, chat_id,
                    f"📂 Save to *'{active_topic['name']}'* or pick a different topic?",
                    keyboard,
                )
                return

        # No active topic — show full picker
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
    app.add_handler(CallbackQueryHandler(handle_pick_topic_for_video, pattern="^picktopic_"))
    app.add_handler(CallbackQueryHandler(lambda u, c: u.callback_query.answer(), pattern="^noop_"))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))