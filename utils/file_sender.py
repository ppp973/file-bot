from pyrogram import Client
from pyrogram.types import Message
from pyrogram.errors import FloodWait
import asyncio
import logging
from config import Config

logger = logging.getLogger(__name__)

class FileSender:
    """Handle sending files to users with protection"""
    
    def __init__(self, client: Client):
        self.client = client
    
    async def send_file_to_user(self, user_id: int, file_data: dict, order: int, total: int) -> bool:
        """
        Send a single file to user with content protection
        
        Args:
            user_id: Telegram user ID
            file_data: File data from database
            order: Current file order
            total: Total files in batch
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            # Send progress message
            progress_text = f"📤 Sending file {order}/{total}"
            
            # Copy message from storage channel with content protection
            await self.client.copy_message(
                chat_id=user_id,
                from_chat_id=Config.STORAGE_CHANNEL,
                message_id=file_data["message_id"],
                caption=f"**File {order}/{total}**\n\n{file_data.get('title', '')}",
                protect_content=True  # This disables forwarding and saving
            )
            
            # Small delay to avoid flood limits
            await asyncio.sleep(Config.FLOOD_WAIT_DELAY)
            return True
            
        except FloodWait as e:
            logger.warning(f"Flood wait required: {e.value} seconds")
            await asyncio.sleep(e.value)
            # Retry after flood wait
            return await self.send_file_to_user(user_id, file_data, order, total)
            
        except Exception as e:
            logger.error(f"Error sending file to user {user_id}: {e}")
            return False
    
    async def send_batch_to_user(self, user_id: int, batch_id: str, files: list) -> tuple:
        """
        Send all files in a batch to user
        
        Returns:
            tuple: (success_count, total_count)
        """
        total_files = len(files)
        success_count = 0
        
        # Send start message
        await self.client.send_message(
            user_id,
            f"📦 **Batch Found!**\n\n"
            f"📁 Batch ID: `{batch_id}`\n"
            f"📊 Total Files: {total_files}\n\n"
            f"🔒 Files are protected and cannot be forwarded or saved.\n"
            f"⏳ Sending files one by one..."
        )
        
        # Send files in order
        for i, file_data in enumerate(files, 1):
            if await self.send_file_to_user(user_id, file_data, i, total_files):
                success_count += 1
        
        # Send completion message
        await self.client.send_message(
            user_id,
            f"✅ **Delivery Complete!**\n\n"
            f"📁 Batch ID: `{batch_id}`\n"
            f"📊 Files Sent: {success_count}/{total_files}\n\n"
            f"🔒 Remember: These files are protected and cannot be forwarded."
        )
        
        return success_count, total_files

# Note: FileSender instance will be created in bot.py