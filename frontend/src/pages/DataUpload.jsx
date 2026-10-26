import { useState, useRef, useCallback } from 'react'
import {
  Upload,
  FileText,
  CheckCircle,
  AlertTriangle,
  Database,
  Settings,
  Download,
  X,
  RefreshCw,
} from 'lucide-react'
import { datasetAPI, clusteringAPI } from '../services/api'
import { useAppContext } from '../App'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorAlert from '../components/ErrorAlert'
import MetricCard from '../components/MetricCard'

const DEFAULT_FEATURES = ['Age', 'AnnualIncome', 'SpendingScore', 'PurchaseFrequency']

export default function DataUpload() {
  const { updateAppState, appState } = useAppContext()
  const fileInputRef = useRef(null)

  // Upload state
  const [dragging, setDragging] = useState(false)
  const [selectedFile, setSelectedFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState('')
  const [summary, setSummary] = useState(null)
  const [sampleRows, setSampleRows] = useState([])
  const [sampleColumns, setSampleColumns] = useState([])

  // Preprocessing state
  const [selectedFeatures, setSelectedFeatures] = useState(new Set(DEFAULT_FEATURES))
  const [removeDuplicates, setRemoveDuplicates] = useState(true)
  const [preprocessing, setPreprocessing] = useState(false)
  const [preprocessError, setPreprocessError] = useState('')
  const [preprocessResult, setPreprocessResult] = useState(null)

  // Compute available features dynamically from uploaded dataset
  const availableFeatures =
    summary?.numerical_features && summary.numerical_features.length > 0
      ? summary.numerical_features
      : (sampleColumns.length > 0
          ? sampleColumns.filter((c) => !c.toLowerCase().includes('id') && !c.toLowerCase().includes('station'))
          : DEFAULT_FEATURES)

  const validateFile = (file) => {
    if (!file) return 'No file selected.'
    if (!file.name.endsWith('.csv')) return 'Only CSV files are supported.'
    if (file.size > 50 * 1024 * 1024) return 'File size must be less than 50 MB.'
    return null
  }

  const handleFileSelected = async (file) => {
    const err = validateFile(file)
    if (err) { setUploadError(err); return }
    setUploadError('')
    setSelectedFile(file)
    await doUpload(file)
  }

  const loadBuiltinDataset = async (datasetPath, filename) => {
    try {
      setUploading(true)
      setUploadError('')
      const response = await fetch(datasetPath)
      if (!response.ok) throw new Error('Could not fetch dataset file')
      const blob = await response.blob()
      const file = new File([blob], filename, { type: 'text/csv' })
      setSelectedFile(file)
      await doUpload(file)
    } catch (e) {
      setUploadError('Failed to load dataset: ' + e.message)
    } finally {
      setUploading(false)
    }
  }

  const doUpload = async (file) => {
    setUploading(true)
    setSummary(null)
    setSampleRows([])
    setUploadError('')
    try {
      const res = await datasetAPI.upload(file)
      const data = res.data
      const summ = data.summary || data
      setSummary(summ)

      // Fetch sample
      const sampleRes = await datasetAPI.getSample()
      const cols = sampleRes.data?.columns || []
      if (cols.length > 0) setSampleColumns(cols)
      if (sampleRes.data?.rows) setSampleRows(sampleRes.data.rows)

      // Auto-select numerical features from the new dataset
      const numCols = summ.numerical_features || cols.filter(c => !c.toLowerCase().includes('id') && !c.toLowerCase().includes('station'))
      if (numCols && numCols.length > 0) {
        setSelectedFeatures(new Set(numCols))
      }

      // Auto-trigger preprocessing so Clustering and Comparison are ready immediately
      let autoPreprocessed = false
      try {
        const feats = (numCols && numCols.length >= 2) ? numCols : ['Age', 'AnnualIncome', 'SpendingScore', 'PurchaseFrequency']
        const prepRes = await clusteringAPI.preprocess({
          features: feats,
          remove_duplicates: true,
        })
        setPreprocessResult(prepRes.data)
        autoPreprocessed = true
      } catch (prepErr) {
        // Manual preprocessing will still be available
      }

      updateAppState({
        dataUploaded: true,
        uploadedFilename: file.name,
        datasetSummary: summ,
        preprocessed: autoPreprocessed,
        modelTrained: false,
      })
    } catch (e) {
      setUploadError(e.message || 'Upload failed.')
    } finally {
      setUploading(false)
    }
  }

  const onDrop = useCallback((e) => {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files?.[0]
    if (file) handleFileSelected(file)
  }, [])

  const onDragOver = (e) => { e.preventDefault(); setDragging(true) }
  const onDragLeave = () => setDragging(false)

  const toggleFeature = (feat) => {
    setSelectedFeatures((prev) => {
      const next = new Set(prev)
      next.has(feat) ? next.delete(feat) : next.add(feat)
      return next
    })
  }

  const handlePreprocess = async () => {
    if (selectedFeatures.size < 2) {
      setPreprocessError('Please select at least 2 features.')
      return
    }
    setPreprocessing(true)
    setPreprocessError('')
    setPreprocessResult(null)
    try {
      const res = await clusteringAPI.preprocess({
        features: Array.from(selectedFeatures),
        remove_duplicates: removeDuplicates,
        imputation_strategy: 'median',
      })
      setPreprocessResult(res.data)
      updateAppState({
        preprocessed: true,
        selectedFeatures: Array.from(selectedFeatures),
      })
    } catch (e) {
      setPreprocessError(e.message || 'Preprocessing failed.')
    } finally {
      setPreprocessing(false)
    }
  }

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Data Upload</h1>
        <p className="text-gray-500 text-sm mt-1">Upload your customer dataset CSV and configure preprocessing options.</p>
      </div>

      {/* Upload Zone */}
      <div className="card">
        <h2 className="section-title flex items-center gap-2">
          <Upload size={20} className="text-blue-600" />
          Upload Dataset
        </h2>

        <div
          onDrop={onDrop}
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all ${
            dragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            className="hidden"
            onChange={(e) => handleFileSelected(e.target.files?.[0])}
          />
          <Upload size={36} className={`mx-auto mb-3 ${dragging ? 'text-blue-500' : 'text-gray-400'}`} />
          <p className="text-gray-700 font-semibold">Drag &amp; drop your CSV file here</p>
          <p className="text-gray-400 text-sm mt-1">or click to browse — Max 50 MB, CSV only</p>
          {selectedFile && (
            <div className="mt-4 inline-flex items-center gap-2 bg-blue-50 text-blue-700 px-4 py-2 rounded-lg text-sm font-medium">
              <FileText size={15} />
              {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
            </div>
          )}
        </div>

        {uploadError && <div className="mt-3"><ErrorAlert message={uploadError} onDismiss={() => setUploadError('')} /></div>}
        {uploading && <LoadingSpinner message="Uploading and processing file..." />}

        {/* Sample Dataset Quick Actions */}
        <div className="mt-4 pt-3 border-t border-gray-100 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2">
            <span className="text-gray-500 font-medium">Try Ready-Made Datasets:</span>
            <button
              type="button"
              onClick={() => loadBuiltinDataset('/supermarket_customer_dataset_500.csv', 'supermarket_customer_dataset_500.csv')}
              className="px-2.5 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-700 font-semibold rounded-lg border border-blue-200 transition-colors flex items-center gap-1.5"
            >
              ⚡ Load Supermarket Dataset (500 Customers)
            </button>
            <button
              type="button"
              onClick={() => loadBuiltinDataset('/sample_customer_data.csv', 'sample_customer_data.csv')}
              className="px-2.5 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium rounded-lg border border-gray-300 transition-colors flex items-center gap-1.5"
            >
              ⚡ Load Sample Dataset (200 Customers)
            </button>
          </div>

          <div className="flex items-center gap-2 text-gray-400">
            <span>Download CSV:</span>
            <a
              href="/supermarket_customer_dataset_500.csv"
              download="supermarket_customer_dataset_500.csv"
              className="text-blue-600 underline hover:text-blue-800 font-medium"
            >
              Supermarket 500 CSV
            </a>
            <span>|</span>
            <a
              href="/sample_customer_data.csv"
              download="sample_customer_data.csv"
              className="text-blue-600 underline hover:text-blue-800 font-medium"
            >
              Sample 200 CSV
            </a>
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div>
          <h2 className="section-title flex items-center gap-2">
            <Database size={20} className="text-blue-600" />
            Dataset Summary
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-4">
            <MetricCard title="Records" value={summary.total_records?.toLocaleString() ?? '—'} icon={<Database size={18} />} color="blue" />
            <MetricCard title="Columns" value={summary.total_features ?? '—'} icon={<FileText size={18} />} color="purple" />
            <MetricCard title="Missing Values" value={summary.missing_values_total ?? 0} icon={<AlertTriangle size={18} />} color={summary.missing_values_total > 0 ? 'orange' : 'green'} />
            <MetricCard title="Duplicates" value={summary.duplicate_count ?? 0} icon={<RefreshCw size={18} />} color={summary.duplicate_count > 0 ? 'red' : 'green'} />
          </div>

          {/* Column info */}
          {summary.column_info && (
            <div className="card overflow-auto">
              <h3 className="text-sm font-bold text-gray-700 mb-3">Column Information</h3>
              <table className="w-full text-xs text-left">
                <thead>
                  <tr className="bg-gray-50 text-gray-600 uppercase tracking-wide">
                    <th className="px-3 py-2">Column</th>
                    <th className="px-3 py-2">Type</th>
                    <th className="px-3 py-2">Missing</th>
                    <th className="px-3 py-2">Unique</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(summary.column_info).map(([col, info]) => (
                    <tr key={col} className="border-t border-gray-100">
                      <td className="px-3 py-2 font-medium text-gray-800">{col}</td>
                      <td className="px-3 py-2 text-gray-500">{info.dtype || '—'}</td>
                      <td className="px-3 py-2 text-gray-500">{info.missing ?? 0}</td>
                      <td className="px-3 py-2 text-gray-500">{info.unique ?? '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Data Preview */}
      {sampleRows.length > 0 && (
        <div className="card overflow-auto">
          <h2 className="section-title flex items-center gap-2">
            <FileText size={20} className="text-blue-600" />
            Data Preview (first {sampleRows.length} rows)
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left border-collapse">
              <thead>
                <tr className="bg-gray-50">
                  {sampleColumns.map((col) => (
                    <th key={col} className="px-3 py-2 text-gray-600 font-semibold border border-gray-200 whitespace-nowrap">
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {sampleRows.map((row, i) => (
                  <tr key={i} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                    {sampleColumns.map((col) => (
                      <td key={col} className="px-3 py-1.5 border border-gray-100 text-gray-700 whitespace-nowrap">
                        {row[col] ?? '—'}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Preprocessing Configuration */}
      {appState.dataUploaded && (
        <div className="card">
          <h2 className="section-title flex items-center gap-2">
            <Settings size={20} className="text-blue-600" />
            Preprocessing Configuration
          </h2>

          {/* Feature selection */}
          <div className="mb-6">
            <label className="label text-gray-800 font-semibold mb-2 block">Select Features for Clustering</label>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {availableFeatures.map((feat) => (
                <label
                  key={feat}
                  className={`flex items-center gap-2 px-3 py-2.5 rounded-lg border cursor-pointer transition-colors text-sm ${
                    selectedFeatures.has(feat)
                      ? 'bg-blue-50 border-blue-400 text-blue-800 font-medium'
                      : 'bg-gray-50 border-gray-200 text-gray-600 hover:border-gray-400'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={selectedFeatures.has(feat)}
                    onChange={() => toggleFeature(feat)}
                    className="accent-blue-600"
                  />
                  {feat}
                </label>
              ))}
            </div>
            <p className="text-xs text-gray-400 mt-2">{selectedFeatures.size} feature(s) selected</p>
          </div>

          {/* Options */}
          <div className="mb-6 space-y-3">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={removeDuplicates}
                onChange={(e) => setRemoveDuplicates(e.target.checked)}
                className="w-4 h-4 accent-blue-600"
              />
              <span className="text-sm font-medium text-gray-700">Remove duplicate records</span>
            </label>
            <div className="flex items-center gap-3 px-3 py-2 bg-gray-50 rounded-lg">
              <span className="text-sm text-gray-600">Imputation strategy:</span>
              <span className="badge-blue">Median (numerical) + Mode (categorical)</span>
            </div>
            <div className="flex items-center gap-3 px-3 py-2 bg-gray-50 rounded-lg">
              <span className="text-sm text-gray-600">Scaling:</span>
              <span className="badge-blue">StandardScaler</span>
            </div>
          </div>

          {preprocessError && <div className="mb-4"><ErrorAlert message={preprocessError} onDismiss={() => setPreprocessError('')} /></div>}

          <button
            onClick={handlePreprocess}
            disabled={preprocessing || !appState.dataUploaded}
            className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {preprocessing ? (
              <><RefreshCw size={16} className="animate-spin" /> Processing...</>
            ) : (
              <><Settings size={16} /> Run Preprocessing</>
            )}
          </button>

          {/* Preprocessing Result */}
          {preprocessResult && (
            <div className="mt-5 bg-green-50 border border-green-200 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-3">
                <CheckCircle size={18} className="text-green-600" />
                <h3 className="text-sm font-bold text-green-800">Preprocessing Complete</h3>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
                <div>
                  <p className="text-xs text-green-600 font-semibold">Records After</p>
                  <p className="font-bold text-green-900">{preprocessResult.records_after?.toLocaleString() ?? '—'}</p>
                </div>
                <div>
                  <p className="text-xs text-green-600 font-semibold">Duplicates Removed</p>
                  <p className="font-bold text-green-900">{preprocessResult.duplicates_removed ?? 0}</p>
                </div>
                <div>
                  <p className="text-xs text-green-600 font-semibold">Features Used</p>
                  <p className="font-bold text-green-900">{preprocessResult.features_used?.length ?? selectedFeatures.size}</p>
                </div>
                <div>
                  <p className="text-xs text-green-600 font-semibold">Missing Imputed</p>
                  <p className="font-bold text-green-900">{preprocessResult.missing_imputed ?? 0}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Downloads */}
      {appState.dataUploaded && (
        <div className="card">
          <h2 className="section-title flex items-center gap-2">
            <Download size={20} className="text-blue-600" />
            Downloads
          </h2>
          <div className="flex flex-wrap gap-3">
            <button onClick={datasetAPI.downloadProcessed} className="btn-secondary flex items-center gap-2 text-sm">
              <Download size={15} /> Download Processed Data
            </button>
            {appState.modelTrained && (
              <button onClick={datasetAPI.downloadClustered} className="btn-secondary flex items-center gap-2 text-sm">
                <Download size={15} /> Download Clustered Data
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
