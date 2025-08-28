# Telegram PYQ Bot

A Telegram bot that helps students find previous year question papers for their subjects. Users can select their year and branch, or directly send a subject code to get the Google Drive link for question papers.

## Features

- Select year and branch to view available subjects
- Directly send subject code to get question paper links
- Support for multiple years and branches
- Donation functionality

## Project Structure

```
├── assets/              # Static assets like QR code for donations
├── handlers/            # Telegram command and message handlers
├── services/            # External service integrations (Google Sheets)
├── utils/               # Utility functions and helpers
├── .env                 # Environment variables (not committed to git)
├── .env.example         # Example environment variables
├── bot.py               # Main bot entry point
├── config.py            # Configuration settings
├── requirements.txt     # Python dependencies
```

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- A Telegram Bot Token (from BotFather)
- Firebase account (for database)
- Google Sheets API credentials (for data source)

### Local Development

1. Clone the repository

```bash
git clone https://github.com/azadmohanty/pyq-bot.git
cd telegram-pyq-bot
```

2. Create a virtual environment and install dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Set up environment variables

```bash
cp .env.example .env
# Edit .env with your actual values
```

4. Run the bot

```bash
python bot.py
```

### Vercel Deployment

1. Fork or clone this repository

2. Create a new project on Vercel and connect your GitHub repository

3. Set up the following environment variables in Vercel:
   - `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
   - `SHEETS_SPREADSHEET_ID`: Your Google Sheets ID
   - All Firebase and Google API credentials as specified in `.env.example`

4. Deploy the project

5. Set up a webhook for your Telegram bot:
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=<YOUR_VERCEL_URL>/api/webhook
   ```

6. Your bot should now be running on Vercel!