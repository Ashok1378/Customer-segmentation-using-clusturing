import axios from 'axios'

const API_BASE = 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 120000,
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const message =
        error.response.data?.detail ||
        error.response.data?.message ||
        `Server error: ${error.response.status}`
      return Promise.reject(new Error(message))
    } else if (error.request) {
      return Promise.reject(
        new Error('No response from server. Is the backend running?')
      )
    } else {
      return Promise.reject(new Error(error.message || 'Unknown error'))
    }
  }
)

export const datasetAPI = {
  upload: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/api/dataset/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  getSummary: () => api.get('/api/dataset/summary'),
  getSample: () => api.get('/api/dataset/sample'),
  downloadProcessed: () =>
    window.open(API_BASE + '/api/dataset/download/processed'),
  downloadClustered: () =>
    window.open(API_BASE + '/api/dataset/download/clustered'),
}

export const clusteringAPI = {
  preprocess: (data) => api.post('/api/preprocess', data),
  analyze: (data) => api.post('/api/clustering/analyze', data),
  train: (data) => api.post('/api/clustering/train', data),
  trainAll: () => api.post('/api/clustering/train-all'),
  getResults: () => api.get('/api/clustering/results'),
  getComparison: () => api.get('/api/clustering/comparison'),
  getPCA: () => api.get('/api/clustering/pca'),
  getSegments: () => api.get('/api/segments'),
  downloadReport: () =>
    window.open(API_BASE + '/api/clustering/download/report'),
}

export const predictionAPI = {
  predict: (data) => api.post('/api/prediction/predict', data),
}

export const databaseAPI = {
  getStatus: () => api.get('/api/database/status'),
  getPredictions: (limit = 20) => api.get(`/api/database/predictions?limit=${limit}`),
  getRuns: (limit = 15) => api.get(`/api/database/runs?limit=${limit}`),
  getDatasets: (limit = 10) => api.get(`/api/database/datasets?limit=${limit}`),
  getCustomers: (datasetId = null, limit = 50) =>
    api.get(`/api/database/customers${datasetId ? `?dataset_id=${datasetId}&limit=${limit}` : `?limit=${limit}`}`),
  autoConnect: () => api.post('/api/database/auto-connect'),
  // MongoDB endpoints
  getMongoStatus: () => api.get('/api/database/mongo/status'),
  connectMongo: (data) => api.post('/api/database/mongo/connect', data),
  syncToMongo: () => api.post('/api/database/mongo/sync'),
  getMongoPredictions: (limit = 50) => api.get(`/api/database/mongo/predictions?limit=${limit}`),
  getMongoCustomers: (limit = 50) => api.get(`/api/database/mongo/customers?limit=${limit}`),
}

export const healthAPI = {
  check: () => api.get('/api/health'),
}

export default api

