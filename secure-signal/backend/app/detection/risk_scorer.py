"""
Composite risk scoring engine that combines multiple detection signals.
"""
from typing import TypedDict
from .text_analyzer import analyze_text_for_ai, TextAnalysis
from .phishing_detector import analyze_phishing, PhishingAnalysis


class ComprehensiveRiskReport(TypedDict):
    overall_risk_score: float
    overall_verdict: str
    severity_level: str
    phishing_analysis: PhishingAnalysis
    ai_text_analysis: TextAnalysis
    combined_risk_factors: list[str]
    priority_action: str
    confidence: float
    threat_summary: str


def compute_comprehensive_risk(text: str, analysis_type: str = "full") -> ComprehensiveRiskReport:
    phishing = analyze_phishing(text)
    ai_analysis = analyze_text_for_ai(text)

    phishing_weight = 0.7
    ai_weight = 0.3
    combined_score = (phishing["risk_score"] * phishing_weight) + (ai_analysis["ai_probability"] * ai_weight)

    if ai_analysis["ai_probability"] > 0.6 and phishing["risk_score"] > 0.3:
        combined_score = min(combined_score * 1.25, 1.0)
        ai_boost = True
    else:
        ai_boost = False

    risk_factors = []

    if phishing["risk_score"] > 0.1:
        for ind in phishing["indicators"][:3]:
            risk_factors.append(ind["label"])

    if ai_analysis["ai_probability"] > 0.5:
        risk_factors.append(f"AI-generated content detected ({ai_analysis['ai_probability']*100:.0f}% confidence)")

    if ai_boost:
        risk_factors.append("AI-generated phishing attempt — elevated risk profile")

    if combined_score >= 0.7:
        severity = "CRITICAL"
        verdict = "Immediate Threat Detected"
        action = "Block sender, do not engage, report to security team."
    elif combined_score >= 0.5:
        severity = "HIGH"
        verdict = "High-Risk Communication"
        action = "Verify through independent channel, do not click links."
    elif combined_score >= 0.3:
        severity = "MEDIUM"
        verdict = "Suspicious Content"
        action = "Exercise caution, verify sender before responding."
    elif combined_score >= 0.1:
        severity = "LOW"
        verdict = "Minor Risk Indicators"
        action = "Monitor, no immediate action needed."
    else:
        severity = "NONE"
        verdict = "No Threats Detected"
        action = "Safe to proceed normally."

    confidence = 0.85 if len(text) > 100 else 0.60

    if phishing["risk_score"] > 0.5:
        summary = f"{phishing['threat_category'].replace('_', ' ').title()} detected with {len(phishing['indicators'])} active indicators."
    elif ai_analysis["ai_probability"] > 0.5:
        summary = "AI-generated content detected — potential automated social engineering."
    else:
        summary = "Communication appears legitimate with no significant threat indicators."

    return ComprehensiveRiskReport(
        overall_risk_score=round(combined_score, 3),
        overall_verdict=verdict,
        severity_level=severity,
        phishing_analysis=phishing,
        ai_text_analysis=ai_analysis,
        combined_risk_factors=risk_factors,
        priority_action=action,
        confidence=confidence,
        threat_summary=summary
    )
