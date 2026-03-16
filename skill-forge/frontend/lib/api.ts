const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8002/api";

export async function createLearner(name: string, role: string, experience: string, skills: string[]) {
  const res = await fetch(`${API_BASE}/learners`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, role, experience_level: experience, initial_skills: skills }),
  });
  if (!res.ok) throw new Error("Failed to create learner");
  return res.json();
}

export async function getLearner(learnerId: string) {
  const res = await fetch(`${API_BASE}/learners/${learnerId}`);
  if (!res.ok) throw new Error("Failed to fetch learner");
  return res.json();
}

export async function updateSkills(learnerId: string, masteredSkills: string[]) {
  const res = await fetch(`${API_BASE}/learners/${learnerId}/skills`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mastered_skills: masteredSkills }),
  });
  if (!res.ok) throw new Error("Failed to update skills");
  return res.json();
}

export async function getSkillGraph() {
  const res = await fetch(`${API_BASE}/graph`);
  if (!res.ok) throw new Error("Failed to fetch graph");
  return res.json();
}

export async function getSkillDetail(skillId: string) {
  const res = await fetch(`${API_BASE}/graph/skill/${skillId}`);
  if (!res.ok) throw new Error("Failed to fetch skill");
  return res.json();
}

export async function getAssessmentQuestions(skillId: string) {
  const res = await fetch(`${API_BASE}/coach/questions/${skillId}`);
  if (!res.ok) throw new Error("Failed to fetch questions");
  return res.json();
}

export async function submitAssessment(learnerId: string, skillId: string, question: string, answer: string) {
  const res = await fetch(`${API_BASE}/coach/assess`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ learner_id: learnerId, skill_id: skillId, question, answer }),
  });
  if (!res.ok) throw new Error("Assessment failed");
  return res.json();
}

export function streamCoachChat(
  learnerId: string,
  message: string,
  skillId: string,
  sessionId: string | null,
  onToken: (token: string) => void,
  onDone: (sessionId: string) => void,
  onError: (err: string) => void
): AbortController {
  const controller = new AbortController();

  fetch(`${API_BASE}/coach/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      learner_id: learnerId,
      message,
      skill_id: skillId,
      session_id: sessionId
    }),
    signal: controller.signal,
  }).then(async (res) => {
    if (!res.ok) { onError("Request failed"); return; }
    const reader = res.body!.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";
      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        try {
          const event = JSON.parse(line.slice(6));
          if (event.type === "token") onToken(event.content);
          else if (event.type === "done") onDone(event.session_id);
        } catch {}
      }
    }
  }).catch((err) => { if (err.name !== "AbortError") onError(err.message); });

  return controller;
}
