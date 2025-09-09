-- Script de Criação de Tabelas para o Projeto Timeline-X / Cronos AI

-- Tabela para armazenar os dados brutos dos sensores em tempo real
-- Esta tabela é otimizada como uma 'hypertable' do TimescaleDB para performance.
CREATE TABLE IF NOT EXISTS sensor_data (
    time TIMESTAMPTZ NOT NULL,
    device_id VARCHAR(50) NOT NULL,
    health_factor REAL,
    rpm INTEGER,
    temperature_c REAL,
    pressure_in_bar REAL,
    pressure_out_bar REAL,
    vibration_axial_mms REAL,
    vibration_radial_mms REAL,
    current_a REAL,
    acoustic_db REAL,
    humidity_percent REAL
);

-- Converte a tabela sensor_data em uma hypertable, particionada pela coluna 'time'.
SELECT create_hypertable('sensor_data', 'time', if_not_exists => TRUE);


-- Tabela para registrar todos os alertas gerados (Nível 1 da borda ou Nível 2 da nuvem).
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    time TIMESTAMPTZ NOT NULL,
    device_id VARCHAR(50) NOT NULL,
    alert_type VARCHAR(100),
    alert_value REAL,
    full_payload JSONB,
    status VARCHAR(20) DEFAULT 'pending' -- Para o feedback continuo do operador (pending, confirmed_true, confirmed_false)
);


-- Tabela para armazenar as configurações de sensibilidade do motor de IA para cada dispositivo.
CREATE TABLE IF NOT EXISTS device_configs (
    device_id VARCHAR(50) PRIMARY KEY,
    temp_std_dev_multiplier REAL DEFAULT 3.0,
    last_updated TIMESTAMPTZ DEFAULT NOW()
);


-- Tabela para armazenar os dados históricos de treinamento do dataset da NASA.
-- Esta tabela é usada para o treinamento do modelo de previsão de RUL (Remaining Useful Life).
CREATE TABLE IF NOT EXISTS nasa_turbofan_data (
    time TIMESTAMPTZ DEFAULT NOW(),
    unit_nr INTEGER,
    cycle REAL,
    setting1 REAL,
    setting2 REAL,
    setting3 REAL,
    sensor1 REAL,
    sensor2 REAL,
    sensor3 REAL,
    sensor4 REAL,
    sensor5 REAL,
    sensor6 REAL,
    sensor7 REAL,
    sensor8 REAL,
    sensor9 REAL,
    sensor10 REAL,
    sensor11 REAL,
    sensor12 REAL,
    sensor13 REAL,
    sensor14 REAL,
    sensor15 REAL,
    sensor16 REAL,
    sensor17 REAL,
    sensor18 REAL,
    sensor19 REAL,
    sensor20 REAL,
    sensor21 REAL,
    RUL REAL
);