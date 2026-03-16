"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Send, Bot, User, Zap } from "lucide-react";
import { streamCoachChat } from "@/lib/api";
import { ChatMessage, CATEGORY_COLORS } from "@/types";

interface CoachChatProps {
  learnerId: string;
  selectedSkill: string | null;
  skillLabel: string;
  skillCategory: string;
}

function renderContent(content: string) {
  const parts = content.split(/(```[\s\S]*?```)/g);
  return parts.map((part, i) => {
    if (part.startsWith("```")) {
      const lines = part.split("\n");
      const lang = lines[0].replace("```", "").trim();
      const code = lines.slice(1, -1).join("\n");
      return (
        <pre key={i} style={{ background: "#1e293b", color: "#e2e8f0", padding: "0.75em", borderRadius: "8px", overflowX: "auto", fontSize: "0.78em", margin: "0.5em 0" }}>
          {lang && <div style={{ color: "#94a3b8", marginBottom: "0.5em", fontSize: "0.75em" }}>{lang}</div>}
          <code>{code}</code>
        </pre>
      );
    }
    const formatted = part
      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
      .replace(/`([^`]+)`/g, '<code style="background:#f1f5f9;color:#6366f1;padding:0.1em 0.3em;border-radius:3px;font-size:0.85em">$1</code>')
      .split("\n")
      .map((line, j) => {
        if (line.startsWith("- ") || line.startsWith("• ")) {
          return `<li style="margin:0.15em 0">${line.slice(2)}</li>`;
        }
        if (line.match(/^\d+\. /)) {
          return `<li style="margin:0.15em 0">${line.replace(/^\d+\. /, "")}</li>`;
        }
        return line ? `<p style="margin-bottom:0.4em">${line}</p>` : "<br/>";
      })
      .join("");
    return <span key={i} dangerouslySetInnerHTML={{ __html: formatted }} />;
  });
}

const STARTER_MESSAGES = [
  "Explain the key concepts I need to understand",
  "Give me a practical code example",
  "What are common mistakes beginners make?",
  "How does this relate to what I already know?",
];

export default function CoachChat({ learnerId, selectedSkill, skillLabel, skillCategory }: CoachChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState({ active: false, content: "" });
  const [sessionId, setSessionId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);
  const color = CATEGORY_COLORS[skillCategory] || "#6366f1";

  useEffect(() => {
    setMessages([]);
    setSessionId(null);
    setStreaming({ active: false, content: "" });
  }, [selectedSkill]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streaming.content]);

  const sendMessage = useCallback((messageText?: string) => {
    const text = (messageText || input).trim();
    if (!text || streaming.active || !selectedSkill) return;

    setInput("");
    setMessages((prev) => [...prev, {
      id: Date.now().toString(),
      role: "user",
      content: text,
      created_at: new Date().toISOString()
    }]);
    setStreaming({ active: true, content: "" });

    abortRef.current = streamCoachChat(
      learnerId,
      text,
      selectedSkill,
      sessionId,
      (token) => setStreaming((prev) => ({ ...prev, content: prev.content + token })),
      (sid) => {
        setSessionId(sid);
        setStreaming((prev) => {
          setMessages((msgs) => [...msgs, {
            id: (Date.now() + 1).toString(),
            role: "assistant",
            content: prev.content,
            skill_context: selectedSkill,
            created_at: new Date().toISOString()
          }]);
          return { active: false, content: "" };
        });
      },
      (err) => {
        setMessages((msgs) => [...msgs, {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: `Unable to connect to coaching service. Make sure the backend is running and your GEMINI_API_KEY is set. Error: ${err}`,
          created_at: new Date().toISOString()
        }]);
        setStreaming({ active: false, content: "" });
      }
    );
  }, [input, streaming.active, selectedSkill, sessionId, learnerId]);

  if (!selectedSkill) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <Bot size={32} className="mx-auto mb-3" style={{ color: "#cbd5e1" }} />
          <p className="text-sm font-medium text-slate-500">Select a skill from the graph</p>
          <p className="text-xs text-slate-400 mt-1">Your AI coach will guide you through it</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div
        className="flex items-center gap-2 px-4 py-3 flex-shrink-0"
        style={{ borderBottom: "1px solid #e2e8f0" }}
      >
        <div
          className="w-6 h-6 rounded-md flex items-center justify-center"
          style={{ background: `${color}15` }}
        >
          <Bot size={12} style={{ color }} />
        </div>
        <div>
          <p className="text-xs font-semibold text-slate-800">AI Coach — {skillLabel}</p>
          <p className="text-[10px] text-slate-400">Ask anything, get expert guidance</p>
        </div>
        <div
          className="ml-auto flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full"
          style={{ background: `${color}15`, color }}
        >
          <Zap size={8} /> Powered by Gemini
        </div>
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-4">
        {messages.length === 0 && !streaming.active && (
          <div className="space-y-3">
            <p className="text-xs text-center text-slate-400">Start learning {skillLabel}</p>
            <div className="grid grid-cols-2 gap-2">
              {STARTER_MESSAGES.map((msg) => (
                <button
                  key={msg}
                  onClick={() => sendMessage(msg)}
                  className="text-left text-xs rounded-lg px-3 py-2 transition-all"
                  style={{
                    background: "#f8fafc",
                    border: "1px solid #e2e8f0",
                    color: "#64748b"
                  }}
                  onMouseEnter={(e) => {
                    (e.currentTarget as HTMLElement).style.borderColor = color + "60";
                    (e.currentTarget as HTMLElement).style.color = color;
                  }}
                  onMouseLeave={(e) => {
                    (e.currentTarget as HTMLElement).style.borderColor = "#e2e8f0";
                    (e.currentTarget as HTMLElement).style.color = "#64748b";
                  }}
                >
                  {msg}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-2 animate-slide-up ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}
          >
            <div
              className="flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center"
              style={{
                background: msg.role === "user" ? "#eff6ff" : `${color}15`,
                border: "1px solid",
                borderColor: msg.role === "user" ? "#bfdbfe" : `${color}30`
              }}
            >
              {msg.role === "user" ? <User size={10} style={{ color: "#3b82f6" }} /> : <Bot size={10} style={{ color }} />}
            </div>
            <div
              className={`rounded-xl px-3 py-2 max-w-[85%] text-sm ${msg.role === "user" ? "rounded-tr-sm" : "rounded-tl-sm"}`}
              style={{
                background: msg.role === "user" ? "#eff6ff" : "white",
                border: "1px solid",
                borderColor: msg.role === "user" ? "#bfdbfe" : "#f1f5f9",
                color: msg.role === "user" ? "#1e40af" : "#334155"
              }}
            >
              {msg.role === "user" ? (
                <p className="text-sm">{msg.content}</p>
              ) : (
                <div className="prose-chat">{renderContent(msg.content)}</div>
              )}
            </div>
          </div>
        ))}

        {streaming.active && (
          <div className="flex gap-2">
            <div
              className="flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center"
              style={{ background: `${color}15`, border: `1px solid ${color}30` }}
            >
              <Bot size={10} style={{ color }} />
            </div>
            <div
              className="rounded-xl rounded-tl-sm px-3 py-2 max-w-[85%] text-sm"
              style={{ background: "white", border: "1px solid #f1f5f9", color: "#334155" }}
            >
              <div className="prose-chat">
                {renderContent(streaming.content)}
                {!streaming.content && (
                  <div className="flex gap-1">
                    {[0, 150, 300].map((d) => (
                      <span key={d} className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ background: color, animationDelay: `${d}ms` }} />
                    ))}
                  </div>
                )}
                {streaming.content && (
                  <span className="animate-blink inline-block w-0.5 h-3.5 ml-0.5 align-middle" style={{ background: color }} />
                )}
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div
        className="flex items-end gap-2 p-3 flex-shrink-0"
        style={{ borderTop: "1px solid #e2e8f0" }}
      >
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              sendMessage();
            }
          }}
          placeholder={`Ask about ${skillLabel}...`}
          disabled={streaming.active}
          rows={1}
          className="flex-1 resize-none rounded-lg px-3 py-2 text-sm outline-none"
          style={{
            background: "#f8fafc",
            border: "1px solid #e2e8f0",
            color: "#1e293b",
            maxHeight: 100,
            overflowY: "auto"
          }}
          onFocus={(e) => (e.target.style.borderColor = color)}
          onBlur={(e) => (e.target.style.borderColor = "#e2e8f0")}
          onInput={(e) => {
            const t = e.target as HTMLTextAreaElement;
            t.style.height = "auto";
            t.style.height = `${Math.min(t.scrollHeight, 100)}px`;
          }}
        />
        <button
          onClick={() => sendMessage()}
          disabled={!input.trim() || streaming.active}
          className="w-8 h-8 rounded-lg flex items-center justify-center transition-all flex-shrink-0"
          style={{
            background: !input.trim() || streaming.active ? "#f1f5f9" : color,
            color: !input.trim() || streaming.active ? "#94a3b8" : "white"
          }}
        >
          <Send size={14} />
        </button>
      </div>
    </div>
  );
}
