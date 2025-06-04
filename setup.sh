#!/bin/bash

echo "🚀 CryptoJobs Telegram Bot Setup"
echo "================================"
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Found Python $python_version"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv
echo "✓ Virtual environment created"

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt
echo "✓ Dependencies installed"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file from template..."
    cp env.example .env
    echo "✓ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your Telegram Bot Token"
    echo "   Get a token from @BotFather on Telegram"
else
    echo ""
    echo "✓ .env file already exists"
fi

# Create data directory
mkdir -p data
echo "✓ Data directory created"

echo ""
echo "================================"
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your Telegram Bot Token"
echo "2. Run the bot with: python main.py"
echo "3. Start chatting with your bot on Telegram"
echo ""