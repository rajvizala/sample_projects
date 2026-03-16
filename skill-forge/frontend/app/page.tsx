"use client";

import { useState, useEffect, useCallback } from "react";
import { Brain, Map, Trophy, ChevronRight, Star, Plus, CheckCircle2, Clock } from "lucide-react";
import dynamic from "next/dynamic";
import CoachChat from "@/components/CoachChat";
import { LearnerProfile, SkillGraph, SkillNode, CATEGORY_COLORS } from "@/types";
import { createLearner, getLearner, getSkillGraph, getSkillDetail, updateSkills } from "@/lib/api";

const SkillGraphViz = dynamic(() => import("@/components/SkillGraphViz"), { ssr: false });

const EXPERIENCE_LEVELS = ["beginner", "intermediate", "advanced"];
const DEFAULT_SKILLS = ["python_basics", "ml_fundamentals", "llm_basics"];
const ROLES = ["Software Engineer", "Data Scientist", "ML Engineer", "Backend Engineer", "Full-Stack Engineer", "DevOps Engineer"];

type Tab = "graph" | "path" | "coach";

export default function HomePage() {
  const [learner, setLearner] = useState<LearnerProfile | null>(null);
  const [graph, setGraph] = useState<SkillGraph | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("graph");
  const [selectedSkill, setSelectedSkill] = useState<string | null>(null);
  const [selectedSkillDetail, setSelectedSkillDetail] = useState<SkillNode | null>(null);
  const [onboarding, setOnboarding] = useState(true);

  const [form, setForm] = useState({
    name: "",
    role: "ML Engineer",
    experience: "intermediate",
    selectedSkills: DEFAULT_SKILLS,
  });
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem("skillforge_learner_id");
    if (saved) {
      getLearner(saved).then((l) => { setLearner(l); setOnboarding(false); }).catch(() => {});
    }
    getSkillGraph().then(setGraph).catch(() => {});
  }, []);

  const handleCreateLearner = async () => {
    if (!form.name.trim()) return;
    setCreating(true);
    try {
      const l = await createLearner(form.name, form.role, form.experience, form.selectedSkills);
      localStorage.setItem("skillforge_learner_id", l.id);
      setLearner(l);
      setOnboarding(false);
    } finally {
      setCreating(false);
    }
  };

  const handleSelectSkill = useCallback(async (skillId: string) => {
    setSelectedSkill(skillId);
    try {
      const detail = await getSkillDetail(skillId);
      setSelectedSkillDetail(detail);
    } catch {}
  }, []);

  const handleMasterSkill = async (skillId: string) => {
    if (!learner) return;
    const newMastered = [...new Set([...learner.mastered_skills, skillId])];
    const result = await updateSkills(learner.id, newMastered);
    setLearner((prev) => prev ? {
      ...prev,
      mastered_skills: newMastered,
      xp_points: prev.xp_points + (result.xp_gained || 0),
      learning_path: result.learning_path || prev.learning_path
    } : null);
  };

  if (onboarding) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4" style={{ background: "#f8fafc" }}>
        <div className="w-full max-w-lg">
          <div className="text-center mb-8">
            <div
              className="inline-flex items-center gap-2 rounded-2xl px-4 py-2 mb-4"
              style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6)", color: "white" }}
            >
              <Brain size={16} />
              <span className="font-semibold text-sm">SkillForge</span>
            </div>
            <h1 className="text-2xl font-bold text-slate-800 mb-2">Build Your AI Skill Path</h1>
            <p className="text-sm text-slate-500">
              Personalized learning powered by knowledge graphs and an AI coach
            </p>
          </div>

          <div
            className="rounded-2xl p-6 shadow-sm"
            style={{ background: "white", border: "1px solid #e2e8f0" }}
          >
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1.5">Your Name</label>
                <input
                  className="w-full rounded-lg px-3 py-2.5 text-sm outline-none"
                  style={{ background: "#f8fafc", border: "1px solid #e2e8f0", color: "#1e293b" }}
                  placeholder="e.g. Alex Chen"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  onFocus={(e) => (e.target.style.borderColor = "#6366f1")}
                  onBlur={(e) => (e.target.style.borderColor = "#e2e8f0")}
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1.5">Your Role</label>
                <div className="grid grid-cols-3 gap-2">
                  {ROLES.map((role) => (
                    <button
                      key={role}
                      onClick={() => setForm({ ...form, role })}
                      className="rounded-lg px-2 py-2 text-xs transition-all"
                      style={{
                        background: form.role === role ? "#eff6ff" : "#f8fafc",
                        border: `1px solid ${form.role === role ? "#6366f1" : "#e2e8f0"}`,
                        color: form.role === role ? "#6366f1" : "#64748b",
                        fontWeight: form.role === role ? 600 : 400
                      }}
                    >
                      {role}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1.5">Experience Level</label>
                <div className="flex gap-2">
                  {EXPERIENCE_LEVELS.map((lvl) => (
                    <button
                      key={lvl}
                      onClick={() => setForm({ ...form, experience: lvl })}
                      className="flex-1 rounded-lg py-2 text-xs capitalize transition-all"
                      style={{
                        background: form.experience === lvl ? "#eff6ff" : "#f8fafc",
                        border: `1px solid ${form.experience === lvl ? "#6366f1" : "#e2e8f0"}`,
                        color: form.experience === lvl ? "#6366f1" : "#64748b",
                        fontWeight: form.experience === lvl ? 600 : 400
                      }}
                    >
                      {lvl}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1.5">
                  Skills you already know <span className="font-normal text-slate-400">(select all that apply)</span>
                </label>
                <div className="flex flex-wrap gap-2 max-h-28 overflow-y-auto">
                  {graph?.nodes.map((node) => {
                    const selected = form.selectedSkills.includes(node.id);
                    return (
                      <button
                        key={node.id}
                        onClick={() => setForm((f) => ({
                          ...f,
                          selectedSkills: selected
                            ? f.selectedSkills.filter((s) => s !== node.id)
                            : [...f.selectedSkills, node.id]
                        }))}
                        className="rounded-full px-2.5 py-1 text-[11px] transition-all"
                        style={{
                          background: selected ? `${CATEGORY_COLORS[node.category]}15` : "#f8fafc",
                          border: `1px solid ${selected ? CATEGORY_COLORS[node.category] : "#e2e8f0"}`,
                          color: selected ? CATEGORY_COLORS[node.category] : "#64748b"
                        }}
                      >
                        {selected && "✓ "}{node.label}
                      </button>
                    );
                  })}
                </div>
              </div>

              <button
                onClick={handleCreateLearner}
                disabled={!form.name.trim() || creating}
                className="w-full flex items-center justify-center gap-2 rounded-xl py-3 text-sm font-semibold transition-all"
                style={{
                  background: !form.name.trim() || creating ? "#e2e8f0" : "linear-gradient(135deg, #6366f1, #8b5cf6)",
                  color: !form.name.trim() || creating ? "#94a3b8" : "white"
                }}
              >
                {creating ? "Building your skill path..." : <>Start Learning <ChevronRight size={14} /></>}
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!learner) return null;

  const masteredCount = learner.mastered_skills.length;
  const totalSkills = graph?.nodes.length || 20;
  const progress = Math.round((masteredCount / totalSkills) * 100);

  return (
    <div className="h-screen flex flex-col overflow-hidden" style={{ background: "#f8fafc" }}>
      <header
        className="flex items-center justify-between px-6 py-3 flex-shrink-0"
        style={{ background: "white", borderBottom: "1px solid #e2e8f0" }}
      >
        <div className="flex items-center gap-3">
          <div
            className="w-7 h-7 rounded-lg flex items-center justify-center"
            style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6)" }}
          >
            <Brain size={14} color="white" />
          </div>
          <div>
            <p className="text-sm font-bold text-slate-800">SkillForge</p>
            <p className="text-[10px] text-slate-400">AI Upskilling Coach</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="hidden md:flex items-center gap-2">
            <div className="w-24 h-1.5 rounded-full bg-slate-100">
              <div
                className="h-full rounded-full transition-all"
                style={{ width: `${progress}%`, background: "linear-gradient(90deg, #6366f1, #8b5cf6)" }}
              />
            </div>
            <span className="text-xs text-slate-500">{progress}% complete</span>
          </div>

          <div className="flex items-center gap-1.5 text-xs font-semibold" style={{ color: "#f59e0b" }}>
            <Trophy size={12} />
            {learner.xp_points} XP
          </div>

          <div
            className="text-xs px-3 py-1 rounded-full"
            style={{ background: "#eff6ff", color: "#6366f1", border: "1px solid #c7d2fe" }}
          >
            {learner.name}
          </div>
        </div>
      </header>

      <div className="flex gap-2 px-6 py-2 flex-shrink-0" style={{ borderBottom: "1px solid #e2e8f0", background: "white" }}>
        {[
          { id: "graph" as Tab, label: "Skill Graph", icon: <Map size={12} /> },
          { id: "path" as Tab, label: "My Path", icon: <ChevronRight size={12} /> },
          { id: "coach" as Tab, label: "AI Coach", icon: <Brain size={12} /> },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all"
            style={{
              background: activeTab === tab.id ? "#eff6ff" : "transparent",
              color: activeTab === tab.id ? "#6366f1" : "#64748b",
              border: activeTab === tab.id ? "1px solid #c7d2fe" : "1px solid transparent"
            }}
          >
            {tab.icon} {tab.label}
          </button>
        ))}

        {selectedSkillDetail && (
          <div
            className="ml-auto flex items-center gap-2 text-xs px-3 py-1.5 rounded-lg"
            style={{ background: `${CATEGORY_COLORS[selectedSkillDetail.category]}10`, color: CATEGORY_COLORS[selectedSkillDetail.category] }}
          >
            <span className="font-medium">{selectedSkillDetail.label}</span>
            {!learner.mastered_skills.includes(selectedSkillDetail.id) && (
              <button
                onClick={() => handleMasterSkill(selectedSkillDetail.id)}
                className="flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full transition-all"
                style={{ background: CATEGORY_COLORS[selectedSkillDetail.category], color: "white" }}
              >
                <Plus size={8} /> Mark mastered
              </button>
            )}
            {learner.mastered_skills.includes(selectedSkillDetail.id) && (
              <CheckCircle2 size={12} />
            )}
          </div>
        )}
      </div>

      <main className="flex-1 overflow-hidden">
        {activeTab === "graph" && graph && (
          <div className="flex h-full">
            <div className="flex-1 relative">
              <SkillGraphViz
                graph={graph}
                masteredSkills={learner.mastered_skills}
                selectedSkill={selectedSkill}
                onSelectSkill={handleSelectSkill}
              />
              <div className="absolute bottom-4 left-4 flex flex-wrap gap-1.5">
                {Object.entries(CATEGORY_COLORS).map(([cat, color]) => (
                  <div key={cat} className="flex items-center gap-1 text-[10px] text-slate-500">
                    <span className="w-2 h-2 rounded-full" style={{ background: color }} />
                    {cat.replace("_", " ")}
                  </div>
                ))}
              </div>
              <div className="absolute top-4 left-4 text-xs text-slate-400">
                Click nodes to select · Drag to rearrange · Scroll to zoom
              </div>
            </div>

            {selectedSkillDetail && (
              <div
                className="w-64 flex-shrink-0 flex flex-col"
                style={{ borderLeft: "1px solid #e2e8f0", background: "white" }}
              >
                <div
                  className="p-4"
                  style={{ borderBottom: "1px solid #e2e8f0" }}
                >
                  <div
                    className="inline-flex text-[10px] px-2 py-0.5 rounded-full mb-2 capitalize"
                    style={{
                      background: `${CATEGORY_COLORS[selectedSkillDetail.category]}15`,
                      color: CATEGORY_COLORS[selectedSkillDetail.category]
                    }}
                  >
                    {selectedSkillDetail.category.replace("_", " ")}
                  </div>
                  <h3 className="text-sm font-bold text-slate-800 mb-1">{selectedSkillDetail.label}</h3>
                  <p className="text-xs text-slate-500">{selectedSkillDetail.description}</p>
                  <div className="flex items-center gap-2 mt-2">
                    <div className="flex">
                      {Array.from({ length: 5 }).map((_, i) => (
                        <Star key={i} size={10} fill={i < selectedSkillDetail.difficulty ? CATEGORY_COLORS[selectedSkillDetail.category] : "#e2e8f0"} style={{ color: CATEGORY_COLORS[selectedSkillDetail.category] }} />
                      ))}
                    </div>
                    <span className="text-[10px] text-slate-400">Difficulty</span>
                  </div>
                </div>

                <div className="flex-1 overflow-y-auto scrollbar-thin p-3 space-y-3">
                  <button
                    onClick={() => { setActiveTab("coach"); }}
                    className="w-full flex items-center gap-2 rounded-lg px-3 py-2.5 text-xs font-medium transition-all"
                    style={{
                      background: `${CATEGORY_COLORS[selectedSkillDetail.category]}10`,
                      color: CATEGORY_COLORS[selectedSkillDetail.category],
                      border: `1px solid ${CATEGORY_COLORS[selectedSkillDetail.category]}30`
                    }}
                  >
                    <Brain size={12} /> Learn with AI Coach
                  </button>

                  {learner.mastered_skills.includes(selectedSkillDetail.id) ? (
                    <div
                      className="flex items-center gap-2 rounded-lg px-3 py-2 text-xs"
                      style={{ background: "#f0fdf4", color: "#16a34a", border: "1px solid #bbf7d0" }}
                    >
                      <CheckCircle2 size={12} /> Mastered
                    </div>
                  ) : (
                    <button
                      onClick={() => handleMasterSkill(selectedSkillDetail.id)}
                      className="w-full flex items-center justify-center gap-2 rounded-lg px-3 py-2 text-xs font-medium transition-all"
                      style={{ background: "#f0fdf4", color: "#16a34a", border: "1px solid #bbf7d0" }}
                    >
                      <Plus size={12} /> Mark as Mastered (+100 XP)
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === "path" && (
          <div className="p-6 overflow-y-auto h-full scrollbar-thin">
            <div className="max-w-2xl mx-auto">
              <h2 className="text-lg font-bold text-slate-800 mb-1">Your Personalized Learning Path</h2>
              <p className="text-sm text-slate-500 mb-6">
                {learner.learning_path.length} skills recommended based on your current knowledge
              </p>

              <div className="space-y-3">
                {learner.learning_path.map((step, i) => {
                  const mastered = learner.mastered_skills.includes(step.id);
                  return (
                    <div
                      key={step.id}
                      className="flex items-start gap-4 rounded-xl p-4 transition-all cursor-pointer"
                      style={{
                        background: mastered ? "#f0fdf4" : "white",
                        border: `1px solid ${mastered ? "#bbf7d0" : "#e2e8f0"}`,
                      }}
                      onClick={() => { handleSelectSkill(step.id); setActiveTab("graph"); }}
                    >
                      <div
                        className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-bold"
                        style={{
                          background: mastered ? "#22c55e" : `${step.color}15`,
                          color: mastered ? "white" : step.color
                        }}
                      >
                        {mastered ? "✓" : step.step}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <p className="text-sm font-semibold text-slate-800">{step.label}</p>
                          <span
                            className="text-[10px] px-2 py-0.5 rounded-full capitalize"
                            style={{ background: `${step.color}15`, color: step.color }}
                          >
                            {step.category.replace("_", " ")}
                          </span>
                        </div>
                        <p className="text-xs text-slate-500">{step.description}</p>
                        <div className="flex items-center gap-3 mt-2">
                          <div className="flex items-center gap-1 text-[10px] text-slate-400">
                            <Clock size={9} />
                            {step.estimated_hours}h estimated
                          </div>
                          <div className="flex">
                            {Array.from({ length: 5 }).map((_, j) => (
                              <Star key={j} size={9} fill={j < step.difficulty ? step.color : "#e2e8f0"} style={{ color: step.color }} />
                            ))}
                          </div>
                        </div>
                      </div>
                      <ChevronRight size={14} className="text-slate-300 flex-shrink-0 mt-1" />
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {activeTab === "coach" && (
          <div className="h-full">
            <CoachChat
              learnerId={learner.id}
              selectedSkill={selectedSkill}
              skillLabel={selectedSkillDetail?.label || ""}
              skillCategory={selectedSkillDetail?.category || "llm"}
            />
          </div>
        )}
      </main>
    </div>
  );
}
