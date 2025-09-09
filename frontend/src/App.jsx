import './App.css';
import AlertsDashboard from './components/AlertsDashboard';
import DeviceConfigDashboard from './components/DeviceConfigDashboard';

function App() {
  const deviceIdToManage = "bomba-centrifuga-01";

  return (
    <div className="container">
      <h1>Painel Admin - Timeline-X</h1>
      
      <div className="dashboard-layout">
        <div className="main-panel">
          <AlertsDashboard />
        </div>
        <div className="side-panel">
          {}
          <DeviceConfigDashboard deviceId={deviceIdToManage} />
        </div>
      </div>

    </div>
  );
}

export default App;