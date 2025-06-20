import logging
import asyncio
from datetime import datetime
from typing import List
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler
)

from config import (
    TELEGRAM_BOT_TOKEN,
    RSS_FEED_URL,
    CHECK_INTERVAL,
    WELCOME_MESSAGE,
    HELP_MESSAGE,
    REDIS_URL
)
from src.rss_parser import RSSParser, Job
from src.storage import get_storage

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize components
rss_parser = RSSParser(RSS_FEED_URL)
storage = get_storage(REDIS_URL)

# Create reply keyboard with command buttons
MAIN_MENU_KEYBOARD = ReplyKeyboardMarkup(
    [
        ['/start', '/latest'],
        ['/filter', '/favorites'],
        ['/help', '/stop']
    ],
    resize_keyboard=True
)

# Define conversation states
SELECTING_FILTER_ACTION = 1
SELECTING_JOB_TYPE = 2
ADDING_CUSTOM_FILTER = 3
REMOVING_FILTER = 4


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command"""
    chat_id = update.effective_chat.id
    
    # Add user to subscribers
    storage.add_subscriber(chat_id)
    
    # Send welcome message with keyboard
    await update.message.reply_text(
        f"✅ <b>Successfully subscribed!</b>\n\n{WELCOME_MESSAGE}",
        parse_mode=ParseMode.HTML,
        reply_markup=MAIN_MENU_KEYBOARD
    )
    
    logger.info(f"User {chat_id} subscribed")


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /stop command"""
    chat_id = update.effective_chat.id
    
    # Remove user from subscribers
    storage.remove_subscriber(chat_id)
    
    await update.message.reply_text(
        "✅ <b>Successfully unsubscribed!</b>\n\n"
        "You've been unsubscribed from job updates. "
        "Use /start to subscribe again.",
        parse_mode=ParseMode.HTML,
        reply_markup=MAIN_MENU_KEYBOARD
    )
    
    logger.info(f"User {chat_id} unsubscribed")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command"""
    await update.message.reply_text(
        HELP_MESSAGE,
        parse_mode=ParseMode.HTML,
        reply_markup=MAIN_MENU_KEYBOARD
    )


async def filters_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /filter command - show filtering options"""
    chat_id = update.effective_chat.id
    
    # Get current filters
    job_type_filters = storage.get_user_job_type_filters(chat_id)
    custom_filters = storage.get_custom_filters(chat_id)
    
    # Create keyboard with filter action buttons
    keyboard = [
        ["View My Filters", "Add Job Type Filter"],
        ["Add Custom Filter", "Remove Filter"],
        ["Clear All Filters", "Cancel"]
    ]
    
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    # Display current filters summary
    filter_msg = ""
    if job_type_filters or custom_filters:
        filter_msg = "Your current filters:\n"
        if job_type_filters:
            filter_msg += f"• Job types: <b>{', '.join(job_type_filters)}</b>\n"
        if custom_filters:
            filter_msg += f"• Custom filters: <b>{', '.join(custom_filters)}</b>\n"
    else:
        filter_msg = "You don't have any active filters. You are receiving all job types."
    
    await update.message.reply_text(
        f"🔍 <b>Job Filters</b>\n\n"
        f"{filter_msg}\n\n"
        f"What would you like to do?",
        parse_mode=ParseMode.HTML,
        reply_markup=reply_markup
    )
    
    return SELECTING_FILTER_ACTION


