"use client";

import { AGENT_META, AgentId } from "@/types";

interface AgentBadgeProps {
  agentId: AgentId;
  size?: "sm" | "md";
}

export default function AgentBadge({ agentId, size = "sm" }: AgentBadgeProps) {
  const meta = AGENT_META[agentId] || AGENT_META.general;
  const sizeClass = size === "sm" ? "text-[10px] px-2 py-0.5" : "text-xs px-2.5 py-1";

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full font-medium ${sizeClass}`}
      style={{ color: meta.color, background: meta.bgColor, border: `1px solid ${meta.color}30` }}
    >
      <span
        className="inline-block rounded-full"
        style={{ width: 5, height: 5, background: meta.color }}
      />
      {meta.label}
    </span>
  );
}
