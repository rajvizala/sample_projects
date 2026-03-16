"use client";

import { useState } from "react";
import { Settings, X, Check } from "lucide-react";
import { updateContext } from "@/lib/api";

interface ContextPanelProps {
  sessionId: string;
  context: Record<string, string>;
  onContextUpdated: (ctx: Record<string, string>) => void;
}

const CONTEXT_FIELDS = [
  { key: "business_name", label: "Business Name", placeholder: "e.g. TechStack Inc" },
  { key: "industry", label: "Industry", placeholder: "e.g. B2B SaaS, E-commerce" },
  { key: "target_audience", label: "Target Audience", placeholder: "e.g. startup founders, SMBs" },
  { key: "stage", label: "Stage", placeholder: "e.g. pre-launch, growth" },
  { key: "tone", label: "Brand Tone", placeholder: "e.g. professional, casual, bold" },
];

export default function ContextPanel({ sessionId, context, onContextUpdated }: ContextPanelProps) {
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState<Record<string, string>>(context);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    try {
      await updateContext(sessionId, draft);
      onContextUpdated(draft);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs transition-all"
        style={{ background: "#1a1a24", color: "#94a3b8", border: "1px solid #1e1e2e" }}
      >
        <Settings size={12} />
        Business Context
      </button>

      {open && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          style={{ background: "rgba(0,0,0,0.8)" }}
        >
          <div
            className="w-full max-w-md rounded-xl p-6"
            style={{ background: "#111118", border: "1px solid #1e1e2e" }}
          >
            <div className="flex items-center justify-between mb-5">
              <div>
                <h2 className="text-base font-semibold text-white">Business Context</h2>
                <p className="text-xs mt-0.5" style={{ color: "#64748b" }}>
                  Help agents understand your business for better output
                </p>
              </div>
              <button onClick={() => setOpen(false)} style={{ color: "#64748b" }}>
                <X size={16} />
              </button>
            </div>

            <div className="space-y-3">
              {CONTEXT_FIELDS.map((field) => (
                <div key={field.key}>
                  <label className="block text-xs font-medium mb-1" style={{ color: "#94a3b8" }}>
                    {field.label}
                  </label>
                  <input
                    className="w-full rounded-lg px-3 py-2 text-sm outline-none transition-all"
                    style={{
                      background: "#0a0a0f",
                      border: "1px solid #1e1e2e",
                      color: "#e2e8f0",
                    }}
                    placeholder={field.placeholder}
                    value={draft[field.key] || ""}
                    onChange={(e) => setDraft({ ...draft, [field.key]: e.target.value })}
                    onFocus={(e) => (e.target.style.borderColor = "#6366f1")}
                    onBlur={(e) => (e.target.style.borderColor = "#1e1e2e")}
                  />
                </div>
              ))}
            </div>

            <button
              onClick={handleSave}
              disabled={saving}
              className="mt-5 w-full flex items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium transition-all"
              style={{
                background: saved ? "rgba(16,185,129,0.15)" : "rgba(99,102,241,0.2)",
                color: saved ? "#10b981" : "#a5b4fc",
                border: `1px solid ${saved ? "#10b98130" : "rgba(99,102,241,0.3)"}`,
              }}
            >
              {saved ? <><Check size={14} /> Saved</> : saving ? "Saving..." : "Save Context"}
            </button>
          </div>
        </div>
      )}
    </>
  );
}
