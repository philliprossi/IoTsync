from config import Config
import logging
from datetime import datetime, timedelta
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from twilio.rest import Client
from db_handler import DatabaseHandler

class AlertManager:
    def __init__(self):
        self.logger = logging.getLogger('IoTsync.alerts')
        self.last_alert_time = None
        self.alert_interval = timedelta(minutes=Config.ALERT_INTERVAL)
        self.min_pool_temp_f = Config.ALERT_MIN_POOL_TEMP_F
        self.alert_active = False
        self.stale_data_alert_active = False
        self.max_data_age = timedelta(hours=8)
        
        # Email configuration
        self.sendgrid_api_key = Config.SENDGRID_API_KEY
        self.from_email = Config.SENDGRID_FROM_EMAIL
        self.alert_recipient = Config.ALERT_EMAIL
        
        # SMS configuration
        self.twilio_account_sid = Config.TWILIO_ACCOUNT_SID
        self.twilio_auth_token = Config.TWILIO_AUTH_TOKEN
        self.twilio_from_number = Config.TWILIO_FROM_NUMBER
        self.alert_phone_number = Config.ALERT_PHONE_NUMBER
        
        # Database handler
        self.db_handler = DatabaseHandler()
        
        if not all([self.sendgrid_api_key, self.from_email]):
            self.logger.warning("SendGrid credentials not configured. Email alerts will be logged only.")
        if not all([self.twilio_account_sid, self.twilio_auth_token, self.twilio_from_number]):
            self.logger.warning("Twilio credentials not configured. SMS alerts will be logged only.")
    
    def should_send_alert(self):
        """Check if enough time has passed since the last alert."""
        if not self.last_alert_time:
            return True
        return datetime.now() - self.last_alert_time >= self.alert_interval
    
    def send_email(self, subject, body):
        """Send an email alert using SendGrid."""
        email_sent = False
        if not all([self.sendgrid_api_key, self.from_email]):
            self.logger.info(f"Would send email: {subject}\n{body}")
            return email_sent
            
        try:
            message = Mail(
                from_email=Email(self.from_email),
                to_emails=To(self.alert_recipient),
                subject=subject,
                plain_text_content=Content("text/plain", body)
            )
            
            sg = SendGridAPIClient(self.sendgrid_api_key)
            response = sg.send(message)
            
            if response.status_code in (200, 201, 202):
                self.logger.info(f"Alert email sent: {subject}")
                self.last_alert_time = datetime.now()
                email_sent = True
            else:
                self.logger.error(f"SendGrid API returned status code: {response.status_code}")
            
        except Exception as e:
            self.logger.error(f"Failed to send alert email: {e}", exc_info=True)
        
        return email_sent
    
    def send_sms(self, body):
        """Send an SMS alert using Twilio."""
        sms_sent = False
        if not all([self.twilio_account_sid, self.twilio_auth_token, self.twilio_from_number]):
            self.logger.info(f"Would send SMS: {body}")
            return sms_sent
            
        try:
            client = Client(self.twilio_account_sid, self.twilio_auth_token)
            message = client.messages.create(
                body=body,
                from_=self.twilio_from_number,
                to=self.alert_phone_number
            )
            
            if message.sid:
                self.logger.info("Alert SMS sent")
                sms_sent = True
            
        except Exception as e:
            self.logger.error(f"Failed to send alert SMS: {e}", exc_info=True)
        
        return sms_sent
    
    def check_data_staleness(self):
        """Check if data hasn't been updated in the last 8 hours."""
        try:
            latest_reading = self.db_handler.get_latest_reading()
            if not latest_reading:
                return
            
            last_update_time = latest_reading.get('timestamp')
            if not last_update_time:
                return
                
            time_since_update = datetime.now() - last_update_time
            
            if time_since_update >= self.max_data_age:
                if not self.stale_data_alert_active and self.should_send_alert():
                    subject = "IoT Sync Data Alert"
                    body = (f"No data updates received in the last 8 hours!\n"
                           f"Last update time: {last_update_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                           f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    email_sent = self.send_email(subject, body)
                    sms_sent = self.send_sms(body)
                    
                    if email_sent or sms_sent:
                        self.last_alert_time = datetime.now()
                        self.stale_data_alert_active = True
                    
                    # Log alert to database
                    self.db_handler.log_alert(
                        alert_type='stale_data',
                        temperature_f=None,
                        threshold_f=None,
                        email_sent=email_sent,
                        sms_sent=sms_sent,
                        email_recipient=self.alert_recipient,
                        phone_recipient=self.alert_phone_number,
                        message=body
                    )
            elif self.stale_data_alert_active:
                # Data updates have resumed
                subject = "IoT Sync Data Restored"
                body = (f"Data updates have resumed.\n"
                       f"Latest update time: {last_update_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                       f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                email_sent = self.send_email(subject, body)
                sms_sent = self.send_sms(body)
                
                if email_sent or sms_sent:
                    self.stale_data_alert_active = False
                    
                    # Log resolution to database
                    self.db_handler.log_alert(
                        alert_type='stale_data_resolved',
                        temperature_f=None,
                        threshold_f=None,
                        email_sent=email_sent,
                        sms_sent=sms_sent,
                        email_recipient=self.alert_recipient,
                        phone_recipient=self.alert_phone_number,
                        message=body
                    )
        except Exception as e:
            self.logger.error(f"Failed to check data staleness: {e}", exc_info=True)

    def check_temperature(self, pool_temp_f):
        """Check pool temperature and send alerts if needed."""
        # First check for stale data
        self.check_data_staleness()
        
        if pool_temp_f is None:
            self.logger.warning("Pool temperature reading is None")
            return
            
        if pool_temp_f < self.min_pool_temp_f:
            if not self.alert_active and self.should_send_alert():
                subject = "Pool Temperature Alert"
                body = (f"Pool temperature is below minimum threshold!\n"
                       f"Current temperature: {pool_temp_f}°F\n"
                       f"Minimum threshold: {self.min_pool_temp_f}°F\n"
                       f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                email_sent = self.send_email(subject, body)
                sms_sent = self.send_sms(body)
                
                if email_sent or sms_sent:
                    self.last_alert_time = datetime.now()
                    self.alert_active = True
                
                # Log alert to database
                self.db_handler.log_alert(
                    alert_type='triggered',
                    temperature_f=pool_temp_f,
                    threshold_f=self.min_pool_temp_f,
                    email_sent=email_sent,
                    sms_sent=sms_sent,
                    email_recipient=self.alert_recipient,
                    phone_recipient=self.alert_phone_number,
                    message=body
                )
                
        elif self.alert_active:
            # Temperature has returned to normal
            subject = "Pool Temperature Restored"
            body = (f"Pool temperature has returned to normal.\n"
                   f"Current temperature: {pool_temp_f}°F\n"
                   f"Minimum threshold: {self.min_pool_temp_f}°F\n"
                   f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            email_sent = self.send_email(subject, body)
            sms_sent = self.send_sms(body)
            
            if email_sent or sms_sent:
                self.alert_active = False
                
                # Log resolution to database
                self.db_handler.log_alert(
                    alert_type='resolved',
                    temperature_f=pool_temp_f,
                    threshold_f=self.min_pool_temp_f,
                    email_sent=email_sent,
                    sms_sent=sms_sent,
                    email_recipient=self.alert_recipient,
                    phone_recipient=self.alert_phone_number,
                    message=body
                ) 