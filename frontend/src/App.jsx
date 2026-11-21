
import { useEffect, useState } from 'react'
import './App.css'
import SystemMetrics from './SystemMetrics.jsx'
import Anomalies from './Anomalies.jsx'
import Incidents from './Incidents.jsx'
import Recommendations from './Recommendations.jsx'

function MiniChart({ title, value, color, data }) {
  const points = data.map((point, index) => {
    const x = (index / (data.length - 1)) * 100
    const y = 100 - point
    return `${x},${y}`
  }).join(' ')

  return (
    <div className="chart-card">
      <div className="chart-heading">
        <div>
          <p>{title}</p>
          <h2>{value}%</h2>
        </div>
        <span className="demo-label">DEMO</span>
      </div>

      <svg className="chart" viewBox="0 0 100 100" preserveAspectRatio="none">
        <polyline
          points={points}
          fill="none"
          stroke={color}
          strokeWidth="2.5"
          vectorEffect="non-scaling-stroke"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>

      <p className="chart-caption">Sample performance trend</p>
    </div>
  )
}

function DashboardHome() {
  const [chartStep, setChartStep] = useState(0)

  useEffect(() => {
    const timer = setInterval(() => {
      setChartStep((previous) => previous + 1)
    }, 2000)

    return () => clearInterval(timer)
  }, [])

  const cpuData = [35, 45, 40, 55, 48, 62, 42, 50, 42]
  const memoryData = [55, 60, 58, 65, 62, 72, 68, 70, 68]

  const rotateData = (data) => {
    const shift = chartStep % data.length
    return [...data.slice(shift), ...data.slice(0, shift)]
  }

  return (
    <main className="main-content">
      <header className="topbar">
        <div>
          <h1>Dashboard</h1>
          <p>Monitor your system performance</p>
        </div>
        <span className="status">● Demo Mode</span>
      </header>

      <section className="welcome">
        <h2>System Overview</h2>
        <p>Here is the current overview of your infrastructure.</p>
      </section>

      <section className="metrics">
        <div className="metric-card">
          <p>CPU Usage</p>
          <h2>42%</h2>
          <span>Normal</span>
        </div>

        <div className="metric-card">
          <p>Memory Usage</p>
          <h2>68%</h2>
          <span>Normal</span>
        </div>

        <div className="metric-card">
          <p>Disk Usage</p>
          <h2>54%</h2>
          <span>Normal</span>
        </div>

        <div className="metric-card">
          <p>Network Usage</p>
          <h2>24 MB/s</h2>
          <span>Active</span>
        </div>
      </section>

      <section className="charts-section">
        <div className="section-heading">
          <h2>Performance Trends</h2>
          <span>Live animation · Sample data</span>
        </div>

        <div className="charts-grid">
          <MiniChart
            title="CPU Usage"
            value={42}
            color="#3b82f6"
            data={rotateData(cpuData)}
          />

          <MiniChart
            title="Memory Usage"
            value={68}
            color="#8b5cf6"
            data={rotateData(memoryData)}
          />
        </div>
      </section>

      <section className="anomaly-panel">
        <div className="section-heading">
          <h2>Detected Anomalies</h2>
          <span className="demo-label">DEMO DATA</span>
        </div>

        <div className="anomaly-item">
          <span className="anomaly-icon warning">!</span>
          <div>
            <h3>High CPU activity</h3>
            <p>Sample alert: CPU usage briefly increased.</p>
          </div>
          <span className="severity medium">Medium</span>
        </div>

        <div className="anomaly-item">
          <span className="anomaly-icon info">i</span>
          <div>
            <h3>Memory usage increased</h3>
            <p>Sample alert: Memory usage is above its usual level.</p>
          </div>
          <span className="severity low">Low</span>
        </div>
      </section>

      <section className="bottom-section">
        <div className="panel">
          <h2>System Health</h2>
          <div className="health">Healthy</div>
          <p>All monitored systems are operating normally in this demo.</p>
        </div>

        <div className="panel">
          <h2>Recent Activity</h2>
          <p>✓ Dashboard initialized</p>
          <p>✓ Demo metrics loaded</p>
          <p>✓ Monitoring interface ready</p>
        </div>
      </section>

      <p className="footer">
        Smart Observability Platform | Sample data for demonstration
      </p>
    </main>
  )
}

function App() {
  const [activePage, setActivePage] = useState('Dashboard')

  const pages = {
    Dashboard: <DashboardHome />,
    'System Metrics': <SystemMetrics />,
    Anomalies: <Anomalies />,
    Incidents: <Incidents />,
    Recommendations: <Recommendations />,
  }

  const menuItems = [
    'Dashboard',
    'System Metrics',
    'Anomalies',
    'Incidents',
    'Recommendations',
  ]

  return (
    <div className="dashboard">
      <aside className="sidebar">
        <h2>SmartObserve</h2>
        <p className="menu-title">MAIN MENU</p>

        {menuItems.map((item) => (
          <p
            key={item}
            className={activePage === item ? 'active' : ''}
            onClick={() => setActivePage(item)}
          >
            {item}
          </p>
        ))}
      </aside>

      {pages[activePage]}
    </div>
  )
}

export default App
