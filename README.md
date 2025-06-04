# CryptoJobs Telegram Bot

A real-time Telegram bot that fetches and notifies users about remote cryptocurrency jobs from the CryptoJobsList RSS feed.

## Features

- 🔔 **Real-time notifications**: Get notified as soon as new jobs are posted
- 📋 **Latest jobs on demand**: Use `/latest` to see the most recent job postings
- 🔄 **Automatic checking**: Polls the RSS feed every 5 minutes (configurable)
- 💾 **Persistent storage**: Remembers subscribers and seen jobs
- 🚀 **Production ready**: Supports both file-based and Redis storage
- 🎯 **Smart filtering**: Avoids duplicate notifications for already seen jobs
- 🔍 **Advanced filtering**: Filter jobs by multiple job types and custom keywords

## Commands

- `/start` - Subscribe to job updates
- `/stop` - Unsubscribe from job updates
- `/latest` - Get the latest 5 jobs
- `/filter` - Manage your job filters
- `/help` - Show help message

## Quick Start

### Prerequisites

- Python 3.8 or higher
- A Telegram Bot Token (get from [@BotFather](https://t.me/botfather))

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Nabeel-Javaid/telegram-cryptojobs-bot.git
cd telegram-cryptojobs-bot
```

2. Create a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file:
```bash
# Copy from the example
cp env.example .env

# Edit with your bot token
nano .env
```

5. Update the `.env` file with your Telegram Bot Token:
```env
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE
```

### Running the Bot

```bash
python main.py
```

## Docker Deployment

The bot can also be deployed using Docker:

```bash
# Build and start with docker-compose
docker-compose up -d
```

## License

MIT