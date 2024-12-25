import sqlite3
from datetime import datetime
from pathlib import Path
from config import Config

class DatabaseHandler:
    def __init__(self):
        self.db_path = Config.DB_FILE
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sensor_readings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    indoor_temp_c REAL,
                    indoor_temp_f REAL,
                    pool_temp_c REAL,
                    pool_temp_f REAL,
                    indoor_humidity INTEGER,
                    outdoor_ch1_temp_c REAL,
                    outdoor_ch1_temp_f REAL,
                    outdoor_ch1_humidity INTEGER,
                    outdoor_ch2_temp_c REAL,
                    outdoor_ch2_temp_f REAL,
                    outdoor_ch2_humidity INTEGER,
                    outdoor_ch3_temp_c REAL,
                    outdoor_ch3_temp_f REAL,
                    outdoor_ch3_humidity INTEGER,
                    atmospheric_pressure REAL,
                    pressure_units TEXT
                )
            ''')
            
            # New alerts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS temperature_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    alert_type TEXT NOT NULL,  -- 'triggered' or 'resolved'
                    temperature_f REAL NOT NULL,
                    threshold_f REAL NOT NULL,
                    email_sent BOOLEAN NOT NULL,
                    email_recipient TEXT,
                    message TEXT
                )
            ''')
            conn.commit()

    def celsius_to_fahrenheit(self, celsius):
        if celsius is None:
            return None
        return (celsius * 9/5) + 32

    def format_temperature(self, value):
        """Convert temperature value to proper format (divide by 10)."""
        return value / 10.0 if value is not None else None

    def store_reading(self, device_status):
        properties = {prop['code']: prop['value'] for prop in device_status.get('properties', [])}
        
        # Convert temperatures from device format to Celsius
        indoor_temp_c = self.format_temperature(properties.get('Tin'))
        pool_temp_c = self.format_temperature(properties.get('ToutCh3'))
        outdoor_ch1_temp_c = self.format_temperature(properties.get('ToutCh1'))
        outdoor_ch2_temp_c = self.format_temperature(properties.get('ToutCh2'))
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO sensor_readings (
                    timestamp,
                    indoor_temp_c, indoor_temp_f,
                    pool_temp_c, pool_temp_f,
                    indoor_humidity,
                    outdoor_ch1_temp_c, outdoor_ch1_temp_f, outdoor_ch1_humidity,
                    outdoor_ch2_temp_c, outdoor_ch2_temp_f, outdoor_ch2_humidity,
                    outdoor_ch3_temp_c, outdoor_ch3_temp_f, outdoor_ch3_humidity,
                    atmospheric_pressure, pressure_units
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                indoor_temp_c, self.celsius_to_fahrenheit(indoor_temp_c),
                pool_temp_c, self.celsius_to_fahrenheit(pool_temp_c),
                properties.get('Hin'),
                outdoor_ch1_temp_c, self.celsius_to_fahrenheit(outdoor_ch1_temp_c),
                properties.get('HoutCh1'),
                outdoor_ch2_temp_c, self.celsius_to_fahrenheit(outdoor_ch2_temp_c),
                properties.get('HoutCh2'),
                pool_temp_c, self.celsius_to_fahrenheit(pool_temp_c),
                properties.get('HoutCh3'),
                properties.get('atmosphere'),
                properties.get('pressure_units')
            ))
            conn.commit() 

    def log_alert(self, alert_type, temperature_f, threshold_f, email_sent, email_recipient, message):
        """Log temperature alert to database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO temperature_alerts (
                    timestamp,
                    alert_type,
                    temperature_f,
                    threshold_f,
                    email_sent,
                    email_recipient,
                    message
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                alert_type,
                temperature_f,
                threshold_f,
                email_sent,
                email_recipient,
                message
            ))
            conn.commit() 