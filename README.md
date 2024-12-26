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
- Web dashboard featuring:
  - Real-time temperature display in both °C and °F
  - Historical temperature charts with day/week/month/year views
  - Alert monitoring with temperature thresholds
  - Responsive design for mobile and desktop
  - Automatic timezone conversion to EST
- Historical temperature data visualization
- Real-time updates every minute

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

## API Endpoints

The backend provides the following REST API endpoints:

- `GET /` - Health check endpoint
- `GET /api/temperature/current` - Get current temperature
- `GET /api/temperature/history?timerange={day|week|month|year}` - Get temperature history
- `GET /api/temperature/stats` - Get min/max temperature stats and alert threshold
- `GET /api/alerts/recent` - Get recent temperature alerts

## Project Structure

```
IoTsync/
├── backend/
│   ├── data/           # SQLite database storage (persisted)
│   ├── logs/           # Application logs (persisted)
│   ├── api.py          # FastAPI backend server
│   ├── alert_manager.py
│   ├── config.py
│   ├── data_collector.py
│   ├── db_handler.py
│   ├── tuya_device_data.py
│   └── requirements.txt
├── frontend/
│   └─ src/
│       ├── index.html  # Main dashboard page
│       ├── styles.css  # Dashboard styling
│       ├── app.js      # Dashboard functionality
│       └── env.js      # Environment configuration
├── docker-compose.yml  # Docker Compose configuration
├── Dockerfile.backend  # Backend Docker image definition
├── Dockerfile.frontend # Frontend Docker image definition
├── supervisord.conf    # Supervisor process manager configuration
└── .env               # Environment variables (not in repo)
```

## Frontend Features

The dashboard provides:
- Current temperature display in both Celsius and Fahrenheit
- 24-hour temperature statistics
- Interactive temperature chart with time range selection
- Recent alerts display
- Automatic updates every minute
- EST timezone display
- Responsive design for all screen sizes

## Backend Features

The backend handles:
- Data collection from Tuya devices
- Database management
- Temperature alert monitoring
- Email notifications via SendGrid
- REST API for frontend data
- Automatic timezone conversion
- Error handling and logging

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

3. Edit `.env` and add your credentials:
```env
# Required
VITE_TUYABASEURL=https://openapi.tuyaus.com
VITE_ACCESSKEY=your_tuya_access_key
VITE_SECRETKEY=your_tuya_secret_key
VITE_TUYAUSERID=your_tuya_user_id
DEVICE_ID=your_device_id

# Optional Email Alerts
SENDGRID_API_KEY=your_sendgrid_api_key
SENDGRID_FROM_EMAIL=your_verified_sender_email
ALERT_EMAIL=recipient_email
```

4. Choose your installation method:

### Option A: Using Docker

Start the services:
```bash
docker-compose up -d
```

Access the dashboard:
- Open http://localhost:3000 in your browser

### Option B: Local Development with UV

1. Install UV package manager:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Create and activate a virtual environment in the project root:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies using UV:
```bash
# Install backend dependencies from project root
cd backend
uv pip install -r requirements.txt
cd ..
```

4. Create necessary directories:
```bash
# From project root
mkdir -p backend/data backend/logs
```

5. Set up Python path and start the backend server (in a terminal):
```bash
# From project root
source venv/bin/activate
export PYTHONPATH=$PYTHONPATH:$(pwd)
cd backend
uvicorn api:app --reload --port 8000
```

6. Start the data collector (in a new terminal):
```bash
# From project root
source venv/bin/activate
export PYTHONPATH=$PYTHONPATH:$(pwd)
cd backend
python3 data_collector.py
```

7. Start the frontend (in a new terminal):
```bash
# From project root
cd frontend/src
python3 -m http.server 3000 --bind 0.0.0.0
```

Access the dashboard:
- Open http://localhost:3000 in your browser

## Development

### Frontend Development
The frontend is built with vanilla JavaScript, HTML, and CSS:
- `index.html` - Main dashboard structure
- `styles.css` - Dashboard styling
- `app.js` - Dashboard functionality and API integration
- `env.js` - Environment configuration

To test the frontend locally:
```bash
cd frontend/src
python3 -m http.server 3000
```

Note: Make sure the backend is running at http://localhost:8000 for the API calls to work.

### Backend Development
The backend is built with Python and FastAPI:
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
cd backend
uv pip install -r requirements.txt

# Set Python path
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Start the development server
uvicorn api:app --reload
```

The API will be available at http://localhost:8000

### Testing the API Endpoints

Once the backend is running, you can test the API endpoints using curl:

```bash
# Health check
curl http://localhost:8000/
# Response: {"message":"API is running"}

# Get current temperature
curl http://localhost:8000/api/temperature/current
# Response:
# {
#   "temperature_c": 25.6,
#   "temperature_f": 78.1,
#   "timestamp": "2024-01-20T14:30:00"
# }

# Get temperature history
# timerange options: day, week, month, year
curl http://localhost:8000/api/temperature/history?timerange=day
# Response:
# [
#   {
#     "time": "2024-01-20T14:00:00",
#     "temperature": 25.6,
#     "temperature_f": 78.1
#   },
#   ...
# ]

# Get 24-hour temperature stats
curl http://localhost:8000/api/temperature/stats
# Response:
# {
#   "min_temperature": 75.2,
#   "max_temperature": 82.4,
#   "alert_threshold": 101.0
# }

# Get recent temperature alerts
curl http://localhost:8000/api/alerts/recent
# Response:
# [
#   {
#     "id": 1,
#     "timestamp": "2024-01-20T14:25:00",
#     "type": "triggered",
#     "temperature": 98.6,
#     "threshold": 101.0,
#     "message": "Pool temperature is below minimum threshold..."
#   },
#   ...
# ]
```

## Configuration

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

## Troubleshooting

1. Docker Issues:
   - If you see "Cannot connect to the Docker daemon" error:
     ```bash
     # On macOS:
     # Open Docker Desktop application
     open -a Docker
     
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
