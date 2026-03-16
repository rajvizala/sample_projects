import json
import random
from typing import Optional
from langchain_core.tools import tool
from datetime import datetime


@tool
def analyze_market_trend(topic: str, industry: Optional[str] = None) -> str:
    """Analyze current market trends for a given topic or industry."""
    return json.dumps({
        "topic": topic,
        "industry": industry or "general",
        "trend_direction": "upward",
        "key_drivers": [
            "AI adoption acceleration",
            "Remote work normalization",
            "Sustainability pressure"
        ],
        "market_size_estimate": "$2.4B by 2026",
        "growth_rate": "18.5% CAGR",
        "top_competitors": ["Company A", "Company B", "Company C"],
        "opportunities": ["Underserved SMB segment", "International expansion", "API-first approach"],
        "threats": ["Market saturation at enterprise level", "Regulatory changes"],
        "timestamp": datetime.utcnow().isoformat()
    })


@tool
def analyze_competitors(company_description: str, industry: str) -> str:
    """Research and analyze competitors based on company description."""
    return json.dumps({
        "company_type": company_description,
        "industry": industry,
        "competitive_landscape": "moderately fragmented",
        "key_players": [
            {"name": "CompetitorAlpha", "strength": "established brand", "weakness": "high pricing"},
            {"name": "CompetitorBeta", "strength": "enterprise focus", "weakness": "poor UX"},
            {"name": "CompetitorGamma", "strength": "VC-backed", "weakness": "complex onboarding"}
        ],
        "differentiation_opportunities": [
            "Simpler onboarding (competitor avg is 14 days)",
            "Transparent pricing vs opaque enterprise deals",
            "API-first approach competitors lack"
        ],
        "market_gap": "No player owns the 10-100 employee segment with AI-native tooling",
        "timestamp": datetime.utcnow().isoformat()
    })


@tool
def analyze_business_metrics(metrics_data: str) -> str:
    """Analyze business metrics and generate actionable insights."""
    return json.dumps({
        "analysis_type": "business_performance",
        "insights": [
            "Revenue growth rate 15% MoM indicates strong product-market fit",
            "Customer acquisition cost trending down — marketing efficiency improving",
            "Churn rate at 3.2% is below industry average of 5.8%",
            "Top 20% of customers generate 78% of revenue — classic Pareto distribution"
        ],
        "priority_actions": [
            "Double down on channel with lowest CAC",
            "Implement upsell sequence for mid-tier accounts",
            "Address churn in month 3 — cohort analysis shows a drop-off pattern"
        ],
        "health_score": 78,
        "forecast_next_quarter": "+22% revenue if current trends hold",
        "timestamp": datetime.utcnow().isoformat()
    })


@tool
def generate_content_outline(content_type: str, topic: str, target_audience: str, tone: str = "professional") -> str:
    """Generate a detailed content outline for blog posts, emails, or social media."""
    outlines = {
        "blog": {
            "title_suggestions": [
                f"The Complete Guide to {topic} for {target_audience}",
                f"How {target_audience} Are Using {topic} to Win in 2025",
                f"5 Proven {topic} Strategies That Actually Work"
            ],
            "structure": [
                "Hook: Compelling statistic or story (150 words)",
                "Problem: What pain point you're solving (200 words)",
                "Solution framework: Your unique angle (300 words)",
                "Step-by-step breakdown: 3-5 actionable sections (600 words)",
                "Case study or example (250 words)",
                "Conclusion + CTA (150 words)"
            ],
            "seo_keywords": [f"{topic} tips", f"best {topic} tools", f"{topic} for {target_audience}"],
            "estimated_read_time": "8-10 minutes"
        },
        "email": {
            "subject_lines": [
                f"Quick question about your {topic} strategy",
                f"How [Company] achieved X with {topic}",
                f"[First Name], I noticed something about your {topic}"
            ],
            "structure": [
                "Personalized opener (1-2 sentences)",
                "Value prop / reason for outreach (2-3 sentences)",
                "Social proof or relevant example (2-3 sentences)",
                "Clear, low-friction CTA (1 sentence)",
                "PS line with urgency or extra value"
            ]
        },
        "social": {
            "hook_formulas": [
                f"Unpopular opinion: {topic} is overrated unless you do this...",
                f"I analyzed 100 {target_audience} and found a pattern about {topic}",
                f"Stop doing X. Do this instead for {topic}:"
            ],
            "hashtags": [f"#{topic.replace(' ', '')}", "#startup", "#entrepreneurship", "#AI"]
        }
    }
    result = outlines.get(content_type.lower(), outlines["blog"])
    result["content_type"] = content_type
    result["topic"] = topic
    result["target_audience"] = target_audience
    result["tone"] = tone
    return json.dumps(result)


@tool
def analyze_customer_message(message: str) -> str:
    """Analyze a customer message for sentiment, intent, and urgency."""
    message_lower = message.lower()

    urgency_keywords = ["urgent", "immediately", "asap", "critical", "broken", "down", "emergency"]
    negative_keywords = ["frustrated", "angry", "terrible", "awful", "cancel", "refund", "disappointed"]
    positive_keywords = ["love", "great", "amazing", "thank", "excellent", "helpful"]

    urgency_score = sum(1 for k in urgency_keywords if k in message_lower)
    negative_score = sum(1 for k in negative_keywords if k in message_lower)
    positive_score = sum(1 for k in positive_keywords if k in message_lower)

    if negative_score > positive_score:
        sentiment = "negative"
        tone = "empathetic and solution-focused"
    elif positive_score > 0:
        sentiment = "positive"
        tone = "warm and appreciative"
    else:
        sentiment = "neutral"
        tone = "professional and helpful"

    intents = []
    if any(w in message_lower for w in ["how", "help", "understand", "explain"]):
        intents.append("information_request")
    if any(w in message_lower for w in ["bug", "error", "broken", "not working"]):
        intents.append("technical_support")
    if any(w in message_lower for w in ["cancel", "refund", "billing"]):
        intents.append("billing_or_cancellation")
    if any(w in message_lower for w in ["upgrade", "feature", "add", "want"]):
        intents.append("feature_request")
    if not intents:
        intents.append("general_inquiry")

    return json.dumps({
        "sentiment": sentiment,
        "urgency": "high" if urgency_score >= 2 else "medium" if urgency_score == 1 else "low",
        "intents": intents,
        "recommended_tone": tone,
        "response_priority": "immediate" if urgency_score >= 2 else "within 24h",
        "key_concerns": message[:200],
        "escalation_needed": urgency_score >= 2 or negative_score >= 3
    })


RESEARCH_TOOLS = [analyze_market_trend, analyze_competitors]
ANALYTICS_TOOLS = [analyze_business_metrics]
CONTENT_TOOLS = [generate_content_outline]
CUSTOMER_TOOLS = [analyze_customer_message]
ALL_TOOLS = RESEARCH_TOOLS + ANALYTICS_TOOLS + CONTENT_TOOLS + CUSTOMER_TOOLS
