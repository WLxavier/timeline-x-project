from pydantic import BaseModel, Field
from enum import Enum

class SensorData(BaseModel):
    device_id: str
    health_factor: float
    rpm: int
    temperature_c: float
    pressure_in_bar: float
    pressure_out_bar: float
    vibration_axial_mms: float
    vibration_radial_mms: float
    current_a: float
    acoustic_db: float
    humidity_percent: float

class DeviceConfig(BaseModel):
    device_id: str
    temp_std_dev_multiplier: float = 3.0

class AlertStatus(str, Enum):
    pending = "pending"
    confirmed_true = "confirmed_true"
    confirmed_false = "confirmed_false"

class AlertFeedback(BaseModel):
    status: AlertStatus = Field(..., description="O novo status do alerta")