#!/usr/bin/env python3
"""
Telegram File Store Bot
A secure file storage bot with protected content delivery
"""

import asyncio
import logging
import os
import signal
import sys
import traceback
from pyrogram import Client
from config import Config
from database import db
from handlers.start import register_start_handlers
from handlers.upload import register_upload_handlers
from handlers.finish import register_finish_handlers
from utils.file_sender import FileSender

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more details
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger(__name__)

class FileStoreBot:
    """Main bot class"""
    
    def __init__(self):
        """Initialize the bot"""
        self.client = None
        self.file_sender = None
        self.active_uploads = {}
        self.is_running = True
        
    async def shutdown(self, signal):
        """Graceful shutdown"""
        logger.info(f"Received exit signal {signal.name}...")
        self.is_running = False
        
    async def start(self):
        """Start the bot and all components"""
        try:
            # Setup signal handlers for graceful shutdown
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGTERM, signal.SIGINT):
                loop.add_signal_handler(
                    sig,
                    lambda s=sig: asyncio.create_task(self.shutdown(s))
                )
            
            # Validate configuration
            logger.info("Validating configuration...")
            Config.validate()
            logger.info("✅ Configuration validated successfully")
            
            # Print config (without sensitive data)
            logger.info(f"ADMINS: {Config.ADMINS}")
            logger.info(f"STORAGE_CHANNEL: {Config.STORAGE_CHANNEL}")
            logger.info(f"BOT_TOKEN exists: {bool(Config.BOT_TOKEN)}")
            logger.info(f"MONGO_URI exists: {bool(Config.MONGO_URI)}")
            
            # Connect to database
            logger.info("Connecting to database...")
            await db.connect()
            logger.info("✅ Database connected")
            
            # Initialize Pyrogram client with Render-specific settings
            logger.info("Initializing bot client...")
            self.client = Client(
                "file_store_bot",
                api_id=Config.API_ID,
                api_hash=Config.API_HASH,
                bot_token=Config.BOT_TOKEN,
                workers=20,
                max_concurrent_transmissions=5,
                sleep_threshold=60,
                no_updates=False,
                in_memory=True  # Add this for better performance
            )
            
            # Initialize file sender
            self.file_sender = FileSender(self.client)
            
            # Register all handlers
            logger.info("Registering handlers...")
            await self.register_handlers()
            
            # Start the bot
            logger.info("Starting bot client...")
            await self.client.start()
            
            # Get bot info
            bot_info = await self.client.get_me()
            logger.info(f"✅ Bot started successfully! @{bot_info.username}")
            
            # Send startup notification to storage channel
            try:
                await self.client.send_message(
                    Config.STORAGE_CHANNEL,
                    f"🚀 **Bot Started**\n\n"
                    f"📦 **Name:** {bot_info.first_name}\n"
                    f"🤖 **Username:** @{bot_info.username}\n"
                    f"⏰ **Time:** Bot is now online and ready!\n"
                    f"🖥️ **Platform:** Render (Free Tier)"
                )
                logger.info("Startup notification sent to storage channel")
            except Exception as e:
                logger.error(f"❌ Failed to send startup notification: {e}")
                logger.error("Check if STORAGE_CHANNEL is correct and bot is admin")
            
            # Keep the bot running with heartbeat
            logger.info("Bot is now running. Waiting for messages...")
            while self.is_running:
                await asyncio.sleep(60)
                logger.debug("Bot heartbeat - still running")
            
        except Exception as e:
            logger.error(f"❌ Failed to start bot: {e}")
            logger.error(traceback.format_exc())
            raise
        finally:
            await self.stop()
    
    async def register_handlers(self):
        """Register all command handlers"""
        
        # Register start handlers
        await register_start_handlers(self.client, self.file_sender)
        
        # Register upload handlers and get active_uploads
        self.active_uploads = await register_upload_handlers(self.client)
        
        # Register finish handlers
        await register_finish_handlers(self.client, self.active_uploads)
        
        logger.info("✅ All handlers registered successfully")
    
    async def stop(self):
        """Stop the bot and clean up"""
        logger.info("Stopping bot...")
        
        # Send shutdown notification
        try:
            await self.client.send_message(
                Config.STORAGE_CHANNEL,
                "🛑 **Bot Stopping**\n\nBot is shutting down for maintenance or restart."
            )
        except:
            pass
        
        # Close database connection
        await db.close()
        
        # Stop the client
        if self.client:
            await self.client.stop()
        
        logger.info("✅ Bot stopped successfully")

async def main():
    """Main entry point"""
    bot = FileStoreBot()
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
