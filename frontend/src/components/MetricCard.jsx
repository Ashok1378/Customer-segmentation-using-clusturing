const colorVariants = {
  blue: {
    bg: 'bg-blue-50',
    border: 'border-blue-200',
    icon: 'bg-blue-100 text-blue-600',
    value: 'text-blue-700',
    label: 'text-blue-900',
    sub: 'text-blue-500',
  },
  green: {
    bg: 'bg-green-50',
    border: 'border-green-200',
    icon: 'bg-green-100 text-green-600',
    value: 'text-green-700',
    label: 'text-green-900',
    sub: 'text-green-500',
  },
  purple: {
    bg: 'bg-purple-50',
    border: 'border-purple-200',
    icon: 'bg-purple-100 text-purple-600',
    value: 'text-purple-700',
    label: 'text-purple-900',
    sub: 'text-purple-500',
  },
  orange: {
    bg: 'bg-orange-50',
    border: 'border-orange-200',
    icon: 'bg-orange-100 text-orange-600',
    value: 'text-orange-700',
    label: 'text-orange-900',
    sub: 'text-orange-500',
  },
  red: {
    bg: 'bg-red-50',
    border: 'border-red-200',
    icon: 'bg-red-100 text-red-600',
    value: 'text-red-700',
    label: 'text-red-900',
    sub: 'text-red-500',
  },
  gray: {
    bg: 'bg-gray-50',
    border: 'border-gray-200',
    icon: 'bg-gray-100 text-gray-600',
    value: 'text-gray-700',
    label: 'text-gray-900',
    sub: 'text-gray-500',
  },
  teal: {
    bg: 'bg-teal-50',
    border: 'border-teal-200',
    icon: 'bg-teal-100 text-teal-600',
    value: 'text-teal-700',
    label: 'text-teal-900',
    sub: 'text-teal-500',
  },
}

/**
 * MetricCard component
 * @param {string} title - Card label
 * @param {string|number} value - Main displayed value
 * @param {string} subtitle - Optional subtitle/description
 * @param {React.ReactNode} icon - Optional icon element
 * @param {'blue'|'green'|'purple'|'orange'|'red'|'gray'|'teal'} color - Color variant
 */
export default function MetricCard({
  title,
  value,
  subtitle,
  icon,
  color = 'blue',
}) {
  const theme = colorVariants[color] || colorVariants.blue

  return (
    <div
      className={`rounded-xl border ${theme.bg} ${theme.border} p-5 flex items-start gap-4 shadow-sm`}
    >
      {icon && (
        <div className={`p-2.5 rounded-lg ${theme.icon} flex-shrink-0`}>
          {icon}
        </div>
      )}
      <div className="min-w-0">
        <p className={`text-xs font-semibold uppercase tracking-wide ${theme.sub} mb-1`}>
          {title}
        </p>
        <p className={`text-2xl font-bold ${theme.value} leading-tight truncate`}>
          {value ?? '—'}
        </p>
        {subtitle && (
          <p className={`text-xs mt-1 ${theme.sub} leading-snug`}>{subtitle}</p>
        )}
      </div>
    </div>
  )
}
