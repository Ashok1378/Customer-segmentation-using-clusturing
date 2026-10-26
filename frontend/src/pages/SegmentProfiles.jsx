import { useEffect, useState } from 'react'
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Legend,
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
} from 'recharts'
import {
  Users,
  AlertTriangle,
  Download,
  Star,
  TrendingUp,
  DollarSign,
  ShoppingCart,
  Calendar,
} from 'lucide-react'
import { clusteringAPI } from '../services/api'
import { useAppContext } from '../App'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorAlert from '../components/ErrorAlert'

const SEGMENT_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6', '#6366f1']

const SEGMENT_HEADER_COLORS = [
  'from-blue-500 to-blue-700',
  'from-green-500 to-green-700',
  'from-amber-500 to-amber-700',
  'from-red-500 to-red-700',
  'from-purple-500 to-purple-700',
  'from-pink-500 to-pink-700',
  'from-teal-500 to-teal-700',
  'from-indigo-500 to-indigo-700',
]

const RADIAN = Math.PI / 180
const renderCustomLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }) => {
  const radius = innerRadius + (outerRadius - innerRadius) * 0.5
  const x = cx + radius * Math.cos(-midAngle * RADIAN)
  const y = cy + radius * Math.sin(-midAngle * RADIAN)
  return percent > 0.05 ? (
    <text x={x} y={y} fill="white" textAnchor="middle" dominantBaseline="central" fontSize={12} fontWeight="bold">
      {`${(percent * 100).toFixed(0)}%`}
    </text>
  ) : null
}

