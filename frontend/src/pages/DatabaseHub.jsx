import { useState, useEffect } from 'react'
import {
  Database,
  Server,
  RefreshCw,
  HardDrive,
  Users,
  GitBranch,
  Cpu,
  CheckCircle,
  AlertCircle,
  Clock,
  Layers,
  ArrowRight,
  Leaf,
  Link,
  UploadCloud,
} from 'lucide-react'
import { databaseAPI } from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorAlert from '../components/ErrorAlert'

export default function DatabaseHub() {
  const [activeTab, setActiveTab] = useState('overview') // 'overview' | 'mongodb' | 'datasets' | 'customers' | 'runs' | 'predictions' | 'settings'
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [connecting, setConnecting] = useState(false)
  const [successMsg, setSuccessMsg] = useState('')
  const [status, setStatus] = useState(null)
  const [datasets, setDatasets] = useState([])
  const [customers, setCustomers] = useState([])
  const [runs, setRuns] = useState([])
  const [predictions, setPredictions] = useState([])

  // MongoDB state
  const [mongoStatus, setMongoStatus] = useState(null)
  const [mongoUri, setMongoUri] = useState('mongodb://localhost:27017')
  const [mongoDbName, setMongoDbName] = useState('customer_segmentation_db')
  const [mongoConnecting, setMongoConnecting] = useState(false)
  const [mongoSyncing, setMongoSyncing] = useState(false)
  const [mongoPredictions, setMongoPredictions] = useState([])

  const handleAutoConnect = async () => {
    setConnecting(true)
    setError('')
    setSuccessMsg('')
    try {
      const res = await databaseAPI.autoConnect()
      setSuccessMsg(res.data?.message || 'Database auto-connected successfully!')
      await fetchAllData()
    } catch (err) {
      setError('Auto-connect failed: ' + (err.message || 'Unknown error'))
    } finally {
      setConnecting(false)
    }
  }

  const handleConnectMongo = async (e) => {
    if (e) e.preventDefault()
    setMongoConnecting(true)
    setError('')
    setSuccessMsg('')
    try {
      const res = await databaseAPI.connectMongo({ uri: mongoUri, db_name: mongoDbName })
      if (res.data?.success) {
        setSuccessMsg(res.data?.message || 'Connected to MongoDB successfully!')
        await fetchAllData()
      } else {
        setError(res.data?.message || 'Could not connect to MongoDB.')
      }
    } catch (err) {
      setError('MongoDB connection failed: ' + (err.message || 'Unknown error'))
    } finally {
      setMongoConnecting(false)
    }
  }

  const handleSyncToMongo = async () => {
    setMongoSyncing(true)
    setError('')
    setSuccessMsg('')
    try {
      const res = await databaseAPI.syncToMongo()
      if (res.data?.success) {
        const counts = res.data?.synced || {}
        setSuccessMsg(`Synced to MongoDB: ${counts.datasets || 0} datasets, ${counts.customers || 0} customers, ${counts.clustering_runs || 0} runs, ${counts.predictions || 0} predictions!`)
        await fetchAllData()
      } else {
        setError(res.data?.message || 'Failed to sync to MongoDB.')
      }
    } catch (err) {
      setError('Sync failed: ' + (err.message || 'Unknown error'))
    } finally {
      setMongoSyncing(false)
    }
  }

  const fetchAllData = async () => {
    setLoading(true)
    setError('')
    try {
      const [statusRes, datasetsRes, runsRes, predsRes, custsRes, mStatusRes, mPredsRes] = await Promise.all([
        databaseAPI.getStatus().catch(() => ({ data: { connected: false } })),
        databaseAPI.getDatasets(20).catch(() => ({ data: [] })),
        databaseAPI.getRuns(20).catch(() => ({ data: [] })),
        databaseAPI.getPredictions(50).catch(() => ({ data: [] })),
        databaseAPI.getCustomers(null, 50).catch(() => ({ data: [] })),
        databaseAPI.getMongoStatus().catch(() => ({ data: { connected: false } })),
        databaseAPI.getMongoPredictions(50).catch(() => ({ data: [] })),
      ])

      setStatus(statusRes.data || null)
      setDatasets(datasetsRes.data || [])
      setRuns(runsRes.data || [])
      setPredictions(predsRes.data || [])
      setCustomers(custsRes.data || [])
      setMongoStatus(mStatusRes.data || null)
      setMongoPredictions(mPredsRes.data || [])
    } catch (err) {
      setError('Failed to load database records: ' + (err.message || 'Unknown error'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAllData()
  }, [])

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header Section */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 bg-gradient-to-r from-slate-900 via-blue-950 to-slate-900 p-6 rounded-2xl text-white shadow-lg border border-blue-900/50">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="p-2 bg-blue-600/30 rounded-lg border border-blue-400/30 text-blue-400">
              <Database size={22} />
            </span>
            <h1 className="text-2xl font-bold text-white tracking-tight">Database Management Hub</h1>
            <span className="flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 ml-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              SQL: {status?.engine?.toLowerCase().includes('mysql') ? 'MySQL' : 'SQLite'}
            </span>
            <span className={`flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full border ${
              mongoStatus?.connected
                ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                : 'bg-amber-500/20 text-amber-300 border-amber-500/30'
            }`}>
              <span className={`w-2 h-2 rounded-full ${mongoStatus?.connected ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
              MongoDB: {mongoStatus?.connected ? 'Connected' : 'Offline'}
            </span>
          </div>
          <p className="text-sm text-slate-300">
            Multi-database system supporting MySQL/SQLite (Relational SQL) and MongoDB (NoSQL Document Store).
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={handleAutoConnect}
            disabled={connecting || loading}
            className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-xl text-sm font-semibold transition-all shadow-sm hover:shadow active:scale-95 disabled:opacity-50"
          >
            <CheckCircle size={15} className={connecting ? 'animate-spin' : ''} />
            {connecting ? 'Auto-Connecting...' : 'Auto-Connect SQL'}
          </button>
          <button
            onClick={() => setActiveTab('mongodb')}
            className="flex items-center gap-2 bg-green-700 hover:bg-green-600 text-white px-4 py-2 rounded-xl text-sm font-semibold transition-all shadow-sm hover:shadow active:scale-95"
          >
            <Leaf size={15} />
            MongoDB Setup
          </button>
          <button
            onClick={fetchAllData}
            disabled={loading}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-xl text-sm font-medium transition-all shadow-sm hover:shadow active:scale-95 disabled:opacity-50"
          >
            <RefreshCw size={15} className={loading ? 'animate-spin' : ''} />
            Refresh Data
          </button>
        </div>
      </div>

      {successMsg && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl flex items-center justify-between text-sm">
          <div className="flex items-center gap-2">
            <CheckCircle size={18} className="text-emerald-600" />
            <span className="font-medium">{successMsg}</span>
          </div>
          <button onClick={() => setSuccessMsg('')} className="text-emerald-600 hover:text-emerald-900 font-bold text-xs">
            ✕
          </button>
        </div>
      )}

      {error && <ErrorAlert message={error} onDismiss={() => setError('')} />}

      {/* Database Connection Summary Banner */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card border-l-4 border-l-blue-500 flex items-center justify-between p-5">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-gray-500">SQL Engine</p>
            <h3 className="text-xl font-bold text-gray-800 mt-1">
              {status?.engine?.toLowerCase().includes('mysql') ? 'MySQL 8.0' : (status?.engine || 'SQLite 3')}
            </h3>
            <p className="text-xs text-gray-400 mt-0.5 font-mono">
              {status?.engine?.toLowerCase().includes('mysql') ? 'customer_segmentation (3306)' : 'customer_segmentation.db'}
            </p>
          </div>
          <div className="w-12 h-12 bg-blue-50 rounded-xl flex items-center justify-center text-blue-600">
            <HardDrive size={24} />
          </div>
        </div>

        <div className={`card border-l-4 flex items-center justify-between p-5 ${
          mongoStatus?.connected ? 'border-l-green-500' : 'border-l-amber-500'
        }`}>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-gray-500">MongoDB (NoSQL)</p>
            <h3 className="text-xl font-bold text-gray-800 mt-1">
              {mongoStatus?.connected ? 'Connected' : 'Offline / Standby'}
            </h3>
            <p className="text-xs text-gray-400 mt-0.5 font-mono truncate max-w-[150px]">
              {mongoStatus?.db_name || 'customer_segmentation_db'}
            </p>
          </div>
          <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
            mongoStatus?.connected ? 'bg-green-50 text-green-600' : 'bg-amber-50 text-amber-600'
          }`}>
            <Leaf size={24} />
          </div>
        </div>

        <div className="card border-l-4 border-l-indigo-500 flex items-center justify-between p-5">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-gray-500">Customer Records</p>
            <h3 className="text-2xl font-bold text-gray-800 mt-1">
              {status?.counts?.customer_records ?? customers.length}
            </h3>
            <p className="text-xs text-indigo-600 font-medium mt-0.5">SQL Database rows</p>
          </div>
          <div className="w-12 h-12 bg-indigo-50 rounded-xl flex items-center justify-center text-indigo-600">
            <Users size={24} />
          </div>
        </div>

        <div className="card border-l-4 border-l-purple-500 flex items-center justify-between p-5">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-gray-500">Predictions &amp; Runs</p>
            <h3 className="text-2xl font-bold text-gray-800 mt-1">
              {(status?.counts?.predictions ?? 0) + (status?.counts?.clustering_runs ?? 0)}
            </h3>
            <p className="text-xs text-purple-600 font-medium mt-0.5">
              {status?.counts?.clustering_runs ?? runs.length} runs | {status?.counts?.predictions ?? predictions.length} preds
            </p>
          </div>
          <div className="w-12 h-12 bg-purple-50 rounded-xl flex items-center justify-center text-purple-600">
            <Cpu size={24} />
          </div>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="flex border-b border-gray-200 bg-white rounded-t-xl px-4 pt-3 gap-2 overflow-x-auto shadow-sm">
        {[
          { id: 'overview', label: 'Database Status', icon: Server, count: null },
          { id: 'mongodb', label: '🍃 MongoDB (NoSQL)', icon: Leaf, count: mongoStatus?.counts?.predictions ?? null },
          { id: 'datasets', label: 'Stored Datasets', icon: Layers, count: datasets.length },
          { id: 'customers', label: 'Customer Rows', icon: Users, count: customers.length },
          { id: 'runs', label: 'Clustering Runs', icon: GitBranch, count: runs.length },
          { id: 'predictions', label: 'Prediction Logs', icon: Cpu, count: predictions.length },
          { id: 'settings', label: 'Connection Info', icon: HardDrive, count: null },
        ].map((tab) => {
          const Icon = tab.icon
          const active = activeTab === tab.id
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 py-3 px-4 border-b-2 font-medium text-sm transition-all whitespace-nowrap ${
                active
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-800 hover:border-gray-300'
              }`}
            >
              <Icon size={16} />
              <span>{tab.label}</span>
              {tab.count !== null && (
                <span
                  className={`text-xs px-2 py-0.5 rounded-full font-bold ${
                    active ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-600'
                  }`}
                >
                  {tab.count}
                </span>
              )}
            </button>
          )
        })}
      </div>

      {loading && <LoadingSpinner message="Fetching database records..." />}

      {/* Tab: MongoDB (NoSQL) */}
      {!loading && activeTab === 'mongodb' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* MongoDB Connection Panel */}
            <div className="lg:col-span-2 card space-y-5">
              <div className="flex items-center justify-between">
                <h2 className="section-title mb-0 flex items-center gap-2 text-green-800">
                  <Leaf size={20} className="text-green-600" />
                  MongoDB Connection &amp; Atlas Setup
                </h2>
                <span className={`text-xs px-3 py-1 rounded-full font-bold flex items-center gap-1.5 ${
                  mongoStatus?.connected
                    ? 'bg-green-100 text-green-800 border border-green-300'
                    : 'bg-amber-100 text-amber-800 border border-amber-300'
                }`}>
                  <span className={`w-2 h-2 rounded-full ${mongoStatus?.connected ? 'bg-green-600' : 'bg-amber-600'}`} />
                  {mongoStatus?.connected ? 'Connected' : 'Not Connected'}
                </span>
              </div>

              <p className="text-sm text-gray-600">
                You can connect to a <strong>Local MongoDB</strong> instance (`mongodb://localhost:27017`) or free <strong>MongoDB Atlas Cloud</strong> (`mongodb+srv://user:password@cluster.mongodb.net/...`).
              </p>

              <form onSubmit={handleConnectMongo} className="space-y-4 bg-gray-50 p-5 rounded-xl border border-gray-200">
                <div>
                  <label className="label font-semibold text-gray-700">MongoDB Connection URI:</label>
                  <input
                    type="text"
                    value={mongoUri}
                    onChange={(e) => setMongoUri(e.target.value)}
                    placeholder="mongodb://localhost:27017 or mongodb+srv://..."
                    className="input-field font-mono text-xs"
                    required
                  />
                  <p className="text-[11px] text-gray-400 mt-1">
                    Examples: <code className="bg-gray-200 px-1 rounded">mongodb://localhost:27017</code> or Cloud Atlas URI
                  </p>
                </div>

                <div>
                  <label className="label font-semibold text-gray-700">Database Name:</label>
                  <input
                    type="text"
                    value={mongoDbName}
                    onChange={(e) => setMongoDbName(e.target.value)}
                    placeholder="customer_segmentation_db"
                    className="input-field font-mono text-xs"
                    required
                  />
                </div>

                <div className="flex items-center gap-3 pt-2">
                  <button
                    type="submit"
                    disabled={mongoConnecting}
                    className="flex items-center gap-2 bg-green-700 hover:bg-green-600 text-white font-semibold px-5 py-2.5 rounded-lg text-sm transition-all disabled:opacity-50"
                  >
                    <Link size={16} />
                    {mongoConnecting ? 'Connecting to MongoDB...' : 'Connect MongoDB'}
                  </button>

                  <button
                    type="button"
                    onClick={handleSyncToMongo}
                    disabled={mongoSyncing || !mongoStatus?.connected}
                    className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold px-5 py-2.5 rounded-lg text-sm transition-all disabled:opacity-50"
                  >
                    <UploadCloud size={16} />
                    {mongoSyncing ? 'Syncing...' : '⚡ Sync SQL Data to MongoDB'}
                  </button>
                </div>
              </form>

              {/* Collections Status */}
              {mongoStatus?.connected && (
                <div className="pt-2 space-y-3">
                  <h3 className="text-sm font-bold text-gray-800">MongoDB Collections ({mongoStatus.db_name}):</h3>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div className="p-3 bg-green-50 rounded-xl border border-green-200 text-center">
                      <p className="text-xs text-green-700 font-medium">datasets</p>
                      <p className="text-lg font-bold text-green-900 mt-0.5">{mongoStatus.counts?.datasets || 0}</p>
                    </div>
                    <div className="p-3 bg-green-50 rounded-xl border border-green-200 text-center">
                      <p className="text-xs text-green-700 font-medium">customers</p>
                      <p className="text-lg font-bold text-green-900 mt-0.5">{mongoStatus.counts?.customers || 0}</p>
                    </div>
                    <div className="p-3 bg-green-50 rounded-xl border border-green-200 text-center">
                      <p className="text-xs text-green-700 font-medium">clustering_runs</p>
                      <p className="text-lg font-bold text-green-900 mt-0.5">{mongoStatus.counts?.clustering_runs || 0}</p>
                    </div>
                    <div className="p-3 bg-green-50 rounded-xl border border-green-200 text-center">
                      <p className="text-xs text-green-700 font-medium">predictions</p>
                      <p className="text-lg font-bold text-green-900 mt-0.5">{mongoStatus.counts?.predictions || 0}</p>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Quick MongoDB Atlas Guide */}
            <div className="card space-y-4">
              <h3 className="section-title mb-1 flex items-center gap-2 text-green-800">
                <Leaf size={18} className="text-green-600" />
                MongoDB Atlas Setup Guide
              </h3>
              <p className="text-xs text-gray-600 leading-relaxed">
                If you don't have local MongoDB installed, you can use <strong>Free MongoDB Atlas Cloud</strong> (512MB free forever):
              </p>
              <ol className="list-decimal list-inside text-xs text-gray-600 space-y-2 leading-relaxed">
                <li>Go to <a href="https://www.mongodb.com/cloud/atlas" target="_blank" rel="noreferrer" className="text-blue-600 underline font-semibold">mongodb.com/atlas</a> and create a free account.</li>
                <li>Create a <strong>Free M0 Cluster</strong> (Shared).</li>
                <li>In <strong>Database Access</strong>, create a user (e.g. `admin` / password).</li>
                <li>In <strong>Network Access</strong>, click `Add IP Address` &rarr; `Allow Access from Anywhere` (0.0.0.0/0).</li>
                <li>Click <strong>Connect &rarr; Drivers (Python)</strong> and copy the URI string!</li>
                <li>Paste your URI into the box on the left and click <strong>Connect MongoDB</strong>!</li>
              </ol>
            </div>
          </div>

          {/* MongoDB Recent Predictions Collection */}
          {mongoPredictions.length > 0 && (
            <div className="card space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="section-title mb-0 flex items-center gap-2 text-green-800">
                  <Leaf size={18} className="text-green-600" />
                  MongoDB `predictions` Collection Documents
                </h3>
                <span className="text-xs text-gray-500 font-medium">Total: {mongoPredictions.length} docs</span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead>
                    <tr className="bg-gray-50 text-gray-600 uppercase tracking-wide border-b border-gray-200">
                      <th className="px-3 py-2.5">MongoDB _id</th>
                      <th className="px-3 py-2.5">Age</th>
                      <th className="px-3 py-2.5">Gender</th>
                      <th className="px-3 py-2.5">Income</th>
                      <th className="px-3 py-2.5">Spending</th>
                      <th className="px-3 py-2.5">Cluster</th>
                      <th className="px-3 py-2.5">Persona</th>
                      <th className="px-3 py-2.5">Timestamp</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100 font-mono">
                    {mongoPredictions.map((m) => (
                      <tr key={m.id} className="hover:bg-gray-50">
                        <td className="px-3 py-2 text-green-700 font-bold">{m.id}</td>
                        <td className="px-3 py-2 text-gray-700">{m.age ?? '—'}</td>
                        <td className="px-3 py-2 text-gray-700">{m.gender || '—'}</td>
                        <td className="px-3 py-2 text-gray-700">${m.annual_income?.toLocaleString() ?? '—'}</td>
                        <td className="px-3 py-2 text-gray-700">{m.spending_score ?? '—'}</td>
                        <td className="px-3 py-2 text-blue-700 font-semibold">Cluster {m.predicted_cluster}</td>
                        <td className="px-3 py-2 text-gray-900 font-sans font-medium">{m.segment_label}</td>
                        <td className="px-3 py-2 text-gray-400 text-[11px]">{m.created_at || '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab 1: Overview & Status */}
      {!loading && activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 card space-y-5">
            <h2 className="section-title mb-1 flex items-center gap-2">
              <CheckCircle size={18} className="text-emerald-500" />
              Active Database Connections
            </h2>
            <p className="text-sm text-gray-500">
              The application uses SQLAlchemy ORM for SQL storage and PyMongo for MongoDB NoSQL storage.
            </p>

            <div className="bg-gray-50 rounded-xl p-4 border border-gray-200 space-y-3 font-mono text-xs">
              <div className="flex justify-between items-center py-1 border-b border-gray-200">
                <span className="text-gray-500">SQL Connection State:</span>
                <span className="text-emerald-700 font-bold bg-emerald-100 px-2 py-0.5 rounded">CONNECTED</span>
              </div>
              <div className="flex justify-between items-center py-1 border-b border-gray-200">
                <span className="text-gray-500">SQL Engine / Driver:</span>
                <span className="text-gray-800 font-bold">{status?.engine || 'sqlite'}</span>
              </div>
              <div className="flex justify-between items-center py-1 border-b border-gray-200">
                <span className="text-gray-500">Database Name:</span>
                <span className="text-gray-800 font-bold">
                  {status?.engine?.toLowerCase().includes('mysql') ? 'MySQL: customer_segmentation (localhost:3306)' : 'SQLite: backend/customer_segmentation.db'}
                </span>
              </div>
              <div className="flex justify-between items-center py-1 border-b border-gray-200">
                <span className="text-gray-500">MongoDB State:</span>
                <span className={`font-bold px-2 py-0.5 rounded ${
                  mongoStatus?.connected ? 'text-green-700 bg-green-100' : 'text-amber-700 bg-amber-100'
                }`}>
                  {mongoStatus?.connected ? 'CONNECTED (NoSQL)' : 'STANDBY / OFFLINE'}
                </span>
              </div>
              <div className="flex justify-between items-center py-1">
                <span className="text-gray-500">ORM / Driver:</span>
                <span className="text-gray-800 font-bold">SQLAlchemy 2.x + PyMongo 4.x</span>
              </div>
            </div>

            <h3 className="text-base font-semibold text-gray-800 pt-2">Database Architecture Configured</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
              <div className="p-3.5 bg-blue-50/60 rounded-xl border border-blue-100">
                <p className="font-bold text-blue-900">1. datasets (SQL &amp; Mongo)</p>
                <p className="text-xs text-blue-700 mt-1">Stores uploaded CSV filenames, shapes, and features metadata.</p>
              </div>
              <div className="p-3.5 bg-emerald-50/60 rounded-xl border border-emerald-100">
                <p className="font-bold text-emerald-900">2. customer_records / customers</p>
                <p className="text-xs text-emerald-700 mt-1">Individual customer rows (Age, Income, Spending, Frequency).</p>
              </div>
              <div className="p-3.5 bg-indigo-50/60 rounded-xl border border-indigo-100">
                <p className="font-bold text-indigo-900">3. clustering_runs</p>
                <p className="text-xs text-indigo-700 mt-1">Algorithm training runs, hyperparams, Silhouette, DB score.</p>
              </div>
              <div className="p-3.5 bg-purple-50/60 rounded-xl border border-purple-100">
                <p className="font-bold text-purple-900">4. prediction_records / predictions</p>
                <p className="text-xs text-purple-700 mt-1">Single-customer prediction logs and matched segment personas.</p>
              </div>
            </div>
          </div>

          <div className="card space-y-4">
            <h2 className="section-title mb-1 flex items-center gap-2">
              <Clock size={18} className="text-blue-600" />
              Recent Activity
            </h2>
            <div className="space-y-3">
              {datasets.slice(0, 3).map((d) => (
                <div key={d.id} className="p-3 bg-gray-50 rounded-lg border border-gray-100 text-xs">
                  <div className="flex justify-between items-start">
                    <span className="font-semibold text-gray-800 truncate max-w-[150px]">{d.filename}</span>
                    <span className="badge-blue">Dataset #{d.id}</span>
                  </div>
                  <p className="text-gray-500 mt-1">{d.total_records} records | {d.total_features} features</p>
                  <p className="text-gray-400 text-[10px] mt-0.5">{d.uploaded_at || 'Recently'}</p>
                </div>
              ))}

              {runs.slice(0, 2).map((r) => (
                <div key={r.id} className="p-3 bg-indigo-50/60 rounded-lg border border-indigo-100 text-xs">
                  <div className="flex justify-between items-start">
                    <span className="font-semibold text-indigo-900 uppercase">{r.algorithm} Run</span>
                    <span className="badge-green">{r.n_clusters} clusters</span>
                  </div>
                  <p className="text-indigo-700 mt-1">Silhouette Score: {r.silhouette_score?.toFixed(3) ?? '—'}</p>
                  <p className="text-indigo-400 text-[10px] mt-0.5">{r.created_at || 'Recently'}</p>
                </div>
              ))}

              {datasets.length === 0 && runs.length === 0 && (
                <p className="text-sm text-gray-400 text-center py-6">No activity recorded yet.</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Stored Datasets */}
      {!loading && activeTab === 'datasets' && (
        <div className="card space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="section-title mb-0 flex items-center gap-2">
              <Layers size={18} className="text-blue-600" />
              Uploaded Datasets in Database
            </h2>
            <span className="text-xs text-gray-500 font-medium">Total: {datasets.length} datasets</span>
          </div>

          {datasets.length === 0 ? (
            <p className="text-sm text-gray-400 py-8 text-center">No datasets stored in database yet.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead>
                  <tr className="bg-gray-50 text-gray-600 uppercase tracking-wide border-b border-gray-200">
                    <th className="px-4 py-3">ID</th>
                    <th className="px-4 py-3">Filename</th>
                    <th className="px-4 py-3">Total Rows</th>
                    <th className="px-4 py-3">Total Columns</th>
                    <th className="px-4 py-3">Features Stored</th>
                    <th className="px-4 py-3">Uploaded At</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {datasets.map((d) => (
                    <tr key={d.id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-4 py-3 font-mono font-bold text-blue-600">#{d.id}</td>
                      <td className="px-4 py-3 font-semibold text-gray-800">{d.filename}</td>
                      <td className="px-4 py-3 text-gray-700">{d.total_records}</td>
                      <td className="px-4 py-3 text-gray-700">{d.total_features}</td>
                      <td className="px-4 py-3 text-gray-500 max-w-xs truncate">
                        {Array.isArray(d.features) ? d.features.join(', ') : '—'}
                      </td>
                      <td className="px-4 py-3 text-gray-400">{d.uploaded_at || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Customer Records */}
      {!loading && activeTab === 'customers' && (
        <div className="card space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="section-title mb-0 flex items-center gap-2">
              <Users size={18} className="text-indigo-600" />
              Customer Records (DB Rows)
            </h2>
            <span className="text-xs text-gray-500 font-medium">Showing {customers.length} records</span>
          </div>

          {customers.length === 0 ? (
            <p className="text-sm text-gray-400 py-8 text-center">No customer rows found in database.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead>
                  <tr className="bg-gray-50 text-gray-600 uppercase tracking-wide border-b border-gray-200">
                    <th className="px-3 py-2.5">Row ID</th>
                    <th className="px-3 py-2.5">Ref / ID</th>
                    <th className="px-3 py-2.5">Gender</th>
                    <th className="px-3 py-2.5">Age</th>
                    <th className="px-3 py-2.5">Annual Income</th>
                    <th className="px-3 py-2.5">Spending Score</th>
                    <th className="px-3 py-2.5">Purchase Frequency</th>
                    <th className="px-3 py-2.5">Created At</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {customers.map((c) => (
                    <tr key={c.id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-3 py-2 font-mono text-gray-500">#{c.id}</td>
                      <td className="px-3 py-2 font-medium text-gray-800">{c.customer_ref || '—'}</td>
                      <td className="px-3 py-2 text-gray-700">{c.gender || '—'}</td>
                      <td className="px-3 py-2 text-gray-700">{c.age ?? '—'}</td>
                      <td className="px-3 py-2 text-gray-700">
                        {c.annual_income != null ? `$${c.annual_income.toLocaleString()}` : '—'}
                      </td>
                      <td className="px-3 py-2 text-gray-700">
                        {c.spending_score != null ? `${c.spending_score}/100` : '—'}
                      </td>
                      <td className="px-3 py-2 text-gray-700">{c.purchase_frequency ?? '—'}</td>
                      <td className="px-3 py-2 text-gray-400 text-[11px]">{c.created_at || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Tab 4: Clustering Runs */}
      {!loading && activeTab === 'runs' && (
        <div className="card space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="section-title mb-0 flex items-center gap-2">
              <GitBranch size={18} className="text-indigo-600" />
              Saved Clustering Experiments
            </h2>
            <span className="text-xs text-gray-500 font-medium">Total: {runs.length} runs</span>
          </div>

          {runs.length === 0 ? (
            <p className="text-sm text-gray-400 py-8 text-center">No clustering runs recorded in database yet.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead>
                  <tr className="bg-gray-50 text-gray-600 uppercase tracking-wide border-b border-gray-200">
                    <th className="px-4 py-3">Run ID</th>
                    <th className="px-4 py-3">Algorithm</th>
                    <th className="px-4 py-3">Clusters</th>
                    <th className="px-4 py-3">Silhouette Score</th>
                    <th className="px-4 py-3">Davies-Bouldin</th>
                    <th className="px-4 py-3">WCSS</th>
                    <th className="px-4 py-3">Trained At</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {runs.map((r) => (
                    <tr key={r.id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-4 py-3 font-mono font-bold text-indigo-600">#{r.id}</td>
                      <td className="px-4 py-3 font-bold text-gray-800 uppercase">{r.algorithm}</td>
                      <td className="px-4 py-3 font-semibold text-gray-700">{r.n_clusters} clusters</td>
                      <td className="px-4 py-3 text-emerald-700 font-medium">
                        {r.silhouette_score != null ? r.silhouette_score.toFixed(4) : '—'}
                      </td>
                      <td className="px-4 py-3 text-blue-700 font-medium">
                        {r.davies_bouldin_score != null ? r.davies_bouldin_score.toFixed(4) : '—'}
                      </td>
                      <td className="px-4 py-3 text-gray-600">
                        {r.wcss != null ? r.wcss.toFixed(2) : '—'}
                      </td>
                      <td className="px-4 py-3 text-gray-400">{r.created_at || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Tab 5: Prediction Logs */}
      {!loading && activeTab === 'predictions' && (
        <div className="card space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="section-title mb-0 flex items-center gap-2">
              <Cpu size={18} className="text-purple-600" />
              Customer Prediction History
            </h2>
            <span className="text-xs text-gray-500 font-medium">Total: {predictions.length} predictions</span>
          </div>

          {predictions.length === 0 ? (
            <p className="text-sm text-gray-400 py-8 text-center">
              No predictions recorded yet. Run a prediction on the Prediction page to view results saved here!
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead>
                  <tr className="bg-gray-50 text-gray-600 uppercase tracking-wide border-b border-gray-200">
                    <th className="px-3 py-2.5">ID</th>
                    <th className="px-3 py-2.5">Gender</th>
                    <th className="px-3 py-2.5">Age</th>
                    <th className="px-3 py-2.5">Income</th>
                    <th className="px-3 py-2.5">Spending</th>
                    <th className="px-3 py-2.5">Frequency</th>
                    <th className="px-3 py-2.5">Cluster</th>
                    <th className="px-3 py-2.5">Assigned Persona</th>
                    <th className="px-3 py-2.5">Timestamp</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {predictions.map((p) => (
                    <tr key={p.id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-3 py-2 font-mono text-gray-500">#{p.id}</td>
                      <td className="px-3 py-2 font-medium text-gray-800">{p.gender || '—'}</td>
                      <td className="px-3 py-2 text-gray-600">{p.age ?? '—'}</td>
                      <td className="px-3 py-2 text-gray-600">
                        {p.annual_income != null ? `$${p.annual_income.toLocaleString()}` : '—'}
                      </td>
                      <td className="px-3 py-2 text-gray-600">
                        {p.spending_score != null ? `${p.spending_score}/100` : '—'}
                      </td>
                      <td className="px-3 py-2 text-gray-600">{p.purchase_frequency ?? '—'}</td>
                      <td className="px-3 py-2">
                        <span className="badge-blue">Cluster {p.predicted_cluster}</span>
                      </td>
                      <td className="px-3 py-2 font-semibold text-gray-800">{p.segment_label}</td>
                      <td className="px-3 py-2 text-gray-400 text-xs">{p.created_at || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Tab 6: Database Settings & Architecture */}
      {!loading && activeTab === 'settings' && (
        <div className="card space-y-6">
          <h2 className="section-title mb-0 flex items-center gap-2">
            <Server size={18} className="text-blue-600" />
            Database Architecture &amp; Integration Guide
          </h2>

          <div className="bg-slate-900 text-slate-100 p-5 rounded-xl font-mono text-xs space-y-3">
            <p className="text-slate-400"># Current SQL Connection</p>
            <p className="text-emerald-400 text-sm">
              {status?.database_url || 'mysql+pymysql://root:***@localhost:3306/customer_segmentation'}
            </p>
            <p className="text-slate-400 mt-2"># Current MongoDB Connection</p>
            <p className="text-green-400 text-sm">
              {mongoStatus?.uri || 'mongodb://localhost:27017'}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div className="p-4 bg-gray-50 rounded-xl border border-gray-200 space-y-2">
              <h4 className="font-bold text-gray-800">✅ Relational SQL (MySQL / SQLite)</h4>
              <ul className="list-disc list-inside text-xs text-gray-600 space-y-1">
                <li>Structured schema with foreign key relationships</li>
                <li>ACID transactions &amp; robust indexing</li>
                <li>Automatic failover to SQLite if MySQL is offline</li>
              </ul>
            </div>

            <div className="p-4 bg-gray-50 rounded-xl border border-gray-200 space-y-2">
              <h4 className="font-bold text-gray-800">🍃 NoSQL Document Store (MongoDB)</h4>
              <ul className="list-disc list-inside text-xs text-gray-600 space-y-1">
                <li>Schema-less JSON documents for flexible customer attributes</li>
                <li>High throughput for ML predictions &amp; customer logs</li>
                <li>Seamless cloud hosting with free MongoDB Atlas</li>
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
