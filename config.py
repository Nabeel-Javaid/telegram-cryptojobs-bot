import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')

# RSS Feed Configuration
RSS_FEED_URL = os.getenv('RSS_FEED_URL', 'https://api.cryptojobslist.com/rss/Remote.xml')

# Check interval in minutes
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '5'))

# Redis Configuration (optional, for production use)
REDIS_URL = os.getenv('REDIS_URL', None)

# Timezone
TIMEZONE = os.getenv('TIMEZONE', 'UTC')

# Bot Messages
WELCOME_MESSAGE = """
🚀 <b>Welcome to CryptoJobs Bot!</b>

I'll help you stay updated with the latest remote crypto jobs from CryptoJobsList.

You can use the menu buttons below or the following commands:

/start - Subscribe to job updates
/stop - Unsubscribe from job updates  
/latest - Get the latest 5 jobs
/filter - Manage your job filters
/favorites - View your saved jobs
/help - Show this help message

You'll receive notifications whenever new jobs are posted!

📌 <b>Pro Tip:</b> Use /filter to set up multiple job type filters and custom keyword filters to receive only the most relevant job opportunities.
"""

HELP_MESSAGE = """
📋 <b>Available Commands:</b>

/start - Subscribe to job updates
/stop - Unsubscribe from job updates
/latest - Get the latest jobs (all available jobs)
/latest new - Show only new jobs you haven't seen before
/filter - Manage your job filters
/favorites - View your saved jobs
/help - Show this help message

📱 <b>Job Filtering:</b>
Use /filter to set up job type filters and custom keyword filters.
You can combine multiple filters to receive only the most relevant job opportunities.

💾 <b>Saving Jobs:</b>
When you receive a job notification, you can save it to your favorites by clicking the "Save" button.
Use /favorites to view your saved jobs.
"""

FILTER_HELP_MESSAGE = """
🔍 <b>Job Filtering System</b>

You can filter jobs by:

1️⃣ <b>Job Type</b> - Select from predefined categories like frontend, backend, blockchain, etc.
2️⃣ <b>Custom Keywords</b> - Enter your own keywords to match in job titles and descriptions

<b>How filtering works:</b>
- You can add multiple job types and custom filters
- A job will match if it belongs to ANY of your selected job types OR contains ANY of your custom keywords
- If you have no filters set, you'll receive all job notifications

Use the buttons below to manage your filters.
"""

NO_FILTERS_MESSAGE = "You don't have any filters set. You will receive all job notifications."

FILTER_ADDED_MESSAGE = "✅ Filter added successfully!"
FILTER_REMOVED_MESSAGE = "✅ Filter removed successfully!"
FILTERS_CLEARED_MESSAGE = "✅ All filters cleared successfully!"

NO_JOBS_MESSAGE = "No jobs found matching your criteria."
NO_FAVORITES_MESSAGE = "You don't have any saved jobs yet."

JOB_SAVED_MESSAGE = "✅ Job saved to favorites!"
JOB_REMOVED_MESSAGE = "✅ Job removed from favorites!"