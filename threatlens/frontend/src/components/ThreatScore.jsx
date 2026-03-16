import React from 'react';

const severityConfig = {
  critical: { color: 'text-red-500', bg: 'bg-red-500/10', border: 'border-red-500/30', ring: 'ring-red-500/40' },
  high: { color: 'text-orange-500', bg: 'bg-orange-500/10', border: 'border-orange-500/30', ring: 'ring-orange-500/40' },
  medium: { color: 'text-amber-500', bg: 'bg-amber-500/10', border: 'border-amber-500/30', ring: 'ring-amber-500/40' },
  low: { color: 'text-green-500', bg: 'bg-green-500/10', border: 'border-green-500/30', ring: 'ring-green-500/40' },
  info: { color: 'text-sky-500', bg: 'bg-sky-500/10', border: 'border-sky-500/30', ring: 'ring-sky-500/40' },
};

export default function ThreatScore({ score, severity, size = 'md' }) {
  const config = severityConfig[severity] || severityConfig.info;
  const sizeClasses = size === 'lg' ? 'w-28 h-28 text-3xl' : 'w-16 h-16 text-lg';

  const circumference = 2 * Math.PI * 40;
  const filled = (score / 100) * circumference;

  return (
    <div className="flex flex-col items-center gap-1">
      <div className={`relative ${sizeClasses} flex items-center justify-center`}>
        {size === 'lg' && (
          <svg className="absolute inset-0 -rotate-90" viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="40" fill="none" stroke="currentColor"
              className="text-gray-800" strokeWidth="6" />
            <circle cx="50" cy="50" r="40" fill="none"
              className={config.color} strokeWidth="6"
              strokeDasharray={circumference}
              strokeDashoffset={circumference - filled}
              strokeLinecap="round" />
          </svg>
        )}
        <span className={`font-bold ${config.color} z-10`}>{Math.round(score)}</span>
      </div>
      <span className={`text-xs font-medium uppercase tracking-wider ${config.color}`}>
        {severity}
      </span>
    </div>
  );
}
