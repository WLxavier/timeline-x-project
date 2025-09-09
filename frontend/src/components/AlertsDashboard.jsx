import { useState, useEffect } from 'react';

const API_BASE_URL = 'http://localhost:8000/api/v1';

function AlertsDashboard() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchAlerts = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/alerts`);
      if (!response.ok) throw new Error('Falha na resposta da rede');
      const data = await response.json();
      setAlerts(data);
    } catch (err) {
      setError('Não foi possível carregar os alertas.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleFeedback = async (alertId, status) => {
    try {
      const response = await fetch(`${API_BASE_URL}/alerts/${alertId}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: status }),
      });
      if (!response.ok) throw new Error('Falha ao enviar feedback');
      
      setAlerts(currentAlerts =>
        currentAlerts.map(alert =>
          alert.id === alertId ? { ...alert, status: status } : alert
        )
      );

    } catch (err) {
      console.error('Erro ao enviar feedback:', err);
      alert('Não foi possível registrar o feedback.');
    }
  };

  useEffect(() => {
    fetchAlerts();
    const intervalId = setInterval(fetchAlerts, 15000);
    return () => clearInterval(intervalId);
  }, []);

  if (loading) return <p>Carregando alertas...</p>;
  if (error) return <p className="error-banner">{error}</p>;

  return (
    <div className="data-section">
      <h2>Gestão de Alertas</h2>
      <table className="alerts-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Hora</th>
            <th>Dispositivo</th>
            <th>Tipo de Alerta</th>
            <th>Valor</th>
            <th>Status</th>
            <th>Ações</th>
          </tr>
        </thead>
        <tbody>
          {alerts.length > 0 ? (
            alerts.map(alert => (
              <tr key={alert.id}>
                <td>{alert.id}</td>
                <td>{new Date(alert.time).toLocaleString()}</td>
                <td>{alert.device_id}</td>
                <td>{alert.alert_type}</td>
                <td>{alert.alert_value ? alert.alert_value.toFixed(2) : 'N/A'}</td>
                <td><span className={`status status-${alert.status}`}>{alert.status}</span></td>
                <td>
                  {alert.status === 'pending' && (
                    <div className="actions">
                      <button onClick={() => handleFeedback(alert.id, 'confirmed_true')} className="btn btn-confirm">Confirmar (Verdadeiro)</button>
                      <button onClick={() => handleFeedback(alert.id, 'confirmed_false')} className="btn btn-false">Marcar como Falso</button>
                    </div>
                  )}
                </td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan="7">Nenhum alerta encontrado.</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

export default AlertsDashboard;