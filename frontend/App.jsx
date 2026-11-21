import { useCallback, useEffect, useMemo, useState } from 'react'
import { Activity, AlertTriangle, ArrowDownRight, ArrowUpRight, Bell, CheckCircle2, ChevronRight, Clock3, Cpu, Database, Download, HardDrive, LayoutDashboard, LockKeyhole, Menu, Monitor, Network, RefreshCw, Server, ShieldAlert, ShieldCheck, Wifi, X, BrainCircuit } from 'lucide-react'
import { Area, AreaChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

const TENANT = import.meta.env.VITE_TENANT_ID || '1'
const NAV = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'metrics', label: 'Infrastructure Metrics', icon: Activity },
  { id: 'events', label: 'Events & Security', icon: ShieldCheck },
  { id: 'incidents', label: 'AI Incidents', icon: BrainCircuit },
  { id: 'security', label: 'Security & Egress', icon: LockKeyhole },
]
const names = { cpu_usage_percent: 'CPU', memory_usage_percent: 'Memory', disk_usage_percent: 'Disk', network_bytes_sent: 'Network sent', network_bytes_received: 'Network received' }
const fmt = (v) => { if (!v) return '—'; const d = new Date(v); return Number.isNaN(d.getTime()) ? '—' : d.toLocaleString() }
const clock = (v) => v ? new Date(v).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : '—'

function Pill({ value }) { const key = String(value || 'unknown').toLowerCase(); return <span className={`pill ${key}`}>{value || 'Unknown'}</span> }
function Stat({ label, value, note, icon: Icon, tone = 'blue' }) { return <div className="stat"><div className={`stat-icon ${tone}`}><Icon size={18}/></div><div className="stat-label">{label}</div><div className="stat-value">{value ?? '—'}</div><div className="stat-note">{note}</div></div> }
function Empty({ title, detail }) { return <div className="empty"><Database size={25}/><b>{title}</b><span>{detail}</span></div> }

