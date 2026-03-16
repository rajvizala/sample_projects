"use client";

import { useState } from "react";
import { Plus, MessageSquare, ChevronRight, Bot, Search, PenTool, BarChart2, HeartHandshake, Briefcase } from "lucide-react";
import { Session } from "@/types";
import { createSession } from "@/lib/api";

const AGENT_ICONS: Record<string, React.ReactNode> = {
  research: <Search size={12} />,
  content: <PenTool size={12} />,
  analytics: <BarChart2 size={12} />,
  customer: <HeartHandshake size={12} />,
  general: <Briefcase size={12} />,
};

const AGENT_COLORS: Record<string, string> = {
  research: "#6366f1",
  content: "#10b981",
  analytics: "#f59e0b",
  customer: "#ec4899",
  general: "#3b82f6",
};

interface SidebarProps {
  sessions: Session[];
  currentSessionId: string | null;
  onSelectSession: (id: string) => void;
  onSessionCreated: (session: Session) => void;
}

const EXAMPLE_PROMPTS = [
  "Research the AI productivity tools market and identify the top 5 competitors",
  "Write a LinkedIn post about why AI is essential for solopreneurs",
  "Analyze my conversion rate of 2.3% — is it good for SaaS?",
  "Draft a response to a frustrated customer asking for a refund",
];

export default function Sidebar({ sessions, currentSessionId, onSelectSession, onSessionCreated }: SidebarProps) {
  const [creating, setCreating] = useState(false);

  const handleNew = async () => {
    setCreating(true);
    try {
      const session = await createSession(`Session ${sessions.length + 1}`);
      onSessionCreated(session);
    } finally {
      setCreating(false);
    }
  };

  return (
    <aside
      className="flex flex-col h-full w-64 flex-shrink-0"
      style={{ background: "#0a0a0f", borderRight: "1px solid #1e1e2e" }}
    >
      <div className="p-4 flex items-center gap-2" style={{ borderBottom: "1px solid #1e1e2e" }}>
        <div
          className="w-7 h-7 rounded-lg flex items-center justify-center"
          style={{ background: "linear-gradient(135deg, #6366f1, #3b82f6)" }}
        >
          <Bot size={14} color="white" />
        </div>
        <div>
          <p className="text-sm font-semibold text-white">AgentOS</p>
          <p className="text-[10px]" style={{ color: "#64748b" }}>AI Business Platform</p>
        </div>
      </div>

      <div className="p-3">
        <button
          onClick={handleNew}
          disabled={creating}
          className="w-full flex items-center gap-2 rounded-lg px-3 py-2.5 text-sm font-medium transition-all"
          style={{
            background: creating ? "#1a1a24" : "rgba(99,102,241,0.15)",
            color: "#a5b4fc",
            border: "1px solid rgba(99,102,241,0.3)",
          }}
        >
          <Plus size={14} />
          {creating ? "Creating..." : "New Session"}
        </button>
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-thin px-3 pb-3">
        {sessions.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-xs" style={{ color: "#64748b" }}>No sessions yet</p>
          </div>
        ) : (
          <div className="space-y-1">
            {sessions.map((s) => (
              <button
                key={s.id}
                onClick={() => onSelectSession(s.id)}
                className="w-full flex items-center gap-2 rounded-lg px-3 py-2.5 text-sm text-left transition-all group"
                style={{
                  background: currentSessionId === s.id ? "#1a1a24" : "transparent",
                  color: currentSessionId === s.id ? "#e2e8f0" : "#94a3b8",
                  border: currentSessionId === s.id ? "1px solid #1e1e2e" : "1px solid transparent",
                }}
              >
                <MessageSquare size={12} style={{ flexShrink: 0 }} />
                <span className="truncate flex-1">{s.name}</span>
                <ChevronRight size={10} className="opacity-0 group-hover:opacity-100 transition-opacity" />
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="p-3" style={{ borderTop: "1px solid #1e1e2e" }}>
        <p className="text-[10px] font-semibold uppercase tracking-wider mb-2" style={{ color: "#475569" }}>
          Available Agents
        </p>
        <div className="space-y-1">
          {Object.entries(AGENT_ICONS).map(([id, icon]) => (
            <div key={id} className="flex items-center gap-2 px-2 py-1">
              <span style={{ color: AGENT_COLORS[id] }}>{icon}</span>
              <span className="text-xs capitalize" style={{ color: "#64748b" }}>{id}</span>
              <span
                className="ml-auto text-[9px] px-1.5 py-0.5 rounded-full"
                style={{ background: `${AGENT_COLORS[id]}15`, color: AGENT_COLORS[id] }}
              >
                ready
              </span>
            </div>
          ))}
        </div>
      </div>
    </aside>
  );
}
