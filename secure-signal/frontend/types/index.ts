export type Severity = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "NONE";

export interface ThreatEvent {
  id: string;
  threat_type: string;
  severity: Severity;
  risk_score: number;
  title: string;
  description: string;
  source?: string;
  indicators: Record<string, unknown>;
  action_required?: string;
  dismissed: boolean;
  created_at: string;
}

export interface AnalysisReport {
  overall_risk_score: number;
  overall_verdict: string;
  severity_level: Severity;
  phishing_analysis: {
    risk_score: number;
    verdict: string;
    threat_category: string;
    indicators: Array<{ type: string; label: string; weight: number; severity: string }>;
    recommended_action: string;
  };
  ai_text_analysis: {
    ai_probability: number;
    perplexity_score: number;
    burstiness_score: number;
    avg_sentence_length: number;
    vocabulary_richness: number;
    repetition_score: number;
    reasoning: string[];
  };
  combined_risk_factors: string[];
  priority_action: string;
  confidence: number;
  threat_summary: string;
}

export interface Stats {
  total_threats_detected: number;
  critical_threats: number;
  analyses_run: number;
  average_risk_score: number;
  monitoring_status: string;
  protected_channels: string[];
}

export const SEVERITY_CONFIG: Record<Severity, { color: string; bg: string; border: string; label: string }> = {
  CRITICAL: { color: "#ef4444", bg: "rgba(239,68,68,0.1)", border: "rgba(239,68,68,0.3)", label: "CRITICAL" },
  HIGH: { color: "#f97316", bg: "rgba(249,115,22,0.1)", border: "rgba(249,115,22,0.3)", label: "HIGH" },
  MEDIUM: { color: "#eab308", bg: "rgba(234,179,8,0.1)", border: "rgba(234,179,8,0.3)", label: "MEDIUM" },
  LOW: { color: "#3b82f6", bg: "rgba(59,130,246,0.1)", border: "rgba(59,130,246,0.3)", label: "LOW" },
  NONE: { color: "#22c55e", bg: "rgba(34,197,94,0.1)", border: "rgba(34,197,94,0.3)", label: "SAFE" },
};
