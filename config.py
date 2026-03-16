import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class to manage environment variables"""
    
    # Bot configuration
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    API_ID = int(os.getenv("API_ID", "0"))
    API_HASH = os.getenv("API_HASH")
    
    # Database configuration
    MONGO_URI = os.getenv("mongodb+srv://vipheromod_db_user:<db_password>@cluster0.vfwzaec.mongodb.net/?appName=Cluster0", "mongodb://localhost:27017")
    DATABASE_NAME = "file_store_bot"
    
    # Admin configuration
    ADMINS = [int(admin_id) for admin_id in os.getenv("ADMINS", "").split(",") if admin_id.strip()]
    
    # Storage channel
    STORAGE_CHANNEL = int(os.getenv("STORAGE_CHANNEL", "0"))
    
    # Bot settings
    BATCH_ID_LENGTH = 32
    FLOOD_WAIT_DELAY = 1  # seconds between messages
    
    # Validate required configurations
    @classmethod
    def validate(cls):
        """Validate that all required configurations are set"""
        required_vars = ["BOT_TOKEN", "API_ID", "API_HASH", "MONGO_URI", "STORAGE_CHANNEL"]
        missing_vars = [var for var in required_vars if not getattr(cls, var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        if not cls.ADMINS:
            raise ValueError("At least one admin must be specified in ADMINS")
        
        if cls.STORAGE_CHANNEL == 0:
            raise ValueError("STORAGE_CHANNEL must be set")
        
        return True