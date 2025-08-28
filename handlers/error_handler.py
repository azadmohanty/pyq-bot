import logging
logger = logging.getLogger(__name__)

async def error_handler(update, context):
	"""
	Catch-all error handler so the bot doesn't crash on exceptions.
	"""
	logger.exception("Error while handling update: %s", update)
	try:
		chat_id = update.effective_chat.id if update and update.effective_chat else None
		if chat_id:
			await context.bot.send_message(chat_id, "Something went wrong. Try again or use /start.")
	except Exception:
		# Avoid cascading failures in the error handler
		pass