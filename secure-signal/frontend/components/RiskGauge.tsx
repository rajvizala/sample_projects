"use client";

import { SEVERITY_CONFIG, Severity } from "@/types";

interface RiskGaugeProps {
  score: number;
  severity: Severity;
  size?: number;
}

export default function RiskGauge({ score, severity, size = 140 }: RiskGaugeProps) {
  const config = SEVERITY_CONFIG[severity] || SEVERITY_CONFIG.NONE;
  const radius = (size / 2) - 16;
  const circumference = Math.PI * radius;
  const progress = score * circumference;
  const offset = circumference - progress;
  const cx = size / 2;
  const cy = size / 2;

  return (
    <div className="flex flex-col items-center gap-2">
      <svg width={size} height={size / 2 + 20} viewBox={`0 0 ${size} ${size / 2 + 20}`}>
        <path
          d={`M 16 ${cy} A ${radius} ${radius} 0 0 1 ${size - 16} ${cy}`}
          fill="none"
          stroke="#1e3a5f"
          strokeWidth="10"
          strokeLinecap="round"
        />
        <path
          d={`M 16 ${cy} A ${radius} ${radius} 0 0 1 ${size - 16} ${cy}`}
          fill="none"
          stroke={config.color}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={`${circumference}`}
          strokeDashoffset={offset}
          className="gauge-arc"
          style={{ filter: `drop-shadow(0 0 6px ${config.color}60)` }}
        />
        <text x={cx} y={cy + 4} textAnchor="middle" fill={config.color} fontSize="22" fontWeight="700">
          {Math.round(score * 100)}
        </text>
        <text x={cx} y={cy + 18} textAnchor="middle" fill="#64748b" fontSize="9">
          RISK SCORE
        </text>
      </svg>
      <span
        className="text-xs font-bold px-3 py-1 rounded-full"
        style={{ background: config.bg, color: config.color, border: `1px solid ${config.border}` }}
      >
        {config.label}
      </span>
    </div>
  );
}
