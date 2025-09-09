import numpy as np
import time
import random
import json

class ComprehensiveSensorSimulator:
    """
    Simula múltiplos sensores de um ativo industrial complexo (ex: uma bomba centrífuga).
    
    Sensores incluídos:
    - Temperatura
    - Pressão (entrada e saída)
    - Vibração (axial e radial)
    - Corrente Elétrica
    - Nível de Ruído Acústico
    - Umidade do Ambiente
    - Velocidade de Rotação (RPM)
    
    Características:
    - Fator de "saúde" que degrada o equipamento ao longo do tempo.
    - Interdependência entre os sensores (ex: mais RPM -> mais vibração e temperatura).
    - Anomalias súbitas e realistas (ex: falha de lubrificação, pico de pressão).
    """

    def __init__(self, device_id="bomba-centrifuga-01"):
        self.device_id = device_id
        self.timestep = 0
        
        self.health_factor = 1.0
        self.degradation_rate = 0.0001

        self.base_rpm = 1500
        self.base_temp = 70.0  # Celsius
        self.base_pressure_in = 2.0  # bar
        self.base_pressure_out = 7.0 # bar
        self.base_vibration_axial = 0.5 # mm/s
        self.base_vibration_radial = 0.8 # mm/s
        self.base_current = 20.0 # Amperes
        self.base_acoustic = 65.0 # dB
        self.base_humidity = 40.0 # %

    def _trigger_anomaly(self):
        if random.random() < 0.02:
            anomaly_type = random.choice(["pressure_spike", "lubrication_failure"])
            print(f"SENSOR_SIM: *** Anomalia Súbita: {anomaly_type} ***")
            return anomaly_type
        return None

    def generate_data(self):
        """Gera uma nova leitura de todos os sensores."""
        self.timestep += 1
        if self.health_factor > 0.1:
            self.health_factor -= self.degradation_rate

        anomaly = self._trigger_anomaly()
        
        
        # RPM varia com a saúde (desgaste reduz eficiência)
        rpm_noise = np.random.normal(0, 10)
        current_rpm = self.base_rpm * (self.health_factor * 0.2 + 0.8) + rpm_noise
        
        # Temperatura é afetada pelo RPM e pela saúde (desgaste gera atrito)
        temp_noise = np.random.normal(0, 0.5)
        current_temp = self.base_temp + (current_rpm / 100) + (10 * (1 - self.health_factor)) + temp_noise
        
        # Pressão de saída depende do RPM, mas é afetada pela saúde (perda de eficiência)
        pressure_noise = np.random.normal(0, 0.1)
        current_pressure_out = self.base_pressure_out * (current_rpm / self.base_rpm) * self.health_factor + pressure_noise
        current_pressure_in = self.base_pressure_in + pressure_noise / 2
        
        # Vibração aumenta com RPM e com o desgaste (1 - health)
        vibration_noise = np.random.normal(0, 0.1)
        vibration_factor = (current_rpm / self.base_rpm) + (2 * (1 - self.health_factor))
        current_vibration_axial = self.base_vibration_axial * vibration_factor + vibration_noise
        current_vibration_radial = self.base_vibration_radial * vibration_factor + vibration_noise
        
        # Corrente aumenta quando a saúde diminui (motor trabalha mais)
        current_noise = np.random.normal(0, 0.2)
        current_current = self.base_current / (self.health_factor * 0.5 + 0.5) + current_noise
        
        # Ruído acústico aumenta com RPM e desgaste
        acoustic_noise = np.random.normal(0, 0.5)
        log_arg = np.maximum(0, current_rpm - self.base_rpm)
        current_acoustic = self.base_acoustic + 5 * np.log1p(log_arg) + (15 * (1 - self.health_factor)) + acoustic_noise
        
        # Umidade do ambiente varia lentamente
        current_humidity = self.base_humidity + np.sin(self.timestep / 200) * 5 + np.random.normal(0, 1)

        # Aplica Efeitos de Anomalias Súbitas
        if anomaly == "pressure_spike":
            current_pressure_out *= 1.5
            current_current *= 1.2
        elif anomaly == "lubrication_failure":
            current_temp += 25
            current_vibration_axial *= 3
            current_vibration_radial *= 3
            current_acoustic += 10
            self.health_factor -= 0.05
        
        return {
            "device_id": self.device_id,
            "health_factor": round(self.health_factor, 4),
            "rpm": int(current_rpm),
            "temperature_c": round(current_temp, 2),
            "pressure_in_bar": round(current_pressure_in, 2),
            "pressure_out_bar": round(current_pressure_out, 2),
            "vibration_axial_mms": round(current_vibration_axial, 3),
            "vibration_radial_mms": round(current_vibration_radial, 3),
            "current_a": round(current_current, 2),
            "acoustic_db": round(current_acoustic, 2),
            "humidity_percent": round(current_humidity, 2)
        }

if __name__ == '__main__':
    simulator = ComprehensiveSensorSimulator()
    print("Iniciando simulador abrangente. Pressione Ctrl+C para parar.")
    for i in range(500):
        data = simulator.generate_data()
        print(json.dumps(data, indent=2))
        time.sleep(1)