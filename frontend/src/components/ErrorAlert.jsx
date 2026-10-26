import { useState } from 'react'
import { AlertCircle, X } from 'lucide-react'

export default function ErrorAlert({ message, onDismiss }) {
  const [visible, setVisible] = useState(true)

  if (!visible || !message) return null

  const handleDismiss = () => {
    setVisible(false)
    if (onDismiss) onDismiss()
  }

  return (
    <div className="flex items-start gap-3 bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
      <AlertCircle size={18} className="flex-shrink-0 mt-0.5 text-red-500" />
      <p className="flex-1 text-sm font-medium leading-relaxed">{message}</p>
      <button
        onClick={handleDismiss}
        className="flex-shrink-0 text-red-400 hover:text-red-600 transition-colors"
        aria-label="Dismiss error"
      >
        <X size={16} />
      </button>
    </div>
  )
}
