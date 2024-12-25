# IoTsync

A Python application that monitors and stores Tuya device data using the Tuya IoT Platform API. This application collects temperature and humidity data from multiple sensors and stores it in a SQLite database for historical tracking.

## Features

- Real-time monitoring of Tuya device sensors
- Automatic data collection every 55 seconds
- Storage of temperature data in both Celsius and Fahrenheit
- Tracking of multiple sensor channels (indoor, pool, and outdoor sensors)
- SQLite database for efficient local storage
- Docker containerization for easy deployment
- Supervisor process management for reliability
- Persistent data storage across container restarts
- UV package manager for faster, more reliable dependency management
- Automated email alerts for pool temperature monitoring via SendGrid

## Prerequisites

- Tuya IoT Platform account and device credentials
- Docker and Docker Compose (installation instructions below)
- UV package manager (automatically installed in container)
- SendGrid account for email alerts (free tier available)

### Installing Docker

#### On macOS:
1. Download Docker Desktop for Mac from [Docker's official website](https://www.docker.com/products/docker-desktop/)
2. Double-click `Docker.dmg` to start the installation
3. Drag Docker to your Applications folder
4. Open Docker Desktop from your Applications folder or Spotlight
5. Wait for Docker to start (whale icon in menu bar will stop animating)


## Installation

1. Clone this repository:
```bash
git clone <your-repo-url>
cd <repo-directory>
```

2. Set up your environment variables:
```bash
cp .env_example .env
```

3. Edit `.env` and add your Tuya credentials:
```env
VITE_TUYABASEURL=https://openapi.tuyaus.com
VITE_ACCESSKEY=your_access_key
VITE_SECRETKEY=your_secret_key
DEVICE_ID=your_device_id

# Email Alert Configuration
SENDGRID_API_KEY=your-sendgrid-api-key
SENDGRID_FROM_EMAIL=your-verified-sender@yourdomain.com
ALERT_EMAIL=recipient@email.com
```

### Setting up SendGrid

1. Create a SendGrid account:
   - Visit [SendGrid.com](https://sendgrid.com/)
   - Sign up for a free account (100 emails/day free)

2. Create an API key:
   - Go to Settings → API Keys
   - Click "Create API Key"
   - Choose "Restricted Access"
   - Enable "Mail Send" permissions
   - Copy the generated API key to your `.env` file

3. Verify your sender email:
   - Go to Settings → Sender Authentication
   - Choose Domain Authentication or Single Sender Verification
   - Follow the verification steps
   - Add the verified email to SENDGRID_FROM_EMAIL in `.env`

## Usage

### Starting the Service

Start the service using Docker Compose:
```bash
docker-compose up -d
```

This will:
- Build the Docker image if needed
- Start the container in detached mode
- Mount the logs and data directories
- Configure automatic restarts

### Monitoring

View the logs:
```bash
# View supervisor logs
docker-compose exec iotsync tail -f /var/log/supervisor/supervisord.log

# View application logs
docker-compose exec iotsync tail -f /var/log/supervisor/data_collector.out.log

# View error logs
docker-compose exec iotsync tail -f /var/log/supervisor/data_collector.err.log

# View application logs from host machine
tail -f logs/iotsync_YYYYMMDD.log
```

### Stopping the Service
```bash
docker-compose down
```

### Updating the Application
```bash
git pull
docker-compose up -d --build
```

## Features in Detail

### Temperature Alerts

The system monitors pool temperature and sends alerts:
- When temperature falls below 101°F (configurable)
- When temperature returns to normal
- Alerts are sent no more frequently than every 30 minutes
- Alerts include current temperature and threshold information
- All alerts and resolutions are logged to the database

Configure alert settings in `.env`:
```env
# Optional Alert Overrides
ALERT_MIN_POOL_TEMP_F=101.0  # Minimum temperature threshold
ALERT_INTERVAL=30            # Minutes between alerts
```

Alert logs are stored in the database with the following schema:

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| timestamp | DATETIME | Time of alert |
| alert_type | TEXT | 'triggered' or 'resolved' |
| temperature_f | REAL | Temperature when alert occurred |
| threshold_f | REAL | Temperature threshold |
| email_sent | BOOLEAN | Whether email was sent successfully |
| email_recipient | TEXT | Email recipient |
| message | TEXT | Alert message content |

## Data Structure

The application stores data in a SQLite database (`data/iotsync.db`) with the following schema:

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| timestamp | DATETIME | Time of reading |
| indoor_temp_c | REAL | Indoor temperature (°C) |
| indoor_temp_f | REAL | Indoor temperature (°F) |
| pool_temp_c | REAL | Pool temperature (°C) |
| pool_temp_f | REAL | Pool temperature (°F) |
| indoor_humidity | INTEGER | Indoor humidity (%) |
| outdoor_ch1_temp_c | REAL | Outdoor Channel 1 temperature (°C) |
| outdoor_ch1_temp_f | REAL | Outdoor Channel 1 temperature (°F) |
| outdoor_ch1_humidity | INTEGER | Outdoor Channel 1 humidity (%) |
| outdoor_ch2_temp_c | REAL | Outdoor Channel 2 temperature (°C) |
| outdoor_ch2_temp_f | REAL | Outdoor Channel 2 temperature (°F) |
| outdoor_ch2_humidity | INTEGER | Outdoor Channel 2 humidity (%) |
| outdoor_ch3_temp_c | REAL | Outdoor Channel 3 temperature (°C) |
| outdoor_ch3_temp_f | REAL | Outdoor Channel 3 temperature (°F) |
| outdoor_ch3_humidity | INTEGER | Outdoor Channel 3 humidity (%) |
| atmospheric_pressure | REAL | Atmospheric pressure |
| pressure_units | TEXT | Units for pressure measurement |

## Project Structure

```
IoTsync/
├── data/                # SQLite database storage (persisted)
├── logs/               # Application logs (persisted)
├── Dockerfile          # Docker image definition
├── docker-compose.yml  # Docker Compose configuration
├── supervisord.conf    # Supervisor process manager configuration
├── requirements.txt    # Python dependencies
├── data_collector.py   # Main application script
├── tuya_device_data.py # Tuya API client
├── db_handler.py       # Database operations
└── .env               # Environment variables (not in repo)
```

## Troubleshooting

1. Docker Issues:
   - If you see "Cannot connect to the Docker daemon" error:
     ```bash
     # On macOS:
     # Open Docker Desktop application
     open -a Docker
     
     # On Linux:
     sudo systemctl start docker
     
     # Verify Docker is running:
     docker info
     ```
   - Wait a few seconds after starting Docker before running docker-compose
   - Ensure you have proper permissions to use Docker
     ```bash
     # On Linux, add your user to the docker group:
     sudo usermod -aG docker $USER
     # Then log out and back in
     ```

2. Container Issues:
   - Check supervisor logs for process status
   - Verify environment variables in `.env`
   - Ensure proper permissions on data and logs directories

3. Data Collection Issues:
   - Verify Tuya API credentials
   - Check network connectivity
   - Review application logs for specific errors

4. Database Issues:
   - Check permissions on the data directory
   - Verify SQLite database file exists and is writable
   - Review error logs for database-specific issues

5. Email Alert Issues:
   - Verify SendGrid API key is correct
   - Ensure sender email is verified with SendGrid
   - Check logs for email sending errors
   - Verify recipient email address is correct
   - Test SendGrid configuration in their web interface
