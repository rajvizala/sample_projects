"""
Optional Gemini API integration for enhanced threat analysis.
Falls back gracefully when API key is not configured.
"""

from app.core.config import get_settings

settings = get_settings()


class GeminiAnalyzer:
    """
    Uses Google Gemini API for advanced natural language threat analysis.
    Provides deeper contextual understanding beyond statistical ML models.

    Requires GEMINI_API_KEY environment variable.
    """

    def __init__(self):
        self.available = False
        self.model = None

        if settings.gemini_api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.gemini_api_key)
                self.model = genai.GenerativeModel("gemini-2.0-flash")
                self.available = True
            except Exception:
                self.available = False

    async def analyze_threat(self, content: str, context: str = "") -> dict | None:
        """
        Perform advanced threat analysis using Gemini.
        Returns None if Gemini is not available.
        """
        if not self.available or not self.model:
            return None

        prompt = f"""Analyze the following content for digital security threats.
Evaluate for:
1. Phishing indicators (social engineering tactics, urgency, impersonation)
2. Scam patterns (financial fraud, identity theft attempts)
3. AI-generated content indicators
4. Malicious intent signals

Content to analyze:
---
{content[:2000]}
---

{f"Additional context: {context}" if context else ""}

Respond in JSON format:
{{
    "threat_level": "none|low|medium|high|critical",
    "confidence": 0.0-1.0,
    "threat_types": ["list of detected threat types"],
    "reasoning": "brief explanation",
    "recommended_action": "what the user should do"
}}"""

        try:
            response = self.model.generate_content(prompt)
            import json
            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(text)
        except Exception:
            return None


_gemini: GeminiAnalyzer | None = None


def get_gemini_analyzer() -> GeminiAnalyzer:
    global _gemini
    if _gemini is None:
        _gemini = GeminiAnalyzer()
    return _gemini
