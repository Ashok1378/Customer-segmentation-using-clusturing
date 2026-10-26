import { useState, useEffect } from 'react'
import {
  Cpu,
  AlertTriangle,
  CheckCircle,
  Shuffle,
  Star,
  DollarSign,
  ShoppingCart,
  Calendar,
  TrendingUp,
  User,
  Database,
  History,
} from 'lucide-react'
import { predictionAPI, databaseAPI } from '../services/api'
import { useAppContext } from '../App'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorAlert from '../components/ErrorAlert'

const SEGMENT_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6', '#6366f1']

const SAMPLE_PROFILES = [
  { label: 'Young High Spender', Age: 25, Gender: 'Female', 'Annual Income (k$)': 45, 'Spending Score (1-100)': 85, 'Purchase Frequency': 18 },
  { label: 'Wealthy Low Spender', Age: 55, Gender: 'Male', 'Annual Income (k$)': 120, 'Spending Score (1-100)': 20, 'Purchase Frequency': 5 },
  { label: 'Budget Shopper', Age: 35, Gender: 'Female', 'Annual Income (k$)': 30, 'Spending Score (1-100)': 40, 'Purchase Frequency': 8 },
  { label: 'Premium Customer', Age: 40, Gender: 'Male', 'Annual Income (k$)': 90, 'Spending Score (1-100)': 75, 'Purchase Frequency': 15 },
]

const INITIAL_FORM = {
  Age: '',
  Gender: 'Male',
  'Annual Income (k$)': '',
  'Spending Score (1-100)': '',
  'Purchase Frequency': '',
}

function validate(form) {
  const errors = {}
  const age = Number(form.Age)
  const income = Number(form['Annual Income (k$)'])
  const spending = Number(form['Spending Score (1-100)'])
  const freq = Number(form['Purchase Frequency'])

  if (form.Age === '' || isNaN(age) || age < 0 || age > 120) {
    errors.Age = 'Age must be between 0 and 120.'
  }
  if (form['Annual Income (k$)'] === '' || isNaN(income) || income < 0) {
    errors['Annual Income (k$)'] = 'Annual income must be a non-negative number.'
  }
  if (form['Spending Score (1-100)'] === '' || isNaN(spending) || spending < 0 || spending > 100) {
    errors['Spending Score (1-100)'] = 'Spending score must be between 0 and 100.'
  }
  if (form['Purchase Frequency'] === '' || isNaN(freq) || freq < 0) {
    errors['Purchase Frequency'] = 'Purchase frequency must be a non-negative number.'
  }
  return errors
}

