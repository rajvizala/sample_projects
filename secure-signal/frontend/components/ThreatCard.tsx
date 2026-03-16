"use client";

import { AlertTriangle, Shield, Info, X, ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";
import { ThreatEvent, SEVERITY_CONFIG } from "@/types";

interface ThreatCardProps {
  threat: ThreatEvent;
  onDismiss: (id: string) => void;
}

const THREAT_TYPE_LABELS: Record<string, string> = {
  phishing_attempt: "Phishing Attempt",
  ai_generated_scam: "AI-Generated Scam",
  account_takeover_attempt: "Account Takeover",
  credential_exposure: "Credential Exposure",
  sim_swap_indicator: "SIM Swap Activity",
  social_engineering: "Social Engineering",
};

export default function ThreatCard({ threat, onDismiss }: ThreatCardProps) {
  const [expanded, setExpanded] = useState(false);
  const config = SEVERITY_CONFIG[threat.severity] || SEVERITY_CONFIG.LOW;
  const typeLabel = THREAT_TYPE_LABELS[threat.threat_type] || threat.threat_type.replace(/_/g, " ");

  const formatTime = (iso: string) => {
    const date = new Date(iso);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    if (diffMins < 1) return "just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    return `${Math.floor(diffMins / 60)}h ago`;
  };

  return (
    <div
      className="threat-card rounded-xl p-4 transition-all"
      style={{
        background: "#0a1628",
        border: `1px solid ${config.border}`,
      }}
    >
      <div className="flex items-start gap-3">
        <div
          className="flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center mt-0.5"
          style={{ background: config.bg }}
        >
          {threat.severity === "CRITICAL" || threat.severity === "HIGH" ? (
            <AlertTriangle size={14} style={{ color: config.color }} />
          ) : (
            <Info size={14} style={{ color: config.color }} />
          )}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span
              className="text-[10px] font-bold px-1.5 py-0.5 rounded"
              style={{ background: config.bg, color: config.color }}
            >
              {config.label}
            </span>
            <span className="text-[10px]" style={{ color: "#475569" }}>{typeLabel}</span>
            <span className="text-[10px] ml-auto flex-shrink-0" style={{ color: "#475569" }}>
              {formatTime(threat.created_at)}
            </span>
          </div>

          <p className="text-sm font-semibold text-white mt-1">{threat.title}</p>

          {threat.source && (
            <p className="text-[11px] mt-0.5" style={{ color: "#64748b" }}>
              Source: {threat.source}
            </p>
          )}

          {expanded && (
            <div className="mt-3 space-y-3">
              <p className="text-xs leading-relaxed" style={{ color: "#94a3b8" }}>
                {threat.description}
              </p>

              {Object.keys(threat.indicators).length > 0 && (
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-wider mb-2" style={{ color: "#475569" }}>
                    Indicators
                  </p>
                  <div className="grid grid-cols-2 gap-1">
                    {Object.entries(threat.indicators).slice(0, 6).map(([key, val]) => (
                      <div key={key} className="flex items-center gap-1.5">
                        <span
                          className="w-1.5 h-1.5 rounded-full flex-shrink-0"
                          style={{ background: config.color }}
                        />
                        <span className="text-[10px]" style={{ color: "#64748b" }}>
                          {key.replace(/_/g, " ")}: <span style={{ color: "#94a3b8" }}>{String(val)}</span>
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {threat.action_required && (
                <div
                  className="rounded-lg p-3"
                  style={{ background: "rgba(16,185,129,0.05)", border: "1px solid rgba(16,185,129,0.2)" }}
                >
                  <div className="flex items-center gap-1.5 mb-1">
                    <Shield size={10} style={{ color: "#10b981" }} />
                    <p className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: "#10b981" }}>
                      Recommended Action
                    </p>
                  </div>
                  <p className="text-xs" style={{ color: "#6ee7b7" }}>{threat.action_required}</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="flex items-center gap-2 mt-3 pt-2" style={{ borderTop: "1px solid #0f2040" }}>
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1 text-[11px] transition-colors"
          style={{ color: "#64748b" }}
        >
          {expanded ? <ChevronUp size={10} /> : <ChevronDown size={10} />}
          {expanded ? "Show less" : "Show details"}
        </button>
        <button
          onClick={() => onDismiss(threat.id)}
          className="ml-auto flex items-center gap-1 text-[11px] px-2 py-1 rounded transition-all"
          style={{ color: "#475569", background: "#0f1e33" }}
        >
          <X size={9} /> Dismiss
        </button>
      </div>
    </div>
  );
}