async def filter_action_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle filter action selection"""
    chat_id = update.effective_chat.id
    action = update.message.text
    
    if action == "View My Filters":
        # Get current filters
        job_type_filters = storage.get_user_job_type_filters(chat_id)
        custom_filters = storage.get_custom_filters(chat_id)
        
        if not job_type_filters and not custom_filters:
            await update.message.reply_text(
                "📋 <b>Your Filters</b>\n\n"
                "You don't have any active filters. You are receiving all job types.",
                parse_mode=ParseMode.HTML,
                reply_markup=MAIN_MENU_KEYBOARD
            )
        else:
            filter_msg = "📋 <b>Your Filters</b>\n\n"
            if job_type_filters:
                filter_msg += "<b>Job Type Filters:</b>\n"
                for i, filter_type in enumerate(job_type_filters, 1):
                    filter_msg += f"{i}. {filter_type}\n"
                filter_msg += "\n"
                
            if custom_filters:
                filter_msg += "<b>Custom Keyword Filters:</b>\n"
                for i, keyword in enumerate(custom_filters, 1):
                    filter_msg += f"{i}. {keyword}\n"
            
            await update.message.reply_text(
                filter_msg,
                parse_mode=ParseMode.HTML,
                reply_markup=MAIN_MENU_KEYBOARD
            )
        
        return ConversationHandler.END
        
    elif action == "Add Job Type Filter":
        # Get available job types from RSS feed
        available_job_types = rss_parser.get_available_job_types()
        
        # Create keyboard with job type buttons
        keyboard = []
        for i in range(0, len(available_job_types), 2):
            row = available_job_types[i:i+2]
            keyboard.append([job_type.title() for job_type in row])
        
        # Add Cancel button
        keyboard.append(["Cancel"])
        
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        
        await update.message.reply_text(
            "Select a job type to add to your filters:",
            reply_markup=reply_markup
        )
        
        return SELECTING_JOB_TYPE
        
    elif action == "Add Custom Filter":
        await update.message.reply_text(
            "📝 Enter a custom keyword or phrase to filter jobs by.\n\n"
            "Jobs that contain this text in their title or description will be shown.\n\n"
            "Type 'cancel' to cancel.",
            reply_markup=ReplyKeyboardRemove()
        )
        
        return ADDING_CUSTOM_FILTER
        
    elif action == "Remove Filter":
        # Get all filters
        job_type_filters = storage.get_user_job_type_filters(chat_id)
        custom_filters = storage.get_custom_filters(chat_id)
        
        if not job_type_filters and not custom_filters:
            await update.message.reply_text(
                "You don't have any filters to remove.",
                reply_markup=MAIN_MENU_KEYBOARD
            )
            return ConversationHandler.END
            
        # Create keyboard with all filters
        keyboard = []
        
        # Add job type filters
        for job_type in job_type_filters:
            keyboard.append([f"Type: {job_type}"])
            
        # Add custom filters
        for keyword in custom_filters:
            keyboard.append([f"Custom: {keyword}"])
            
        # Add Cancel button
        keyboard.append(["Cancel"])
        
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        
        await update.message.reply_text(
            "Select a filter to remove:",
            reply_markup=reply_markup
        )
        
        return REMOVING_FILTER
        
    elif action == "Clear All Filters":
        # Clear all filters
        storage.clear_user_job_type_filters(chat_id)
        storage.clear_custom_filters(chat_id)
        storage.clear_user_job_type(chat_id)  # Clear legacy filter too
        
        await update.message.reply_text(
            "✅ All filters cleared. You will now receive all job types.",
            reply_markup=MAIN_MENU_KEYBOARD
        )
        
        return ConversationHandler.END
        
    else:  # Cancel
        await update.message.reply_text(
            "Filter management cancelled. No changes made.",
            reply_markup=MAIN_MENU_KEYBOARD
        )
        
        return ConversationHandler.END


async def add_job_type_filter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Add a job type filter"""
    chat_id = update.effective_chat.id
    selected_type = update.message.text.lower()
    
    if selected_type == "cancel":
        await update.message.reply_text(
            "Operation cancelled. No changes made.",
            reply_markup=MAIN_MENU_KEYBOARD
        )
        return ConversationHandler.END
    
    # Add the job type filter
    storage.add_user_job_type_filter(chat_id, selected_type)
    
    # Get all job type filters
    job_type_filters = storage.get_user_job_type_filters(chat_id)
    
    await update.message.reply_text(
        f"✅ Added <b>{selected_type}</b> to your job type filters.\n\n"
        f"Current job type filters: <b>{', '.join(job_type_filters)}</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=MAIN_MENU_KEYBOARD
    )
    
    return ConversationHandler.END


