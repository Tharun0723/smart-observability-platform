
import './SystemMetrics.css'

function SystemMetrics() {
  return (
    <div className="metrics-page">
      <header className="metrics-header">
        <div>
          <h1>System Metrics</h1>
          <p>Detailed infrastructure performance monitoring</p>
        </div>
        <span className="metrics-demo-badge">Demo Mode</span>
      </header>

      <section className="metrics-summary">
        <div className="metrics-box">
          <p>CPU Usage</p>
          <h2>42%</h2>
          <span>Normal</span>
        </div>

        <div className="metrics-box">
          <p>Memory Usage</p>
          <h2>68%</h2>
          <span>Normal</span>
        </div>

        <div className="metrics-box">
          <p>Disk Usage</p>
          <h2>54%</h2>
          <span>Normal</span>
        </div>

        <div className="metrics-box">
          <p>Network</p>
          <h2>24 MB/s</h2>
          <span>Active</span>
        </div>
      </section>

      <section className="metrics-details">
        <div className="metrics-panel">
          <h2>CPU Performance</h2>
          <p>Current utilization: 42%</p>
          <div className="metrics-progress">
            <div className="metrics-progress-fill cpu-fill"></div>
          </div>
          <p className="metrics-description">
            Sample CPU usage across the monitored system.
          </p>
        </div>

        <div className="metrics-panel">
          <h2>Memory Performance</h2>
          <p>Current utilization: 68%</p>
          <div className="metrics-progress">
            <div className="metrics-progress-fill memory-fill"></div>
          </div>
          <p className="metrics-description">
            Sample memory consumption.
          </p>
        </div>

        <div className="metrics-panel">
          <h2>Disk Performance</h2>
          <p>Current utilization: 54%</p>
          <div className="metrics-progress">
            <div className="metrics-progress-fill disk-fill"></div>
          </div>
          <p className="metrics-description">
            Sample disk space utilization.
          </p>
        </div>

        <div className="metrics-panel">
          <h2>Network Performance</h2>
          <p>Current activity: 24 MB/s</p>
          <div className="metrics-progress">
            <div className="metrics-progress-fill network-fill"></div>
          </div>
          <p className="metrics-description">
            Sample network activity indicator.
          </p>
        </div>
      </section>

      <div className="metrics-note">
        These values are sample data and are not connected to the backend yet.
      </div>
    </div>
  )
}

export default SystemMetrics
