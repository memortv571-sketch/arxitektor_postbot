import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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

def is_admin(user_id):
    return not ADMIN_IDS or user_id in ADMIN_IDS

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Siz admin emassiz!")
        return
    await update.message.reply_text(
        "👋 *Post Bot ishga tayyor!*\n\n"
        "Post yuborish uchun /post buyrug'ini yuboring.",
        parse_mode="Markdown"
    )

async def post_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Siz admin emassiz!")
        return
    context.user_data["waiting_post"] = True
    await update.message.reply_text(
        "✍️ Post matnini yozing:\n\n(Bekor qilish uchun /cancel)"
    )

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Bekor qilindi.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Siz admin emassiz!")
        return

    if context.user_data.get("waiting_post"):
        context.user_data["waiting_post"] = False
        context.user_data["pending_text"] = update.message.text

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
        await update.message.reply_text(
            f"📋 *Post ko'rinishi:*\n\n{update.message.text}\n\n"
            "Qaysi kanalga yuboray?",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(
            "Post yuborish uchun /post buyrug'ini yuboring."
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    text = context.user_data.get("pending_text")
    if not text:
        await query.edit_message_text("❌ Matn topilmadi. /post yuboring.")
        return

    data = query.data

    if data == "send_cancel":
        context.user_data.clear()
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

    success, failed = [], []
    for channel in targets:
        try:
            await context.bot.send_message(chat_id=channel, text=text, parse_mode="Markdown")
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

    await query.edit_message_text(result, parse_mode="Markdown")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("post", post_command))
    app.add_handler(CommandHandler("cancel", cancel_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Post Bot ishga tushdi...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
