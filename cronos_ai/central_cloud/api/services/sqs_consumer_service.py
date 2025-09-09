import boto3
import json
import threading
import time
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import numpy as np
from collections import deque
from cronos_ai.shared.data_models import SensorData

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "cronos_db")
DB_USER = os.getenv("DB_USER", "cronos_user")
DB_PASS = os.getenv("DB_PASS", "cronos_password")

class AnomalyDetectorN2:
    def __init__(self, window_size=100, default_std_dev_multiplier=3.0):
        self.window_size=window_size; self.default_std_dev_multiplier=default_std_dev_multiplier; self.history={}; self.configs={}
    def load_configs(self, db_conn):
        print("DETECTOR_N2: Recarregando configurações..."); self.configs.clear()
        try:
            with db_conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM device_configs;"); [self.configs.update({row['device_id']: row}) for row in cur.fetchall()]
            print(f"DETECTOR_N2: {len(self.configs)} configuração(ões) carregada(s).")
        except Exception as e: print(f"DETECTOR_N2: Erro ao carregar configurações: {e}")
    def check(self, data: SensorData):
        device_id=data.device_id; alerts=[]; config=self.configs.get(device_id); std_dev_multiplier=config['temp_std_dev_multiplier'] if config else self.default_std_dev_multiplier
        if device_id not in self.history: self.history[device_id]={'temperature_c':deque(maxlen=self.window_size)}
        hist=self.history[device_id]
        if len(hist['temperature_c']) > self.window_size/2:
            mean=np.mean(hist['temperature_c']); std_dev=np.std(hist['temperature_c']); upper_bound=mean+std_dev_multiplier*std_dev
            if data.temperature_c > upper_bound: alerts.append({"type":"HighTemperatureN2", "value":data.temperature_c, "details":f"Valor {data.temperature_c:.2f} excedeu o limite dinâmico de {upper_bound:.2f} (multiplicador={std_dev_multiplier})"})
        hist['temperature_c'].append(data.temperature_c)
        return alerts

anomaly_detector_n2 = AnomalyDetectorN2()

def get_db_connection():
    retries=5; conn=None
    while retries>0 and not conn:
        try: conn=psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)
        except psycopg2.OperationalError: retries-=1; time.sleep(5)
    if conn: print("API_CONSUMER: Conexão com o TimescaleDB estabelecida!")
    return conn

def setup_database(conn):
    """Cria/Altera todas as tabelas, incluindo a coluna 'status' em 'alerts'."""
    with conn.cursor() as cur:
        cur.execute("CREATE TABLE IF NOT EXISTS sensor_data (time TIMESTAMPTZ NOT NULL, device_id VARCHAR(50) NOT NULL, health_factor REAL, rpm INTEGER, temperature_c REAL, pressure_in_bar REAL, pressure_out_bar REAL, vibration_axial_mms REAL, vibration_radial_mms REAL, current_a REAL, acoustic_db REAL, humidity_percent REAL);")
        cur.execute("SELECT create_hypertable('sensor_data', 'time', if_not_exists => TRUE);")
        cur.execute("CREATE TABLE IF NOT EXISTS device_configs (device_id VARCHAR(50) PRIMARY KEY, temp_std_dev_multiplier REAL DEFAULT 3.0, last_updated TIMESTAMPTZ DEFAULT NOW());")

        cur.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='alerts' AND column_name='status') THEN
                    ALTER TABLE alerts ADD COLUMN status VARCHAR(20) DEFAULT 'pending';
                END IF;
            END $$;
        """)
        cur.execute("CREATE TABLE IF NOT EXISTS alerts (id SERIAL PRIMARY KEY, time TIMESTAMPTZ NOT NULL, device_id VARCHAR(50) NOT NULL, alert_type VARCHAR(100), alert_value REAL, full_payload JSONB, status VARCHAR(20) DEFAULT 'pending');")

        conn.commit()
    print("API_CONSUMER: Todas as tabelas prontas e atualizadas.")

def auto_tuner_service():
    """Serviço que roda em background para ajustar a sensibilidade dos alertas."""
    print("AUTO_TUNER: Serviço de autoajuste iniciado.")
    while True:
        time.sleep(3600) 
        
        print("AUTO_TUNER: Procurando por feedback para otimizar modelos...")
        db_conn = get_db_connection()
        if not db_conn: continue

        try:
            with db_conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT device_id, COUNT(*) as false_positives
                    FROM alerts
                    WHERE status = 'confirmed_false' AND time > NOW() - INTERVAL '1 hour'
                    GROUP BY device_id
                    HAVING COUNT(*) >= 5;
                """)
                devices_to_tune = cur.fetchall()

                for device in devices_to_tune:
                    device_id = device['device_id']
                    cur.execute("SELECT temp_std_dev_multiplier FROM device_configs WHERE device_id = %s;", (device_id,))
                    current_multiplier = (cur.fetchone() or {}).get('temp_std_dev_multiplier', 3.0)
                    
                    new_multiplier = current_multiplier * 1.1
                    
                    print(f"AUTO_TUNER: Muitos falsos positivos para {device_id}. Ajustando sensibilidade de {current_multiplier:.2f} para {new_multiplier:.2f}.")
                    
                    cur.execute(
                        "INSERT INTO device_configs (device_id, temp_std_dev_multiplier) VALUES (%s, %s) ON CONFLICT (device_id) DO UPDATE SET temp_std_dev_multiplier = EXCLUDED.temp_std_dev_multiplier, last_updated = NOW();",
                        (device_id, new_multiplier)
                    )
                db_conn.commit()
            
            anomaly_detector_n2.load_configs(db_conn)

        except Exception as e:
            print(f"AUTO_TUNER: Erro durante o ciclo de ajuste: {e}")
        finally:
            if db_conn: db_conn.close()

