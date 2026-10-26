import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Users,
  Database,
  AlertTriangle,
  Copy,
  GitBranch,
  BarChart2,
  CheckCircle,
  Circle,
  ArrowRight,
  Upload,
  Cpu,
  Scale,
  TrendingUp,
} from 'lucide-react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { datasetAPI, clusteringAPI, databaseAPI } from '../services/api'
import { useAppContext } from '../App'
import MetricCard from '../components/MetricCard'
import LoadingSpinner from '../components/LoadingSpinner'

const PIPELINE_STEPS = [
  { id: 1, label: 'Upload Dataset', desc: 'CSV file with customer data', icon: Upload, key: 'dataUploaded' },
  { id: 2, label: 'Preprocess', desc: 'Handle missing values & scaling', icon: Database, key: 'preprocessed' },
  { id: 3, label: 'Cluster Analysis', desc: 'Elbow + Silhouette methods', icon: GitBranch, key: null },
  { id: 4, label: 'Train Model', desc: 'K-Means / Hierarchical / DBSCAN', icon: Cpu, key: 'modelTrained' },
  { id: 5, label: 'Explore Results', desc: 'Profiles & comparisons', icon: BarChart2, key: null },
]

export default function Dashboard() {
  const navigate = useNavigate()
  const { appState } = useAppContext()
  const [summary, setSummary] = useState(null)
  const [results, setResults] = useState(null)
  const [clusterDistData, setClusterDistData] = useState([])
  const [loading, setLoading] = useState(false)
  const [dbInfo, setDbInfo] = useState(null)

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true)
      try {
        const [sumRes, resRes, dbRes] = await Promise.allSettled([
          datasetAPI.getSummary(),
          clusteringAPI.getResults(),
          databaseAPI.getStatus(),
        ])
        if (sumRes.status === 'fulfilled') setSummary(sumRes.value.data)
        if (dbRes.status === 'fulfilled') setDbInfo(dbRes.value.data)
        if (resRes.status === 'fulfilled') {
          const r = resRes.value.data
          const list = r?.results || (Array.isArray(r) ? r : [])
          const latest = list.length > 0 ? list[0] : r
          setResults(latest)
          if (latest?.cluster_distribution) {
            const dist = Object.entries(latest.cluster_distribution).map(([k, v]) => ({
              name: `Cluster ${k}`,
              customers: v,
            }))
            setClusterDistData(dist)
          }
        }

        // Also fetch segments for cluster distribution chart if needed
        try {
          const segRes = await clusteringAPI.getSegments()
          const segs = segRes.data?.profiles || segRes.data?.segments || []
          if (segs.length > 0) {
            const dist = segs.map((s) => ({
              name: s.label || `Cluster ${s.cluster_id}`,
              customers: s.size ?? s.count ?? 0,
            }))
            setClusterDistData(dist)
          }
        } catch {
          // ignore
        }
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  const getStepStatus = (key) => {
    if (!key) return 'neutral'
    return appState[key] ? 'done' : 'pending'
  }

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Hero */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 rounded-2xl p-8 text-white shadow-lg">
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-3xl font-bold mb-2">Customer Segmentation ML</h1>
            <p className="text-blue-100 text-sm max-w-xl leading-relaxed">
              An end-to-end machine learning pipeline for discovering customer groups using
              K-Means, Hierarchical Clustering, and DBSCAN. Upload your dataset, preprocess,
              analyze, train, and explore actionable segments.
            </p>
          </div>
          <button
            onClick={() => navigate('/upload')}
            className="flex items-center gap-2 bg-white text-blue-700 font-semibold px-5 py-2.5 rounded-xl hover:bg-blue-50 transition-colors text-sm shadow"
          >
            Get Started <ArrowRight size={16} />
          </button>
        </div>
      </div>

      {/* Pipeline Flowchart */}
      <div className="card">
        <h2 className="section-title flex items-center gap-2">
          <TrendingUp size={20} className="text-blue-600" />
          ML Pipeline
        </h2>
        <div className="flex flex-wrap items-center gap-2">
          {PIPELINE_STEPS.map((step, idx) => {
            const status = getStepStatus(step.key)
            const Icon = step.icon
            return (
              <div key={step.id} className="flex items-center gap-2">
                <div
                  className={`flex items-start gap-3 px-4 py-3 rounded-xl border-2 min-w-[140px] transition-all ${
                    status === 'done'
                      ? 'bg-green-50 border-green-400'
                      : 'bg-gray-50 border-gray-200'
                  }`}
                >
                  <div
                    className={`p-1.5 rounded-lg ${
                      status === 'done' ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-400'
                    }`}
                  >
                    <Icon size={16} />
                  </div>
                  <div>
                    <div className="flex items-center gap-1.5">
                      <p className="text-xs font-bold text-gray-800">{step.label}</p>
                      {status === 'done' && <CheckCircle size={12} className="text-green-500" />}
                    </div>
                    <p className="text-xs text-gray-500 mt-0.5 leading-tight">{step.desc}</p>
                  </div>
                </div>
                {idx < PIPELINE_STEPS.length - 1 && (
                  <ArrowRight size={16} className="text-gray-300 flex-shrink-0" />
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Status Indicators */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {[
          { label: 'Dataset Uploaded', done: appState.dataUploaded, info: appState.uploadedFilename || 'No file uploaded' },
          { label: 'Preprocessing Done', done: appState.preprocessed, info: appState.preprocessed ? 'Data ready for clustering' : 'Not yet processed' },
          { label: 'Model Trained', done: appState.modelTrained, info: appState.modelTrained ? 'Results available' : 'No model trained yet' },
        ].map(({ label, done, info }) => (
          <div
            key={label}
            className={`rounded-xl border p-4 flex items-center gap-3 ${
              done ? 'bg-green-50 border-green-300' : 'bg-gray-50 border-gray-200'
            }`}
          >
            {done ? (
              <CheckCircle size={20} className="text-green-500 flex-shrink-0" />
            ) : (
              <Circle size={20} className="text-gray-300 flex-shrink-0" />
            )}
            <div>
              <p className={`text-sm font-semibold ${done ? 'text-green-800' : 'text-gray-600'}`}>{label}</p>
              <p className="text-xs text-gray-500 truncate">{info}</p>
            </div>
          </div>
        ))}
      </div>

      {loading && <LoadingSpinner message="Loading dashboard data..." />}

      {/* Dataset Summary Cards */}
      {summary ? (
        <div>
          <h2 className="section-title flex items-center gap-2">
            <Database size={20} className="text-blue-600" />
            Dataset Overview
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <MetricCard
              title="Total Customers"
              value={summary.total_records?.toLocaleString() ?? '—'}
              icon={<Users size={18} />}
              color="blue"
            />
            <MetricCard
              title="Total Features"
              value={summary.total_features ?? '—'}
              icon={<Database size={18} />}
              color="purple"
            />
            <MetricCard
              title="Missing Values"
              value={summary.missing_values_total ?? 0}
              icon={<AlertTriangle size={18} />}
              color={summary.missing_values_total > 0 ? 'orange' : 'green'}
            />
            <MetricCard
              title="Duplicate Records"
              value={summary.duplicate_count ?? 0}
              icon={<Copy size={18} />}
              color={summary.duplicate_count > 0 ? 'red' : 'green'}
            />
          </div>
        </div>
      ) : (
        !loading && (
          <div className="card text-center py-12">
            <Database size={40} className="text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500 font-medium">No dataset uploaded yet</p>
            <p className="text-gray-400 text-sm mb-4">Upload a CSV file to see dataset statistics</p>
            <button
              onClick={() => navigate('/upload')}
              className="btn-primary inline-flex items-center gap-2 text-sm"
            >
              <Upload size={16} /> Upload Dataset
            </button>
          </div>
        )
      )}

      {/* Clustering Results Cards */}
      {results && (
        <div>
          <h2 className="section-title flex items-center gap-2">
            <GitBranch size={20} className="text-blue-600" />
            Latest Clustering Results
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-4 mb-6">
            <MetricCard
              title="Algorithm"
              value={results.algorithm ?? '—'}
              icon={<Cpu size={18} />}
              color="blue"
            />
            <MetricCard
              title="Clusters"
              value={results.n_clusters ?? '—'}
              icon={<GitBranch size={18} />}
              color="purple"
            />
            <MetricCard
              title="Silhouette Score"
              value={results.silhouette_score != null ? results.silhouette_score.toFixed(4) : '—'}
              subtitle="Higher is better (max 1)"
              icon={<TrendingUp size={18} />}
              color="green"
            />
            <MetricCard
              title="Davies-Bouldin"
              value={results.davies_bouldin_score != null ? results.davies_bouldin_score.toFixed(4) : '—'}
              subtitle="Lower is better"
              icon={<Scale size={18} />}
              color="orange"
            />
            <MetricCard
              title="WCSS"
              value={results.wcss != null ? results.wcss.toFixed(2) : '—'}
              subtitle="Inertia"
              icon={<BarChart2 size={18} />}
              color="teal"
            />
          </div>

          {clusterDistData.length > 0 && (
            <div className="card">
              <h3 className="text-sm font-bold text-gray-700 mb-4">Cluster Distribution</h3>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={clusterDistData} barSize={40}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Bar dataKey="customers" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}

      {/* Database Storage Overview */}
      {dbInfo && dbInfo.connected && (
        <div className="card bg-gradient-to-r from-slate-50 to-blue-50 border-blue-200">
          <div className="flex items-center justify-between mb-4">
            <h2 className="section-title flex items-center gap-2 mb-0">
              <Database size={20} className="text-blue-600" />
              Relational Database Storage (SQLite)
            </h2>
            <span className="badge-blue">Connected &amp; Active</span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="bg-white rounded-xl p-3.5 border border-blue-100 shadow-xs">
              <p className="text-xs text-gray-500 font-medium">Datasets Saved</p>
              <p className="text-2xl font-bold text-gray-800 mt-1">{dbInfo.counts?.datasets ?? 0}</p>
            </div>
            <div className="bg-white rounded-xl p-3.5 border border-blue-100 shadow-xs">
              <p className="text-xs text-gray-500 font-medium">Customer Records in DB</p>
              <p className="text-2xl font-bold text-blue-700 mt-1">{dbInfo.counts?.customer_records?.toLocaleString() ?? 0}</p>
            </div>
            <div className="bg-white rounded-xl p-3.5 border border-blue-100 shadow-xs">
              <p className="text-xs text-gray-500 font-medium">Clustering Runs Logged</p>
              <p className="text-2xl font-bold text-purple-700 mt-1">{dbInfo.counts?.clustering_runs ?? 0}</p>
            </div>
            <div className="bg-white rounded-xl p-3.5 border border-blue-100 shadow-xs">
              <p className="text-xs text-gray-500 font-medium">Predictions Persisted</p>
              <p className="text-2xl font-bold text-emerald-700 mt-1">{dbInfo.counts?.predictions ?? 0}</p>
            </div>
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="card">
        <h2 className="section-title">Quick Actions</h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {[
            { label: 'Upload Data', path: '/upload', icon: Upload, color: 'bg-blue-600' },
            { label: 'Analyze Data', path: '/analysis', icon: BarChart2, color: 'bg-purple-600' },
            { label: 'Cluster Analysis', path: '/clustering', icon: GitBranch, color: 'bg-green-600' },
            { label: 'Compare Models', path: '/comparison', icon: Scale, color: 'bg-orange-500' },
            { label: 'Segment Profiles', path: '/segments', icon: Users, color: 'bg-teal-600' },
            { label: 'Predict Segment', path: '/prediction', icon: Cpu, color: 'bg-indigo-600' },
          ].map(({ label, path, icon: Icon, color }) => (
            <button
              key={path}
              onClick={() => navigate(path)}
              className="flex flex-col items-center gap-2 p-4 rounded-xl border border-gray-200 hover:border-blue-300 hover:shadow-sm transition-all bg-white group"
            >
              <div className={`${color} text-white p-2.5 rounded-lg group-hover:scale-110 transition-transform`}>
                <Icon size={18} />
              </div>
              <span className="text-xs font-medium text-gray-700 text-center leading-tight">{label}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
