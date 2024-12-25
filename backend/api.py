from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import sqlite3
from datetime import datetime, timedelta
from config import Config
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

# Configure CORS
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://[::1]:3000",  # IPv6 localhost
]

logger.info(f"Configuring CORS with origins: {origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # More permissive during development
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "API is running"}

def get_db():
    return sqlite3.connect(Config.DB_FILE)

@app.get("/api/temperature/current")
async def get_current_temperature(request: Request):
    logger.debug(f"Received request for current temperature from {request.client.host}")
    logger.debug(f"Request headers: {request.headers}")
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT pool_temp_c, pool_temp_f, timestamp
            FROM sensor_readings
            ORDER BY timestamp DESC
            LIMIT 1
        """)
        result = cursor.fetchone()
        
        if not result:
            logger.warning("No temperature data found in database")
            raise HTTPException(status_code=404, detail="No temperature data found")
        
        response = {
            "temperature_c": result[0],
            "temperature_f": result[1],
            "timestamp": result[2]
        }
        logger.debug(f"Returning current temperature data: {response}")
        return response

@app.get("/api/temperature/history")
async def get_temperature_history(request: Request, timerange: str = "day"):
    logger.debug(f"Received request for temperature history from {request.client.host}")
    logger.debug(f"Timerange: {timerange}")
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        if timerange == "day":
            interval = "1 minute"
            time_ago = "1 day"
        elif timerange == "week":
            interval = "1 hour"
            time_ago = "7 days"
        elif timerange == "month":
            interval = "1 hour"
            time_ago = "30 days"
        else:  # year
            interval = "1 day"
            time_ago = "365 days"
            
        logger.debug(f"Using interval: {interval}, time_ago: {time_ago}")
            
        cursor.execute(f"""
            SELECT 
                datetime(timestamp) as time,
                pool_temp_c as temperature,
                pool_temp_f as temperature_f
            FROM sensor_readings
            WHERE timestamp > datetime('now', '-{time_ago}')
            GROUP BY strftime('%Y-%m-%d %H:%M', timestamp)
            ORDER BY timestamp ASC
        """)
        
        results = cursor.fetchall()
        response = [{
            "time": row[0],
            "temperature": row[1],
            "temperature_f": row[2]
        } for row in results]
        
        logger.debug(f"Returning {len(response)} history records")
        return response

@app.get("/api/alerts/recent")
async def get_recent_alerts():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                timestamp,
                alert_type,
                temperature_f,
                threshold_f,
                message
            FROM temperature_alerts
            ORDER BY timestamp DESC
            LIMIT 10
        """)
        
        results = cursor.fetchall()
        return [{
            "id": i,
            "timestamp": row[0],
            "type": row[1],
            "temperature": row[2],
            "threshold": row[3],
            "message": row[4]
        } for i, row in enumerate(results)]

@app.get("/api/temperature/stats")
async def get_temperature_stats():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                MIN(pool_temp_f) as min_temp,
                MAX(pool_temp_f) as max_temp
            FROM sensor_readings
            WHERE timestamp > datetime('now', '-1 day')
        """)
        
        min_temp, max_temp = cursor.fetchone()
        return {
            "min_temperature": min_temp,
            "max_temperature": max_temp,
            "alert_threshold": Config.ALERT_MIN_POOL_TEMP_F
        } 