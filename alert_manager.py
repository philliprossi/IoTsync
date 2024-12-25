from config import Config
import logging
from datetime import datetime, timedelta
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

class AlertManager:
    def __init__(self):
        self.logger = logging.getLogger('IoTsync.alerts')
        self.last_alert_time = None
        self.alert_interval = timedelta(minutes=Config.ALERT_INTERVAL)
        self.min_pool_temp_f = Config.ALERT_MIN_POOL_TEMP_F
        self.alert_active = False
        
        # Email configuration
        self.sendgrid_api_key = Config.SENDGRID_API_KEY
        self.from_email = Config.SENDGRID_FROM_EMAIL
        self.alert_recipient = Config.ALERT_EMAIL
        
        if not all([self.sendgrid_api_key, self.from_email]):
            self.logger.warning("SendGrid credentials not configured. Alerts will be logged only.")
    
    def should_send_alert(self):
        """Check if enough time has passed since the last alert."""
        if not self.last_alert_time:
            return True
        return datetime.now() - self.last_alert_time >= self.alert_interval
    
    def send_email(self, subject, body):
        """Send an email alert using SendGrid."""
        if not all([self.sendgrid_api_key, self.from_email]):
            self.logger.info(f"Would send email: {subject}\n{body}")
            return
            
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
            else:
                self.logger.error(f"SendGrid API returned status code: {response.status_code}")
            
        except Exception as e:
            self.logger.error(f"Failed to send alert email: {e}", exc_info=True)
    
    def check_temperature(self, pool_temp_f):
        """Check pool temperature and send alerts if needed."""
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
                self.send_email(subject, body)
                self.alert_active = True
                
        elif self.alert_active:
            # Temperature has returned to normal
            subject = "Pool Temperature Restored"
            body = (f"Pool temperature has returned to normal.\n"
                   f"Current temperature: {pool_temp_f}°F\n"
                   f"Minimum threshold: {self.min_pool_temp_f}°F\n"
                   f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.send_email(subject, body)
            self.alert_active = False 