from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from config import Config
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    """MongoDB database handler for the bot"""
    
    def __init__(self):
        """Initialize database connection"""
        self.client = None
        self.db = None
        self.uploads = None
        self.files = None
    
    async def connect(self):
        """Establish connection to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(Config.MONGO_URI)
            self.db = self.client[Config.DATABASE_NAME]
            self.uploads = self.db["uploads"]
            self.files = self.db["files"]
            
            # Create indexes for better performance
            await self.uploads.create_index("batch_id", unique=True)
            await self.uploads.create_index("created_at")
            await self.files.create_index([("batch_id", 1), ("order", 1)], unique=True)
            await self.files.create_index("batch_id")
            
            logger.info("Database connected successfully")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    async def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("Database connection closed")
    
    async def create_upload_session(self, batch_id: str) -> dict:
        """Create a new upload session"""
        upload_data = {
            "batch_id": batch_id,
            "total_files": 0,
            "created_at": datetime.utcnow()
        }
        await self.uploads.insert_one(upload_data)
        return upload_data
    
    async def add_file(self, batch_id: str, file_id: str, message_id: int, order: int) -> bool:
        """Add a file to the database"""
        try:
            file_data = {
                "batch_id": batch_id,
                "file_id": file_id,
                "message_id": message_id,
                "order": order
            }
            await self.files.insert_one(file_data)
            
            # Update total files count
            await self.uploads.update_one(
                {"batch_id": batch_id},
                {"$inc": {"total_files": 1}}
            )
            return True
        except Exception as e:
            logger.error(f"Error adding file: {e}")
            return False
    
    async def get_batch_files(self, batch_id: str) -> list:
        """Get all files for a batch in order"""
        cursor = self.files.find({"batch_id": batch_id}).sort("order", 1)
        return await cursor.to_list(length=None)
    
    async def get_upload_session(self, batch_id: str) -> dict:
        """Get upload session details"""
        return await self.uploads.find_one({"batch_id": batch_id})
    
    async def delete_batch(self, batch_id: str) -> bool:
        """Delete a batch and all its files"""
        try:
            await self.files.delete_many({"batch_id": batch_id})
            await self.uploads.delete_one({"batch_id": batch_id})
            return True
        except Exception as e:
            logger.error(f"Error deleting batch: {e}")
            return False
    
    async def get_stats(self) -> dict:
        """Get bot statistics"""
        total_batches = await self.uploads.count_documents({})
        total_files = await self.files.count_documents({})
        return {
            "total_batches": total_batches,
            "total_files": total_files
        }

# Create global database instance
db = Database()