export default function App() {
  const [section, setSection] = useState('overview')
  const [menu, setMenu] = useState(false)
  const [busy, setBusy] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [updated, setUpdated] = useState(null)
  const [dashboard, setDashboard] = useState(null)
  const [metrics, setMetrics] = useState([])
  const [events, setEvents] = useState([])
  const [incidents, setIncidents] = useState([])
  const [incidentSummary, setIncidentSummary] = useState(null)

  const request = useCallback(async (path) => {
    const response = await fetch(`/api${path}`)
    if (!response.ok) throw new Error(`API ${response.status}: ${(await response.text()).slice(0, 160)}`)
    return response.json()
  }, [])

  const refresh = useCallback(async (quiet = false) => {
    if (quiet) setBusy(true); else setLoading(true)
    setError('')
    const base = `/v1/admin/tenants/${TENANT}`
    const paths = [`${base}/dashboard`, `${base}/metrics?limit=100`, `${base}/events?limit=50`, `${base}/incidents?limit=50`, `${base}/incidents/summary`]
    const results = await Promise.allSettled(paths.map(request))
    if (results[0].status === 'fulfilled') setDashboard(results[0].value)
    if (results[1].status === 'fulfilled') setMetrics(results[1].value)
    if (results[2].status === 'fulfilled') setEvents(results[2].value)
    if (results[3].status === 'fulfilled') setIncidents(results[3].value)
    if (results[4].status === 'fulfilled') setIncidentSummary(results[4].value)
    const failed = results.filter(r => r.status === 'rejected')
    if (failed.length === results.length) setError(failed[0].reason?.message || 'Cannot reach CICADA backend')
    else if (failed.length) console.warn('Some dashboard endpoints failed', failed)
    setUpdated(new Date()); setBusy(false); setLoading(false)
  }, [request])

  useEffect(() => { refresh(); const timer = setInterval(() => refresh(true), 10000); return () => clearInterval(timer) }, [refresh])

  const latest = useMemo(() => Object.fromEntries((dashboard?.latest_metrics || []).map(m => [m.metric_name, m])), [dashboard])
  const chart = useMemo(() => {
    const rows = new Map()
    for (const m of [...metrics].reverse()) {
      if (!m.recorded_at) continue
      if (!rows.has(m.recorded_at)) rows.set(m.recorded_at, { time: clock(m.recorded_at), stamp: new Date(m.recorded_at).getTime() })
      const row = rows.get(m.recorded_at)
      if (m.metric_name === 'cpu_usage_percent') row.cpu = m.value
      if (m.metric_name === 'memory_usage_percent') row.memory = m.value
      if (m.metric_name === 'disk_usage_percent') row.disk = m.value
    }
    return [...rows.values()].sort((a,b) => a.stamp-b.stamp).slice(-40)
  }, [metrics])
  const health = dashboard?.critical_devices ? 'Critical' : dashboard?.warning_devices ? 'Warning' : dashboard?.offline_devices ? 'Offline' : 'Healthy'
  const title = NAV.find(n => n.id === section)?.label || 'Overview'

  function exportCsv() {
    const csv = ['metric_name,value,unit,recorded_at,collector_id', ...metrics.map(m => [m.metric_name,m.value,m.unit,m.recorded_at,m.collector_id].map(v => `"${String(v ?? '').replaceAll('"','""')}"`).join(','))].join('\n')
    const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv' })); const a = document.createElement('a'); a.href = url; a.download = `cicada-tenant-${TENANT}-metrics.csv`; a.click(); URL.revokeObjectURL(url)
  }

  const metricChart = (height = 270) => chart.length ? <ResponsiveContainer width="100%" height={height}><AreaChart data={chart}><CartesianGrid stroke="#26364b" strokeDasharray="3 4" vertical={false}/><XAxis dataKey="time" tick={{fill:'#8495ad',fontSize:10}} axisLine={false} tickLine={false}/><YAxis domain={[0,100]} tick={{fill:'#8495ad',fontSize:10}} axisLine={false} tickLine={false}/><Tooltip contentStyle={{background:'#111c2d',border:'1px solid #30415a',borderRadius:9,color:'#edf3fd'}}/><Legend/><Area type="monotone" dataKey="cpu" name="CPU %" stroke="#65a5ff" fill="#65a5ff" fillOpacity={.09} strokeWidth={2} connectNulls/><Area type="monotone" dataKey="memory" name="Memory %" stroke="#36cda0" fill="#36cda0" fillOpacity={.08} strokeWidth={2} connectNulls/><Area type="monotone" dataKey="disk" name="Disk %" stroke="#f2b65d" fill="#f2b65d" fillOpacity={.05} strokeWidth={2} connectNulls/></AreaChart></ResponsiveContainer> : <Empty title="Waiting for metric history" detail="Start the collector to populate performance charts." />

  function overview() { return <>
    <div className="welcome"><div><div className="eyebrow">INFRASTRUCTURE OVERVIEW</div><h2>Your infrastructure at a glance</h2><p>Live resource and operational health for tenant {TENANT}.</p></div><div className={`health ${health.toLowerCase()}`}><i/>{health} infrastructure</div></div>
    <div className="stats"><Stat label="Total devices" value={dashboard?.total_devices} note={`${dashboard?.active_collectors ?? 0} active collectors`} icon={Monitor}/><Stat label="Healthy devices" value={dashboard?.healthy_devices} note="Within configured thresholds" icon={CheckCircle2} tone="green"/><Stat label="Warning devices" value={dashboard?.warning_devices} note="Need operator attention" icon={AlertTriangle} tone="amber"/><Stat label="Critical devices" value={dashboard?.critical_devices} note={`${dashboard?.offline_devices ?? 0} offline`} icon={ShieldAlert} tone="red"/></div>
    <div className="columns"><section className="panel"><div className="panel-head"><div><h3>Infrastructure performance</h3><p>CPU, memory and disk utilization</p></div><span className="live"><i/>LIVE</span></div>{metricChart()}</section><section className="panel"><div className="panel-head"><div><h3>Latest readings</h3><p>Most recent collector values</p></div></div>{[['cpu_usage_percent','CPU',Cpu],['memory_usage_percent','Memory',Activity],['disk_usage_percent','Disk',HardDrive]].map(([key,label,Icon]) => <div className="reading" key={key}><div><span><Icon size={15}/> {label}</span><b>{latest[key] ? `${latest[key].value}%` : '—'}</b></div><div className="track"><i className={Number(latest[key]?.value)>=90?'danger':Number(latest[key]?.value)>=75?'warn':''} style={{width:`${Math.min(100,Math.max(0,Number(latest[key]?.value)||0))}%`}}/></div></div>)}<div className="collector"><Server size={18}/><div><b>Collector #1</b><span>Tenant {TENANT}</span></div><Pill value={dashboard?.active_collectors ? 'Online' : 'Offline'}/></div></section></div>
    <div className="columns"><section className="panel"><div className="panel-head"><div><h3>Recent incidents</h3><p>AI-detected infrastructure issues</p></div><button className="link" onClick={()=>setSection('incidents')}>View all ›</button></div>{incidents.length ? incidents.slice(0,4).map(i=><div className="listrow" key={i.id}><div><b>{i.title}</b><span>{fmt(i.last_seen_at)}</span></div><Pill value={i.severity}/></div>) : <Empty title="No incidents yet" detail="Live AIOps-to-backend delivery is the next integration step."/>}</section><section className="panel"><div className="panel-head"><div><h3>Event activity</h3><p>Security and application events</p></div><button className="link" onClick={()=>setSection('events')}>View all ›</button></div><div className="eventcounts"><div><b>{dashboard?.total_events ?? 0}</b><span>Total events</span></div><div><b className="redtext">{dashboard?.critical_events ?? 0}</b><span>Critical events</span></div></div>{events.length ? events.slice(0,3).map(e=><div className="listrow" key={e.id}><div><b>{e.title || e.event_type}</b><span>{fmt(e.occurred_at)}</span></div><Pill value={e.severity}/></div>) : <Empty title="No events received" detail="Collector event ingestion has not been connected yet."/>}</section></div>
  </> }

  function metricsPage() { return <><div className="intro"><div className="eyebrow">TELEMETRY</div><h2>Infrastructure metrics</h2><p>Historical resource utilization from the local collector.</p></div><div className="stats"><Stat label="CPU usage" value={latest.cpu_usage_percent?.value ?? '—'} note="Latest reading (%)" icon={Cpu}/><Stat label="Memory usage" value={latest.memory_usage_percent?.value ?? '—'} note="Latest reading (%)" icon={Activity} tone="green"/><Stat label="Disk usage" value={latest.disk_usage_percent?.value ?? '—'} note="Latest reading (%)" icon={HardDrive} tone="amber"/><Stat label="Metric records" value={metrics.length} note="Records loaded" icon={Database}/></div><section className="panel"><div className="panel-head"><div><h3>Resource utilization history</h3><p>Recent percentage readings</p></div><button className="outline" onClick={exportCsv}><Download size={14}/> Export CSV</button></div>{metricChart(320)}</section><section className="panel tablepanel"><h3>Recent telemetry records</h3><div className="scroll"><table><thead><tr><th>Metric</th><th>Value</th><th>Unit</th><th>Collector</th><th>Recorded at</th></tr></thead><tbody>{metrics.slice(0,40).map((m,i)=><tr key={m.id ?? i}><td>{names[m.metric_name] || m.metric_name}</td><td>{m.value}</td><td>{m.unit}</td><td>#{m.collector_id}</td><td>{fmt(m.recorded_at)}</td></tr>)}</tbody></table></div></section></> }

  function eventsPage() { return <><div className="intro"><div className="eyebrow">OBSERVABILITY & SECURITY</div><h2>Events & security</h2><p>Review events received from registered collectors.</p></div><div className="stats"><Stat label="Total events" value={dashboard?.total_events ?? 0} note="Received by backend" icon={Bell}/><Stat label="Critical events" value={dashboard?.critical_events ?? 0} note="Immediate review" icon={ShieldAlert} tone="red"/><Stat label="Active collectors" value={dashboard?.active_collectors ?? 0} note="Authenticated collectors" icon={Wifi} tone="green"/><Stat label="Inactive collectors" value={dashboard?.inactive_collectors ?? 0} note="Not active" icon={Monitor} tone="amber"/></div><section className="panel tablepanel"><h3>Event log</h3><div className="scroll"><table><thead><tr><th>Event</th><th>Type</th><th>Severity</th><th>Source</th><th>Occurred at</th></tr></thead><tbody>{events.map((e,i)=><tr key={e.id ?? i}><td><b>{e.title || 'Untitled event'}</b><small>{e.summary || ''}</small></td><td>{e.event_type}</td><td><Pill value={e.severity}/></td><td>{e.source || '—'}</td><td>{fmt(e.occurred_at)}</td></tr>)}</tbody></table></div>{!events.length && <Empty title="No events received" detail="Application, system and security events will appear here when ingested."/>}</section></> }

  function incidentsPage() { return <><div className="intro"><div className="eyebrow">INTELLIGENT OPERATIONS</div><h2>AI incidents</h2><p>Correlated anomalies, severity and explainable remediation guidance.</p></div><div className="stats"><Stat label="Total incidents" value={incidentSummary?.total_incidents ?? incidents.length} note="Recorded incidents" icon={BrainCircuit}/><Stat label="Repeated incidents" value={incidentSummary?.repeated_incidents ?? 0} note="Observed more than once" icon={RefreshCw} tone="amber"/><Stat label="Correlated incidents" value={incidentSummary?.correlated_incidents ?? 0} note="Related signals" icon={Network}/><Stat label="Open incidents" value={incidentSummary?.by_status?.find(x=>x.status==='open')?.count ?? '—'} note="Awaiting investigation" icon={AlertTriangle} tone="red"/></div>{incidents.length ? <div className="incidentgrid">{incidents.map((i,n)=><article className="panel incident" key={i.id ?? n}><div className="panel-head"><BrainCircuit size={19}/><Pill value={i.severity}/></div><h3>{i.title}</h3><p>{i.description || 'No additional description provided.'}</p><small>Priority: {i.priority} · Status: {i.status}</small>{i.recommendation && <div className="recommendation"><b>Recommendation</b><p>{i.recommendation}</p></div>}<small>Last seen {fmt(i.last_seen_at)} · {i.occurrence_count || 1} occurrence(s)</small></article>)}</div> : <section className="panel"><Empty title="No AI incidents received yet" detail="The engine has passed its standalone test. Live history analysis and incident delivery are still to be connected."/></section>}</> }

  const payload = { metrics: (dashboard?.latest_metrics || []).map(({metric_name,value,unit,recorded_at})=>({metric_name,value,unit,recorded_at})) }
  function securityPage() { return <><div className="intro"><div className="eyebrow">PRIVACY-FIRST ARCHITECTURE</div><h2>Security & egress proof</h2><p>Inspect approved telemetry metadata held by the central backend.</p></div><div className="securitybanner"><ShieldCheck size={23}/><div><b>Metadata-only telemetry design</b><span>Collector maps approved numeric measurements. Raw logs and credentials should remain local.</span></div></div><div className="columns"><section className="panel"><h3>Approved metric fields</h3>{Object.entries(names).map(([key,label])=><div className="allowrow" key={key}><CheckCircle2 size={16}/><div><b>{label}</b><code>{key}</code></div><span>Allowed</span></div>)}</section><section className="panel"><h3>Metadata payload preview</h3><p className="subtext">Reconstructed from the latest backend records</p><pre className="json">{JSON.stringify(payload,null,2)}</pre><p className="disclaimer">This is a reconstructed preview, not a packet capture or exact copy of the original HTTP request. A collector-side egress audit log is still required for full proof.</p></section></div><section className="panel flow"><h3>Telemetry trust boundary</h3><div>Local collector　→　Privacy filter　→　Authenticated transport　→　CICADA backend</div></section></> }

  return <div className="shell"><aside className={`sidebar ${menu?'open':''}`}><div className="brand"><div className="brandmark"><Activity size={21}/></div><div><b>CICADA</b><small>SMART OBSERVABILITY</small></div><button className="closemenu" onClick={()=>setMenu(false)}><X/></button></div><div className="sidecaption">WORKSPACE</div><div className="tenant"><span>C</span><div><b>CICADA Demo</b><small>Tenant #{TENANT}</small></div><ChevronRight size={15}/></div><div className="sidecaption">MONITORING</div><nav>{NAV.map(n=>{const Icon=n.icon;return <button key={n.id} className={section===n.id?'selected':''} onClick={()=>{setSection(n.id);setMenu(false)}}><Icon size={18}/>{n.label}</button>})}</nav><div className="sidebottom"><div className="privacymini"><ShieldCheck size={18}/><div><b>Privacy-first mode</b><small>Metadata focused</small></div><i/></div><div className="operator"><span>OP</span><div><b>Operator</b><small>Administrator view</small></div></div><small className="version">CICADA · Local development</small></div></aside>{menu&&<div className="backdrop" onClick={()=>setMenu(false)}/>}<main><header className="topbar"><div className="crumb"><button className="menubtn" onClick={()=>setMenu(true)}><Menu/></button>CICADA <ChevronRight size={14}/> <b>{title}</b></div><div className="topright"><span className="connected"><i/> Backend connected</span><button className="refreshicon" onClick={()=>refresh(true)} title="Refresh"><RefreshCw size={17}/></button><span className="avatar">OP</span></div></header><div className="content"><div className="pagehead"><div><h1>{title}</h1><small>Monitoring workspace / Tenant #{TENANT}</small></div><div className="pageactions"><span><Clock3 size={13}/> Updated {clock(updated)}</span><button className="outline" disabled={busy} onClick={()=>refresh(true)}><RefreshCw size={14}/> Refresh</button></div></div>{error&&<div className="error"><AlertTriangle size={17}/>{error}<button onClick={()=>refresh(true)}>Retry</button></div>}{loading&&!dashboard?<div className="loading"><RefreshCw className="spin"/><b>Connecting to CICADA backend…</b></div>:<>{section==='overview'&&overview()}{section==='metrics'&&metricsPage()}{section==='events'&&eventsPage()}{section==='incidents'&&incidentsPage()}{section==='security'&&securityPage()}</>}<footer>© 2026 CICADA Smart Observability Platform <span><i/> Local backend · Auto-refresh 10s</span></footer></div></main></div>
}
