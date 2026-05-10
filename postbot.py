import os
import logging
import aiohttp
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("POST_BOT_TOKEN", "YOUR_TOKEN_HERE")
ADMIN_IDS = [int(x) for x in os.environ.get("ADMIN_IDS", "0").split(",") if x]
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# Guruh chat sozlamalari
DISCUSSION_GROUPS = {
    "arxitektor_komilov_chat": {
        "channel": "@arxitektor_komilov",
        "instagram": "https://instagram.com/arxitektor_komilov",
        "telegram": "https://t.me/arxitektor_komilov",
        "system_prompt": """Siz "Arxitektor Komilov" arxitektura va dizayn studiyasining AI yordamchisisiz.

Asosiy ma'lumotlar:
- 8+ yil tajriba
- 3D render, turar-joy loyihalari, dizayn
- Tel: +99833 877-67-33
- Instagram: @arxitektor_komilov
- Telegram: @arxitektor_komilov

Qoidalar:
1. Faqat o'zbek tilida javob bering
2. Samimiy va do'stona bo'ling
3. Arxitektura, dizayn, loyiha, narx savollarga javob bering
4. Mijozni qiziqtiring va aloqaga undang
5. Har doim oxirida Instagram yoki Telegram kanalga taklif qiling
6. Narx so'rasa: "Bepul konsultatsiya uchun +99833 877-67-33 ga murojaat qiling" de
7. Qisqa va aniq javob bering (3-5 jumla)"""
    },
    "baitun_group_chat": {
        "channel": "@baitungroup",
        "instagram": "https://www.instagram.com/baitungroup/",
        "telegram": "https://t.me/baitungroup",
        "system_prompt": """Siz "Baitun Group" qurilish va loyiha korxonasining AI yordamchisisiz.

Asosiy ma'lumotlar:
- Qurulish va ta'mirlash
- Interior dizayn
- Pod-kalit ta'mirlash
- Sifat, Zamonaviylik, Kafolat
- Tel: +998 77 621 23 88
- Instagram: @baitungroup
- Telegram: @baitungroup

Qoidalar:
1. Faqat o'zbek tilida javob bering
2. Samimiy va do'stona bo'ling
3. Qurilish, ta'mirlash, dizayn, narx savollarga javob bering
4. Mijozni qiziqtiring va aloqaga undang
5. Har doim oxirida Instagram yoki Telegram kanalga taklif qiling
6. Narx so'rasa: "Bepul hisob-kitob uchun +998 77 621 23 88 ga murojaat qiling" de
7. Qisqa va aniq javob bering (3-5 jumla)"""
    },
}

# Kanal post sozlamalari
CHANNEL_SETTINGS = {
    "arxitektor": {
        "chat_id": "@arxitektor_komilov",
        "footer": (
            "\n\n"
            "#arxitektor #dizayn #interyer\n"
            "📸 Instagram: @arxitektor\_komilov\n"
            "💬 Telegram: @arxitektor\_komilov"
        ),
        "keyboard": InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📸 Instagram", url="https://instagram.com/arxitektor_komilov"),
                InlineKeyboardButton("💬 Telegram", url="https://t.me/arxitektor_komilov"),
            ],
            [
                InlineKeyboardButton("📤 Yaqinlaringizga ham ulashing!", switch_inline_query=""),
            ],
        ]),
    },
    "baitun": {
        "chat_id": "@baitungroup",
        "footer": (
            "\n\n"
            "#baitun #qurilish #dizayn\n"
            "📸 Instagram: @baitungroup\n"
            "💬 Telegram: @baitungroup"
        ),
        "keyboard": InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📸 Instagram", url="https://www.instagram.com/baitungroup/"),
                InlineKeyboardButton("💬 Telegram", url="https://t.me/baitungroup"),
            ],
            [
                InlineKeyboardButton("📤 Yaqinlaringizga ham ulashing!", switch_inline_query=""),
            ],
        ]),
    },
}

def is_admin(user_id):
    return not ADMIN_IDS or user_id in ADMIN_IDS

def get_group_settings(chat_username):
    if not chat_username:
        return None
    username = chat_username.lstrip("@").lower()
    for key, settings in DISCUSSION_GROUPS.items():
        if key.lower() == username:
            return settings
    return None

async def ask_ai(system_prompt, user_message):
    if not ANTHROPIC_API_KEY:
        return None
    headers = {
        "Content-Type": "application/json",
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01"
    }
    payload = {
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 500,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_message}]
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data["content"][0]["text"]
                else:
                    logger.error(f"Anthropic API error: {resp.status}")
                    return None
    except Exception as e:
        logger.error(f"AI request error: {e}")
        return None

