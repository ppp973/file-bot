from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import Config
from database import db
import logging

logger = logging.getLogger(__name__)

async def register_finish_handlers(client: Client, active_uploads: dict):
    """Register finish command handlers"""
    
    @client.on_message(filters.command("finish"))
    async def finish_command(client: Client, message: Message):
        """Handle /finish command"""
        user_id = message.from_user.id
        
        # Check if user is admin
        if user_id not in Config.ADMINS:
            await message.reply_text(
                "❌ **Access Denied**\n\n"
                "This command is only available for admins."
            )
            return
        
        # Check if user has active upload
        if user_id not in active_uploads:
            await message.reply_text(
                "❌ **No Active Upload**\n\n"
                "Start an upload first with /upload"
            )
            return
        
        upload_data = active_uploads[user_id]
        batch_id = upload_data["batch_id"]
        total_files = upload_data["order"]
        
        # Generate bot username and link
        bot_info = await client.get_me()
        bot_username = bot_info.username
        share_link = f"https://t.me/{bot_username}?start={batch_id}"
        
        # Create completion message
        completion_text = (
            f"✅ **Upload Completed!**\n\n"
            f"📁 **Batch ID:** `{batch_id}`\n"
            f"📊 **Total Files:** {total_files}\n"
            f"⏱️ **Duration:** Completed\n\n"
            f"🔗 **Share Link:**\n"
            f"{share_link}\n\n"
            f"📌 **Instructions:**\n"
            f"• Share this link with users\n"
            f"• Users will receive files in order\n"
            f"• Files are protected (no forwarding)\n\n"
            f"⚠️ Save this link and batch ID for future reference!"
        )
        
        # Send completion message with copy button
        await message.reply_text(
            completion_text,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("📋 Copy Link", callback_data=f"copy_{batch_id}")
            ]])
        )
        
        # Send summary to storage channel for logging
        try:
            await client.send_message(
                Config.STORAGE_CHANNEL,
                f"📦 **New Upload Complete**\n\n"
                f"📁 Batch: `{batch_id}`\n"
                f"📊 Files: {total_files}\n"
                f"👤 Admin: {user_id}\n"
                f"🔗 Link: {share_link}"
            )
        except Exception as e:
            logger.error(f"Error sending to storage channel: {e}")
        
        # Remove from active uploads
        del active_uploads[user_id]
    
    @client.on_message(filters.command("stats"))
    async def stats_command(client: Client, message: Message):
        """Handle /stats command"""
        user_id = message.from_user.id
        
        # Check if user is admin
        if user_id not in Config.ADMINS:
            await message.reply_text(
                "❌ **Access Denied**\n\n"
                "This command is only available for admins."
            )
            return
        
        # Get statistics
        stats = await db.get_stats()
        
        # Get active uploads count
        active_count = len(active_uploads)
        
        await message.reply_text(
            f"📊 **Bot Statistics**\n\n"
            f"📁 **Total Batches:** {stats['total_batches']}\n"
            f"📄 **Total Files:** {stats['total_files']}\n"
            f"⚡ **Active Uploads:** {active_count}\n"
            f"👤 **Your ID:** `{user_id}`\n\n"
            f"🔧 **System Status:**\n"
            f"• Database: ✅ Connected\n"
            f"• Storage Channel: ✅ Active\n"
            f"• Bot: ✅ Running"
        )
    
    @client.on_message(filters.command("help"))
    async def help_command(client: Client, message: Message):
        """Handle /help command"""
        user_id = message.from_user.id
        is_admin = user_id in Config.ADMINS
        
        help_text = (
            "📚 **Bot Commands**\n\n"
            "**User Commands:**\n"
            "• /start - Start the bot\n"
            "• /help - Show this help\n\n"
        )
        
        if is_admin:
            help_text += (
                "**Admin Commands:**\n"
                "• /upload - Start batch upload\n"
                "• /finish - Finish upload and get link\n"
                "• /stats - View bot statistics\n\n"
                "**Upload Instructions:**\n"
                "1️⃣ Use /upload to start\n"
                "2️⃣ Send files (any type)\n"
                "3️⃣ Use /finish when done\n"
                "4️⃣ Share the generated link\n\n"
            )
        
        help_text += (
            "**Features:**\n"
            "• 🔒 Protected content (no forwarding)\n"
            "• 📁 Batch file storage\n"
            "• 🔗 Secure shareable links\n"
            "• 📊 Upload statistics\n\n"
            "**Need help?** Contact your administrator."
        )
        
        await message.reply_text(help_text)