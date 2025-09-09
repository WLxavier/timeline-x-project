import boto3
import time
import json
import os

from cronos_ai.edge.simulators import ComprehensiveSensorSimulator

DEVICE_ID = "bomba-01-edge"
QUEUE_NAME = 'sensor_data_queue'

endpoint_url = 'http://host.docker.internal:4566'
region_name = 'us-east-1'

class AnomalyDetectorN1:
    def __init__(self):
        self.thresholds = {
            "temperature_c_upper": 95.0, "pressure_diff_lower": 3.0,
            "vibration_radial_mms_upper": 4.5, "current_a_upper": 28.0,
            "acoustic_db_upper": 85.0
        }

    def check_anomaly(self, data):
        alerts = []
        if data["temperature_c"] > self.thresholds["temperature_c_upper"]:
            alerts.append({"type": "HighTemperature", "value": data["temperature_c"]})
        pressure_diff = data["pressure_out_bar"] - data["pressure_in_bar"]
        if pressure_diff < self.thresholds["pressure_diff_lower"]:
             alerts.append({"type": "LowPressureDifferential", "value": pressure_diff})
        if data["vibration_radial_mms"] > self.thresholds["vibration_radial_mms_upper"]:
            alerts.append({"type": "HighVibration", "value": data["vibration_radial_mms"]})
        if data["current_a"] > self.thresholds["current_a_upper"]:
            alerts.append({"type": "HighCurrent", "value": data["current_a"]})
        if data["acoustic_db"] > self.thresholds["acoustic_db_upper"]:
            alerts.append({"type": "HighAcousticNoise", "value": data["acoustic_db"]})
        return alerts

def main():
    sqs_client = boto3.client('sqs', endpoint_url=endpoint_url, region_name=region_name)
    queue_url = None
    
    max_retries = 6
    retry_count = 0
    while not queue_url and retry_count < max_retries:
        try:
            response = sqs_client.get_queue_url(QueueName=QUEUE_NAME)
            queue_url = response['QueueUrl']
            print(f"EDGE: Cliente SQS conectado. URL da Fila: {queue_url}")
        except sqs_client.exceptions.QueueDoesNotExist:
            retry_count += 1
            print(f"EDGE: Fila SQS ainda não encontrada. Tentando novamente em 5 segundos... ({retry_count}/{max_retries})")
            time.sleep(5)

    if not queue_url:
        print("EDGE: Não foi possível encontrar a fila SQS após várias tentativas. Desligando.")
        return

    sensor_simulator = ComprehensiveSensorSimulator(device_id="bomba-centrifuga-01")
    anomaly_detector = AnomalyDetectorN1()
    
    print(f"--- Dispositivo de Borda '{DEVICE_ID}' iniciado (Modo SQS) ---")

    try:
        while True:
            data = sensor_simulator.generate_data()
            
            alerts = anomaly_detector.check_anomaly(data)
            
            payload_data = data.copy()
            if alerts:
                print(f"EDGE: Anomalia N1 detectada: {[a['type'] for a in alerts]}")
                payload_data['alerts'] = alerts
            
            payload = json.dumps(payload_data)
            
            sqs_client.send_message(
                QueueUrl=queue_url,
                MessageBody=payload
            )
            print(f"EDGE: Mensagem enviada para a fila SQS -> {payload}")
            
            time.sleep(5)

    except KeyboardInterrupt:
        print("\n--- Desligando o dispositivo de borda ---")

if __name__ == "__main__":
    main()