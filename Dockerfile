FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ./cronos_ai /app/cronos_ai

CMD ["python", "-m", "cronos_ai.edge.edge_device_main"]