async def add_custom_filter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Add a custom keyword filter"""
    chat_id = update.effective_chat.id
    keyword = update.message.text
    
    if keyword.lower() == "cancel":
        await update.message.reply_text(
            "Operation cancelled. No changes made.",
            reply_markup=MAIN_MENU_KEYBOARD
        )
        return ConversationHandler.END
    
    # Add the custom filter
    storage.add_custom_filter(chat_id, keyword)
    
    # Get all custom filters
    custom_filters = storage.get_custom_filters(chat_id)
    
    await update.message.reply_text(
        f"✅ Added custom filter: <b>{keyword}</b>\n\n"
        f"Current custom filters: <b>{', '.join(custom_filters)}</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=MAIN_MENU_KEYBOARD
    )
    
    return ConversationHandler.END


async def remove_filter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Remove a filter"""
    chat_id = update.effective_chat.id
    filter_text = update.message.text
    
    if filter_text == "Cancel":
        await update.message.reply_text(
            "Operation cancelled. No changes made.",
            reply_markup=MAIN_MENU_KEYBOARD
        )
        return ConversationHandler.END
    
    # Parse the filter text
    if filter_text.startswith("Type: "):
        # Remove job type filter
        job_type = filter_text[6:].lower()
        storage.remove_user_job_type_filter(chat_id, job_type)
        await update.message.reply_text(
            f"✅ Removed job type filter: <b>{job_type}</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=MAIN_MENU_KEYBOARD
        )
    elif filter_text.startswith("Custom: "):
        # Remove custom filter
        keyword = filter_text[8:]
        storage.remove_custom_filter(chat_id, keyword)
        await update.message.reply_text(
            f"✅ Removed custom filter: <b>{keyword}</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=MAIN_MENU_KEYBOARD
        )
    else:
        await update.message.reply_text(
            "❌ Invalid filter selection. Please try again.",
            reply_markup=MAIN_MENU_KEYBOARD
        )
    
    return ConversationHandler.END


