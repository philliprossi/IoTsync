import os
import time
import hmac
import json
import hashlib
import logging
import requests
from urllib.parse import urljoin
from datetime import datetime
from dotenv import load_dotenv
from backend.config import Config

# Load environment variables
load_dotenv()

class TuyaClient:
    def __init__(self):
        self.base_url = Config.TUYA_BASE_URL
        self.access_key = Config.TUYA_ACCESS_KEY
        self.secret_key = Config.TUYA_SECRET_KEY
        self.device_id = Config.DEVICE_ID
        self.token_info = None
        self.logger = logging.getLogger('IoTsync.tuya')

    def calculate_sign(self, method, path, timestamp, params=None, body=None):
        # Create the string to sign
        str_to_sign = [method]
        
        # Calculate body hash if exists
        content_hash = hashlib.sha256(json.dumps(body).encode() if body else b'').hexdigest()
        str_to_sign.append(content_hash)
        str_to_sign.append('')  # Empty headers
        
        # Add path and parameters
        if params:
            # Sort parameters
            sorted_params = sorted(params.items(), key=lambda x: x[0])
            path = path + '?' + '&'.join([f"{k}={v}" for k, v in sorted_params])
        str_to_sign.append(path)
        
        str_to_hash = '\n'.join(str_to_sign)
        
        # Prepare the message to sign
        message = self.access_key
        if self.token_info:
            message += self.token_info.get('access_token', '')
        message += str(timestamp) + str_to_hash
        
        # Log signature components in detail
        self.logger.debug("=== Signature Generation Details ===")
        self.logger.debug(f"Timestamp (raw): {timestamp}")
        self.logger.debug(f"Timestamp (human): {datetime.fromtimestamp(timestamp/1000).strftime('%Y-%m-%d %H:%M:%S.%f')}")
        self.logger.debug(f"Access Key Length: {len(self.access_key)}")
        if self.token_info:
            self.logger.debug(f"Access Token Length: {len(self.token_info.get('access_token', ''))}")
            self.logger.debug(f"Token obtained at: {datetime.fromtimestamp(self.token_info.get('obtained_at', 0)).strftime('%Y-%m-%d %H:%M:%S.%f')}")
            self.logger.debug(f"Token expire time: {self.token_info.get('expire_time')} seconds")
        
        self.logger.debug("\nString to sign components:")
        for i, component in enumerate(str_to_sign):
            self.logger.debug(f"{i+1}. {repr(component)}")
        
        self.logger.debug("\nFinal message to sign:")
        self.logger.debug(repr(message))
        
        # Calculate signature
        try:
            signature = hmac.new(
                self.secret_key.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha256
            ).hexdigest().upper()
            
            self.logger.debug(f"\nFinal signature: {signature}")
            self.logger.debug("=== End Signature Generation ===\n")
            return signature
        except Exception as e:
            self.logger.error("Error during signature generation:", exc_info=True)
            raise

    def request_signed(self, method, path, params=None, body=None):
        # Get server time with retries
        MAX_RETRIES = 3
        RETRY_DELAY = 1  # seconds
        timestamp = None
        
        for attempt in range(MAX_RETRIES):
            try:
                time_response = requests.get(f"{self.base_url}/v1.0/time")
                time_response.raise_for_status()
                server_time = time_response.json().get('t')
                
                if not server_time:
                    raise ValueError("Server returned empty timestamp")
                
                # Convert to milliseconds if server time is in seconds
                if len(str(server_time)) <= 10:  # If timestamp is in seconds
                    server_time = int(server_time) * 1000
                else:
                    server_time = int(server_time)
                
                timestamp = server_time
                local_time = int(time.time() * 1000)
                time_diff = abs(local_time - server_time)
                
                self.logger.debug(f"\n=== Time Synchronization ===")
                self.logger.debug(f"Local Time: {local_time}")
                self.logger.debug(f"Server Time: {server_time}")
                self.logger.debug(f"Difference: {time_diff}ms")
                
                # Warn if time difference is significant
                if time_diff > 5000:  # 5 seconds
                    self.logger.warning(f"Large time difference detected: {time_diff}ms")
                
                break  # Success, exit retry loop
                
            except Exception as e:
                self.logger.warning(f"Server time sync attempt {attempt + 1} failed: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                else:
                    self.logger.error("All server time sync attempts failed, using local time")
                    timestamp = int(time.time() * 1000)
        
        if timestamp is None:
            timestamp = int(time.time() * 1000)
        
        # Log request attempt
        self.logger.debug(f"\n=== New Request ===")
        self.logger.debug(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
        self.logger.debug(f"Method: {method}")
        self.logger.debug(f"Path: {path}")
        self.logger.debug(f"Params: {params}")
        self.logger.debug(f"Body: {body}")
        
        # Calculate signature
        try:
            signature = self.calculate_sign(method, path, timestamp, params, body)
        except Exception as e:
            self.logger.error("Failed to calculate signature:", exc_info=True)
            raise
        
        # Prepare headers
        headers = {
            'client_id': self.access_key,
            'sign': signature,
            'sign_method': 'HMAC-SHA256',
            't': str(timestamp),
            'lang': 'en'
        }
        
        if self.token_info:
            headers['access_token'] = self.token_info.get('access_token')

        # Log complete request details
        self.logger.debug("\nRequest Details:")
        self.logger.debug(f"URL: {urljoin(self.base_url, path.lstrip('/'))}")
        self.logger.debug("Headers:")
        for key, value in headers.items():
            if key in ['client_id', 'access_token']:
                self.logger.debug(f"{key}: {value[:4]}...{value[-4:]} (length: {len(value)})")
            else:
                self.logger.debug(f"{key}: {value}")

        # Make request
        url = urljoin(self.base_url, path.lstrip('/'))
        
        try:
            response = requests.request(
                method=method,
                url=url,
                params=params,
                json=body,
                headers=headers
            )
            
            # Log response details
            self.logger.debug("\nResponse Details:")
            self.logger.debug(f"Status Code: {response.status_code}")
            self.logger.debug(f"Response Headers: {dict(response.headers)}")
            
            response.raise_for_status()
            data = response.json()
            
            self.logger.debug(f"Response Body: {data}")
            self.logger.debug("=== End Request ===\n")
            
            if data.get('success', False):
                return data.get('result')
            else:
                error_msg = f"API Error - Code: {data.get('code')}, Message: {data.get('msg')}"
                self.logger.error(error_msg)
                self.logger.error(f"Full Response: {data}")
                raise Exception(f"API request failed: {data.get('msg')} - URL: {url}")
        except requests.exceptions.RequestException as e:
            self.logger.error("Request failed:", exc_info=True)
            raise Exception(f"Request failed: {str(e)} - URL: {url}")

    def connect(self):
        self.logger.info("Attempting to connect and obtain token...")
        response = self.request_signed(
            'GET',
            '/v1.0/token',
            params={'grant_type': '1'}
        )
        # Store when we got the token
        response['obtained_at'] = time.time()
        
        # Calculate absolute expiration timestamp
        # expire_time from API is in seconds, convert current time to seconds
        current_time = int(time.time())
        response['expires_at'] = current_time + response['expire_time']
        
        self.token_info = response
        self.logger.info(f"Token obtained successfully. Expires in {response['expire_time']} seconds")
        self.logger.debug(f"Token expires at: {datetime.fromtimestamp(response['expires_at']).strftime('%Y-%m-%d %H:%M:%S')}")
        return response

    def get_device_info(self):
        if not self.token_info or self.is_token_expired():
            self.connect()
        return self.request_signed('GET', f'/v1.0/devices/{self.device_id}')

    def get_device_status(self):
        if not self.token_info or self.is_token_expired():
            self.connect()
        return self.request_signed('GET', f'/v2.0/cloud/thing/{self.device_id}/shadow/properties')

    def is_token_expired(self):
        """Check if the current token is expired or about to expire within 30 seconds."""
        if not self.token_info:
            return True
            
        current_time = time.time()
        expires_at = self.token_info.get('expires_at')
        
        if not expires_at:
            return True
            
        # Consider token expired if less than 30 seconds remaining
        buffer_time = 30
        return current_time + buffer_time >= expires_at

def format_temperature(value):
    """Convert temperature value to proper format (divide by 10)."""
    return value / 10.0 if value is not None else None

def main():
    try:
        client = TuyaClient()
        
        # Get device information
        print("\nDevice Information:")
        print("-" * 50)
        device_info = client.get_device_info()
        print(json.dumps(device_info, indent=2))

        # Get current device status
        print("\nCurrent Device Status:")
        print("-" * 50)
        try:
            device_status = client.get_device_status()
            
            # Extract current temperatures
            current_indoor = None
            current_pool = None
            current_humidity = None
            
            for prop in device_status.get('properties', []):
                if prop['code'] == 'Tin':
                    current_indoor = format_temperature(prop['value'])
                elif prop['code'] == 'ToutCh3':
                    current_pool = format_temperature(prop['value'])
                elif prop['code'] == 'Hin':
                    current_humidity = prop['value']
            
            print(f"Current Indoor Temperature: {current_indoor:.1f}°C")
            print(f"Current Pool Temperature:  {current_pool:.1f}°C")
            print(f"Current Indoor Humidity:   {current_humidity}%")
            
            print("\nFull Device Status:")
            print(json.dumps(device_status, indent=2))
            
        except Exception as e:
            print(f"Could not get status: {str(e)}")

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()