from fastapi import APIRouter, HTTPException
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any
from cronos_ai.shared.data_models import AlertFeedback

router = APIRouter()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "cronos_db")
DB_USER = os.getenv("DB_USER", "cronos_user")
DB_PASS = os.getenv("DB_PASS", "cronos_password")

@router.get("/", response_model=List[Dict[str, Any]])
def get_all_alerts():
    try:
        with psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM alerts ORDER BY time DESC LIMIT 100;")
                results = cur.fetchall()
                return results
    except Exception as e:
        print(f"API_ENDPOINT: Erro ao consultar alertas: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar alertas no banco de dados.")

@router.post("/{alert_id}/feedback", response_model=Dict[str, Any])
def provide_alert_feedback(alert_id: int, feedback: AlertFeedback):
    try:
        with psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("UPDATE alerts SET status = %s WHERE id = %s RETURNING *;", (feedback.status.value, alert_id))
                updated_alert = cur.fetchone()
                conn.commit()
                if not updated_alert:
                    raise HTTPException(status_code=404, detail=f"Alerta com id {alert_id} não encontrado.")
                return updated_alert
    except Exception as e:
        print(f"API_ENDPOINT: Erro ao registrar feedback: {e}")
        raise HTTPException(status_code=500, detail="Erro ao registrar feedback.")