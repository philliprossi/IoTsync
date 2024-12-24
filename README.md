# Tuya Device Monitor

A Python application that monitors Tuya device data using the Tuya IoT Platform API.

## Prerequisites

- Python 3.8 or higher
- uv package manager (installation instructions below)

## Installation

1. Install uv using one of these methods:
   
   # On macOS and Linux
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

   # Or via pip
   ```
   pip install uv
   ```

2. Clone this repository:
   ```bash
   git clone <your-repo-url>
   cd <repo-directory>
   ```

3. Create and activate a virtual environment:
   ```bash
   uv venv
   source .venv/bin/activate  # On Unix/macOS
   ```

4. Install dependencies:
   ```bash
   uv pip install -r requirements.txt
   ```

5. Create a `.env` file with your Tuya credentials. You can use the provided `.env_example` as a template:
   ```bash
   cp .env_example .env
   ```
   Then, fill in the required values in the `.env` file:
   ```env
   VITE_TUYABASEURL=https://openapi.tuyaus.com
   VITE_ACCESSKEY=your_access_key
   VITE_SECRETKEY=your_secret_key
   DEVICE_ID=your_device_id
   ```

## Usage

Run the script:
```bash
python tuya_device_data.py
```

This will display:
- Device information
- Current indoor temperature
- Current pool temperature
- Current humidity
- Full device status

## Development

To add new dependencies:
```bash
uv pip install <package-name>
```

To update requirements.txt:
```bash
uv pip freeze > requirements.txt
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| VITE_TUYABASEURL | Tuya API base URL (default: https://openapi.tuyaus.com) |
| VITE_ACCESSKEY | Your Tuya IoT Platform access key |
| VITE_SECRETKEY | Your Tuya IoT Platform secret key |
| DEVICE_ID | The ID of your Tuya device |

## License

MIT

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request