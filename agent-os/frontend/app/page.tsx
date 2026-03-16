"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { Send, Zap, ArrowRight } from "lucide-react";
import Sidebar from "@/components/Sidebar";
import ChatMessage from "@/components/ChatMessage";
import ContextPanel from "@/components/ContextPanel";
import AgentBadge from "@/components/AgentBadge";
import { Session, Message, AgentId } from "@/types";
import { createSession, getSessions, getMessages, streamChat } from "@/lib/api";

const STARTER_PROMPTS = [
  { label: "Research competitors", prompt: "Research the top 5 competitors in the B2B SaaS productivity space and identify the biggest market gap I can target." },
  { label: "Write a blog post", prompt: "Write a compelling blog post about how solopreneurs can use AI agents to run an entire business solo in 2025." },
  { label: "Analyze my metrics", prompt: "My MRR is $8,500, growing at 12% MoM with a 4.1% churn rate. Analyze this and tell me the top 3 actions I should take." },
  { label: "Draft customer response", prompt: "Draft a professional response to this customer: 'I've been waiting 5 days for a refund and no one has replied to my emails. This is unacceptable.'" },
];

interface StreamingState {
  content: string;
  agent: AgentId | null;
  thoughts: string[];
  active: boolean;
}

export default function HomePage() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSession, setCurrentSession] = useState<Session | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState<StreamingState>({ content: "", agent: null, thoughts: [], active: false });
  const [initialized, setInitialized] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    getSessions()
      .then((data) => {
        setSessions(data);
        if (data.length > 0) {
          setCurrentSession(data[0]);
          loadMessages(data[0].id);
        }
      })
      .finally(() => setInitialized(true));
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streaming.content]);

  const loadMessages = async (sessionId: string) => {
    try {
      const msgs = await getMessages(sessionId);
      setMessages(msgs);
    } catch {}
  };

  const selectSession = async (id: string) => {
    const session = sessions.find((s) => s.id === id);
    if (!session) return;
    setCurrentSession(session);
    await loadMessages(id);
  };

  const handleSessionCreated = (session: Session) => {
    setSessions((prev) => [session, ...prev]);
    setCurrentSession(session);
    setMessages([]);
  };

  const sendMessage = useCallback(async (messageText?: string) => {
    const text = (messageText || input).trim();
    if (!text || streaming.active) return;

    let sessionToUse: Session | null = currentSession;
    if (!sessionToUse) {
      try {
        const newSession = await createSession("New Session");
        sessionToUse = newSession;
        setSessions((prev) => [newSession, ...prev]);
        setCurrentSession(newSession);
      } catch {
        return;
      }
    }

    if (!sessionToUse) return;

    setInput("");
    setMessages((prev) => [
      ...prev,
      {
        id: Date.now().toString(),
        role: "user",
        content: text,
        created_at: new Date().toISOString(),
      },
    ]);
    setStreaming({ content: "", agent: null, thoughts: [], active: true });

    abortRef.current = streamChat(
      sessionToUse.id,
      text,
      (thought, agent) => {
        setStreaming((prev) => ({
          ...prev,
          thoughts: [...prev.thoughts, thought],
          agent: agent as AgentId,
        }));
      },
      (agent) => setStreaming((prev) => ({ ...prev, agent: agent as AgentId })),
      (token) => setStreaming((prev) => ({ ...prev, content: prev.content + token })),
      (agent) => {
        setStreaming((prev) => {
          const finalContent = prev.content;
          const finalAgent = (agent as AgentId) || prev.agent || "general";
          setMessages((msgs) => [
            ...msgs,
            {
              id: (Date.now() + 1).toString(),
              role: "assistant",
              content: finalContent,
              agent: finalAgent,
              created_at: new Date().toISOString(),
            },
          ]);
          return { content: "", agent: null, thoughts: [], active: false };
        });
      },
      (err) => {
        setMessages((msgs) => [
          ...msgs,
          {
            id: (Date.now() + 1).toString(),
            role: "assistant",
            content: `Error: ${err}. Please check your API configuration.`,
            agent: "general",
            created_at: new Date().toISOString(),
          },
        ]);
        setStreaming({ content: "", agent: null, thoughts: [], active: false });
      }
    );
  }, [input, currentSession, streaming.active]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex h-screen overflow-hidden" style={{ background: "#0a0a0f" }}>
      <Sidebar
        sessions={sessions}
        currentSessionId={currentSession?.id || null}
        onSelectSession={selectSession}
        onSessionCreated={handleSessionCreated}
      />

      <main className="flex flex-col flex-1 min-w-0 h-full">
        <header
          className="flex items-center justify-between px-6 py-3 flex-shrink-0"
          style={{ borderBottom: "1px solid #1e1e2e", background: "#0a0a0f" }}
        >
          <div>
            <h1 className="text-sm font-semibold text-white">
              {currentSession?.name || "AgentOS"}
            </h1>
            <p className="text-xs" style={{ color: "#475569" }}>
              Multi-agent AI operating system
            </p>
          </div>
          {currentSession && (
            <ContextPanel
              sessionId={currentSession.id}
              context={currentSession.business_context}
              onContextUpdated={(ctx) => setCurrentSession({ ...currentSession, business_context: ctx })}
            />
          )}
        </header>

        <div className="flex-1 overflow-y-auto scrollbar-thin px-6 py-4">
          {messages.length === 0 && !streaming.active && initialized ? (
            <div className="flex flex-col items-center justify-center h-full gap-8 max-w-2xl mx-auto">
              <div className="text-center">
                <div
                  className="inline-flex items-center gap-2 rounded-xl px-4 py-2 mb-4 text-sm"
                  style={{ background: "rgba(99,102,241,0.1)", border: "1px solid rgba(99,102,241,0.2)", color: "#a5b4fc" }}
                >
                  <Zap size={12} />
                  5 specialized agents standing by
                </div>
                <h2 className="text-2xl font-bold text-white mb-2">Your AI Business Team</h2>
                <p className="text-sm" style={{ color: "#64748b" }}>
                  Research, write, analyze, and respond — all from a single conversation.
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3 w-full">
                {STARTER_PROMPTS.map((p) => (
                  <button
                    key={p.label}
                    onClick={() => sendMessage(p.prompt)}
                    className="group flex items-start gap-2 rounded-xl px-4 py-3 text-left text-sm transition-all"
                    style={{
                      background: "#111118",
                      border: "1px solid #1e1e2e",
                      color: "#94a3b8",
                    }}
                    onMouseEnter={(e) => {
                      (e.currentTarget as HTMLElement).style.borderColor = "#6366f130";
                      (e.currentTarget as HTMLElement).style.color = "#e2e8f0";
                    }}
                    onMouseLeave={(e) => {
                      (e.currentTarget as HTMLElement).style.borderColor = "#1e1e2e";
                      (e.currentTarget as HTMLElement).style.color = "#94a3b8";
                    }}
                  >
                    <ArrowRight size={12} className="mt-0.5 flex-shrink-0 text-indigo-400 opacity-50 group-hover:opacity-100" />
                    <span>{p.label}</span>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="max-w-3xl mx-auto space-y-6 pb-4">
              {messages.map((msg) => (
                <ChatMessage key={msg.id} message={msg} />
              ))}

              {streaming.active && (
                <ChatMessage
                  message={{
                    id: "streaming",
                    role: "assistant",
                    content: streaming.content,
                    agent: streaming.agent || "general",
                    created_at: new Date().toISOString(),
                  }}
                  isStreaming
                  streamContent={streaming.content}
                  thoughts={streaming.thoughts}
                />
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        <div className="px-6 py-4 flex-shrink-0" style={{ borderTop: "1px solid #1e1e2e", background: "#0a0a0f" }}>
          <div className="max-w-3xl mx-auto">
            {streaming.active && streaming.agent && (
              <div className="flex items-center gap-2 mb-2">
                <div className="flex gap-1">
                  {[0, 150, 300].map((delay) => (
                    <span
                      key={delay}
                      className="animate-pulse-dot inline-block rounded-full"
                      style={{ width: 4, height: 4, background: "#6366f1", animationDelay: `${delay}ms` }}
                    />
                  ))}
                </div>
                <AgentBadge agentId={streaming.agent as AgentId} />
                <span className="text-xs" style={{ color: "#475569" }}>is responding...</span>
              </div>
            )}

            <div
              className="flex items-end gap-3 rounded-xl p-3"
              style={{ background: "#111118", border: "1px solid #1e1e2e" }}
            >
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask your AI team anything — research markets, write content, analyze metrics..."
                disabled={streaming.active}
                rows={1}
                className="flex-1 resize-none bg-transparent text-sm outline-none"
                style={{
                  color: "#e2e8f0",
                  minHeight: "24px",
                  maxHeight: "120px",
                  overflowY: "auto",
                }}
                onInput={(e) => {
                  const t = e.target as HTMLTextAreaElement;
                  t.style.height = "auto";
                  t.style.height = `${Math.min(t.scrollHeight, 120)}px`;
                }}
              />
              <button
                onClick={() => sendMessage()}
                disabled={!input.trim() || streaming.active}
                className="flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center transition-all"
                style={{
                  background: !input.trim() || streaming.active ? "#1a1a24" : "rgba(99,102,241,0.8)",
                  color: !input.trim() || streaming.active ? "#475569" : "white",
                }}
              >
                <Send size={14} />
              </button>
            </div>
            <p className="text-center text-[10px] mt-2" style={{ color: "#334155" }}>
              Powered by Google Gemini — set your API key in backend .env
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