export default function Prediction() {
  const { appState, updateAppState } = useAppContext()
  const [form, setForm] = useState(INITIAL_FORM)
  const [errors, setErrors] = useState({})
  const [predicting, setPredicting] = useState(false)
  const [predError, setPredError] = useState('')
  const [result, setResult] = useState(null)
  const [selectedSample, setSelectedSample] = useState(null)
  const [history, setHistory] = useState([])

  const fetchHistory = async () => {
    try {
      const res = await databaseAPI.getPredictions(10)
      if (Array.isArray(res.data)) {
        setHistory(res.data)
      }
    } catch {
      // ignore
    }
  }

  useEffect(() => {
    fetchHistory()
    // Auto-detect if trained model or segments exist
    clusteringAPI.getSegments().then((res) => {
      const segs = res.data?.profiles || res.data?.segments || []
      if (segs.length > 0) {
        updateAppState({ modelTrained: true, preprocessed: true, dataUploaded: true })
      }
    }).catch(() => {})
  }, [])

  const handleChange = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }))
    if (errors[field]) {
      setErrors((prev) => { const e = { ...prev }; delete e[field]; return e })
    }
  }

  const applySample = (sample) => {
    setSelectedSample(sample.label)
    setForm({
      Age: String(sample.Age),
      Gender: sample.Gender,
      'Annual Income (k$)': String(sample['Annual Income (k$)']),
      'Spending Score (1-100)': String(sample['Spending Score (1-100)']),
      'Purchase Frequency': String(sample['Purchase Frequency']),
    })
    setErrors({})
    setResult(null)
  }

  const handleAutoTrain = async () => {
    setPredicting(true)
    setPredError('')
    try {
      await clusteringAPI.trainAll()
      updateAppState({ modelTrained: true, preprocessed: true, dataUploaded: true })
      fetchHistory()
    } catch (e) {
      setPredError(e.message || 'Auto-training failed.')
    } finally {
      setPredicting(false)
    }
  }

  const handlePredict = async () => {
    const validationErrors = validate(form)
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors)
      return
    }
    setPredicting(true)
    setPredError('')
    setResult(null)
    try {
      const incVal = Number(form['Annual Income (k$)'])
      const spendVal = Number(form['Spending Score (1-100)'])
      const freqVal = Number(form['Purchase Frequency'] || 0)
      const ageVal = Number(form.Age)

      const payload = {
        age: ageVal,
        gender: form.Gender,
        annual_income: incVal,
        spending_score: spendVal,
        purchase_frequency: freqVal,
        Age: ageVal,
        Gender: form.Gender,
        AnnualIncome: incVal,
        'Annual Income (k$)': incVal,
        SpendingScore: spendVal,
        'Spending Score (1-100)': spendVal,
        PurchaseFrequency: freqVal,
        'Purchase Frequency': freqVal,
      }
      const res = await predictionAPI.predict(payload)
      setResult(res.data)
      updateAppState({ modelTrained: true })
      fetchHistory()
    } catch (e) {
      setPredError(e.message || 'Prediction failed.')
    } finally {
      setPredicting(false)
    }
  }

  const handleReset = () => {
    setForm(INITIAL_FORM)
    setErrors({})
    setResult(null)
    setPredError('')
    setSelectedSample(null)
  }

  const resultColor = result ? SEGMENT_COLORS[(result.cluster_id ?? 0) % SEGMENT_COLORS.length] : '#3b82f6'

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Customer Segment Prediction</h1>
        <p className="text-gray-500 text-sm mt-1">Enter customer attributes to predict their segment.</p>
      </div>

      {!appState.modelTrained && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-3">
            <AlertTriangle size={20} className="text-amber-500 flex-shrink-0" />
            <p className="text-sm text-amber-800">
              No model is loaded yet in your session. You can click <strong>Auto-Train</strong> or fill the form below to auto-predict.
            </p>
          </div>
          <button
            onClick={handleAutoTrain}
            disabled={predicting}
            className="btn-primary text-xs py-1.5 px-3 flex items-center gap-1.5"
          >
            <Cpu size={14} /> ⚡ Auto-Train Model
          </button>
        </div>
      )}

      {/* Sample profiles */}
      <div className="card">
        <h2 className="text-sm font-bold text-gray-700 mb-3 flex items-center gap-2">
          <Shuffle size={16} className="text-blue-500" />
          Try Sample Profiles
        </h2>
        <div className="flex flex-wrap gap-2">
          {SAMPLE_PROFILES.map((s) => (
            <button
              key={s.label}
              onClick={() => applySample(s)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                selectedSample === s.label
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-gray-50 text-gray-700 border-gray-200 hover:border-blue-400'
              }`}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Input Form */}
        <div className="card">
          <h2 className="section-title flex items-center gap-2">
            <User size={20} className="text-blue-600" />
            Customer Attributes
          </h2>

          <div className="space-y-4">
            {/* Age */}
            <div>
              <label className="label">Age <span className="text-red-500">*</span></label>
              <input
                type="number"
                min={0}
                max={120}
                value={form.Age}
                onChange={(e) => handleChange('Age', e.target.value)}
                placeholder="e.g. 35"
                className={`input-field ${errors.Age ? 'border-red-400 focus:ring-red-400' : ''}`}
              />
              {errors.Age && <p className="text-red-500 text-xs mt-1">{errors.Age}</p>}
            </div>

            {/* Gender */}
            <div>
              <label className="label">Gender <span className="text-red-500">*</span></label>
              <select
                value={form.Gender}
                onChange={(e) => handleChange('Gender', e.target.value)}
                className="input-field"
              >
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Other">Other</option>
              </select>
            </div>

            {/* Annual Income */}
            <div>
              <label className="label">Annual Income (k$) <span className="text-red-500">*</span></label>
              <input
                type="number"
                min={0}
                step={1}
                value={form['Annual Income (k$)']}
                onChange={(e) => handleChange('Annual Income (k$)', e.target.value)}
                placeholder="e.g. 60"
                className={`input-field ${errors['Annual Income (k$)'] ? 'border-red-400 focus:ring-red-400' : ''}`}
              />
              {errors['Annual Income (k$)'] && (
                <p className="text-red-500 text-xs mt-1">{errors['Annual Income (k$)']}</p>
              )}
            </div>

            {/* Spending Score */}
            <div>
              <label className="label">Spending Score (1-100) <span className="text-red-500">*</span></label>
              <input
                type="number"
                min={0}
                max={100}
                value={form['Spending Score (1-100)']}
                onChange={(e) => handleChange('Spending Score (1-100)', e.target.value)}
                placeholder="e.g. 72"
                className={`input-field ${errors['Spending Score (1-100)'] ? 'border-red-400 focus:ring-red-400' : ''}`}
              />
              {errors['Spending Score (1-100)'] && (
                <p className="text-red-500 text-xs mt-1">{errors['Spending Score (1-100)']}</p>
              )}
            </div>

            {/* Purchase Frequency */}
            <div>
              <label className="label">Purchase Frequency <span className="text-red-500">*</span></label>
              <input
                type="number"
                min={0}
                step={1}
                value={form['Purchase Frequency']}
                onChange={(e) => handleChange('Purchase Frequency', e.target.value)}
                placeholder="e.g. 10"
                className={`input-field ${errors['Purchase Frequency'] ? 'border-red-400 focus:ring-red-400' : ''}`}
              />
              {errors['Purchase Frequency'] && (
                <p className="text-red-500 text-xs mt-1">{errors['Purchase Frequency']}</p>
              )}
            </div>
          </div>

          {predError && (
            <div className="mt-4">
              <ErrorAlert message={predError} onDismiss={() => setPredError('')} />
            </div>
          )}

          <div className="flex gap-3 mt-6">
            <button
              onClick={handlePredict}
              disabled={predicting}
              className="btn-primary flex items-center gap-2 disabled:opacity-50 flex-1 justify-center"
            >
              {predicting ? (
                <><Cpu size={16} className="animate-spin" /> Predicting...</>
              ) : (
                <><Cpu size={16} /> Predict Segment</>
              )}
            </button>
            <button onClick={handleReset} className="btn-secondary text-sm">Reset</button>
          </div>

          {predicting && <LoadingSpinner message="Predicting customer segment..." />}
        </div>

        {/* Result */}
        <div>
          {result ? (
            <div className="rounded-xl overflow-hidden shadow-sm border-2" style={{ borderColor: resultColor }}>
              {/* Result header */}
              <div className="px-6 py-5 text-white" style={{ background: resultColor }}>
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-10 h-10 bg-white bg-opacity-20 rounded-xl flex items-center justify-center">
                    <CheckCircle size={22} />
                  </div>
                  <div>
                    <p className="text-xs font-semibold opacity-80">Predicted Cluster {result.cluster_id}</p>
                    <h2 className="text-xl font-bold leading-tight">
                      {result.segment_label || `Segment ${result.cluster_id}`}
                    </h2>
                  </div>
                </div>
              </div>

              {/* Result body */}
              <div className="bg-white p-5 space-y-4">
                {/* Segment profile */}
                {result.segment_profile && (
                  <div>
                    <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Segment Averages</p>
                    <div className="grid grid-cols-2 gap-3">
                      {[
                        { label: 'Avg Age', value: result.segment_profile.avg_age?.toFixed(1), icon: <Calendar size={14} /> },
                        {
                          label: 'Avg Income',
                          value: result.segment_profile.avg_income != null
                            ? (result.segment_profile.avg_income > 1000
                                ? `$${(result.segment_profile.avg_income / 1000).toFixed(1)}k`
                                : `$${result.segment_profile.avg_income.toFixed(1)}k`)
                            : '—',
                          icon: <DollarSign size={14} />,
                        },
                        {
                          label: 'Avg Spending',
                          value: (result.segment_profile.avg_spending_score ?? result.segment_profile.avg_spending)?.toFixed(1),
                          icon: <ShoppingCart size={14} />,
                        },
                        {
                          label: 'Avg Freq',
                          value: (result.segment_profile.avg_purchase_frequency ?? result.segment_profile.avg_frequency)?.toFixed(1),
                          icon: <TrendingUp size={14} />,
                        },
                      ].map(({ label, value, icon }) => (
                        <div key={label} className="flex items-center gap-2 bg-gray-50 rounded-lg p-2.5">
                          <div style={{ color: resultColor }}>{icon}</div>
                          <div>
                            <p className="text-xs text-gray-400">{label}</p>
                            <p className="text-sm font-bold text-gray-800">{value ?? '—'}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Characteristics */}
                {result.characteristics && result.characteristics.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Characteristics</p>
                    <ul className="space-y-1.5">
                      {result.characteristics.map((c, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                          <Star size={12} className="flex-shrink-0 mt-0.5" style={{ color: resultColor }} />
                          {c}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Confidence */}
                {result.confidence != null && (
                  <div className="pt-2 border-t border-gray-100">
                    <p className="text-xs text-gray-500">
                      Model confidence: <span className="font-bold text-gray-700">{(result.confidence * 100).toFixed(1)}%</span>
                    </p>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="card h-full flex flex-col items-center justify-center text-center py-16 text-gray-300">
              <Cpu size={48} className="mb-4 opacity-30" />
              <p className="text-gray-400 font-medium">Prediction result will appear here</p>
              <p className="text-gray-300 text-sm mt-1">Fill in the form and click "Predict Segment"</p>
            </div>
          )}
        </div>
      </div>


      {/* Database Prediction History */}
      {history.length > 0 && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="section-title flex items-center gap-2 mb-0">
              <Database size={18} className="text-blue-600" />
              Database Prediction History
            </h2>
            <span className="text-xs text-gray-500 font-medium">
              Saved in SQLite Database ({history.length} records)
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead>
                <tr className="bg-gray-50 text-gray-600 uppercase tracking-wide">
                  <th className="px-3 py-2">ID</th>
                  <th className="px-3 py-2">Gender</th>
                  <th className="px-3 py-2">Age</th>
                  <th className="px-3 py-2">Income</th>
                  <th className="px-3 py-2">Spending</th>
                  <th className="px-3 py-2">Frequency</th>
                  <th className="px-3 py-2">Cluster</th>
                  <th className="px-3 py-2">Segment Persona</th>
                  <th className="px-3 py-2">Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {history.map((h) => (
                  <tr key={h.id} className="border-t border-gray-100 hover:bg-gray-50">
                    <td className="px-3 py-2 font-mono text-gray-500">#{h.id}</td>
                    <td className="px-3 py-2 font-medium text-gray-800">{h.gender || '—'}</td>
                    <td className="px-3 py-2 text-gray-600">{h.age ?? '—'}</td>
                    <td className="px-3 py-2 text-gray-600">${h.annual_income?.toLocaleString() ?? '—'}</td>
                    <td className="px-3 py-2 text-gray-600">{h.spending_score ?? '—'}/100</td>
                    <td className="px-3 py-2 text-gray-600">{h.purchase_frequency ?? '—'}</td>
                    <td className="px-3 py-2">
                      <span className="badge-blue">Cluster {h.predicted_cluster}</span>
                    </td>
                    <td className="px-3 py-2 font-semibold text-gray-800">{h.segment_label}</td>
                    <td className="px-3 py-2 text-gray-400 text-xs">{h.created_at || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

