"""
Multi-layer phishing and social engineering detector.
Uses pattern matching, heuristics, and structural analysis.
"""
import re
from typing import TypedDict
from urllib.parse import urlparse


class PhishingAnalysis(TypedDict):
    risk_score: float
    verdict: str
    threat_category: str
    indicators: list[dict]
    highlighted_segments: list[dict]
    recommended_action: str


URGENCY_PATTERNS = [
    (r"\baccount\s+(has\s+been\s+)?(suspended|locked|disabled|compromised)\b", "Account suspension threat", 0.35),
    (r"\bimmediate(ly)?\s+(action|attention|response|verify)\b", "Urgency trigger", 0.25),
    (r"\b(within\s+)?(24|48|72)\s+hours?\b", "Time pressure", 0.20),
    (r"\byour\s+(account\s+)?(will\s+be\s+)?(terminated|closed|suspended)\b", "Termination threat", 0.35),
    (r"\bact\s+now\b|\bdon't\s+delay\b|\bexpires?\s+(today|soon)\b", "Urgency language", 0.20),
    (r"\bunusual\s+(activity|sign.in|access|login)\b", "Security alert claim", 0.25),
]

CREDENTIAL_HARVESTING_PATTERNS = [
    (r"\bverify\s+your\s+(account|identity|email|password|information)\b", "Credential verification request", 0.40),
    (r"\bclick\s+(here|below|the\s+link)\s+to\s+(verify|confirm|reset|update)\b", "Phishing CTA", 0.40),
    (r"\benter\s+your\s+(password|credentials|login|username|ssn|social\s+security)\b", "Credential input request", 0.45),
    (r"\bupdate\s+your\s+(billing|payment|credit\s+card|account)\s+(information|details)\b", "Financial data request", 0.40),
    (r"\bsecure\s+your\s+account\s+by\s+(clicking|following|visiting)\b", "Fake security action", 0.35),
]

IMPERSONATION_PATTERNS = [
    (r"\b(paypal|apple\s+pay|google\s+pay|amazon\s+pay|venmo|zelle)\s+(team|support|security|billing)\b", "Payment platform impersonation", 0.50),
    (r"\b(irs|internal\s+revenue\s+service|social\s+security\s+administration|ssa)\b", "Government agency impersonation", 0.55),
    (r"\b(microsoft|apple|google|amazon|netflix|bank\s+of\s+america|chase|wells\s+fargo)\s+(security|support|team|billing)\b", "Brand impersonation", 0.45),
    (r"\bthis\s+is\s+a\s+(official|secure|authorized)\s+(message|notification)\s+from\b", "Fake official claim", 0.40),
]

FINANCIAL_SCAM_PATTERNS = [
    (r"\b(you\s+have\s+)?(won|been\s+selected|are\s+eligible\s+for)\s+.{0,30}(prize|reward|lottery|jackpot)\b", "Prize scam", 0.55),
    (r"\b(wire\s+transfer|western\s+union|money\s+gram|gift\s+card)\b", "High-risk payment method", 0.45),
    (r"\brefund\s+of\s+\$[\d,]+\b", "Fake refund offer", 0.40),
    (r"\badvance\s+fee\b|\bprocessing\s+fee\b.{0,30}(lottery|prize|inheritance)\b", "Advance fee fraud", 0.60),
    (r"\bunclaimed\s+(funds|money|inheritance|property)\b", "Unclaimed funds scam", 0.45),
]

SUSPICIOUS_URL_PATTERNS = [
    r"(login|verify|secure|account|update|confirm)\.(.*?)\.(tk|ml|ga|cf|xyz|top|click|download)",
    r"[a-z0-9]+-[a-z0-9]+-[a-z0-9]+\.(com|net|org)/(verify|login|secure)",
    r"(paypal|amazon|apple|google|microsoft)\.[a-z]{4,}\.(com|net|org)",
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/",
]


def _check_url_suspicious(url: str) -> tuple[bool, str]:
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        trusted = ["paypal.com", "amazon.com", "apple.com", "google.com", "microsoft.com",
                   "chase.com", "bankofamerica.com", "irs.gov", "ssa.gov"]
        if any(domain == t or domain.endswith("." + t) for t in trusted):
            return False, ""

        for pattern in SUSPICIOUS_URL_PATTERNS:
            if re.search(pattern, url.lower()):
                return True, f"Suspicious URL pattern: {url[:60]}..."

        subdomain_count = domain.count(".")
        if subdomain_count > 3:
            return True, f"Excessive subdomains in URL: {domain}"

        tld_suspicious = [".tk", ".ml", ".ga", ".cf", ".xyz", ".top", ".click"]
        if any(domain.endswith(t) for t in tld_suspicious):
            return True, f"High-risk TLD detected: {domain}"

    except Exception:
        pass
    return False, ""


def analyze_phishing(text: str) -> PhishingAnalysis:
    text_lower = text.lower()
    indicators = []
    total_score = 0.0

    for pattern, label, weight in URGENCY_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            indicators.append({"type": "urgency", "label": label, "weight": weight, "severity": "medium"})
            total_score += weight

    for pattern, label, weight in CREDENTIAL_HARVESTING_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            indicators.append({"type": "credential_harvesting", "label": label, "weight": weight, "severity": "high"})
            total_score += weight

    for pattern, label, weight in IMPERSONATION_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            indicators.append({"type": "impersonation", "label": label, "weight": weight, "severity": "high"})
            total_score += weight

    for pattern, label, weight in FINANCIAL_SCAM_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            indicators.append({"type": "financial_scam", "label": label, "weight": weight, "severity": "critical"})
            total_score += weight

    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    urls = re.findall(url_pattern, text)
    for url in urls:
        suspicious, reason = _check_url_suspicious(url)
        if suspicious:
            indicators.append({"type": "malicious_url", "label": reason, "weight": 0.50, "severity": "critical"})
            total_score += 0.50

    risk_score = min(total_score, 1.0)

    if risk_score >= 0.7:
        verdict = "HIGH RISK — Likely Phishing"
        threat_category = "phishing"
        action = "Do NOT click any links or provide information. Report to your email provider and delete immediately."
    elif risk_score >= 0.4:
        verdict = "SUSPICIOUS — Proceed with Caution"
        threat_category = "social_engineering"
        action = "Verify the sender through a separate, trusted channel before taking any action."
    elif risk_score >= 0.15:
        verdict = "LOW RISK — Minor Concerns"
        threat_category = "spam"
        action = "Use caution. Verify sender identity if you weren't expecting this message."
    else:
        verdict = "SAFE — No Threats Detected"
        threat_category = "none"
        action = "No immediate action required."

    highlighted = []
    for _, pattern, label, _ in [(i["type"], p, i["label"], i["weight"])
                                   for i, (p, _, _) in
                                   zip(indicators, [(p, l, w) for p, l, w in
                                                    URGENCY_PATTERNS + CREDENTIAL_HARVESTING_PATTERNS +
                                                    IMPERSONATION_PATTERNS + FINANCIAL_SCAM_PATTERNS])
                                   if re.search(p, text_lower, re.IGNORECASE)]:
        match = re.search(label.lower().replace(" ", ".{0,5}"), text_lower)
        if match:
            highlighted.append({"start": match.start(), "end": match.end(), "label": label})

    return PhishingAnalysis(
        risk_score=round(risk_score, 3),
        verdict=verdict,
        threat_category=threat_category,
        indicators=indicators[:10],
        highlighted_segments=highlighted[:5],
        recommended_action=action
    )
