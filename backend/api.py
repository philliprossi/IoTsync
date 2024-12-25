from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
from datetime import datetime, timedelta
from config import Config

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    return sqlite3.connect(Config.DB_FILE)

@app.get("/api/temperature/current")
async def get_current_temperature():
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
            raise HTTPException(status_code=404, detail="No temperature data found")
            
        return {
            "temperature_c": result[0],
            "temperature_f": result[1],
            "timestamp": result[2]
        }

@app.get("/api/temperature/history")
async def get_temperature_history(timerange: str = "day"):
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
        return [{
            "time": row[0],
            "temperature": row[1],
            "temperature_f": row[2]
        } for row in results]

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
            "max_temperature": max_temp
        } 