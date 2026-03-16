export interface SkillNode {
  id: string;
  label: string;
  category: string;
  difficulty: number;
  description: string;
  color: string;
  size: number;
}

export interface SkillEdge {
  from: string;
  to: string;
  relationship: string;
  weight: number;
}

export interface SkillGraph {
  nodes: SkillNode[];
  edges: SkillEdge[];
}

export interface LearnerProfile {
  id: string;
  name: string;
  role: string;
  experience_level: string;
  mastered_skills: string[];
  learning_path: LearningStep[];
  xp_points: number;
  streak_days: number;
  created_at: string;
}

export interface LearningStep {
  id: string;
  label: string;
  category: string;
  difficulty: number;
  description: string;
  step: number;
  color: string;
  estimated_hours: number;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  skill_context?: string;
  created_at: string;
}

export const CATEGORY_COLORS: Record<string, string> = {
  programming: "#6366f1",
  machine_learning: "#10b981",
  deep_learning: "#f59e0b",
  llm: "#ec4899",
  frameworks: "#3b82f6",
  infrastructure: "#8b5cf6",
  engineering: "#06b6d4",
};
