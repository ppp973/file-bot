from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from database import db
from utils.file_sender import FileSender
import logging

logger = logging.getLogger(__name__)

async def register_start_handlers(client: Client, file_sender: FileSender):
    """Register start command handlers"""
    
    @client.on_message(filters.command("start"))
    async def start_command(client: Client, message: Message):
        """Handle /start command and deep links"""
        
        user_id = message.from_user.id
        args = message.text.split()
        
        # Check if it's a deep link with batch ID
        if len(args) > 1:
            batch_id = args[1]
            await handle_deep_link(client, message, batch_id)
        else:
            # Regular start command
            await send_welcome_message(client, message)
    
    @client.on_callback_query()
    async def handle_callbacks(client: Client, callback_query):
        """Handle callback queries"""
        data = callback_query.data
        
        if data == "help":
            await callback_query.message.edit_text(
                get_help_text(),
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back", callback_data="back_to_main")
                ]])
            )
        
        elif data == "stats":
            stats = await db.get_stats()
            await callback_query.message.edit_text(
                f"📊 **Bot Statistics**\n\n"
                f"📁 Total Batches: {stats['total_batches']}\n"
                f"📄 Total Files: {stats['total_files']}\n"
                f"👤 Your ID: `{callback_query.from_user.id}`",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back", callback_data="back_to_main")
                ]])
            )
        
        elif data == "back_to_main":
            await callback_query.message.edit_text(
                get_welcome_text(callback_query.from_user.first_name),
                reply_markup=get_main_keyboard()
            )
        
        await callback_query.answer()
    
    async def handle_deep_link(client: Client, message: Message, batch_id: str):
        """Handle deep links with batch IDs"""
        user_id = message.from_user.id
        
        # Send initial message
        status_msg = await message.reply_text("🔍 **Searching for batch...**")
        
        # Check if batch exists
        batch = await db.get_upload_session(batch_id)
        
        if not batch:
            await status_msg.edit_text(
                "❌ **Invalid or Expired Link**\n\n"
                "The batch you're looking for doesn't exist or has been removed."
            )
            return
        
        # Get all files for this batch
        files = await db.get_batch_files(batch_id)
        
        if not files:
            await status_msg.edit_text(
                "❌ **No Files Found**\n\n"
                "This batch exists but contains no files."
            )
            return
        
        # Update status message
        await status_msg.edit_text(
            f"✅ **Batch Found!**\n\n"
            f"📁 Total Files: {len(files)}\n"
            f"⏳ Preparing to send..."
        )
        
        # Send files to user
        success, total = await file_sender.send_batch_to_user(user_id, batch_id, files)
        
        # Delete status message after completion
        await status_msg.delete()
    
    async def send_welcome_message(client: Client, message: Message):
        """Send welcome message to user"""
        user_name = message.from_user.first_name
        
        await message.reply_text(
            get_welcome_text(user_name),
            reply_markup=get_main_keyboard(),
            disable_web_page_preview=True
        )

def get_welcome_text(user_name: str) -> str:
    """Get welcome message text"""
    return (
        f"👋 **Hello {user_name}!**\n\n"
        "Welcome to **Secure File Store Bot** 🔐\n\n"
        "This bot allows admins to securely store and share files with protected content.\n\n"
        "📌 **Features:**\n"
        "• 🔒 Protected files (no forwarding/saving)\n"
        "• 📁 Batch file uploads\n"
        "• 🔗 Secure shareable links\n"
        "• 📊 Detailed statistics\n\n"
        "Use the buttons below to navigate:"
    )

def get_help_text() -> str:
    """Get help message text"""
    return (
        "📚 **Available Commands**\n\n"
        "**User Commands:**\n"
        "• /start - Start the bot\n"
        "• /help - Show this help\n\n"
        "**Admin Commands:**\n"
        "• /upload - Start batch upload\n"
        "• /finish - Finish upload and get link\n"
        "• /stats - View bot statistics\n\n"
        "**How to Use:**\n"
        "1️⃣ Admins use /upload to start\n"
        "2️⃣ Send files one by one\n"
        "3️⃣ Use /finish to get shareable link\n"
        "4️⃣ Share link with users\n"
        "5️⃣ Users click link to get files\n\n"
        "🔒 All files are protected and cannot be forwarded!"
    )

def get_main_keyboard():
    """Get main menu keyboard"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("❓ Help", callback_data="help"),
            InlineKeyboardButton("📊 Stats", callback_data="stats")
        ]
    ])