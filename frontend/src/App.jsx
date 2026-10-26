import { Routes, Route, NavLink, useNavigate } from 'react-router-dom'
import { useState, useEffect, createContext, useContext } from 'react'
import {
  LayoutDashboard,
  Upload,
  BarChart2,
  GitBranch,
  Scale,
  Users,
  Cpu,
  Database,
  ChevronRight,
  Menu,
  X,
} from 'lucide-react'

import Dashboard from './pages/Dashboard.jsx'
import DataUpload from './pages/DataUpload.jsx'
import DataAnalysis from './pages/DataAnalysis.jsx'
import ClusteringAnalysis from './pages/ClusteringAnalysis.jsx'
import ModelComparison from './pages/ModelComparison.jsx'
import SegmentProfiles from './pages/SegmentProfiles.jsx'
import Prediction from './pages/Prediction.jsx'
import DatabaseHub from './pages/DatabaseHub.jsx'
import Navbar from './components/Navbar.jsx'
import { clusteringAPI, datasetAPI } from './services/api'

export const AppContext = createContext(null)

export function useAppContext() {
  return useContext(AppContext)
}

const navItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard, exact: true },
  { path: '/upload', label: 'Data Upload', icon: Upload },
  { path: '/analysis', label: 'Data Analysis', icon: BarChart2 },
  { path: '/clustering', label: 'Clustering', icon: GitBranch },
  { path: '/comparison', label: 'Model Comparison', icon: Scale },
  { path: '/segments', label: 'Segment Profiles', icon: Users },
  { path: '/prediction', label: 'Prediction', icon: Cpu },
  { path: '/database', label: 'Database Hub', icon: Database },
]

function Sidebar({ collapsed, onToggle }) {
  return (
    <aside
      className={`bg-gray-900 text-white flex flex-col transition-all duration-300 ${
        collapsed ? 'w-16' : 'w-60'
      } min-h-screen flex-shrink-0`}
    >
      {/* Logo */}
      <div className="flex items-center justify-between px-4 py-4 border-b border-gray-700">
        {!collapsed && (
          <span className="text-sm font-bold text-blue-400 leading-tight">
            Customer<br />Segmentation
          </span>
        )}
        <button
          onClick={onToggle}
          className="p-1.5 rounded-lg hover:bg-gray-700 text-gray-400 hover:text-white transition-colors ml-auto"
        >
          {collapsed ? <Menu size={18} /> : <X size={18} />}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 space-y-1 px-2">
        {navItems.map(({ path, label, icon: Icon, exact }) => (
          <NavLink
            key={path}
            to={path}
            end={exact}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 group ${
                isActive
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'text-gray-400 hover:bg-gray-800 hover:text-white'
              }`
            }
          >
            <Icon size={18} className="flex-shrink-0" />
            {!collapsed && (
              <>
                <span className="flex-1 truncate">{label}</span>
                <ChevronRight
                  size={14}
                  className="opacity-0 group-hover:opacity-60 transition-opacity"
                />
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      {!collapsed && (
        <div className="px-4 py-3 border-t border-gray-700 text-xs text-gray-500">
          ML Dashboard v1.0
        </div>
      )}
    </aside>
  )
}

function App() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [appState, setAppState] = useState({
    dataUploaded: false,
    datasetSummary: null,
    preprocessed: false,
    modelTrained: false,
    lastResults: null,
    uploadedFilename: null,
    selectedFeatures: [],
    trainedAlgorithms: [],
  })

  const updateAppState = (updates) => {
    setAppState((prev) => ({ ...prev, ...updates }))
  }

  useEffect(() => {
    // Hydrate state from server if model or dataset exists
    clusteringAPI.getSegments().then((res) => {
      const segs = res.data?.profiles || res.data?.segments || []
      if (segs.length > 0) {
        updateAppState({ modelTrained: true, preprocessed: true, dataUploaded: true })
      }
    }).catch(() => {})

    datasetAPI.getSummary().then((res) => {
      if (res.data) {
        updateAppState({ dataUploaded: true, datasetSummary: res.data })
      }
    }).catch(() => {})
  }, [])

  return (
    <AppContext.Provider value={{ appState, setAppState, updateAppState }}>
      <div className="flex min-h-screen bg-gray-50">
        {/* Sidebar */}
        <Sidebar
          collapsed={sidebarCollapsed}
          onToggle={() => setSidebarCollapsed((c) => !c)}
        />

        {/* Main area */}
        <div className="flex flex-col flex-1 min-w-0">
          {/* Top navbar */}
          <Navbar />

          {/* Page content */}
          <main className="flex-1 overflow-auto p-6">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/upload" element={<DataUpload />} />
              <Route path="/analysis" element={<DataAnalysis />} />
              <Route path="/clustering" element={<ClusteringAnalysis />} />
              <Route path="/comparison" element={<ModelComparison />} />
              <Route path="/segments" element={<SegmentProfiles />} />
              <Route path="/prediction" element={<Prediction />} />
              <Route path="/database" element={<DatabaseHub />} />
            </Routes>
          </main>
        </div>
      </div>
    </AppContext.Provider>
  )
}

export default App
