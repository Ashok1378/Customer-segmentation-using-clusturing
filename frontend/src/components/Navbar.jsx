import { useState, useEffect } from 'react'
import { Brain, Wifi, WifiOff, Database } from 'lucide-react'
import { healthAPI } from '../services/api'

export default function Navbar() {
  const [backendStatus, setBackendStatus] = useState('checking') // 'checking' | 'online' | 'offline'
  const [dbStatus, setDbStatus] = useState(null)

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await healthAPI.check()
        setBackendStatus('online')
        if (res.data?.database) {
          setDbStatus(res.data.database)
        }
      } catch {
        setBackendStatus('offline')
        setDbStatus(null)
      }
    }

    checkHealth()
    const interval = setInterval(checkHealth, 20000)
    return () => clearInterval(interval)
  }, [])

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between shadow-sm flex-shrink-0">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
          <Brain size={18} className="text-white" />
        </div>
        <div>
          <h1 className="text-base font-bold text-gray-900 leading-tight">
            Customer Segmentation ML
          </h1>
          <p className="text-xs text-gray-500">Unsupervised Learning &amp; Database System</p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* Database Status Badge */}
        {dbStatus && dbStatus.connected && (
          <div className="flex items-center gap-1.5 text-xs text-blue-700 bg-blue-50 px-3 py-1.5 rounded-full border border-blue-200">
            <Database size={13} className="text-blue-600" />
            <span className="font-medium">
              DB: Connected ({dbStatus.engine?.toLowerCase().includes('mysql') ? 'MySQL' : (dbStatus.engine || 'SQLite')})
            </span>
          </div>
        )}

        {/* Backend Status Badge */}
        {backendStatus === 'checking' && (
          <div className="flex items-center gap-1.5 text-xs text-gray-500">
            <div className="w-2 h-2 bg-yellow-400 rounded-full animate-pulse" />
            <span>Connecting...</span>
          </div>
        )}
        {backendStatus === 'online' && (
          <div className="flex items-center gap-1.5 text-xs text-green-700 bg-green-50 px-3 py-1.5 rounded-full border border-green-200">
            <Wifi size={13} />
            <span className="font-medium">Backend Online</span>
          </div>
        )}
        {backendStatus === 'offline' && (
          <div className="flex items-center gap-1.5 text-xs text-red-700 bg-red-50 px-3 py-1.5 rounded-full border border-red-200">
            <WifiOff size={13} />
            <span className="font-medium">Backend Offline</span>
          </div>
        )}
      </div>
    </header>
  )
}

