from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config
from database import db
from utils.id_generator import id_generator
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Store active upload sessions
active_uploads = {}

async def register_upload_handlers(client: Client):
    """Register upload command handlers"""
    
    @client.on_message(filters.command("upload"))
    async def upload_command(client: Client, message: Message):
        """Handle /upload command"""
        user_id = message.from_user.id
        
        # Check if user is admin
        if user_id not in Config.ADMINS:
            await message.reply_text(
                "❌ **Access Denied**\n\n"
                "This command is only available for admins."
            )
            return
        
        # Check if user already has an active upload
        if user_id in active_uploads:
            await message.reply_text(
                "⚠️ **Upload Already in Progress**\n\n"
                "You have an active upload session. Use /finish to complete it."
            )
            return
        
        # Generate new batch ID
        batch_id = id_generator.generate_batch_id()
        
        # Create upload session in database
        await db.create_upload_session(batch_id)
        
        # Store active upload
        active_uploads[user_id] = {
            "batch_id": batch_id,
            "files": [],
            "order": 0,
            "start_time": datetime.utcnow()
        }
        
        await message.reply_text(
            f"✅ **Upload Mode Started**\n\n"
            f"📁 Batch ID: `{batch_id}`\n"
            f"📤 Send your files now.\n\n"
            f"**Supported formats:**\n"
            f"• 📷 Images\n"
            f"• 📄 Documents\n"
            f"• 🎥 Videos\n"
            f"• 🔊 Audio\n"
            f"• 📁 PDFs\n\n"
            f"Send /finish when you're done."
        )
    
    @client.on_message(filters.private & ~filters.command(["start", "upload", "finish", "help", "stats"]))
    async def handle_files(client: Client, message: Message):
        """Handle file uploads during active session"""
        user_id = message.from_user.id
        
        # Check if user has active upload
        if user_id not in active_uploads:
            return
        
        # Check if message contains media
        if not (message.document or message.video or message.audio or 
                message.photo or message.voice or message.video_note):
            await message.reply_text(
                "⚠️ Please send a file (document, video, audio, or image)."
            )
            return
        
        upload_data = active_uploads[user_id]
        upload_data["order"] += 1
        current_order = upload_data["order"]
        batch_id = upload_data["batch_id"]
        
        # Forward file to storage channel
        try:
            # Get the media message
            media_message = message
            
            # Forward to storage channel
            forwarded = await media_message.forward(Config.STORAGE_CHANNEL)
            
            # Get file ID based on media type
            file_id = None
            file_title = None
            
            if media_message.document:
                file_id = media_message.document.file_id
                file_title = media_message.document.file_name or f"Document_{current_order}"
            elif media_message.video:
                file_id = media_message.video.file_id
                file_title = f"Video_{current_order}"
            elif media_message.audio:
                file_id = media_message.audio.file_id
                file_title = media_message.audio.title or f"Audio_{current_order}"
            elif media_message.photo:
                file_id = media_message.photo.file_id
                file_title = f"Photo_{current_order}"
            elif media_message.voice:
                file_id = media_message.voice.file_id
                file_title = f"Voice_{current_order}"
            elif media_message.video_note:
                file_id = media_message.video_note.file_id
                file_title = f"VideoNote_{current_order}"
            
            # Save to database
            await db.add_file(
                batch_id=batch_id,
                file_id=file_id,
                message_id=forwarded.id,
                order=current_order
            )
            
            # Send confirmation
            await message.reply_text(
                f"✅ **File {current_order} Saved**\n\n"
                f"📁 Batch: `{batch_id}`\n"
                f"📊 Total: {current_order} files\n\n"
                f"Send more files or use /finish"
            )
            
        except Exception as e:
            logger.error(f"Error forwarding file: {e}")
            await message.reply_text(
                "❌ **Error Saving File**\n\n"
                "Please try again or contact support."
            )
    
    # Return active_uploads for use in finish handler
    return active_uploads