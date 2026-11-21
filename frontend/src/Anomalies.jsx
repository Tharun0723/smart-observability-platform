
import './Anomalies.css'

function Anomalies() {
  const alerts = [
    {
      title: 'High CPU Activity',
      description: 'CPU usage suddenly increased above its usual level.',
      severity: 'Medium',
      type: 'warning',
    },
    {
      title: 'Memory Usage Spike',
      description: 'Memory consumption increased unexpectedly.',
      severity: 'High',
      type: 'danger',
    },
    {
      title: 'Unusual Network Traffic',
      description: 'A sample increase in network traffic was detected.',
      severity: 'Low',
      type: 'info',
    },
  ]

  return (
    <div className="anomalies-page">
      <header className="anomalies-header">
        <div>
          <h1>Anomaly Detection</h1>
          <p>Identify unusual behaviour in your infrastructure</p>
        </div>
        <span className="anomalies-demo">Demo Mode</span>
      </header>

      <section className="anomaly-summary">
        <div className="anomaly-summary-card">
          <p>Total Anomalies</p>
          <h2>3</h2>
        </div>

        <div className="anomaly-summary-card">
          <p>High Severity</p>
          <h2 className="high-number">1</h2>
        </div>

        <div className="anomaly-summary-card">
          <p>Medium Severity</p>
          <h2 className="medium-number">1</h2>
        </div>

        <div className="anomaly-summary-card">
          <p>Low Severity</p>
          <h2 className="low-number">1</h2>
        </div>
      </section>

      <section className="anomaly-list-panel">
        <h2>Detected Anomalies</h2>
        <p className="anomaly-subtitle">
          Sample alerts generated for demonstration
        </p>

        {alerts.map((alert, index) => (
          <div className="anomaly-row" key={index}>
            <div className={`alert-symbol ${alert.type}`}>
              !
            </div>

            <div className="alert-details">
              <h3>{alert.title}</h3>
              <p>{alert.description}</p>
            </div>

            <span className={`alert-severity ${alert.type}`}>
              {alert.severity}
            </span>
          </div>
        ))}
      </section>

      <div className="anomalies-note">
        These anomalies are sample data and are not connected to the detection engine.
      </div>
    </div>
  )
}

export default Anomalies
