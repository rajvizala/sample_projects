export interface Agent {
  id: string;
  name: string;
  description: string;
  icon: string;
  color: string;
}

export interface Session {
  id: string;
  name: string;
  business_context: Record<string, string>;
  created_at: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  agent?: string;
  created_at: string;
}

export interface StreamEvent {
  type: "thought" | "agent" | "token" | "done" | "error";
  content?: string;
  agent?: string;
}

export type AgentId = "research" | "content" | "analytics" | "customer" | "general";

export const AGENT_META: Record<AgentId, { label: string; color: string; bgColor: string }> = {
  research: { label: "Research", color: "#6366f1", bgColor: "rgba(99,102,241,0.1)" },
  content: { label: "Content", color: "#10b981", bgColor: "rgba(16,185,129,0.1)" },
  analytics: { label: "Analytics", color: "#f59e0b", bgColor: "rgba(245,158,11,0.1)" },
  customer: { label: "Customer", color: "#ec4899", bgColor: "rgba(236,72,153,0.1)" },
  general: { label: "Advisor", color: "#3b82f6", bgColor: "rgba(59,130,246,0.1)" },
};
