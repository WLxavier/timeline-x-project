from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .endpoints import sensor_data, alerts, configurations
from .services.sqs_consumer_service import start_consumer_thread

app = FastAPI(title="Cronos AI API")

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    start_consumer_thread()

app.include_router(sensor_data.router, prefix="/api/v1/sensordata", tags=["Sensor Data"])
app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["Alerts"])
app.include_router(configurations.router, prefix="/api/v1/configurations", tags=["Configurations"])

@app.get("/")
def read_root():
    return {"message": "Bem-vindo à API do Cronos AI!"}