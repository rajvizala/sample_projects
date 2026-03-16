const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001/api";
const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8001";

export async function analyzeContent(content: string) {
  const res = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content, analysis_type: "full" }),
  });
  if (!res.ok) throw new Error("Analysis failed");
  return res.json();
}

export async function getThreats() {
  const res = await fetch(`${API_BASE}/analyze/threats`);
  if (!res.ok) throw new Error("Failed to fetch threats");
  return res.json();
}

export async function dismissThreat(threatId: string) {
  const res = await fetch(`${API_BASE}/analyze/threats/${threatId}/dismiss`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to dismiss threat");
  return res.json();
}

export async function getStats() {
  const res = await fetch(`${API_BASE.replace("/api", "")}/api/stats`);
  if (!res.ok) throw new Error("Failed to fetch stats");
  return res.json();
}

export function createThreatWebSocket(
  onThreat: (threat: unknown) => void,
  onConnect: () => void,
  onDisconnect: () => void
): WebSocket {
  const ws = new WebSocket(`${WS_BASE}/ws/threats`);

  ws.onopen = onConnect;
  ws.onclose = onDisconnect;
  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data);
      if (msg.type === "new_threat") {
        onThreat(msg.data);
      }
    } catch {}
  };

  const pingInterval = setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: "ping" }));
    }
  }, 30000);

  ws.onclose = () => {
    clearInterval(pingInterval);
    onDisconnect();
  };

  return ws;
}
