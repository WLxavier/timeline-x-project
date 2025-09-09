from fastapi import APIRouter, HTTPException
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, Any
from cronos_ai.shared.data_models import DeviceConfig

router = APIRouter()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "cronos_db")
DB_USER = os.getenv("DB_USER", "cronos_user")
DB_PASS = os.getenv("DB_PASS", "cronos_password")

@router.get("/{device_id}", response_model=DeviceConfig)
def get_device_config(device_id: str):
    try:
        with psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM device_configs WHERE device_id = %s;", (device_id,))
                config = cur.fetchone()
                if not config:
                    return DeviceConfig(device_id=device_id)
                return config
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{device_id}", response_model=DeviceConfig)
def set_device_config(device_id: str, config: DeviceConfig):
    if device_id != config.device_id:
        raise HTTPException(status_code=400, detail="O device_id na URL não corresponde ao do corpo da requisição.")
    
    try:
        with psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    INSERT INTO device_configs (device_id, temp_std_dev_multiplier)
                    VALUES (%s, %s)
                    ON CONFLICT (device_id) DO UPDATE SET
                        temp_std_dev_multiplier = EXCLUDED.temp_std_dev_multiplier,
                        last_updated = NOW();
                    """,
                    (config.device_id, config.temp_std_dev_multiplier)
                )
                conn.commit()
                
                cur.execute("SELECT * FROM device_configs WHERE device_id = %s;", (device_id,))
                updated_config = cur.fetchone()
                return updated_config
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))