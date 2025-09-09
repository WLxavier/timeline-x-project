import boto3
from fastapi import APIRouter, HTTPException, Query
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

router = APIRouter()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "cronos_db")
DB_USER = os.getenv("DB_USER", "cronos_user")
DB_PASS = os.getenv("DB_PASS", "cronos_password")

def get_db_connection():
    return psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)

@router.get("/latest", response_model=List[Dict[str, Any]])
def get_latest_sensor_data():
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM sensor_data ORDER BY time DESC LIMIT 10;")
                results = cur.fetchall()
                return results
    except Exception as e:
        print(f"API_ENDPOINT: Erro ao consultar o TimescaleDB: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar dados no banco de dados.")

@router.get("/{device_id}", response_model=List[Dict[str, Any]])
def get_sensor_data_by_device(
    device_id: str,
    start_time: Optional[datetime] = Query(None, description="Data de início no formato ISO (ex: 2025-08-10T10:00:00)"),
    end_time: Optional[datetime] = Query(None, description="Data de fim no formato ISO (ex: 2025-08-10T11:00:00)")
):
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query_params = [device_id]
                query = "SELECT * FROM sensor_data WHERE device_id = %s"
                if start_time:
                    query += " AND time >= %s"
                    query_params.append(start_time)
                if end_time:
                    query += " AND time <= %s"
                    query_params.append(end_time)
                query += " ORDER BY time DESC LIMIT 1000;"
                
                cur.execute(query, tuple(query_params))
                results = cur.fetchall()
                if not results:
                    raise HTTPException(status_code=404, detail=f"Nenhum dado encontrado para os critérios fornecidos.")
                return results
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"API_ENDPOINT: Erro ao consultar o TimescaleDB por device_id: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar dados no banco de dados.")

@router.get("/{device_id}/summary", response_model=List[Dict[str, Any]])
def get_device_summary(
    device_id: str,
    interval: str = Query("1 hour", description="Intervalo de agregação (ex: '15 minutes', '1 hour', '1 day')"),
    start_time: datetime = Query(default_factory=lambda: datetime.now() - timedelta(days=1)),
    end_time: datetime = Query(default_factory=datetime.now)
):
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = """
                    SELECT
                        time_bucket(%s, time) AS bucket,
                        AVG(temperature_c) AS avg_temperature,
                        MAX(vibration_radial_mms) AS max_vibration,
                        MIN(pressure_in_bar) AS min_pressure_in,
                        MAX(pressure_out_bar) AS max_pressure_out,
                        AVG(current_a) AS avg_current
                    FROM sensor_data
                    WHERE device_id = %s AND time BETWEEN %s AND %s
                    GROUP BY bucket
                    ORDER BY bucket DESC;
                """
                cur.execute(query, (interval, device_id, start_time, end_time))
                results = cur.fetchall()
                if not results:
                     raise HTTPException(status_code=404, detail=f"Nenhum dado de sumário encontrado para os critérios fornecidos.")
                return results
    except Exception as e:
        print(f"API_ENDPOINT: Erro ao gerar sumário: {e}")
        raise HTTPException(status_code=500, detail="Erro ao gerar sumário dos dados.")