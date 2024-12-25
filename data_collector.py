import time
import schedule
import random
import logging
from datetime import datetime
from tuya_device_data import TuyaClient
from db_handler import DatabaseHandler
from pathlib import Path

class DataCollector:
    def __init__(self):
        self.setup_logging()
        self.tuya_client = TuyaClient()
        self.db_handler = DatabaseHandler()
        self.max_retries = 3
        self.retry_delay = 5  # seconds
        self.collection_interval = 55  # collect data every 55 seconds
        self.logger = logging.getLogger('IoTsync')

    def setup_logging(self):
        # Create logs directory if it doesn't exist
        log_dir = Path('/app/logs')
        log_dir.mkdir(exist_ok=True)
        
        # Configure logging
        logger = logging.getLogger('IoTsync')
        logger.setLevel(logging.DEBUG)
        
        # File handler for all logs
        file_handler = logging.FileHandler(
            log_dir / f'iotsync_{datetime.now().strftime("%Y%m%d")}.log'
        )
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S.%f'
        )
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