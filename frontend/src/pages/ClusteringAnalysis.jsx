import { useState } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  ZAxis,
  Legend,
  BarChart,
  Bar,
  Cell,
} from 'recharts'
import {
  GitBranch,
  AlertTriangle,
  TrendingUp,
  Play,
  CheckCircle,
  SlidersHorizontal,
} from 'lucide-react'
import { clusteringAPI } from '../services/api'
import { useAppContext } from '../App'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorAlert from '../components/ErrorAlert'
import MetricCard from '../components/MetricCard'

const CLUSTER_COLORS = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6', '#6366f1', '#ec4899', '#14b8a6']

const ALGO_TABS = [
  { id: 'kmeans', label: 'K-Means' },
  { id: 'hierarchical', label: 'Hierarchical' },
  { id: 'dbscan', label: 'DBSCAN' },
]

export default function ClusteringAnalysis() {
  const { appState, updateAppState } = useAppContext()

  // Elbow / silhouette state
  const [kMin, setKMin] = useState(2)
  const [kMax, setKMax] = useState(10)
  const [analyzing, setAnalyzing] = useState(false)
  const [analyzeError, setAnalyzeError] = useState('')
  const [elbowData, setElbowData] = useState([])
  const [silhouetteData, setSilhouetteData] = useState([])
  const [optimalK, setOptimalK] = useState(null)

  // Training state
  const [activeAlgo, setActiveAlgo] = useState('kmeans')
  const [kmeansK, setKmeansK] = useState(4)
  const [hierK, setHierK] = useState(4)
  const [hierLinkage, setHierLinkage] = useState('ward')
  const [dbscanEps, setDbscanEps] = useState(0.5)
  const [dbscanMinSamples, setDbscanMinSamples] = useState(5)
  const [training, setTraining] = useState(false)
  const [trainError, setTrainError] = useState('')
  const [trainResult, setTrainResult] = useState(null)
  const [pcaData, setPcaData] = useState([])
  const [clusterDist, setClusterDist] = useState([])

  const [autoPreprocessing, setAutoPreprocessing] = useState(false)

  const handleAutoPreprocess = async () => {
    setAutoPreprocessing(true)
    setAnalyzeError('')
    try {
      await clusteringAPI.preprocess({
        features: ['Age', 'AnnualIncome', 'SpendingScore', 'PurchaseFrequency'],
        remove_duplicates: true
      })
      updateAppState({ preprocessed: true, dataUploaded: true })
    } catch (e) {
      setAnalyzeError(e.message || 'Auto-preprocessing failed.')
    } finally {
      setAutoPreprocessing(false)
    }
  }

  const handleAnalyze = async () => {
    setAnalyzing(true)
    setAnalyzeError('')
    setElbowData([])
    setSilhouetteData([])
    try {
      const kRange = Array.from({ length: kMax - kMin + 1 }, (_, i) => kMin + i)
      const res = await clusteringAPI.analyze({ k_min: kMin, k_max: kMax, k_range: kRange })
      const data = res.data
      if (data.wcss_values) {
        const ed = data.wcss_values.map((v, i) => ({ k: kMin + i, wcss: Number(v.toFixed(2)) }))
        setElbowData(ed)
      }
      if (data.silhouette_scores) {
        const sd = data.silhouette_scores.map((v, i) => ({ k: kMin + i, score: Number(v.toFixed(4)) }))
        setSilhouetteData(sd)
      }
      const opt = data.recommended_k || data.optimal_k_silhouette || data.optimal_k_elbow || data.optimal_k
      if (opt) setOptimalK(opt)
      updateAppState({ preprocessed: true })
    } catch (e) {
      setAnalyzeError(e.message || 'Analysis failed.')
    } finally {
      setAnalyzing(false)
    }
  }

  const buildTrainParams = () => {
    if (activeAlgo === 'kmeans') return { algorithm: 'kmeans', k: kmeansK, n_clusters: kmeansK }
    if (activeAlgo === 'hierarchical') return { algorithm: 'hierarchical', k: hierK, n_clusters: hierK, linkage: hierLinkage }
    if (activeAlgo === 'dbscan') return { algorithm: 'dbscan', eps: dbscanEps, min_samples: dbscanMinSamples }
  }

  const handleTrain = async () => {
    setTraining(true)
    setTrainError('')
    setTrainResult(null)
    setPcaData([])
    setClusterDist([])
    try {
      const res = await clusteringAPI.train(buildTrainParams())
      const data = res.data
      setTrainResult(data)
      updateAppState({
        modelTrained: true,
        lastResults: data,
        trainedAlgorithms: [...(appState.trainedAlgorithms || []), activeAlgo],
      })
      // Fetch PCA
      try {
        const pcaRes = await clusteringAPI.getPCA()
        const pca = pcaRes.data
        if (pca?.points) {
          const grouped = {}
          pca.points.forEach((pt) => {
            const c = pt.cluster
            if (!grouped[c]) grouped[c] = []
            grouped[c].push({ x: pt.x, y: pt.y })
          })
          setPcaData(grouped)
        }
      } catch {}
      // Cluster distribution
      if (data.cluster_distribution) {
        const dist = Object.entries(data.cluster_distribution).map(([k, v]) => ({
          name: `Cluster ${k}`,
          customers: v,
        }))
        setClusterDist(dist)
      }
    } catch (e) {
      setTrainError(e.message || 'Training failed.')
    } finally {
      setTraining(false)
    }
  }

  if (!appState.preprocessed) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="card text-center py-16">
          <AlertTriangle size={48} className="text-yellow-400 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-gray-700 mb-2">Dataset Preprocessing</h2>
          <p className="text-gray-500 text-sm max-w-md mx-auto mb-6">
            To run clustering analysis, the dataset features need to be scaled and prepared. Click below to automatically preprocess using standard features.
          </p>
          <div className="flex justify-center items-center gap-4">
            <button
              onClick={handleAutoPreprocess}
              disabled={autoPreprocessing}
              className="btn-primary flex items-center gap-2"
            >
              <Play size={16} />
              {autoPreprocessing ? 'Preprocessing...' : '⚡ Auto-Preprocess Dataset & Unlock'}
            </button>
            <a href="/upload" className="btn-secondary">
              Go to Upload Page
            </a>
          </div>
          {analyzeError && (
            <div className="mt-4 max-w-md mx-auto">
              <ErrorAlert message={analyzeError} onDismiss={() => setAnalyzeError('')} />
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Clustering Analysis</h1>
        <p className="text-gray-500 text-sm mt-1">Find optimal clusters and train your segmentation model.</p>
      </div>

      {/* Step 1: Elbow + Silhouette Analysis */}
      <div className="card">
        <h2 className="section-title flex items-center gap-2">
          <TrendingUp size={20} className="text-blue-600" />
          Step 1: Optimal K Analysis (Elbow + Silhouette)
        </h2>
        <div className="flex flex-wrap items-end gap-4 mb-6">
          <div>
            <label className="label">K Minimum</label>
            <input
              type="number"
              min={2}
              max={kMax - 1}
              value={kMin}
              onChange={(e) => setKMin(Number(e.target.value))}
              className="input-field w-24"
            />
          </div>
          <div>
            <label className="label">K Maximum</label>
            <input
              type="number"
              min={kMin + 1}
              max={15}
              value={kMax}
              onChange={(e) => setKMax(Number(e.target.value))}
              className="input-field w-24"
            />
          </div>
          <button
            onClick={handleAnalyze}
            disabled={analyzing}
            className="btn-primary flex items-center gap-2 disabled:opacity-50"
          >
            {analyzing ? (
              <><TrendingUp size={16} className="animate-pulse" /> Analyzing...</>
            ) : (
              <><Play size={16} /> Run Analysis</>
            )}
          </button>
        </div>

        {analyzeError && <ErrorAlert message={analyzeError} onDismiss={() => setAnalyzeError('')} />}
        {analyzing && <LoadingSpinner message="Running elbow and silhouette analysis..." />}

        {optimalK && (
          <div className="mb-4 inline-flex items-center gap-2 bg-green-50 border border-green-300 text-green-800 px-4 py-2 rounded-lg text-sm font-medium">
            <CheckCircle size={16} /> Recommended K: <span className="font-bold text-lg ml-1">{optimalK}</span>
          </div>
        )}

        {elbowData.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="text-sm font-bold text-gray-700 mb-3">Elbow Method (WCSS vs K)</h3>
              <ResponsiveContainer width="100%" height={240}>
                <LineChart data={elbowData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="k" label={{ value: 'K', position: 'insideBottom', offset: -2 }} tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip formatter={(v) => [v.toFixed(2), 'WCSS']} />
                  <Line type="monotone" dataKey="wcss" stroke="#3b82f6" strokeWidth={2} dot={{ fill: '#3b82f6', r: 4 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
            {silhouetteData.length > 0 && (
              <div>
                <h3 className="text-sm font-bold text-gray-700 mb-3">Silhouette Score vs K</h3>
                <ResponsiveContainer width="100%" height={240}>
                  <LineChart data={silhouetteData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="k" label={{ value: 'K', position: 'insideBottom', offset: -2 }} tick={{ fontSize: 12 }} />
                    <YAxis domain={[0, 1]} tick={{ fontSize: 12 }} />
                    <Tooltip formatter={(v) => [v.toFixed(4), 'Silhouette']} />
                    <Line type="monotone" dataKey="score" stroke="#10b981" strokeWidth={2} dot={{ fill: '#10b981', r: 4 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Step 2: Train Model */}
      <div className="card">
        <h2 className="section-title flex items-center gap-2">
          <SlidersHorizontal size={20} className="text-blue-600" />
          Step 2: Train Clustering Model
        </h2>

        {/* Algorithm Tabs */}
        <div className="flex gap-1 mb-6 p-1 bg-gray-100 rounded-xl w-fit">
          {ALGO_TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveAlgo(tab.id)}
              className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                activeAlgo === tab.id
                  ? 'bg-white text-blue-700 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Algorithm Params */}
        <div className="mb-6 grid grid-cols-1 sm:grid-cols-3 gap-4">
          {activeAlgo === 'kmeans' && (
            <div>
              <label className="label">Number of Clusters (K)</label>
              <input
                type="number"
                min={2}
                max={15}
                value={kmeansK}
                onChange={(e) => setKmeansK(Number(e.target.value))}
                className="input-field"
              />
              {optimalK && (
                <button
                  onClick={() => setKmeansK(optimalK)}
                  className="mt-1 text-xs text-blue-600 underline"
                >
                  Use recommended K={optimalK}
                </button>
              )}
            </div>
          )}
          {activeAlgo === 'hierarchical' && (
            <>
              <div>
                <label className="label">Number of Clusters (K)</label>
                <input
                  type="number"
                  min={2}
                  max={15}
                  value={hierK}
                  onChange={(e) => setHierK(Number(e.target.value))}
                  className="input-field"
                />
              </div>
              <div>
                <label className="label">Linkage</label>
                <select
                  value={hierLinkage}
                  onChange={(e) => setHierLinkage(e.target.value)}
                  className="input-field"
                >
                  <option value="ward">Ward</option>
                  <option value="complete">Complete</option>
                  <option value="average">Average</option>
                  <option value="single">Single</option>
                </select>
              </div>
            </>
          )}
          {activeAlgo === 'dbscan' && (
            <>
              <div>
                <label className="label">Epsilon (eps)</label>
                <input
                  type="number"
                  step="0.1"
                  min={0.1}
                  value={dbscanEps}
                  onChange={(e) => setDbscanEps(Number(e.target.value))}
                  className="input-field"
                />
              </div>
              <div>
                <label className="label">Min Samples</label>
                <input
                  type="number"
                  min={2}
                  value={dbscanMinSamples}
                  onChange={(e) => setDbscanMinSamples(Number(e.target.value))}
                  className="input-field"
                />
              </div>
            </>
          )}
        </div>

        {trainError && <div className="mb-4"><ErrorAlert message={trainError} onDismiss={() => setTrainError('')} /></div>}

        <button
          onClick={handleTrain}
          disabled={training}
          className="btn-success flex items-center gap-2 disabled:opacity-50"
        >
          {training ? (
            <><GitBranch size={16} className="animate-spin" /> Training...</>
          ) : (
            <><Play size={16} /> Train Model</>
          )}
        </button>

        {training && <LoadingSpinner message="Training clustering model..." />}

        {/* Results */}
        {trainResult && (
          <div className="mt-6 space-y-6">
            <div className="flex items-center gap-2 text-green-700">
              <CheckCircle size={18} />
              <span className="font-semibold text-sm">Model trained successfully — {trainResult.algorithm?.toUpperCase()}</span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <MetricCard
                title="Silhouette Score"
                value={trainResult.silhouette_score != null ? trainResult.silhouette_score.toFixed(4) : '—'}
                subtitle="Higher is better"
                color="green"
              />
              <MetricCard
                title="Davies-Bouldin"
                value={trainResult.davies_bouldin_score != null ? trainResult.davies_bouldin_score.toFixed(4) : '—'}
                subtitle="Lower is better"
                color="orange"
              />
              <MetricCard
                title="WCSS"
                value={trainResult.wcss != null ? trainResult.wcss.toFixed(2) : 'N/A'}
                color="blue"
              />
              <MetricCard
                title="Clusters Found"
                value={trainResult.n_clusters ?? '—'}
                color="purple"
              />
            </div>

            {/* DBSCAN noise */}
            {trainResult.noise_points != null && (
              <div className="badge-yellow px-3 py-1.5 text-sm">
                Noise Points: {trainResult.noise_points}
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* PCA Scatter */}
              {Object.keys(pcaData).length > 0 && (
                <div>
                  <h3 className="text-sm font-bold text-gray-700 mb-3">PCA Scatter Plot (2D)</h3>
                  <ResponsiveContainer width="100%" height={280}>
                    <ScatterChart>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis dataKey="x" name="PC1" tick={{ fontSize: 11 }} />
                      <YAxis dataKey="y" name="PC2" tick={{ fontSize: 11 }} />
                      <ZAxis range={[30, 30]} />
                      <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                      <Legend />
                      {Object.entries(pcaData).map(([clId, pts], i) => (
                        <Scatter
                          key={clId}
                          name={clId === '-1' ? 'Noise' : `Cluster ${clId}`}
                          data={pts}
                          fill={CLUSTER_COLORS[i % CLUSTER_COLORS.length]}
                          opacity={0.75}
                        />
                      ))}
                    </ScatterChart>
                  </ResponsiveContainer>
                </div>
              )}

              {/* Cluster distribution */}
              {clusterDist.length > 0 && (
                <div>
                  <h3 className="text-sm font-bold text-gray-700 mb-3">Cluster Distribution</h3>
                  <ResponsiveContainer width="100%" height={280}>
                    <BarChart data={clusterDist} barSize={40}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                      <YAxis tick={{ fontSize: 12 }} />
                      <Tooltip />
                      <Bar dataKey="customers" radius={[4, 4, 0, 0]}>
                        {clusterDist.map((_, i) => (
                          <Cell key={i} fill={CLUSTER_COLORS[i % CLUSTER_COLORS.length]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
