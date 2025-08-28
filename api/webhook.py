from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import json
import logging
import sys
import os

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import TELEGRAM_BOT_TOKEN
from handlers.start_handler import start_handler, register_callback_handlers
from handlers.help_handler import help_handler
from handlers.subject_handler import subject_code_handler
from handlers.donation_handler import donation_handler
from handlers.error_handler import error_handler

# Setup logging
logging.basicConfig(
    format="%(asctime)s %(name)s %(levelname)s %(message)s", level=logging.INFO
)

# Initialize the application
app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

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

async def handler(request):
    """Handle webhook requests from Telegram"""
    try:
        # Parse the request body
        body = await request.json()
        
        # Process the update
        update = Update.de_json(body, app.bot)
        await app.process_update(update)
        
        # Return a success response
        return {
            "statusCode": 200,
            "body": json.dumps({"status": "success"})
        }
    except Exception as e:
        logging.error(f"Error processing update: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"status": "error", "message": str(e)})
        }