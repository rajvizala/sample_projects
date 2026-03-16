"use client";

import { useState } from "react";
import { Search, Loader2, AlertTriangle, CheckCircle, ChevronDown, ChevronUp } from "lucide-react";
import { analyzeContent } from "@/lib/api";
import { AnalysisReport, SEVERITY_CONFIG } from "@/types";
import RiskGauge from "./RiskGauge";

const SAMPLE_TEXTS = [
  {
    label: "Phishing email",
    text: "Dear Customer, Your PayPal account has been suspended due to unusual activity. You must verify your account immediately within 24 hours or your account will be permanently closed. Click here to verify: http://paypal-verify-secure.tk/login and enter your password to restore access."
  },
  {
    label: "Legitimate email",
    text: "Hi Sarah, Just wanted to follow up on our meeting last Tuesday. I've been thinking about the proposal and I think there are a few points worth revisiting before we move forward. Could we schedule a 30-minute call sometime this week? I'm free Thursday afternoon or Friday morning."
  },
  {
    label: "AI-generated scam",
    text: "Congratulations! You have been selected as the winner of our annual customer loyalty program. Your prize of $5,000 has been approved for immediate transfer. To claim your reward, you must verify your identity by providing your banking information within 48 hours. Please click the link below to verify your account details and receive your payment via wire transfer."
  }
];