async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.text:
        return
    if message.from_user and message.from_user.is_bot:
        return

    chat = message.chat
    settings = get_group_settings(chat.username)
    if not settings:
        return

    bot_mentioned = False
    if message.entities:
        for entity in message.entities:
            if entity.type == "mention":
                mention = message.text[entity.offset:entity.offset + entity.length]
                bot_info = await context.bot.get_me()
                if mention.lower() == f"@{bot_info.username.lower()}":
                    bot_mentioned = True
                    break

    is_reply_to_bot = (
        message.reply_to_message and
        message.reply_to_message.from_user and
        message.reply_to_message.from_user.is_bot
    )

    if not bot_mentioned and not is_reply_to_bot:
        return

    user_name = message.from_user.first_name if message.from_user else "Mijoz"
    user_text = message.text

    if bot_mentioned:
        bot_info = await context.bot.get_me()
        user_text = user_text.replace(f"@{bot_info.username}", "").strip()

    if not user_text:
        await message.reply_text("Salom! Qanday yordam bera olaman? 😊")
        return

    await context.bot.send_chat_action(chat_id=chat.id, action="typing")
    ai_response = await ask_ai(settings["system_prompt"], f"{user_name}: {user_text}")

    if ai_response:
        await message.reply_text(ai_response)
    else:
        await message.reply_text(
            f"Salom {user_name}! 👋\n\n"
            f"Savolingiz uchun rahmat. Mutaxassisimiz tez orada javob beradi.\n\n"
            f"📞 Tezroq aloqa: {settings['telegram']}"
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Siz admin emassiz!")
        return
    await update.message.reply_text(
        "👋 *Post Bot ishga tayyor!*\n\n"
        "Post yuborish uchun /post buyrug'ini yuboring.\n\n"
        "📌 *Imkoniyatlar:*\n"
        "🖼️ Rasm \+ matn\n"
        "📝 Har kanal uchun avtomatik footer\n"
        "🔘 Inline tugmalar\n"
        "📤 Ulashish tugmasi\n"
        "🤖 AI guruh yordamchisi",
        parse_mode="Markdown"
    )

async def post_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Siz admin emassiz!")
        return
    context.user_data["waiting_post"] = True
    context.user_data["pending_photo"] = None
    await update.message.reply_text(
        "🖼️ *Post uchun rasm yuboring*\n"
        "Rasmsiz yuborish uchun matnni yozing\n\n"
        "Bekor qilish: /cancel",
        parse_mode="Markdown"
    )

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Bekor qilindi.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not context.user_data.get("waiting_post"):
        return

    photo = update.message.photo[-1]
    caption = update.message.caption or ""
    context.user_data["pending_photo"] = photo.file_id
    context.user_data["pending_text"] = caption
    context.user_data["waiting_post"] = False

    if not caption:
        context.user_data["waiting_caption"] = True
        await update.message.reply_text(
            "✍️ Endi post matnini yozing:\n(Bekor qilish: /cancel)"
        )
    else:
        await ask_channel(update, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.chat.type in ["group", "supergroup"]:
        await handle_group_message(update, context)
        return

    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Siz admin emassiz!")
        return

    if context.user_data.get("waiting_caption"):
        context.user_data["waiting_caption"] = False
        context.user_data["pending_text"] = update.message.text
        await ask_channel(update, context)
        return

    if context.user_data.get("waiting_post"):
        context.user_data["waiting_post"] = False
        context.user_data["pending_text"] = update.message.text
        context.user_data["pending_photo"] = None
        await ask_channel(update, context)
        return

    await update.message.reply_text("Post yuborish uchun /post buyrug'ini yuboring.")

async def ask_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = context.user_data.get("pending_text", "")
    photo = context.user_data.get("pending_photo")
    preview = f"📋 *Post ko'rinishi:*\n\n{text}"

    keyboard = [
        [
            InlineKeyboardButton("1️⃣ @arxitektor_komilov", callback_data="send_arxitektor"),
            InlineKeyboardButton("2️⃣ @baitungroup", callback_data="send_baitun"),
        ],
        [
            InlineKeyboardButton("3️⃣ Ikkalasiga ham", callback_data="send_both"),
        ],
        [
            InlineKeyboardButton("❌ Bekor qilish", callback_data="send_cancel"),
        ],
    ]

    if photo:
        await update.message.reply_photo(
            photo=photo,
            caption=preview,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(
            preview,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def send_to_channel(context, key, text, photo):
    settings = CHANNEL_SETTINGS[key]
    chat_id = settings["chat_id"]
    full_text = text + settings["footer"]
    keyboard = settings["keyboard"]

    if photo:
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=photo,
            caption=full_text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text=full_text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    text = context.user_data.get("pending_text", "")
    photo = context.user_data.get("pending_photo")
    data = query.data

    if data == "send_cancel":
        context.user_data.clear()
        if photo:
            await query.edit_message_caption("❌ Bekor qilindi.")
        else:
            await query.edit_message_text("❌ Bekor qilindi.")
        return

    if data == "send_arxitektor":
        targets = ["arxitektor"]
    elif data == "send_baitun":
        targets = ["baitun"]
    elif data == "send_both":
        targets = ["arxitektor", "baitun"]
    else:
        return

    success, failed = [], []
    for key in targets:
        try:
            await send_to_channel(context, key, text, photo)
            success.append(CHANNEL_SETTINGS[key]["chat_id"])
        except Exception as e:
            logger.error(f"Error sending to {key}: {e}")
            failed.append(CHANNEL_SETTINGS[key]["chat_id"])

    context.user_data.clear()

    result = "✅ *Post yuborildi!*\n\n"
    if success:
        result += "Muvaffaqiyatli:\n" + "\n".join(f"✅ {c}" for c in success) + "\n\n"
    if failed:
        result += "Xato:\n" + "\n".join(f"❌ {c}" for c in failed)

    if photo:
        await query.edit_message_caption(result, parse_mode="Markdown")
    else:
        await query.edit_message_text(result, parse_mode="Markdown")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("post", post_command))
    app.add_handler(CommandHandler("cancel", cancel_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Post Bot ishga tushdi...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
