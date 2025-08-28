async def help_handler(update, context):
    """
    Minimal help text explaining usage.
    """
    msg = (
        "*📚 PYQ Bot Help*\n\n"
        "• 🚀 Use /start to select your year and branch\n"
        "• 📝 Copy a subject code (e.g., 23BS1001) and send it to receive the Google Drive folder link\n"
        "• ❤️ Use /donate to support us\n\n"
        "_Need more help? Contact the administrator._"
    )
    await update.message.reply_text(msg, parse_mode="MarkdownV2")