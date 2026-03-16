"use client";

import { Message, AgentId } from "@/types";
import AgentBadge from "./AgentBadge";
import { User } from "lucide-react";

interface ChatMessageProps {
  message: Message;
  isStreaming?: boolean;
  streamContent?: string;
  thoughts?: string[];
}

function formatContent(content: string): React.ReactNode {
  const lines = content.split("\n");
  return lines.map((line, i) => {
    if (line.startsWith("## ")) return <h2 key={i} style={{ color: "#e2e8f0", fontWeight: 600, fontSize: "1rem", marginTop: "1em", marginBottom: "0.3em" }}>{line.slice(3)}</h2>;
    if (line.startsWith("# ")) return <h1 key={i} style={{ color: "#f1f5f9", fontWeight: 700, fontSize: "1.1rem", marginTop: "0.5em", marginBottom: "0.3em" }}>{line.slice(2)}</h1>;
    if (line.startsWith("**") && line.endsWith("**")) return <p key={i} style={{ color: "#f1f5f9", fontWeight: 600, marginBottom: "0.25em" }}>{line.slice(2, -2)}</p>;
    if (line.startsWith("- ") || line.startsWith("* ")) return <li key={i} style={{ color: "#cbd5e1", marginLeft: "1.2em", marginBottom: "0.15em", listStyleType: "disc" }}>{line.slice(2)}</li>;
    if (line.match(/^\d+\. /)) return <li key={i} style={{ color: "#cbd5e1", marginLeft: "1.2em", marginBottom: "0.15em", listStyleType: "decimal" }}>{line.replace(/^\d+\. /, "")}</li>;
    if (line === "") return <br key={i} />;
    return <p key={i} style={{ color: "#cbd5e1", marginBottom: "0.25em" }}>{line}</p>;
  });
}

export default function ChatMessage({ message, isStreaming, streamContent, thoughts }: ChatMessageProps) {
  const isUser = message.role === "user";
  const displayContent = isStreaming ? streamContent || "" : message.content;

  return (
    <div className={`flex gap-3 animate-slide-in ${isUser ? "flex-row-reverse" : "flex-row"}`}>
      <div
        className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold"
        style={{
          background: isUser ? "#3b82f6" : "#1a1a24",
          border: "1px solid",
          borderColor: isUser ? "#3b82f620" : "#1e1e2e",
        }}
      >
        {isUser ? <User size={14} /> : <span style={{ color: "#6366f1" }}>AI</span>}
      </div>

      <div className={`flex flex-col gap-1 max-w-[80%] ${isUser ? "items-end" : "items-start"}`}>
        {!isUser && message.agent && (
          <AgentBadge agentId={message.agent as AgentId} />
        )}

        {!isUser && thoughts && thoughts.length > 0 && (
          <div
            className="rounded-lg px-3 py-2 text-xs mb-1"
            style={{ background: "#0d0d14", border: "1px solid #1e1e2e", color: "#64748b" }}
          >
            {thoughts.map((t, i) => (
              <div key={i} className="flex items-center gap-1.5">
                <span style={{ color: "#6366f150" }}>...</span>
                <span>{t}</span>
              </div>
            ))}
          </div>
        )}

        <div
          className="rounded-2xl px-4 py-3 text-sm leading-relaxed"
          style={{
            background: isUser ? "#1e3a5f" : "#111118",
            border: "1px solid",
            borderColor: isUser ? "#2563eb30" : "#1e1e2e",
            color: isUser ? "#bfdbfe" : "#cbd5e1",
          }}
        >
          {isUser ? (
            <p>{displayContent}</p>
          ) : (
            <div className="prose-dark">
              {formatContent(displayContent)}
              {isStreaming && (
                <span
                  className="animate-blink inline-block w-0.5 h-4 ml-0.5 align-middle"
                  style={{ background: "#6366f1" }}
                />
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
