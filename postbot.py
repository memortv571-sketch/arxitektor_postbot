import os
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("POST_BOT_TOKEN", "YOUR_TOKEN_HERE")

# Kanallar ro'yxati
CHANNELS = [
    "@arxitektor_komilov",
    "@baitungroup",
]

# Admin ID — faqat siz post yubora olasiz
ADMIN_IDS = [int(x) for x in os.environ.get("ADMIN_IDS", "0").split(",") if x]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if ADMIN_IDS and user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Siz admin emassiz!")
        return
    await update.message.reply_text(
        "👋 *Post Bot ishga tayyor!*\n\n"
        "Kanallar:\n"
        "📢 @arxitektor\\_komilov\n"
        "📢 @baitungroup\n\n"
        "Post yuborish uchun:\n"
        "1️⃣ /post buyrug'ini yuboring\n"
        "2️⃣ Keyin matnni yozing\n\n"
        "Yoki shunchaki matn yozing — men so'rayman!",
        parse_mode="Markdown"
    )

async def post_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if ADMIN_IDS and user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Siz admin emassiz!")
        return
    
    # /post dan keyin matn bor bo'lsa
    if context.args:
        text = " ".join(context.args)
        await send_to_channels(update, context, text)
    else:
        context.user_data["waiting_post"] = True
        await update.message.reply_text(
            "✍️ Post matnini yozing:\n\n"
            "(Bekor qilish uchun /cancel)"
        )

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["waiting_post"] = False
    await update.message.reply_text("❌ Bekor qilindi.")

async def send_to_channels(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    success = []
    failed = []
    
    for channel in CHANNELS:
        try:
            await context.bot.send_message(
                chat_id=channel,
                text=text,
                parse_mode="Markdown"
            )
            success.append(channel)
        except Exception as e:
            logger.error(f"Error sending to {channel}: {e}")
            failed.append(channel)
    
    result = f"✅ *Post yuborildi!*\n\n"
    if success:
        result += "Muvaffaqiyatli:\n" + "\n".join(f"✅ {c}" for c in success) + "\n\n"
    if failed:
        result += "Xato:\n" + "\n".join(f"❌ {c}" for c in failed)
    
    await update.message.reply_text(result, parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if ADMIN_IDS and user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Siz admin emassiz!")
        return
    
    if context.user_data.get("waiting_post"):
        context.user_data["waiting_post"] = False
        text = update.message.text
        
        # Tasdiqlash
        context.user_data["pending_text"] = text
        await update.message.reply_text(
            f"📋 *Post ko'rinishi:*\n\n{text}\n\n"
            "Yuborilsinmi?\n"
            "✅ /confirm — Ha, yuborish\n"
            "❌ /cancel — Bekor qilish",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "Post yuborish uchun /post buyrug'ini yuboring."
        )

async def confirm_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if ADMIN_IDS and user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Siz admin emassiz!")
        return
    
    text = context.user_data.get("pending_text")
    if not text:
        await update.message.reply_text("❌ Yuborish uchun matn yo'q. /post yuboring.")
        return
    
    context.user_data["pending_text"] = None
    await send_to_channels(update, context, text)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("post", post_command))
    app.add_handler(CommandHandler("confirm", confirm_command))
    app.add_handler(CommandHandler("cancel", cancel_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Post Bot ishga tushdi...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
