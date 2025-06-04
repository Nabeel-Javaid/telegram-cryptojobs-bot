#!/usr/bin/env python3
"""
CryptoJobs Telegram Bot
A real-time bot that fetches and notifies users about remote crypto jobs from CryptoJobsList RSS feed
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Apply patch for Python 3.12 compatibility with APScheduler
from src.apscheduler_patch import patch_apscheduler
patch_apscheduler()

# Import bot main function
from src.bot import main

if __name__ == "__main__":
    main()