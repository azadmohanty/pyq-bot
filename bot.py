import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from config import TELEGRAM_BOT_TOKEN
from handlers.start_handler import start_handler, register_callback_handlers
from handlers.help_handler import help_handler
from handlers.subject_handler import subject_code_handler
from handlers.donation_handler import donation_handler
from handlers.error_handler import error_handler

def setup_logging():
    logging.basicConfig(
        format="%(asctime)s %(name)s %(levelname)s %(message)s", level=logging.INFO
    )

def main():
    setup_logging()
    
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Register command handlers
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CommandHandler("donate", donation_handler))
    
    # Register message handlers
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, subject_code_handler))
    
    # Register callback query handlers
    register_callback_handlers(app)
    
    # Register error handler
    app.add_error_handler(error_handler)
    
    # Start the bot
    app.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == "__main__":
    main()