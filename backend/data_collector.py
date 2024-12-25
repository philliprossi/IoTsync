import time
import schedule
import random
import logging
from datetime import datetime
from backend.tuya_device_data import TuyaClient
from backend.db_handler import DatabaseHandler
from pathlib import Path
from backend.alert_manager import AlertManager
from backend.config import Config

class DataCollector:
    def __init__(self):
        self.setup_logging()
        self.tuya_client = TuyaClient()
        self.db_handler = DatabaseHandler()
        self.alert_manager = AlertManager()
        self.max_retries = Config.MAX_RETRIES
        self.retry_delay = Config.RETRY_DELAY
        self.collection_interval = Config.COLLECTION_INTERVAL
        self.logger = logging.getLogger('IoTsync')

    def setup_logging(self):
        # Create logs directory if it doesn't exist
        Config.LOG_DIR.mkdir(exist_ok=True)
        
        # Configure logging
        logger = logging.getLogger('IoTsync')
        logger.setLevel(getattr(logging, Config.LOG_LEVEL))
        
        # File handler for all logs
        file_handler = logging.FileHandler(
            Config.LOG_DIR / f'iotsync_{datetime.now().strftime("%Y%m%d")}.log'
        )
        file_handler.setLevel(getattr(logging, Config.LOG_LEVEL))
        file_format = logging.Formatter(Config.LOG_FORMAT, datefmt=Config.LOG_DATE_FORMAT)
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
        
        # Console handler for INFO and above
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        logger.addHandler(console_handler)
        
        # Prevent logs from propagating to the root logger
        logger.propagate = False

    def collect_data_with_retry(self):
        for attempt in range(self.max_retries):
            try:
                # Get device status first, only refresh token if needed
                try:
                    device_status = self.tuya_client.get_device_status()
                except Exception as e:
                    self.logger.debug(f"Failed to get device status: {str(e)}, refreshing token...")
                    self.tuya_client.connect()
                    device_status = self.tuya_client.get_device_status()
                
                # Store the reading
                self.db_handler.store_reading(device_status)
                self.logger.info(f"Data collected successfully at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Log detailed device status at debug level
                self.logger.debug(f"Device status: {device_status}")
                
                # Get pool temperature after storing reading
                properties = {prop['code']: prop['value'] for prop in device_status.get('properties', [])}
                pool_temp_c = self.db_handler.format_temperature(properties.get('ToutCh3'))
                if pool_temp_c is not None:
                    pool_temp_f = self.db_handler.celsius_to_fahrenheit(pool_temp_c)
                    # Check temperature and send alerts if needed
                    self.alert_manager.check_temperature(pool_temp_f)
                
                return True
                
            except Exception as e:
                self.logger.error(
                    f"Error collecting data (Attempt {attempt + 1}/{self.max_retries}): {str(e)}",
                    exc_info=True
                )
                # Reset token info on any error
                self.tuya_client.token_info = None
                
                if attempt < self.max_retries - 1:
                    retry_wait = self.retry_delay * (attempt + 1)
                    self.logger.info(f"Retrying in {retry_wait} seconds...")
                    time.sleep(retry_wait)
        
        return False

    def start(self):
        self.logger.info("Starting data collection service...")
        self.logger.info(f"Collection interval: {self.collection_interval} seconds")
        self.logger.info("Press Ctrl+C to stop")
        
        while True:
            try:
                # Initial connection
                if self.collect_data_with_retry():
                    self.logger.info("Successfully connected to Tuya API")
                    break
                else:
                    self.logger.warning("Failed initial connection, retrying in 10 seconds...")
                    time.sleep(10)
            except KeyboardInterrupt:
                self.logger.info("Stopping data collection service...")
                return
            except Exception as e:
                self.logger.error(f"Fatal error during initialization: {str(e)}", exc_info=True)
                time.sleep(10)

        try:
            # Schedule the job to run every 55 seconds instead of every minute
            schedule.every(self.collection_interval).seconds.do(self.collect_data_with_retry)
            
            # Keep the script running
            while True:
                schedule.run_pending()
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.logger.info("Stopping data collection service...")
        except Exception as e:
            self.logger.error(f"Fatal error: {str(e)}", exc_info=True)
            raise

if __name__ == "__main__":
    collector = DataCollector()
    collector.start() 