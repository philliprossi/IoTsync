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
            
            # First, check if we need to migrate the temperature_alerts table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='temperature_alerts'")
            if cursor.fetchone() is not None:
                # Table exists, check if we need to add new columns
                cursor.execute("PRAGMA table_info(temperature_alerts)")
                columns = [col[1] for col in cursor.fetchall()]
                
                # If sms_sent column doesn't exist, we need to recreate the table
                if 'sms_sent' not in columns:
                    # Rename existing table
                    cursor.execute("ALTER TABLE temperature_alerts RENAME TO temperature_alerts_old")
                    
                    # Create new table with updated schema
                    cursor.execute('''
                        CREATE TABLE temperature_alerts (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            timestamp DATETIME NOT NULL,
                            alert_type TEXT NOT NULL,
                            temperature_f REAL NOT NULL,
                            threshold_f REAL NOT NULL,
                            email_sent BOOLEAN NOT NULL,
                            sms_sent BOOLEAN NOT NULL,
                            email_recipient TEXT,
                            phone_recipient TEXT,
                            message TEXT
                        )
                    ''')
                    
                    # Copy data from old table to new table
                    cursor.execute('''
                        INSERT INTO temperature_alerts 
                        (timestamp, alert_type, temperature_f, threshold_f, 
                         email_sent, sms_sent, email_recipient, phone_recipient, message)
                        SELECT 
                            timestamp, alert_type, temperature_f, threshold_f,
                            email_sent, FALSE, email_recipient, NULL, message
                        FROM temperature_alerts_old
                    ''')
                    
                    # Drop old table
                    cursor.execute("DROP TABLE temperature_alerts_old")
                    
                    conn.commit()
            else:
                # Create table if it doesn't exist
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS temperature_alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME NOT NULL,
                        alert_type TEXT NOT NULL,
                        temperature_f REAL NOT NULL,
                        threshold_f REAL NOT NULL,
                        email_sent BOOLEAN NOT NULL,
                        sms_sent BOOLEAN NOT NULL,
                        email_recipient TEXT,
                        phone_recipient TEXT,
                        message TEXT
                    )
                ''')
            
            # Create sensor_readings table
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

    def log_alert(self, alert_type, temperature_f, threshold_f, email_sent, sms_sent, email_recipient, phone_recipient, message):
        """Log a temperature alert to the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO temperature_alerts 
                (timestamp, alert_type, temperature_f, threshold_f, email_sent, sms_sent, email_recipient, phone_recipient, message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                alert_type,
                temperature_f,
                threshold_f,
                email_sent,
                sms_sent,
                email_recipient,
                phone_recipient,
                message
            ))
            conn.commit()