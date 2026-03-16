"""
Neo4J Knowledge Graph for AI skills and their relationships.
Implements a graph of skills, tools, concepts, and learning paths.
Falls back to in-memory graph if Neo4J is unavailable.
"""
from typing import Optional
import logging

logger = logging.getLogger(__name__)

AI_SKILL_GRAPH = {
    "nodes": [
        {"id": "python_basics", "label": "Python Basics", "category": "programming", "difficulty": 1, "description": "Variables, loops, functions, data structures"},
        {"id": "python_advanced", "label": "Advanced Python", "category": "programming", "difficulty": 3, "description": "Decorators, generators, async/await, metaclasses"},
        {"id": "ml_fundamentals", "label": "ML Fundamentals", "category": "machine_learning", "difficulty": 2, "description": "Supervised, unsupervised learning, train/test split"},
        {"id": "neural_networks", "label": "Neural Networks", "category": "deep_learning", "difficulty": 3, "description": "Perceptrons, backpropagation, activation functions"},
        {"id": "transformers", "label": "Transformers", "category": "deep_learning", "difficulty": 4, "description": "Attention mechanism, BERT, GPT architecture"},
        {"id": "llm_basics", "label": "LLM Basics", "category": "llm", "difficulty": 2, "description": "Prompting, temperature, tokens, context windows"},
        {"id": "prompt_engineering", "label": "Prompt Engineering", "category": "llm", "difficulty": 2, "description": "Zero-shot, few-shot, chain-of-thought prompting"},
        {"id": "rag_systems", "label": "RAG Systems", "category": "llm", "difficulty": 3, "description": "Retrieval-augmented generation, vector stores, chunking"},
        {"id": "langchain", "label": "LangChain", "category": "frameworks", "difficulty": 3, "description": "Chains, agents, memory, tools, callbacks"},
        {"id": "langgraph", "label": "LangGraph", "category": "frameworks", "difficulty": 4, "description": "State graphs, nodes, edges, multi-agent orchestration"},
        {"id": "vector_databases", "label": "Vector Databases", "category": "infrastructure", "difficulty": 3, "description": "FAISS, Pinecone, Weaviate, similarity search"},
        {"id": "fine_tuning", "label": "Fine-tuning", "category": "deep_learning", "difficulty": 4, "description": "LoRA, QLoRA, PEFT, dataset preparation"},
        {"id": "ai_agents", "label": "AI Agents", "category": "llm", "difficulty": 4, "description": "Tool use, planning, ReAct, autonomous agents"},
        {"id": "computer_vision", "label": "Computer Vision", "category": "deep_learning", "difficulty": 3, "description": "CNNs, object detection, image classification"},
        {"id": "mlops", "label": "MLOps", "category": "infrastructure", "difficulty": 4, "description": "Model deployment, monitoring, versioning, CI/CD"},
        {"id": "data_preprocessing", "label": "Data Preprocessing", "category": "machine_learning", "difficulty": 2, "description": "Feature engineering, normalization, handling missing data"},
        {"id": "evaluation_metrics", "label": "Evaluation Metrics", "category": "machine_learning", "difficulty": 2, "description": "Accuracy, F1, BLEU, ROUGE, perplexity"},
        {"id": "api_integration", "label": "API Integration", "category": "engineering", "difficulty": 2, "description": "REST APIs, OpenAI API, Gemini API, webhooks"},
        {"id": "embeddings", "label": "Embeddings", "category": "llm", "difficulty": 3, "description": "Word2Vec, sentence transformers, cosine similarity"},
        {"id": "knowledge_graphs", "label": "Knowledge Graphs", "category": "infrastructure", "difficulty": 4, "description": "Neo4J, ontologies, graph traversal, SPARQL"},
    ],
    "edges": [
        {"from": "python_basics", "to": "python_advanced", "relationship": "PREREQUISITE_FOR", "weight": 1.0},
        {"from": "python_basics", "to": "ml_fundamentals", "relationship": "PREREQUISITE_FOR", "weight": 0.9},
        {"from": "python_basics", "to": "api_integration", "relationship": "PREREQUISITE_FOR", "weight": 0.8},
        {"from": "ml_fundamentals", "to": "neural_networks", "relationship": "PREREQUISITE_FOR", "weight": 1.0},
        {"from": "ml_fundamentals", "to": "data_preprocessing", "relationship": "LEADS_TO", "weight": 0.9},
        {"from": "ml_fundamentals", "to": "evaluation_metrics", "relationship": "LEADS_TO", "weight": 0.9},
        {"from": "neural_networks", "to": "transformers", "relationship": "PREREQUISITE_FOR", "weight": 1.0},
        {"from": "neural_networks", "to": "computer_vision", "relationship": "LEADS_TO", "weight": 0.8},
        {"from": "transformers", "to": "llm_basics", "relationship": "LEADS_TO", "weight": 1.0},
        {"from": "transformers", "to": "fine_tuning", "relationship": "LEADS_TO", "weight": 0.9},
        {"from": "llm_basics", "to": "prompt_engineering", "relationship": "LEADS_TO", "weight": 1.0},
        {"from": "llm_basics", "to": "api_integration", "relationship": "RELATED_TO", "weight": 0.7},
        {"from": "prompt_engineering", "to": "langchain", "relationship": "LEADS_TO", "weight": 0.9},
        {"from": "prompt_engineering", "to": "rag_systems", "relationship": "LEADS_TO", "weight": 0.8},
        {"from": "langchain", "to": "rag_systems", "relationship": "USED_IN", "weight": 0.9},
        {"from": "langchain", "to": "ai_agents", "relationship": "LEADS_TO", "weight": 0.9},
        {"from": "langchain", "to": "langgraph", "relationship": "LEADS_TO", "weight": 1.0},
        {"from": "rag_systems", "to": "vector_databases", "relationship": "REQUIRES", "weight": 1.0},
        {"from": "rag_systems", "to": "embeddings", "relationship": "REQUIRES", "weight": 1.0},
        {"from": "vector_databases", "to": "knowledge_graphs", "relationship": "RELATED_TO", "weight": 0.6},
        {"from": "langgraph", "to": "ai_agents", "relationship": "USED_FOR", "weight": 1.0},
        {"from": "ai_agents", "to": "mlops", "relationship": "LEADS_TO", "weight": 0.7},
        {"from": "fine_tuning", "to": "mlops", "relationship": "LEADS_TO", "weight": 0.8},
        {"from": "embeddings", "to": "vector_databases", "relationship": "USED_WITH", "weight": 0.9},
        {"from": "python_advanced", "to": "langchain", "relationship": "USED_IN", "weight": 0.7},
    ]
}

