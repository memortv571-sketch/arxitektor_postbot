import os
import logging
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

CHANNELS = {
    "arxitektor": "@arxitektor_komilov",
    "baitun": "@baitungroup",
}

ADMIN_IDS = [int(x) for x in os.environ.get("ADMIN_IDS", "0").split(",") if x]

# Avtomatik footer
FOOTER = (
    "\n\n"
    "#arxitektor #dizayn #interyer\n"
    "📸 Instagram: @arxitektor\_komilov\n"
    "💬 Telegram: @arxitektor\_komilov"
)

# Inline tugmalar
def get_inline_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("📸 Instagram", url="https://instagram.com/arxitektor_komilov"),
            InlineKeyboardButton("💬 Telegram", url="https://t.me/arxitektor_komilov"),
        ],
        [
            InlineKeyboardButton("💬 Izoh qoldiring", url="https://t.me/arxitektor_komilov"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

def is_admin(user_id):
    return not ADMIN_IDS or user_id in ADMIN_IDS

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Siz admin emassiz!")
        return
    await update.message.reply_text(
        "👋 *Post Bot ishga tayyor!*\n\n"
        "Post yuborish uchun /post buyrug'ini yuboring.\n\n"
        "📌 *Imkoniyatlar:*\n"
        "🖼️ Rasm \+ matn\n"
        "📝 Avtomatik footer\n"
        "🔘 Inline tugmalar\n"
        "💬 Izoh tugmasi",
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
        await update.message.reply_text("❌ Siz admin emassiz!")
        return

    if not context.user_data.get("waiting_post"):
        await update.message.reply_text("Post yuborish uchun /post buyrug'ini yuboring.")
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

    preview = f"📋 *Post ko'rinishi:*\n\n{text}{FOOTER}"

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
        targets = [CHANNELS["arxitektor"]]
    elif data == "send_baitun":
        targets = [CHANNELS["baitun"]]
    elif data == "send_both":
        targets = list(CHANNELS.values())
    else:
        return

    full_text = text + FOOTER
    success, failed = [], []

    for channel in targets:
        try:
            if photo:
                await context.bot.send_photo(
                    chat_id=channel,
                    photo=photo,
                    caption=full_text,
                    parse_mode="Markdown",
                    reply_markup=get_inline_keyboard()
                )
            else:
                await context.bot.send_message(
                    chat_id=channel,
                    text=full_text,
                    parse_mode="Markdown",
                    reply_markup=get_inline_keyboard()
                )
            success.append(channel)
        except Exception as e:
            logger.error(f"Error sending to {channel}: {e}")
            failed.append(channel)

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