export default function AnalysisPanel() {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<AnalysisReport | null>(null);
  const [error, setError] = useState("");
  const [showDetails, setShowDetails] = useState(false);

  const handleAnalyze = async () => {
    if (!input.trim() || loading) return;
    setLoading(true);
    setError("");
    setReport(null);
    try {
      const result = await analyzeContent(input);
      setReport(result);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  const severity = report?.severity_level || "NONE";
  const config = SEVERITY_CONFIG[severity];

  return (
    <div className="flex flex-col gap-4">
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="text-sm font-semibold" style={{ color: "#94a3b8" }}>
            Paste message, email, or text to analyze
          </label>
          <div className="flex gap-2">
            {SAMPLE_TEXTS.map((s) => (
              <button
                key={s.label}
                onClick={() => setInput(s.text)}
                className="text-[10px] px-2 py-1 rounded transition-all"
                style={{ background: "#0a1628", color: "#64748b", border: "1px solid #1e3a5f" }}
              >
                {s.label}
              </button>
            ))}
          </div>
        </div>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          rows={6}
          placeholder="Paste a suspicious email, message, or any text here to analyze it for phishing, social engineering, or AI-generated content..."
          className="w-full rounded-xl px-4 py-3 text-sm outline-none resize-none"
          style={{
            background: "#060b14",
            border: "1px solid #1e3a5f",
            color: "#cbd5e1",
          }}
          onFocus={(e) => (e.target.style.borderColor = "#3b82f6")}
          onBlur={(e) => (e.target.style.borderColor = "#1e3a5f")}
        />
        <div className="flex items-center justify-between mt-2">
          <span className="text-[11px]" style={{ color: "#334155" }}>
            {input.length} / 10,000 characters
          </span>
          <button
            onClick={handleAnalyze}
            disabled={!input.trim() || loading}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all"
            style={{
              background: !input.trim() || loading ? "#0a1628" : "rgba(59,130,246,0.2)",
              color: !input.trim() || loading ? "#334155" : "#60a5fa",
              border: `1px solid ${!input.trim() || loading ? "#1e3a5f" : "rgba(59,130,246,0.4)"}`,
            }}
          >
            {loading ? <Loader2 size={14} className="animate-spin" /> : <Search size={14} />}
            {loading ? "Analyzing..." : "Analyze Threat"}
          </button>
        </div>
      </div>

      {error && (
        <div
          className="rounded-lg px-4 py-3 text-sm"
          style={{ background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)", color: "#fca5a5" }}
        >
          {error}
        </div>
      )}

      {report && (
        <div
          className="rounded-xl p-5"
          style={{ background: "#090f1c", border: `1px solid ${config.border}` }}
        >
          <div className="flex items-start gap-6">
            <RiskGauge score={report.overall_risk_score} severity={severity} />

            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                {report.overall_risk_score > 0.3 ? (
                  <AlertTriangle size={16} style={{ color: config.color }} />
                ) : (
                  <CheckCircle size={16} style={{ color: config.color }} />
                )}
                <h3 className="text-sm font-bold text-white">{report.overall_verdict}</h3>
              </div>

              <p className="text-xs mb-3" style={{ color: "#64748b" }}>{report.threat_summary}</p>

              <div className="grid grid-cols-2 gap-2 mb-3">
                <div className="rounded-lg p-2" style={{ background: "#060b14", border: "1px solid #1e3a5f" }}>
                  <p className="text-[10px] mb-0.5" style={{ color: "#475569" }}>Phishing Risk</p>
                  <p className="text-sm font-bold" style={{ color: config.color }}>
                    {Math.round(report.phishing_analysis.risk_score * 100)}%
                  </p>
                </div>
                <div className="rounded-lg p-2" style={{ background: "#060b14", border: "1px solid #1e3a5f" }}>
                  <p className="text-[10px] mb-0.5" style={{ color: "#475569" }}>AI-Generated</p>
                  <p className="text-sm font-bold" style={{ color: "#a78bfa" }}>
                    {Math.round(report.ai_text_analysis.ai_probability * 100)}%
                  </p>
                </div>
              </div>

              {report.combined_risk_factors.length > 0 && (
                <div className="space-y-1">
                  {report.combined_risk_factors.slice(0, 3).map((factor, i) => (
                    <div key={i} className="flex items-start gap-2">
                      <span className="flex-shrink-0 w-1 h-1 rounded-full mt-1.5" style={{ background: config.color }} />
                      <p className="text-[11px]" style={{ color: "#94a3b8" }}>{factor}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div
            className="mt-4 rounded-lg p-3"
            style={{ background: "rgba(16,185,129,0.05)", border: "1px solid rgba(16,185,129,0.15)" }}
          >
            <p className="text-[10px] font-semibold uppercase mb-1" style={{ color: "#10b981" }}>
              Recommended Action
            </p>
            <p className="text-xs" style={{ color: "#6ee7b7" }}>{report.priority_action}</p>
          </div>

          <button
            onClick={() => setShowDetails(!showDetails)}
            className="flex items-center gap-1 mt-3 text-[11px] transition-colors"
            style={{ color: "#475569" }}
          >
            {showDetails ? <ChevronUp size={10} /> : <ChevronDown size={10} />}
            {showDetails ? "Hide" : "Show"} detailed analysis
          </button>

          {showDetails && (
            <div className="mt-3 pt-3 space-y-3" style={{ borderTop: "1px solid #1e3a5f" }}>
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-wider mb-2" style={{ color: "#475569" }}>
                  AI Text Analysis
                </p>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { label: "Perplexity", val: report.ai_text_analysis.perplexity_score },
                    { label: "Burstiness", val: report.ai_text_analysis.burstiness_score },
                    { label: "Vocab Richness", val: report.ai_text_analysis.vocabulary_richness },
                  ].map((m) => (
                    <div key={m.label} className="rounded-lg p-2 text-center" style={{ background: "#060b14" }}>
                      <p className="text-[10px]" style={{ color: "#475569" }}>{m.label}</p>
                      <p className="text-sm font-semibold" style={{ color: "#a78bfa" }}>{m.val.toFixed(0)}</p>
                    </div>
                  ))}
                </div>
                {report.ai_text_analysis.reasoning.length > 0 && (
                  <div className="mt-2 space-y-1">
                    {report.ai_text_analysis.reasoning.map((r, i) => (
                      <p key={i} className="text-[11px]" style={{ color: "#64748b" }}>• {r}</p>
                    ))}
                  </div>
                )}
              </div>

              {report.phishing_analysis.indicators.length > 0 && (
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-wider mb-2" style={{ color: "#475569" }}>
                    Phishing Indicators
                  </p>
                  <div className="space-y-1">
                    {report.phishing_analysis.indicators.map((ind, i) => (
                      <div key={i} className="flex items-center gap-2">
                        <span className="text-[10px] px-1.5 py-0.5 rounded" style={{
                          background: ind.severity === "critical" ? "rgba(239,68,68,0.1)" : "rgba(234,179,8,0.1)",
                          color: ind.severity === "critical" ? "#ef4444" : "#eab308"
                        }}>
                          {ind.type.replace(/_/g, " ")}
                        </span>
                        <p className="text-[11px]" style={{ color: "#94a3b8" }}>{ind.label}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