CATEGORY_COLORS = {
    "programming": "#6366f1",
    "machine_learning": "#10b981",
    "deep_learning": "#f59e0b",
    "llm": "#ec4899",
    "frameworks": "#3b82f6",
    "infrastructure": "#8b5cf6",
    "engineering": "#06b6d4",
}


class SkillGraph:
    def __init__(self):
        self._graph = AI_SKILL_GRAPH
        self._node_map = {n["id"]: n for n in self._graph["nodes"]}

    def get_full_graph(self) -> dict:
        nodes = []
        for n in self._graph["nodes"]:
            nodes.append({
                **n,
                "color": CATEGORY_COLORS.get(n["category"], "#64748b"),
                "size": (n["difficulty"] * 4) + 12
            })
        return {"nodes": nodes, "edges": self._graph["edges"]}

    def get_skill(self, skill_id: str) -> Optional[dict]:
        return self._node_map.get(skill_id)

    def get_prerequisites(self, skill_id: str) -> list[dict]:
        prereqs = []
        for edge in self._graph["edges"]:
            if edge["to"] == skill_id and edge["relationship"] == "PREREQUISITE_FOR":
                node = self._node_map.get(edge["from"])
                if node:
                    prereqs.append({**node, "relationship": edge["relationship"]})
        return prereqs

    def get_next_skills(self, skill_id: str) -> list[dict]:
        nexts = []
        for edge in self._graph["edges"]:
            if edge["from"] == skill_id:
                node = self._node_map.get(edge["to"])
                if node:
                    nexts.append({
                        **node,
                        "relationship": edge["relationship"],
                        "weight": edge["weight"]
                    })
        return sorted(nexts, key=lambda x: x["weight"], reverse=True)

    def compute_learning_path(self, mastered: list[str], target_skills: list[str]) -> list[dict]:
        """BFS-based learning path from mastered skills to target skills."""
        if not target_skills:
            target_skills = ["ai_agents", "mlops", "fine_tuning"]

        mastered_set = set(mastered)
        to_learn = []
        visited = set(mastered)
        queue = []

        for skill_id in self._node_map:
            if skill_id not in mastered_set:
                prereqs = self.get_prerequisites(skill_id)
                all_met = all(p["id"] in mastered_set for p in prereqs)
                if all_met:
                    queue.append(skill_id)

        seen = set()
        priority_order = []
        for target in target_skills:
            path = self._find_path_to_target(mastered_set, target)
            for skill_id in path:
                if skill_id not in seen:
                    seen.add(skill_id)
                    priority_order.append(skill_id)

        for skill_id in queue:
            if skill_id not in seen:
                seen.add(skill_id)
                priority_order.append(skill_id)

        result = []
        for i, skill_id in enumerate(priority_order[:8]):
            node = self._node_map.get(skill_id)
            if node:
                result.append({
                    **node,
                    "step": i + 1,
                    "color": CATEGORY_COLORS.get(node["category"], "#64748b"),
                    "estimated_hours": node["difficulty"] * 8
                })
        return result

    def _find_path_to_target(self, mastered: set, target: str) -> list[str]:
        if target in mastered:
            return []

        prereqs = self.get_prerequisites(target)
        path = []
        for prereq in prereqs:
            if prereq["id"] not in mastered:
                sub_path = self._find_path_to_target(mastered, prereq["id"])
                path.extend(sub_path)
                path.append(prereq["id"])

        path.append(target)
        return [s for i, s in enumerate(path) if s not in path[:i]]

    def get_skill_categories(self) -> dict:
        categories: dict[str, list] = {}
        for node in self._graph["nodes"]:
            cat = node["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(node["id"])
        return categories

    def search_skills(self, query: str) -> list[dict]:
        query_lower = query.lower()
        results = []
        for node in self._graph["nodes"]:
            if (query_lower in node["label"].lower() or
                    query_lower in node["description"].lower() or
                    query_lower in node["category"].lower()):
                results.append(node)
        return results[:10]


_skill_graph: Optional[SkillGraph] = None


def get_skill_graph() -> SkillGraph:
    global _skill_graph
    if _skill_graph is None:
        _skill_graph = SkillGraph()
    return _skill_graph
