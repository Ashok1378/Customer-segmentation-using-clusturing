import { useEffect, useState } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  Legend,
} from 'recharts'
import { Scale, AlertTriangle, Download, Info, TrendingUp, TrendingDown } from 'lucide-react'
import { clusteringAPI } from '../services/api'
import { useAppContext } from '../App'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorAlert from '../components/ErrorAlert'

const COLORS = ['#3b82f6', '#10b981', '#f59e0b']

function BestCell({ value, isBest, lowerBetter }) {
  const isGood = lowerBetter ? isBest : isBest
  return (
    <td
      className={`px-4 py-3 text-sm font-semibold ${
        isGood ? 'text-green-700 bg-green-50' : 'text-gray-700'
      }`}
    >
      <div className="flex items-center gap-1.5">
        {value != null ? (typeof value === 'number' ? value.toFixed(4) : value) : 'N/A'}
        {isGood && <TrendingUp size={13} className="text-green-500" />}
      </div>
    </td>
  )
}

export default function ModelComparison() {
  const { appState, updateAppState } = useAppContext()
  const [comparison, setComparison] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const fetchComparison = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await clusteringAPI.getComparison()
      setComparison(res.data)
      const list = res.data?.models || res.data?.results || []
      if (list.length > 0) {
        updateAppState({ modelTrained: true })
      }
    } catch (e) {
      setError(e.message || 'Failed to load comparison data.')
    } finally {
      setLoading(false)
    }
  }

  const handleTrainAll = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await clusteringAPI.trainAll()
      setComparison(res.data)
      updateAppState({ modelTrained: true })
    } catch (e) {
      setError(e.message || 'Failed to train all models.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchComparison()
  }, [])

  const models = comparison?.models || comparison?.results || []

  if (!loading && models.length === 0) {
    return (
      <div className="max-w-4xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Model Comparison</h1>
          <p className="text-gray-500 text-sm mt-1">Compare trained clustering algorithms side by side.</p>
        </div>
        <div className="card text-center py-16">
          <AlertTriangle size={48} className="text-yellow-400 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-gray-700 mb-2">No Models Trained Yet</h2>
          <p className="text-gray-500 text-sm max-w-sm mx-auto mb-6">
            Train at least one clustering algorithm or click below to train all 3 algorithms (K-Means, Hierarchical, DBSCAN) in 1-click.
          </p>
          <div className="flex justify-center items-center gap-4">
            <button
              onClick={handleTrainAll}
              disabled={loading}
              className="btn-primary flex items-center gap-2"
            >
              <Scale size={16} />
              ⚡ Train & Compare All Algorithms Now
            </button>
            <a href="/clustering" className="btn-secondary">
              Go to Clustering Analysis
            </a>
          </div>
          {error && (
            <div className="mt-4 max-w-md mx-auto">
              <ErrorAlert message={error} onDismiss={() => setError('')} />
            </div>
          )}
        </div>
      </div>
    )
  }

  // Find best values
  const bestSilhouette = models.length > 0
    ? Math.max(...models.map((m) => m.silhouette_score ?? -Infinity))
    : null
  const bestDB = models.length > 0
    ? Math.min(...models.filter((m) => m.davies_bouldin_score != null).map((m) => m.davies_bouldin_score))
    : null
  const bestWCSS = models.length > 0
    ? Math.min(...models.filter((m) => m.wcss != null).map((m) => m.wcss))
    : null

  const silhouetteChartData = models.map((m) => ({
    name: m.algorithm,
    Silhouette: m.silhouette_score != null ? Number(m.silhouette_score.toFixed(4)) : 0,
  }))
  const dbChartData = models.map((m) => ({
    name: m.algorithm,
    'Davies-Bouldin': m.davies_bouldin_score != null ? Number(m.davies_bouldin_score.toFixed(4)) : 0,
  }))

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Model Comparison</h1>
          <p className="text-gray-500 text-sm mt-1">Compare trained clustering algorithms side by side.</p>
        </div>
        <div className="flex gap-3">
          <button onClick={fetchComparison} className="btn-secondary text-sm flex items-center gap-2">
            <Scale size={15} /> Refresh
          </button>
          <button onClick={clusteringAPI.downloadReport} className="btn-primary text-sm flex items-center gap-2">
            <Download size={15} /> Download Report
          </button>
        </div>
      </div>

      {loading && <LoadingSpinner message="Loading comparison..." />}
      {error && <ErrorAlert message={error} onDismiss={() => setError('')} />}

      {/* Instructions */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 flex gap-3">
        <Info size={18} className="text-blue-500 flex-shrink-0 mt-0.5" />
        <div className="text-sm text-blue-800">
          <p className="font-semibold mb-1">How to use this page</p>
          <p>Train all three algorithms (K-Means, Hierarchical, DBSCAN) in the Clustering Analysis page, then refresh here to compare their performance metrics.</p>
        </div>
      </div>

      {models.length > 0 && (
        <>
          {/* Comparison Table */}
          <div className="card overflow-x-auto">
            <h2 className="section-title flex items-center gap-2">
              <Scale size={20} className="text-blue-600" />
              Algorithm Performance Comparison
            </h2>
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-gray-50 text-gray-600 text-xs uppercase tracking-wide">
                  <th className="px-4 py-3 border border-gray-200">Algorithm</th>
                  <th className="px-4 py-3 border border-gray-200">Clusters</th>
                  <th className="px-4 py-3 border border-gray-200">
                    Silhouette ↑
                    <span className="ml-1 text-green-600 font-normal">(higher)</span>
                  </th>
                  <th className="px-4 py-3 border border-gray-200">
                    Davies-Bouldin ↓
                    <span className="ml-1 text-green-600 font-normal">(lower)</span>
                  </th>
                  <th className="px-4 py-3 border border-gray-200">
                    WCSS ↓
                    <span className="ml-1 text-green-600 font-normal">(lower)</span>
                  </th>
                  <th className="px-4 py-3 border border-gray-200">Noise Points</th>
                </tr>
              </thead>
              <tbody>
                {models.map((model, i) => (
                  <tr key={i} className="border-t border-gray-100 hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3 font-bold text-gray-900 border border-gray-100">
                      <span className={`badge ${i === 0 ? 'badge-blue' : i === 1 ? 'badge-green' : 'badge-yellow'}`}>
                        {model.algorithm}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-700 border border-gray-100">
                      {model.n_clusters ?? '—'}
                    </td>
                    <BestCell
                      value={model.silhouette_score}
                      isBest={model.silhouette_score === bestSilhouette}
                      lowerBetter={false}
                    />
                    <BestCell
                      value={model.davies_bouldin_score}
                      isBest={model.davies_bouldin_score === bestDB}
                      lowerBetter={true}
                    />
                    <BestCell
                      value={model.wcss}
                      isBest={model.wcss === bestWCSS}
                      lowerBetter={true}
                    />
                    <td className="px-4 py-3 text-sm text-gray-500 border border-gray-100">
                      {model.noise_points ?? '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="card">
              <h3 className="text-sm font-bold text-gray-700 mb-4 flex items-center gap-2">
                <TrendingUp size={16} className="text-green-500" />
                Silhouette Score Comparison (Higher is Better)
              </h3>
              <ResponsiveContainer width="100%" height={230}>
                <BarChart data={silhouetteChartData} barSize={50}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                  <YAxis domain={[0, 1]} tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Bar dataKey="Silhouette" radius={[4, 4, 0, 0]}>
                    {silhouetteChartData.map((_, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="card">
              <h3 className="text-sm font-bold text-gray-700 mb-4 flex items-center gap-2">
                <TrendingDown size={16} className="text-orange-500" />
                Davies-Bouldin Score Comparison (Lower is Better)
              </h3>
              <ResponsiveContainer width="100%" height={230}>
                <BarChart data={dbChartData} barSize={50}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Bar dataKey="Davies-Bouldin" radius={[4, 4, 0, 0]}>
                    {dbChartData.map((_, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Explanation */}
          <div className="card bg-gray-50">
            <h2 className="section-title flex items-center gap-2">
              <Info size={20} className="text-blue-600" />
              Metric Interpretation Guide
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm">
              <div className="bg-white rounded-lg p-4 border border-gray-200">
                <h3 className="font-bold text-blue-700 mb-2">Silhouette Score</h3>
                <p className="text-gray-600 text-xs leading-relaxed">
                  Ranges from -1 to 1. <strong>Higher values</strong> indicate that data points are well-matched to their own cluster and poorly matched to neighboring clusters. Above 0.5 is considered good.
                </p>
              </div>
              <div className="bg-white rounded-lg p-4 border border-gray-200">
                <h3 className="font-bold text-orange-700 mb-2">Davies-Bouldin Index</h3>
                <p className="text-gray-600 text-xs leading-relaxed">
                  Measures average similarity between clusters. <strong>Lower values</strong> indicate better-defined, more separated clusters. Zero is the minimum possible value (perfect clustering).
                </p>
              </div>
              <div className="bg-white rounded-lg p-4 border border-gray-200">
                <h3 className="font-bold text-purple-700 mb-2">WCSS (Inertia)</h3>
                <p className="text-gray-600 text-xs leading-relaxed">
                  Within-cluster sum of squares. <strong>Lower values</strong> mean tighter clusters, but always decreases as K increases. Best interpreted alongside the Elbow Method. Not applicable for DBSCAN.
                </p>
              </div>
            </div>
          </div>
        </>
      )}

      {!loading && models.length === 0 && appState.modelTrained && (
        <div className="card text-center py-12 text-gray-400">
          <Scale size={40} className="mx-auto mb-3 opacity-40" />
          <p>No comparison data available. Try refreshing.</p>
        </div>
      )}
    </div>
  )
}
