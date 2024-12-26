import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Application paths
    BASE_DIR = Path(__file__).parent
    DATA_DIR = BASE_DIR / 'data'
    LOG_DIR = BASE_DIR / 'logs'
    
    # Server Configuration
    API_PORT = int(os.getenv('API_PORT', '8000'))
    FRONTEND_PORT = int(os.getenv('FRONTEND_PORT', '3000'))
    
    # Ensure directories exist
    DATA_DIR.mkdir(exist_ok=True)
    LOG_DIR.mkdir(exist_ok=True)
    
    # Database
    DB_FILE = DATA_DIR / 'iotsync.db'
    
    # Tuya API Configuration
    TUYA_BASE_URL = os.getenv('VITE_TUYABASEURL', 'https://openapi.tuyaus.com').rstrip('/')
    TUYA_ACCESS_KEY = os.getenv('VITE_ACCESSKEY')
    TUYA_SECRET_KEY = os.getenv('VITE_SECRETKEY')
    TUYA_USER_ID = os.getenv('VITE_TUYAUSERID')
    DEVICE_ID = os.getenv('DEVICE_ID')
    
    # Data Collection Settings
    COLLECTION_INTERVAL = 55  # seconds
    MAX_RETRIES = 3
    RETRY_DELAY = 5  # seconds
    
    # Alert Configuration
    ALERT_MIN_POOL_TEMP_F = 101.0
    ALERT_INTERVAL = 30  # minutes
    
    # Email Configuration
    SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
    SENDGRID_FROM_EMAIL = os.getenv('SENDGRID_FROM_EMAIL')
    ALERT_EMAIL = os.getenv('ALERT_EMAIL')
    
    # Logging Configuration
    LOG_LEVEL = 'DEBUG'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S.%f'
    CONSOLE_LOG_LEVEL = 'INFO'
    
    @classmethod
    def validate(cls):
        """Validate required configuration values."""
        required = {
            'TUYA_ACCESS_KEY': cls.TUYA_ACCESS_KEY,
            'TUYA_SECRET_KEY': cls.TUYA_SECRET_KEY,
            'DEVICE_ID': cls.DEVICE_ID,
        }
        
        missing = [k for k, v in required.items() if not v]
        if missing:
            raise ValueError(f"Missing required configuration values: {', '.join(missing)}") 