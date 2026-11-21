
import './Incidents.css'

function Incidents() {
  const incidents = [
    {
      id: 'INC-101',
      title: 'High CPU Utilization',
      description: 'CPU usage exceeded the sample warning threshold.',
      severity: 'High',
      status: 'Open',
    },
    {
      id: 'INC-102',
      title: 'Memory Pressure',
      description: 'Memory usage increased above the usual level.',
      severity: 'Medium',
      status: 'Investigating',
    },
    {
      id: 'INC-103',
      title: 'Network Latency',
      description: 'Sample network response delay was detected.',
      severity: 'Low',
      status: 'Resolved',
    },
  ]

  return (
    <div className="incidents-page">
      <header className="incidents-header">
        <div>
          <h1>Incident Management</h1>
          <p>Track, investigate and manage system incidents</p>
        </div>
        <span className="incidents-demo">Demo Mode</span>
      </header>

      <section className="incident-summary">
        <div className="incident-card">
          <p>Total Incidents</p>
          <h2>3</h2>
        </div>

        <div className="incident-card">
          <p>Open</p>
          <h2 className="open-color">1</h2>
        </div>

        <div className="incident-card">
          <p>Investigating</p>
          <h2 className="investigating-color">1</h2>
        </div>

        <div className="incident-card">
          <p>Resolved</p>
          <h2 className="resolved-color">1</h2>
        </div>
      </section>

      <section className="incidents-table-panel">
        <h2>Recent Incidents</h2>
        <p className="incidents-subtitle">
          Sample incident records
        </p>

        <div className="incident-table-wrapper">
          <table className="incident-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Incident</th>
                <th>Severity</th>
                <th>Status</th>
              </tr>
            </thead>

            <tbody>
              {incidents.map((incident) => (
                <tr key={incident.id}>
                  <td>{incident.id}</td>

                  <td>
                    <strong>{incident.title}</strong>
                    <p>{incident.description}</p>
                  </td>

                  <td>
                    <span className={`incident-severity ${incident.severity.toLowerCase()}`}>
                      {incident.severity}
                    </span>
                  </td>

                  <td>
                    <span className={`incident-status ${incident.status.toLowerCase()}`}>
                      {incident.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <div className="incidents-note">
        These incidents are sample records and are not connected to the backend.
      </div>
    </div>
  )
}

export default Incidents