def consume_sqs_messages():
    print("API_CONSUMER: Iniciando consumidor SQS...")
    db_conn = get_db_connection()
    if not db_conn: return
    setup_database(db_conn)
    anomaly_detector_n2.load_configs(db_conn)
    endpoint_url = 'http://host.docker.internal:4566'; queue_name = 'sensor_data_queue'
    sqs_client = boto3.client('sqs', endpoint_url=endpoint_url, region_name='us-east-1')
    try: queue_url = sqs_client.get_queue_url(QueueName=queue_name)['QueueUrl']
    except Exception as e: print(f"API_CONSUMER: Falha ao obter URL da fila: {e}"); return
    while True:
        try:
            response = sqs_client.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=10, WaitTimeSeconds=10)
            if 'Messages' in response:
                with db_conn.cursor() as cur:
                    for message in response['Messages']:
                        data_dict = json.loads(message['Body'])
                        sd = SensorData(**data_dict)
                        cur.execute("INSERT INTO sensor_data (time, device_id, health_factor, rpm, temperature_c, pressure_in_bar, pressure_out_bar, vibration_axial_mms, vibration_radial_mms, current_a, acoustic_db, humidity_percent) VALUES (NOW(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);", (sd.device_id, sd.health_factor, sd.rpm, sd.temperature_c, sd.pressure_in_bar, sd.pressure_out_bar, sd.vibration_axial_mms, sd.vibration_radial_mms, sd.current_a, sd.acoustic_db, sd.humidity_percent))
                        if 'alerts' in data_dict and data_dict['alerts']:
                            for alert in data_dict['alerts']:
                                cur.execute("INSERT INTO alerts (time, device_id, alert_type, alert_value, full_payload) VALUES (NOW(), %s, %s, %s, %s);", (sd.device_id, alert['type'], alert['value'], json.dumps(data_dict)))
                            print(f"API_CONSUMER: Alerta N1 de {sd.device_id} salvo.")
                        alerts_n2 = anomaly_detector_n2.check(sd)
                        if alerts_n2:
                            for alert in alerts_n2:
                                cur.execute("INSERT INTO alerts (time, device_id, alert_type, alert_value, full_payload) VALUES (NOW(), %s, %s, %s, %s);", (sd.device_id, alert['type'], alert['value'], json.dumps(alert['details'])))
                            print(f"API_CONSUMER: Alerta N2 de {sd.device_id} detectado e salvo.")
                db_conn.commit()
                entries_to_delete = [{'Id': msg['MessageId'], 'ReceiptHandle': msg['ReceiptHandle']} for msg in response['Messages']]
                sqs_client.delete_message_batch(QueueUrl=queue_url, Entries=entries_to_delete)
        except Exception as e: print(f"API_CONSUMER: Erro no loop principal: {e}"); time.sleep(5)


def start_consumer_thread():
    """Inicia a thread do consumidor SQS e a NOVA thread do auto-tuner."""
    consumer_thread = threading.Thread(target=consume_sqs_messages, daemon=True)
    tuner_thread = threading.Thread(target=auto_tuner_service, daemon=True)
    
    consumer_thread.start()
    tuner_thread.start()