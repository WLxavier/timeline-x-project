import boto3
import time

print("--- Iniciando configuração da infraestrutura no LocalStack (apenas SQS) ---")

endpoint_url = 'http://host.docker.internal:4566'
region_name = 'us-east-1'
queue_name = 'sensor_data_queue'

def wait_for_localstack():
    print("Aguardando LocalStack ficar pronto...")
    client = boto3.client("sts", endpoint_url=endpoint_url, region_name=region_name, aws_access_key_id='test', aws_secret_access_key='test')
    for _ in range(30):
        try:
            client.get_caller_identity()
            print("LocalStack está pronto!")
            return True
        except Exception:
            time.sleep(2)
    print("Erro: LocalStack não ficou pronto a tempo.")
    return False

def setup_sqs(sqs_client):
    print(f"Criando fila SQS: {queue_name}...")
    try:
        sqs_client.create_queue(QueueName=queue_name)
        print("Fila SQS criada com sucesso.")
    except Exception as e:
        print(f"Não foi possível criar a fila (ela pode já existir): {e}")

if wait_for_localstack():
    sqs = boto3.client("sqs", endpoint_url=endpoint_url, region_name=region_name)
    setup_sqs(sqs)
    print("--- Configuração finalizada com sucesso! ---")