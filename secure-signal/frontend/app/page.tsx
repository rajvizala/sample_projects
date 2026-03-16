"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import {
  Shield, Wifi, WifiOff, Bell, BarChart2, Activity, AlertTriangle, CheckCircle,
  Eye, Radio
} from "lucide-react";
import ThreatCard from "@/components/ThreatCard";
import AnalysisPanel from "@/components/AnalysisPanel";
import { ThreatEvent, Stats } from "@/types";
import { getThreats, getStats, dismissThreat, createThreatWebSocket } from "@/lib/api";

type Tab = "monitor" | "analyze";

export default function HomePage() {
  const [activeTab, setActiveTab] = useState<Tab>("monitor");
  const [threats, setThreats] = useState<ThreatEvent[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [connected, setConnected] = useState(false);
  const [newThreatCount, setNewThreatCount] = useState(0);
  const wsRef = useRef<WebSocket | null>(null);

  const loadInitialData = useCallback(async () => {
    try {
      const [threatsData, statsData] = await Promise.all([getThreats(), getStats()]);
      setThreats(threatsData);
      setStats(statsData);
    } catch {}
  }, []);

  useEffect(() => {
    loadInitialData();

    wsRef.current = createThreatWebSocket(
      (threat) => {
        setThreats((prev) => [threat as ThreatEvent, ...prev].slice(0, 50));
        setNewThreatCount((c) => c + 1);
        setStats((s) => s ? { ...s, total_threats_detected: s.total_threats_detected + 1 } : s);
      },
      () => setConnected(true),
      () => {
        setConnected(false);
        setTimeout(() => {
          wsRef.current = createThreatWebSocket(
            (threat) => setThreats((prev) => [threat as ThreatEvent, ...prev].slice(0, 50)),
            () => setConnected(true),
            () => setConnected(false)
          );
        }, 3000);
      }
    );

    return () => wsRef.current?.close();
  }, [loadInitialData]);

  const handleDismiss = async (id: string) => {
    try {
      await dismissThreat(id);
      setThreats((prev) => prev.filter((t) => t.id !== id));
    } catch {}
  };

  const criticalCount = threats.filter((t) => t.severity === "CRITICAL").length;
  const highCount = threats.filter((t) => t.severity === "HIGH").length;

  return (
    <div className="min-h-screen" style={{ background: "#060b14" }}>
      <header
        className="sticky top-0 z-10 flex items-center justify-between px-6 py-3"
        style={{ background: "#060b14", borderBottom: "1px solid #0f2040" }}
      >
        <div className="flex items-center gap-3">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center"
            style={{ background: "linear-gradient(135deg, #ef4444, #f97316)" }}
          >
            <Shield size={16} color="white" />
          </div>
          <div>
            <p className="text-sm font-bold text-white">SecureSignal</p>
            <p className="text-[10px]" style={{ color: "#475569" }}>Personal AI Threat Monitor</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {criticalCount > 0 && (
            <div className="flex items-center gap-1.5 animate-pulse-ring rounded-full px-3 py-1"
              style={{ background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)" }}
            >
              <AlertTriangle size={10} style={{ color: "#ef4444" }} />
              <span className="text-[11px] font-bold" style={{ color: "#ef4444" }}>
                {criticalCount} Critical
              </span>
            </div>
          )}

          <div className="flex items-center gap-1.5">
            {connected ? (
              <>
                <span className="animate-blink w-1.5 h-1.5 rounded-full bg-green-500" />
                <Wifi size={12} style={{ color: "#22c55e" }} />
                <span className="text-[11px]" style={{ color: "#22c55e" }}>Live</span>
              </>
            ) : (
              <>
                <WifiOff size={12} style={{ color: "#64748b" }} />
                <span className="text-[11px]" style={{ color: "#64748b" }}>Connecting...</span>
              </>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-6">
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            {[
              { label: "Threats Detected", value: stats.total_threats_detected, icon: <Eye size={14} />, color: "#ef4444" },
              { label: "Critical Alerts", value: stats.critical_threats, icon: <AlertTriangle size={14} />, color: "#f97316" },
              { label: "Analyses Run", value: stats.analyses_run, icon: <BarChart2 size={14} />, color: "#3b82f6" },
              { label: "Avg Risk Score", value: `${Math.round(stats.average_risk_score * 100)}`, icon: <Activity size={14} />, color: "#a78bfa" },
            ].map((stat) => (
              <div
                key={stat.label}
                className="rounded-xl p-4"
                style={{ background: "#090f1c", border: "1px solid #0f2040" }}
              >
                <div className="flex items-center gap-2 mb-2">
                  <span style={{ color: stat.color }}>{stat.icon}</span>
                  <p className="text-[11px]" style={{ color: "#475569" }}>{stat.label}</p>
                </div>
                <p className="text-2xl font-bold" style={{ color: stat.color }}>{stat.value}</p>
              </div>
            ))}
          </div>
        )}

        <div className="flex gap-2 mb-6">
          {[
            { id: "monitor" as Tab, label: "Threat Monitor", icon: <Radio size={12} /> },
            { id: "analyze" as Tab, label: "Analyze Content", icon: <Shield size={12} /> },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => { setActiveTab(tab.id); if (tab.id === "monitor") setNewThreatCount(0); }}
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-all"
              style={{
                background: activeTab === tab.id ? "rgba(59,130,246,0.15)" : "transparent",
                color: activeTab === tab.id ? "#60a5fa" : "#64748b",
                border: activeTab === tab.id ? "1px solid rgba(59,130,246,0.3)" : "1px solid transparent",
              }}
            >
              {tab.icon}
              {tab.label}
              {tab.id === "monitor" && newThreatCount > 0 && (
                <span
                  className="ml-1 w-4 h-4 rounded-full text-[9px] font-bold flex items-center justify-center"
                  style={{ background: "#ef4444", color: "white" }}
                >
                  {newThreatCount}
                </span>
              )}
            </button>
          ))}
        </div>

        {activeTab === "monitor" && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Radio size={14} style={{ color: "#3b82f6" }} />
                <h2 className="text-sm font-semibold text-white">Live Threat Feed</h2>
                {connected && (
                  <span
                    className="text-[10px] px-2 py-0.5 rounded-full"
                    style={{ background: "rgba(34,197,94,0.1)", color: "#22c55e", border: "1px solid rgba(34,197,94,0.2)" }}
                  >
                    monitoring active
                  </span>
                )}
              </div>
              <p className="text-[11px]" style={{ color: "#475569" }}>
                {threats.length} active threats
              </p>
            </div>

            {threats.length === 0 ? (
              <div
                className="rounded-xl p-12 text-center"
                style={{ background: "#090f1c", border: "1px solid #0f2040" }}
              >
                <CheckCircle size={32} className="mx-auto mb-3" style={{ color: "#22c55e" }} />
                <p className="text-sm font-semibold text-white mb-1">All Clear</p>
                <p className="text-xs" style={{ color: "#475569" }}>
                  No active threats detected. Monitoring your digital identity...
                </p>
                {!connected && (
                  <p className="text-[11px] mt-2" style={{ color: "#334155" }}>
                    Connect the backend server to start live monitoring
                  </p>
                )}
              </div>
            ) : (
              <div className="space-y-3">
                {threats.map((threat) => (
                  <ThreatCard key={threat.id} threat={threat} onDismiss={handleDismiss} />
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === "analyze" && (
          <div
            className="rounded-xl p-6"
            style={{ background: "#090f1c", border: "1px solid #0f2040" }}
          >
            <div className="flex items-center gap-2 mb-5">
              <Shield size={16} style={{ color: "#3b82f6" }} />
              <h2 className="text-sm font-semibold text-white">Threat Analysis Engine</h2>
              <span
                className="text-[10px] px-2 py-0.5 rounded-full ml-auto"
                style={{ background: "rgba(167,139,250,0.1)", color: "#a78bfa", border: "1px solid rgba(167,139,250,0.2)" }}
              >
                No API key required
              </span>
            </div>
            <AnalysisPanel />
          </div>
        )}
      </main>
    </div>
  );
}