function SegmentCard({ segment, index }) {
  const colorGradient = SEGMENT_HEADER_COLORS[index % SEGMENT_HEADER_COLORS.length]
  const color = SEGMENT_COLORS[index % SEGMENT_COLORS.length]

  return (
    <div className="rounded-xl overflow-hidden shadow-sm border border-gray-200">
      {/* Header */}
      <div className={`bg-gradient-to-r ${colorGradient} px-5 py-4 text-white`}>
        <div className="flex items-start justify-between">
          <div>
            <p className="text-xs font-semibold opacity-80">Cluster {segment.cluster_id}</p>
            <h3 className="text-lg font-bold mt-0.5 leading-tight">{segment.label || `Segment ${segment.cluster_id}`}</h3>
          </div>
          <div className="text-right">
            <p className="text-2xl font-bold">{segment.count?.toLocaleString()}</p>
            <p className="text-xs opacity-80">customers ({segment.percentage?.toFixed(1)}%)</p>
          </div>
        </div>
      </div>

      {/* Metrics */}
      <div className="bg-white p-4">
        <div className="grid grid-cols-2 gap-3 mb-4">
          {[
            { label: 'Avg Age', value: segment.avg_age?.toFixed(1), icon: <Calendar size={14} /> },
            { label: 'Avg Income', value: segment.avg_income_k != null ? `$${segment.avg_income_k.toFixed(1)}k` : '—', icon: <DollarSign size={14} /> },
            { label: 'Avg Spending', value: segment.avg_spending?.toFixed(1), icon: <ShoppingCart size={14} /> },
            { label: 'Avg Frequency', value: segment.avg_frequency?.toFixed(1), icon: <TrendingUp size={14} /> },
          ].map(({ label, value, icon }) => (
            <div key={label} className="bg-gray-50 rounded-lg p-2.5 flex items-center gap-2">
              <div style={{ color }} className="flex-shrink-0">{icon}</div>
              <div>
                <p className="text-xs text-gray-500">{label}</p>
                <p className="text-sm font-bold text-gray-800">{value ?? '—'}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Characteristics */}
        {segment.characteristics && segment.characteristics.length > 0 && (
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Characteristics</p>
            <ul className="space-y-1">
              {segment.characteristics.map((c, i) => (
                <li key={i} className="flex items-start gap-2 text-xs text-gray-700">
                  <Star size={10} className="flex-shrink-0 mt-0.5" style={{ color }} />
                  {c}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}

export default function SegmentProfiles() {
  const { appState, updateAppState } = useAppContext()
  const [segments, setSegments] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const normalizeSegments = (rawList) => {
    const list = Array.isArray(rawList) ? rawList : []
    const total = list.reduce((acc, curr) => acc + (curr.size || curr.count || 0), 0)
    return list.map((s) => {
      const count = s.size ?? s.count ?? 0
      const pct = total > 0 ? (count / total) * 100 : (s.percentage ?? 0)
      const inc = s.avg_income ?? 0
      const incomeK = inc > 1000 ? inc / 1000 : inc
      const spending = s.avg_spending_score ?? s.avg_spending ?? 0
      const freq = s.avg_purchase_frequency ?? s.avg_frequency ?? 0
      return {
        ...s,
        count,
        percentage: pct,
        avg_income_k: incomeK,
        avg_spending: spending,
        avg_frequency: freq,
      }
    })
  }

  const fetchSegments = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await clusteringAPI.getSegments()
      const raw = res.data?.profiles || res.data?.segments || (Array.isArray(res.data) ? res.data : [])
      const normalized = normalizeSegments(raw)
      setSegments(normalized)
      if (normalized.length > 0) {
        updateAppState({ modelTrained: true, preprocessed: true, dataUploaded: true })
      }
    } catch (e) {
      setError(e.message || 'Failed to load segment data.')
    } finally {
      setLoading(false)
    }
  }

  const handleTrainAll = async () => {
    setLoading(true)
    setError('')
    try {
      await clusteringAPI.trainAll()
      await fetchSegments()
      updateAppState({ modelTrained: true, preprocessed: true, dataUploaded: true })
    } catch (e) {
      setError(e.message || 'Failed to train and generate profiles.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSegments()
  }, [])

  if (loading) return <LoadingSpinner message="Loading segment profiles..." />

  // Derived chart data
  const pieData = segments.map((s, i) => ({
    name: s.label || `Cluster ${s.cluster_id}`,
    value: s.count || 0,
  }))

  const avgMetricsData = segments.map((s) => ({
    name: s.label || `Cluster ${s.cluster_id}`,
    Age: Number(s.avg_age?.toFixed(1) ?? 0),
    Income: Number(s.avg_income_k?.toFixed(1) ?? 0),
    Spending: Number(s.avg_spending?.toFixed(1) ?? 0),
    Frequency: Number(s.avg_frequency?.toFixed(1) ?? 0),
  }))

  const radarData = ['Age', 'Income', 'Spending', 'Frequency'].map((metric) => {
    const entry = { metric }
    segments.forEach((s) => {
      const key = s.label || `Cluster ${s.cluster_id}`
      if (metric === 'Age') entry[key] = s.avg_age ?? 0
      if (metric === 'Income') entry[key] = s.avg_income_k ?? 0
      if (metric === 'Spending') entry[key] = s.avg_spending ?? 0
      if (metric === 'Frequency') entry[key] = s.avg_frequency ?? 0
    })
    return entry
  })

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Segment Profiles</h1>
          <p className="text-gray-500 text-sm mt-1">Detailed profiles of identified customer segments.</p>
        </div>
        <div className="flex gap-3">
          <button onClick={fetchSegments} className="btn-secondary text-sm flex items-center gap-2">
            Refresh
          </button>
          <button onClick={clusteringAPI.downloadReport} className="btn-primary text-sm flex items-center gap-2">
            <Download size={15} /> Download Profiles
          </button>
        </div>
      </div>

      {error && <ErrorAlert message={error} onDismiss={() => setError('')} />}

      {segments.length === 0 && !loading && (
        <div className="card text-center py-16">
          <AlertTriangle size={48} className="text-yellow-400 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-gray-700 mb-2">No Profiles Found</h2>
          <p className="text-gray-500 text-sm max-w-sm mx-auto mb-6">
            Train a clustering model or click below to automatically train and generate segment profiles.
          </p>
          <button
            onClick={handleTrainAll}
            disabled={loading}
            className="btn-primary inline-flex items-center gap-2"
          >
            ⚡ Generate Segment Profiles Now
          </button>
        </div>
      )}

      {segments.length > 0 && (
        <>
          {/* Segment Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
            {segments.map((seg, i) => (
              <SegmentCard key={seg.cluster_id ?? i} segment={seg} index={i} />
            ))}
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Pie chart */}
            <div className="card">
              <h2 className="section-title flex items-center gap-2">
                <Users size={20} className="text-blue-600" />
                Segment Distribution
              </h2>
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    outerRadius={110}
                    dataKey="value"
                    labelLine={false}
                    label={renderCustomLabel}
                  >
                    {pieData.map((_, i) => (
                      <Cell key={i} fill={SEGMENT_COLORS[i % SEGMENT_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(v) => [`${v} customers`, 'Count']} />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>

            {/* Average metrics grouped bar */}
            <div className="card">
              <h2 className="section-title">Average Metrics by Segment</h2>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={avgMetricsData} barSize={12}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Bar dataKey="Age" fill="#3b82f6" radius={[2, 2, 0, 0]} />
                  <Bar dataKey="Income" fill="#10b981" radius={[2, 2, 0, 0]} />
                  <Bar dataKey="Spending" fill="#f59e0b" radius={[2, 2, 0, 0]} />
                  <Bar dataKey="Frequency" fill="#8b5cf6" radius={[2, 2, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Radar Chart */}
          {segments.length >= 2 && (
            <div className="card">
              <h2 className="section-title">Multi-Metric Comparison (Radar)</h2>
              <ResponsiveContainer width="100%" height={320}>
                <RadarChart data={radarData}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="metric" tick={{ fontSize: 12 }} />
                  <PolarRadiusAxis tick={{ fontSize: 10 }} />
                  {segments.map((s, i) => {
                    const name = s.label || `Cluster ${s.cluster_id}`
                    return (
                      <Radar
                        key={i}
                        name={name}
                        dataKey={name}
                        stroke={SEGMENT_COLORS[i % SEGMENT_COLORS.length]}
                        fill={SEGMENT_COLORS[i % SEGMENT_COLORS.length]}
                        fillOpacity={0.15}
                      />
                    )
                  })}
                  <Tooltip />
                  <Legend />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          )}
        </>
      )}
    </div>
  )
}
