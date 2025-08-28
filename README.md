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
git clone https://github.com/yourusername/telegram-pyq-bot.git
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
# Edit .env with your credentials
```

4. Add your Firebase and Google API credentials

- Place `firebase-credentials.json` in the project root
- Place `client_secret.json` in the project root

5. Run the bot

```bash
python bot.py
```

### Deployment to Vercel

1. Create a Vercel account and install the Vercel CLI

```bash
npm install -g vercel
```

2. Configure Vercel environment variables

Add the following environment variables in the Vercel dashboard:

- `TELEGRAM_BOT_TOKEN`
- `SHEETS_SPREADSHEET_ID`
- `SHEETS_RANGE`
- Firebase credentials (all `FIREBASE_*` variables)
- Google API credentials (all `GOOGLE_*` variables)

3. Deploy to Vercel

```bash
vercel
```

## Environment Variables

### Required Variables

- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token from BotFather
- `SHEETS_SPREADSHEET_ID`: ID of your Google Sheet with subject data
- `SHEETS_RANGE`: Range in the sheet containing data (e.g., "Sheet1!A2:C")

### Firebase Variables (for production)

- `FIREBASE_TYPE`: Usually "service_account"
- `FIREBASE_PROJECT_ID`: Your Firebase project ID
- `FIREBASE_PRIVATE_KEY_ID`: Private key ID from Firebase credentials
- `FIREBASE_PRIVATE_KEY`: Private key from Firebase credentials
- `FIREBASE_CLIENT_EMAIL`: Client email from Firebase credentials
- `FIREBASE_CLIENT_ID`: Client ID from Firebase credentials
- `FIREBASE_AUTH_URI`: Auth URI (usually "https://accounts.google.com/o/oauth2/auth")
- `FIREBASE_TOKEN_URI`: Token URI (usually "https://oauth2.googleapis.com/token")
- `FIREBASE_AUTH_PROVIDER_X509_CERT_URL`: Auth provider cert URL
- `FIREBASE_CLIENT_X509_CERT_URL`: Client cert URL

### Google API Variables (for production)

- `GOOGLE_CLIENT_TYPE`: Usually "service_account"
- `GOOGLE_PROJECT_ID`: Your Google project ID
- `GOOGLE_PRIVATE_KEY_ID`: Private key ID from Google credentials
- `GOOGLE_PRIVATE_KEY`: Private key from Google credentials
- `GOOGLE_CLIENT_EMAIL`: Client email from Google credentials
- `GOOGLE_CLIENT_ID`: Client ID from Google credentials
- `GOOGLE_AUTH_URI`: Auth URI (usually "https://accounts.google.com/o/oauth2/auth")
- `GOOGLE_TOKEN_URI`: Token URI (usually "https://oauth2.googleapis.com/token")
- `GOOGLE_AUTH_PROVIDER_X509_CERT_URL`: Auth provider cert URL
- `GOOGLE_CLIENT_X509_CERT_URL`: Client cert URL

## License

MIT