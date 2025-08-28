import logging
from telegram import Update
from telegram.ext import ContextTypes
import os

logger = logging.getLogger(__name__)

async def donation_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Send a QR code image for donations.
    """
    try:
        # Path to the QR code image
        qr_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "qr.png")
        
        # Check if the file exists
        if os.path.exists(qr_path):
            # Send the QR code image
            await update.message.reply_document(
                document=open(qr_path, "rb"),
                caption="❤️ Thank you for supporting us! Scan this QR code to donate.\n\nCreated with ♥ by someone like you"
            )
        else:
            # If the QR code image doesn't exist, send a text message
            logger.warning(f"Donation QR code not found at {qr_path}")
            await update.message.reply_text(
                "❤️ Thank you for your interest in supporting us! "
                "Please contact the administrator for donation details.\n\n"
                "Created with ♥ by someone like you"
            )
    except Exception as e:
        logger.exception(f"Error in donation handler: {e}")
        await update.message.reply_text(
            "Sorry, there was an error processing your request. Please try again later."
        )