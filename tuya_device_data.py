import os
import time
import hmac
import json
import hashlib
import requests
from urllib.parse import urljoin
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class TuyaClient:
    def __init__(self):
        self.base_url = os.getenv('VITE_TUYABASEURL', 'https://openapi.tuyaus.com').rstrip('/') + '/'
        self.access_key = os.getenv('VITE_ACCESSKEY')
        self.secret_key = os.getenv('VITE_SECRETKEY')
        self.device_id = os.getenv('DEVICE_ID')
        self.token_info = None

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
        
        # Calculate signature
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest().upper()
        
        return signature

    def request_signed(self, method, path, params=None, body=None):
        timestamp = int(time.time() * 1000)
        
        # Calculate signature
        signature = self.calculate_sign(method, path, timestamp, params, body)
        
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
            response.raise_for_status()  # Raise an error for bad status codes
            
            data = response.json()
            if data.get('success', False):
                return data.get('result')
            else:
                raise Exception(f"API request failed: {data.get('msg')} - URL: {url}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {str(e)} - URL: {url}")

    def connect(self):
        response = self.request_signed(
            'GET',
            '/v1.0/token',
            params={'grant_type': '1'}
        )
        response['expire_time'] = int(time.time() * 1000) + (response['expire_time'] * 1000)
        self.token_info = response

    def get_device_info(self):
        if not self.token_info:
            self.connect()
        return self.request_signed('GET', f'/v1.0/devices/{self.device_id}')

    def get_device_status(self):
        if not self.token_info:
            self.connect()
        return self.request_signed('GET', f'/v2.0/cloud/thing/{self.device_id}/shadow/properties')

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