async def cancel_filter_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the filter selection process"""
    await update.message.reply_text(
        "🔍 Filter selection cancelled. No changes were made.",
        reply_markup=MAIN_MENU_KEYBOARD
    )
    return ConversationHandler.END


async def latest_jobs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the latest jobs"""
    chat_id = update.effective_chat.id
    
    # Check if this is a request for new jobs only
    new_only = False
    if context.args and context.args[0] == "new":
        new_only = True
        # If we have a page number as second argument
        if len(context.args) > 1 and context.args[1].isdigit():
            page = int(context.args[1])
        else:
            page = 1
    else:
        # Get pagination parameter (default: page 1, 5 jobs per page)
        page = 1
        if context.args and context.args[0].isdigit():
            page = int(context.args[0])
    
    jobs_per_page = 5
    
    # Determine if this is a callback query or direct command
    is_callback = update.callback_query is not None
    
    # Show loading message
    if is_callback:
        # For callback queries, edit the existing message
        loading_message = await update.callback_query.message.edit_text(
            "🔍 <b>Fetching jobs...</b>",
            parse_mode=ParseMode.HTML
        )
    else:
        # For direct commands, send a new message
        loading_message = await update.message.reply_text(
            "🔍 <b>Fetching jobs...</b>",
            parse_mode=ParseMode.HTML
        )
    
    try:
        # Fetch jobs from RSS feed
        jobs = rss_parser.fetch_jobs()
        
        # Filter jobs based on user preferences
        filtered_jobs = check_job_filters(jobs, chat_id)
        
        # If new_only is True, filter out jobs that the user has already seen
        if new_only:
            seen_jobs = storage.get_seen_jobs(chat_id)
            filtered_jobs = [job for job in filtered_jobs if job.guid not in seen_jobs]
            
            # Mark these jobs as seen
            for job in filtered_jobs:
                storage.add_seen_job(chat_id, job.guid)
        
        # Calculate total pages
        total_jobs = len(filtered_jobs)
        total_pages = (total_jobs + jobs_per_page - 1) // jobs_per_page
        
        # Adjust page number if out of bounds
        if page < 1:
            page = 1
        elif page > total_pages and total_pages > 0:
            page = total_pages
        
        # Get jobs for the current page
        start_idx = (page - 1) * jobs_per_page
        end_idx = start_idx + jobs_per_page
        page_jobs = filtered_jobs[start_idx:end_idx]
        
        # Create a mapping for save IDs
        if not hasattr(context.application, 'save_id_map'):
            context.application.save_id_map = {}
        
        # If no jobs found
        if not page_jobs:
            if new_only:
                message = "No new jobs found matching your filters."
            else:
                message = "No jobs found matching your filters."
                
            if is_callback:
                await update.callback_query.message.edit_text(
                    message,
                    reply_markup=MAIN_MENU_KEYBOARD
                )
            else:
                await loading_message.edit_text(
                    message,
                    reply_markup=MAIN_MENU_KEYBOARD
                )
            return
        
        # Send header message
        header = f"📋 <b>Latest Jobs</b> ({total_jobs} total)"
        if new_only:
            header = f"🆕 <b>New Jobs</b> ({total_jobs} total)"
            
        if is_callback:
            await update.callback_query.message.edit_text(
                header,
                parse_mode=ParseMode.HTML
            )
        else:
            await loading_message.edit_text(
                header,
                parse_mode=ParseMode.HTML
            )
        
        # Send each job
        for job in page_jobs:
            # Create a short hash for the callback data
            short_id = str(abs(hash(job.guid)) % 10000000)
            context.application.save_id_map[short_id] = job
            
            # Format job message
            message = job.to_telegram_message()
            
            # Create inline keyboard with Apply and Save buttons
            keyboard = [
                [
                    InlineKeyboardButton("🔗 Apply", url=job.link),
                    InlineKeyboardButton("💾 Save", callback_data=f"save_{short_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if is_callback:
                await update.callback_query.message.reply_text(
                    message,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                    reply_markup=reply_markup
                )
            else:
                await update.message.reply_text(
                    message,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                    reply_markup=reply_markup
                )
            
            await asyncio.sleep(0.5)  # Rate limiting
        
        # Add pagination buttons if needed
        if total_pages > 1:
            # Create pagination keyboard
            pagination_buttons = []
            
            # Previous page button
            if page > 1:
                pagination_buttons.append(
                    InlineKeyboardButton("⬅️ Previous", callback_data=f"p_{page-1}{'_new' if new_only else ''}")
                )
            
            # Page indicator
            pagination_buttons.append(
                InlineKeyboardButton(f"Page {page}/{total_pages}", callback_data="noop")
            )
            
            # Next page button
            if page < total_pages:
                pagination_buttons.append(
                    InlineKeyboardButton("Next ➡️", callback_data=f"p_{page+1}{'_new' if new_only else ''}")
                )
            
            pagination_markup = InlineKeyboardMarkup([pagination_buttons])
            
            if is_callback:
                await update.callback_query.message.reply_text(
                    f"Page {page} of {total_pages}",
                    reply_markup=pagination_markup
                )
            else:
                await update.message.reply_text(
                    f"Page {page} of {total_pages}",
                    reply_markup=pagination_markup
                )
        
        # Final message with menu keyboard
        if is_callback:
            await update.callback_query.message.reply_text(
                "Use the menu below for more commands:",
                reply_markup=MAIN_MENU_KEYBOARD
            )
        else:
            await update.message.reply_text(
                "Use the menu below for more commands:",
                reply_markup=MAIN_MENU_KEYBOARD
            )
            
    except Exception as e:
        logger.error(f"Error fetching jobs: {e}")
        error_message = "❌ Error fetching jobs. Please try again later."
        
        if is_callback:
            await update.callback_query.message.edit_text(
                error_message,
                reply_markup=MAIN_MENU_KEYBOARD
            )
        else:
            await loading_message.edit_text(
                error_message,
                reply_markup=MAIN_MENU_KEYBOARD
            )


async def pagination_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle pagination callbacks"""
    query = update.callback_query
    await query.answer()
    
    # Extract page number from callback data
    callback_data = query.data
    
    # Check if this is a no-op callback (page indicator)
    if callback_data == "noop":
        return
    
    # Parse callback data
    parts = callback_data.split('_')
    page = int(parts[1])
    
    # Check if this is for new jobs only
    new_only = len(parts) > 2 and parts[2] == "new"
    
    # Set args for latest_jobs function
    if new_only:
        context.args = ["new", str(page)]
    else:
        context.args = [str(page)]
    
    # Call latest_jobs with the updated page
    await latest_jobs(update, context)


async def save_job(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Save a job to favorites"""
    query = update.callback_query
    await query.answer()
    
    # Extract short ID from callback data
    short_id = query.data.split('_')[1]
    chat_id = update.effective_chat.id
    
    # Get the job from the mapping
    if hasattr(context.application, 'save_id_map') and short_id in context.application.save_id_map:
        job = context.application.save_id_map[short_id]
    else:
        await query.edit_message_text(
            "❌ Error: Job not found.",
            reply_markup=None
        )
        return
    
    # Save job to favorites
    storage.save_favorite_job(chat_id, job.guid, job.to_dict())
    
    # Update the inline keyboard to show job was saved
    keyboard = [
        [
            InlineKeyboardButton("🔗 Apply", url=job.link),
            InlineKeyboardButton("✅ Saved", callback_data="noop")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_reply_markup(reply_markup=reply_markup)


async def send_commands_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the commands menu when receiving a text message that's not a command"""
    await update.message.reply_text(
        "Please use one of the following commands:",
        reply_markup=MAIN_MENU_KEYBOARD
    )


async def check_new_jobs(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check for new jobs and notify subscribers"""
    logger.info("Checking for new jobs...")
    
    try:
        # Get subscribers
        subscribers = storage.get_subscribers()
        if not subscribers:
            logger.info("No subscribers found")
            return
        
        # Fetch jobs from RSS feed
        jobs = rss_parser.fetch_jobs()
        
        # Get last check time
        last_check_time = storage.get_last_check_time()
        current_time = datetime.now()
        
        # Filter new jobs since last check
        new_jobs = []
        if last_check_time:
            new_jobs = [job for job in jobs if job.published_date > last_check_time]
        else:
            # First run, don't notify about all jobs
            new_jobs = []
        
        # Update last check time
        storage.set_last_check_time(current_time)
        
        if not new_jobs:
            logger.info("No new jobs found")
            return
            
        logger.info(f"Found {len(new_jobs)} new jobs")
        
        # Notify subscribers about new jobs
        for chat_id in subscribers:
            # Filter jobs based on user preferences
            filtered_jobs = check_job_filters(new_jobs, chat_id)
            
            # Skip if no jobs match filters
            if not filtered_jobs:
                continue
                
            # Get seen jobs for this user
            seen_jobs = storage.get_seen_jobs(chat_id)
            
            # Filter out jobs that the user has already seen
            unseen_jobs = [job for job in filtered_jobs if job.guid not in seen_jobs]
            
            # Skip if no unseen jobs
            if not unseen_jobs:
                continue
                
            # Mark these jobs as seen
            for job in unseen_jobs:
                storage.add_seen_job(chat_id, job.guid)
            
            # Send notification about new jobs
            try:
                # Send header message
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"🔔 <b>New Jobs Alert!</b> ({len(unseen_jobs)} new)",
                    parse_mode=ParseMode.HTML
                )
                
                # Create a mapping for save IDs if it doesn't exist
                if not hasattr(context.application, 'save_id_map'):
                    context.application.save_id_map = {}
                
                # Send each job (max 5 to avoid spam)
                for job in unseen_jobs[:5]:
                    # Create a short hash for the callback data
                    short_id = str(abs(hash(job.guid)) % 10000000)
                    context.application.save_id_map[short_id] = job
                    
                    # Format job message
                    message = job.to_telegram_message()
                    
                    # Create inline keyboard with Apply and Save buttons
                    keyboard = [
                        [
                            InlineKeyboardButton("🔗 Apply", url=job.link),
                            InlineKeyboardButton("💾 Save", callback_data=f"save_{short_id}")
                        ]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True,
                        reply_markup=reply_markup
                    )
                    
                    await asyncio.sleep(0.5)  # Rate limiting
                
                # If there are more jobs, add a message
                if len(unseen_jobs) > 5:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"... and {len(unseen_jobs) - 5} more new jobs. Use /latest new to see all.",
                        reply_markup=MAIN_MENU_KEYBOARD
                    )
                else:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text="Use the menu below for more commands:",
                        reply_markup=MAIN_MENU_KEYBOARD
                    )
                    
            except Exception as e:
                logger.error(f"Error sending notification to {chat_id}: {e}")
                
    except Exception as e:
        logger.error(f"Error checking for new jobs: {e}")


def check_job_filters(jobs: List[Job], chat_id: int) -> List[Job]:
    """Filter jobs based on user preferences"""
    # Get user filters
    job_type_filters = storage.get_user_job_type_filters(chat_id)
    custom_filters = storage.get_custom_filters(chat_id)
    
    # If no filters are set, return all jobs
    if not job_type_filters and not custom_filters:
        return jobs
    
    filtered_jobs = []
    
    for job in jobs:
        # Check if job matches any job type filter
        job_type_match = False
        if job_type_filters:
            job_type_match = job.job_type.lower() in [jt.lower() for jt in job_type_filters]
        
        # Check if job matches any custom filter
        custom_match = False
        if custom_filters:
            # Check if any custom filter is in the job title or description
            job_text = (job.title + " " + job.description).lower()
            custom_match = any(keyword.lower() in job_text for keyword in custom_filters)
        
        # Add job if it matches any filter (job type OR custom)
        if job_type_match or custom_match or (not job_type_filters and not custom_filters):
            filtered_jobs.append(job)
    
    return filtered_jobs


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")
    
    try:
        # Send error message to user
        if update and update.effective_chat:
            # For callback queries, use the bot.send_message instead of reply_text
            # since update.message might be None
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ An error occurred. Please try again later.",
                reply_markup=MAIN_MENU_KEYBOARD
            )
    except Exception as e:
        logger.error(f"Error in error handler: {e}")


async def favorites_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user's favorite jobs"""
    chat_id = update.effective_chat.id
    
    # Get favorite jobs
    favorites = storage.get_favorite_jobs(chat_id)
    
    if not favorites:
        await update.message.reply_text(
            "You don't have any saved jobs. Use the 'Save' button on job listings to add them to favorites.",
            reply_markup=MAIN_MENU_KEYBOARD
        )
        return
    
    # Send header message
    await update.message.reply_text(
        f"📌 <b>Your Saved Jobs</b> ({len(favorites)} total)",
        parse_mode=ParseMode.HTML
    )
    
    # Create a mapping for short IDs
    if not hasattr(context.application, 'remove_id_map'):
        context.application.remove_id_map = {}
        
    # Send each favorite job
    for i, (guid, job_data) in enumerate(favorites.items(), 1):
        # Create job object from data
        job = Job.from_dict(job_data)
        
        # Create a short hash for the callback data
        short_id = str(abs(hash(guid)) % 10000000)
        context.application.remove_id_map[short_id] = guid
        
        # Format job message
        message = job.to_telegram_message()
        
        # Create inline keyboard with Apply and Remove buttons
        keyboard = [
            [
                InlineKeyboardButton("🔗 Apply", url=job.link),
                InlineKeyboardButton("❌ Remove", callback_data=f"remove_{short_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            message,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=reply_markup
        )
        await asyncio.sleep(0.5)  # Rate limiting
    
    # Final message with menu keyboard
    await update.message.reply_text(
        "Use the menu below for more commands:",
        reply_markup=MAIN_MENU_KEYBOARD
    )


async def remove_favorite(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove a job from favorites"""
    query = update.callback_query
    await query.answer()
    
    # Extract short ID from callback data
    short_id = query.data.split('_')[1]
    chat_id = update.effective_chat.id
    
    # Get the actual job GUID from the mapping
    if hasattr(context.application, 'remove_id_map') and short_id in context.application.remove_id_map:
        job_guid = context.application.remove_id_map[short_id]
    else:
        await query.edit_message_text(
            "❌ Error: Job not found.",
            reply_markup=None
        )
        return
    
    # Remove job from favorites
    storage.remove_favorite_job(chat_id, job_guid)
    
    # Update the message to show job was removed
    await query.edit_message_text(
        "✅ Job removed from favorites.",
        reply_markup=None
    )


def main() -> None:
    """Start the bot"""
    # Set up application with token from config
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("latest", latest_jobs))
    application.add_handler(CommandHandler("favorites", favorites_command))
    
    # Add filter conversation handler
    try:
        from src.filters import filters_conversation_handler
        application.add_handler(filters_conversation_handler)
        logger.info("Advanced filtering system loaded")
    except ImportError as e:
        logger.error(f"Error loading advanced filtering system: {e}")
        # Fallback to basic filter handler
        filters_conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler("filters", legacy_filters_command),
                CommandHandler("filter", legacy_filters_command)
            ],
            states={
                SELECTING_JOB_TYPE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, set_job_type)
                ],
            },
            fallbacks=[CommandHandler("cancel", cancel_filter_selection)],
        )
        application.add_handler(filters_conv_handler)
        logger.info("Basic filtering system loaded")
    
    # Add callback handlers
    application.add_handler(CallbackQueryHandler(pagination_callback, pattern=r"^p_"))
    application.add_handler(CallbackQueryHandler(save_job, pattern=r"^save_\d+$"))
    application.add_handler(CallbackQueryHandler(remove_favorite, pattern=r"^remove_\d+$"))
    
    # Add message handler for text messages that are not commands
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, send_commands_menu))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Schedule job checking
    job_queue = application.job_queue
    job_queue.run_repeating(check_new_jobs, interval=CHECK_INTERVAL * 60, first=10)  # Convert minutes to seconds
    
    # Start the Bot
    logger.info("Starting bot...")
    application.run_polling()


if __name__ == '__main__':
    main()

async def legacy_filters_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Legacy filter command handler - redirects to the new filters system"""
    # Import and call the filters command from the filters module
    try:
        from src.filters import filters_command as new_filters_command
        return await new_filters_command(update, context)
    except ImportError:
        # Fallback if filters module is not available
        await update.message.reply_text(
            "Filter system is not available. Please try again later.",
            reply_markup=MAIN_MENU_KEYBOARD
        )
        return ConversationHandler.END

async def set_job_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Legacy method for backward compatibility"""
    chat_id = update.effective_chat.id
    selected_type = update.message.text.lower()
    
    if selected_type == "all":
        # Clear the job type filter
        storage.clear_user_job_type(chat_id)
        await update.message.reply_text(
            "✅ <b>Filter removed.</b> You will now receive all job types.",
            parse_mode=ParseMode.HTML,
            reply_markup=MAIN_MENU_KEYBOARD
        )
    else:
        # Set the job type filter
        # Normalize job type (remove "Title" formatting)
        job_type = selected_type.lower()
        storage.set_user_job_type(chat_id, job_type)
        await update.message.reply_text(
            f"✅ <b>Filter set!</b> You will now only receive <b>{job_type}</b> jobs.",
            parse_mode=ParseMode.HTML,
            reply_markup=MAIN_MENU_KEYBOARD
        )
    
    return ConversationHandler.END