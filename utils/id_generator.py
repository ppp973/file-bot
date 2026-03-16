import secrets
import string
from config import Config

class IDGenerator:
    """Generate secure random IDs for batches"""
    
    @staticmethod
    def generate_batch_id() -> str:
        """
        Generate a cryptographically secure random ID
        
        Returns:
            str: Random string of length BATCH_ID_LENGTH
        """
        # Use alphanumeric characters for the ID
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(Config.BATCH_ID_LENGTH))
    
    @staticmethod
    def generate_short_id(length: int = 8) -> str:
        """Generate a shorter random ID (useful for other purposes)"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))

# Create global instance
id_generator = IDGenerator()