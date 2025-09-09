import { useState, useEffect } from 'react';

const API_BASE_URL = 'http://localhost:8000/api/v1';

function DeviceConfigDashboard({ deviceId }) {
  const [config, setConfig] = useState(null);
  const [newMultiplier, setNewMultiplier] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState('');

  const fetchConfig = async () => {
    if (!deviceId) return;
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/configurations/${deviceId}`);
      if (!response.ok) throw new Error('Dispositivo não encontrado ou falha na API');
      const data = await response.json();
      setConfig(data);
      setNewMultiplier(data.temp_std_dev_multiplier);
    } catch (err) {
      setError('Não foi possível carregar a configuração.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveConfig = async (e) => {
    e.preventDefault();
    setSuccessMessage('');
    setError(null);

    const updatedConfig = {
      device_id: deviceId,
      temp_std_dev_multiplier: parseFloat(newMultiplier)
    };

    try {
      const response = await fetch(`${API_BASE_URL}/configurations/${deviceId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updatedConfig),
      });
      if (!response.ok) throw new Error('Falha ao salvar a configuração');
      const data = await response.json();
      setConfig(data);
      setSuccessMessage('Configuração salva com sucesso!');
    } catch (err) {
      setError('Não foi possível salvar a configuração.');
      console.error(err);
    }
  };

  useEffect(() => {
    fetchConfig();
  }, [deviceId]);

  return (
    <div className="data-section">
      <h2>Configuração de Sensibilidade do Dispositivo</h2>
      <h4>Dispositivo: <strong>{deviceId}</strong></h4>

      {loading && <p>Carregando configuração...</p>}
      {error && <p className="error-banner">{error}</p>}
      
      {config && (
        <form onSubmit={handleSaveConfig} className="config-form">
          <label htmlFor="multiplier">
            Multiplicador de Desvio Padrão (Temperatura):
            <br/>
            <small>(Valores maiores = menos sensível, menos alertas)</small>
          </label>
          <input
            id="multiplier"
            type="number"
            step="0.1"
            value={newMultiplier}
            onChange={(e) => setNewMultiplier(e.target.value)}
          />
          <button type="submit" className="btn btn-confirm">Salvar</button>
        </form>
      )}
      {successMessage && <p className="success-message">{successMessage}</p>}
    </div>
  );
}

export default DeviceConfigDashboard;