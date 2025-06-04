"""
Enhanced filtering system for the telegram bot.
This file defines the conversation handlers and logic for managing job filters.
"""

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters
)
from telegram.constants import ParseMode

# Define conversation states
SELECTING_FILTER_ACTION = 1
SELECTING_JOB_TYPE = 2
ADDING_CUSTOM_FILTER = 3
REMOVING_FILTER = 4

# Main menu keyboard
from src.bot import MAIN_MENU_KEYBOARD, rss_parser, storage


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


# Create the conversation handler
filters_conversation_handler = ConversationHandler(
    entry_points=[
        CommandHandler("filters", filters_command),
        CommandHandler("filter", filters_command)  # Support both singular and plural forms
    ],
    states={
        SELECTING_FILTER_ACTION: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, filter_action_handler)
        ],
        SELECTING_JOB_TYPE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, add_job_type_filter)
        ],
        ADDING_CUSTOM_FILTER: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, add_custom_filter)
        ],
        REMOVING_FILTER: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, remove_filter)
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel_filter_selection)],
)