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
} from 'recharts'
import { BarChart2, AlertTriangle, Database, Copy, Info } from 'lucide-react'
import { datasetAPI } from '../services/api'
import { useAppContext } from '../App'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorAlert from '../components/ErrorAlert'

const COLORS = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#6366f1']

function StatTable({ stats }) {
  if (!stats || Object.keys(stats).length === 0) return null
  const columns = ['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max']
  const features = Object.keys(stats)
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs text-left border-collapse">
        <thead>
          <tr className="bg-gray-50 text-gray-600 uppercase tracking-wide">
            <th className="px-3 py-2 border border-gray-200">Feature</th>
            {columns.map((c) => (
              <th key={c} className="px-3 py-2 border border-gray-200 whitespace-nowrap">{c}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {features.map((feat, i) => (
            <tr key={feat} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
              <td className="px-3 py-2 font-medium text-gray-800 border border-gray-100 whitespace-nowrap">{feat}</td>
              {columns.map((col) => (
                <td key={col} className="px-3 py-2 text-gray-600 border border-gray-100">
                  {stats[feat]?.[col] != null ? Number(stats[feat][col]).toFixed(2) : '—'}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function DataAnalysis() {
  const { appState, updateAppState } = useAppContext()
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const fetchSummary = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await datasetAPI.getSummary()
      if (res.data) {
        setSummary(res.data)
        updateAppState({ dataUploaded: true })
      }
    } catch (e) {
      setError(e.message || 'Failed to load data summary.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSummary()
  }, [])

  if (loading) return <LoadingSpinner message="Loading data analysis..." />

  if (!loading && !summary) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="card text-center py-16">
          <AlertTriangle size={48} className="text-yellow-400 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-gray-700 mb-2">No Dataset Uploaded</h2>
          <p className="text-gray-500 text-sm mb-6">Please upload a CSV dataset first to view analysis.</p>
          <a href="/upload" className="btn-primary inline-flex items-center gap-2">
            Go to Data Upload
          </a>
        </div>
      </div>
    )
  }

  if (loading) return <LoadingSpinner message="Loading data analysis..." />
  if (error) return <ErrorAlert message={error} />

  // Build chart data from summary
  const genderData = summary?.gender_distribution
    ? Object.entries(summary.gender_distribution).map(([k, v]) => ({ name: k, count: v }))
    : []

  const ageData = summary?.age_distribution?.map((b) => ({
    name: `${b.bin_start}-${b.bin_end}`,
    count: b.count,
  })) || []

  const incomeData = summary?.income_distribution?.map((b) => ({
    name: `${b.bin_start}-${b.bin_end}k`,
    count: b.count,
  })) || []

  const spendingData = summary?.spending_distribution?.map((b) => ({
    name: `${b.bin_start}-${b.bin_end}`,
    count: b.count,
  })) || []

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Data Analysis</h1>
        <p className="text-gray-500 text-sm mt-1">Exploratory data analysis of your uploaded dataset.</p>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="card text-center">
          <Database size={24} className="text-blue-500 mx-auto mb-2" />
          <p className="text-2xl font-bold text-gray-900">{summary?.total_records?.toLocaleString() ?? '—'}</p>
          <p className="text-xs text-gray-500 mt-1">Total Records</p>
        </div>
        <div className="card text-center">
          <BarChart2 size={24} className="text-purple-500 mx-auto mb-2" />
          <p className="text-2xl font-bold text-gray-900">{summary?.total_features ?? '—'}</p>
          <p className="text-xs text-gray-500 mt-1">Features</p>
        </div>
        <div className="card text-center">
          <AlertTriangle size={24} className={`mx-auto mb-2 ${summary?.missing_values_total > 0 ? 'text-orange-500' : 'text-green-500'}`} />
          <p className="text-2xl font-bold text-gray-900">{summary?.missing_values_total ?? 0}</p>
          <p className="text-xs text-gray-500 mt-1">Missing Values</p>
        </div>
        <div className="card text-center">
          <Copy size={24} className={`mx-auto mb-2 ${summary?.duplicate_count > 0 ? 'text-red-500' : 'text-green-500'}`} />
          <p className="text-2xl font-bold text-gray-900">{summary?.duplicate_count ?? 0}</p>
          <p className="text-xs text-gray-500 mt-1">Duplicates</p>
        </div>
      </div>

      {/* Descriptive Statistics */}
      {summary?.statistics && (
        <div className="card">
          <h2 className="section-title flex items-center gap-2">
            <Info size={20} className="text-blue-600" />
            Descriptive Statistics
          </h2>
          <StatTable stats={summary.statistics} />
        </div>
      )}

      {/* Missing values breakdown */}
      {summary?.missing_values && Object.keys(summary.missing_values).length > 0 && (
        <div className="card">
          <h2 className="section-title flex items-center gap-2">
            <AlertTriangle size={20} className="text-orange-500" />
            Missing Values by Column
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {Object.entries(summary.missing_values).map(([col, count]) => (
              <div key={col} className="bg-orange-50 border border-orange-200 rounded-lg p-3">
                <p className="text-xs font-semibold text-orange-800 truncate">{col}</p>
                <p className="text-xl font-bold text-orange-700">{count}</p>
                <p className="text-xs text-orange-500">missing</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Dynamic Feature Distributions */}
      {Object.keys(summary?.numerical_distributions || {}).length > 0 && (
        <div>
          <h2 className="text-lg font-bold text-gray-800 mb-4">Numerical Feature Distributions</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {Object.entries(summary.numerical_distributions).map(([feat, bins], idx) => (
              <div key={feat} className="card">
                <h3 className="section-title text-base">{feat} Distribution</h3>
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={bins} barSize={28}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="name" tick={{ fontSize: 10 }} angle={-25} textAnchor="end" height={45} />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Bar dataKey="count" fill={COLORS[idx % COLORS.length]} radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Categorical Distributions */}
      {Object.keys(summary?.categorical_distributions || {}).length > 0 && (
        <div>
          <h2 className="text-lg font-bold text-gray-800 mb-4">Categorical Feature Distributions</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {Object.entries(summary.categorical_distributions).map(([feat, items], idx) => (
              <div key={feat} className="card">
                <h3 className="section-title text-base">{feat} Breakdown</h3>
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={items} barSize={36}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                      {items.map((_, i) => (
                        <Cell key={i} fill={COLORS[(idx + i) % COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Correlation Info */}
      {summary?.correlations && (
        <div className="card">
          <h2 className="section-title">Feature Correlations (with Spending Score)</h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {Object.entries(summary.correlations).map(([feat, val]) => (
              <div key={feat} className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                <p className="text-xs text-gray-500 font-semibold truncate">{feat}</p>
                <p
                  className={`text-xl font-bold mt-1 ${
                    Math.abs(val) > 0.5
                      ? 'text-blue-700'
                      : Math.abs(val) > 0.3
                      ? 'text-green-700'
                      : 'text-gray-500'
                  }`}
                >
                  {Number(val).toFixed(3)}
                </p>
                <p className="text-xs text-gray-400 mt-0.5">
                  {Math.abs(val) > 0.5 ? 'Strong' : Math.abs(val) > 0.3 ? 'Moderate' : 'Weak'}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
