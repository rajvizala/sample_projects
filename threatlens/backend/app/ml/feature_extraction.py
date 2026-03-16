"""
Feature extraction pipelines for threat detection.
Extracts structured features from raw text, URLs, and communication patterns.
"""

import re
import math
from urllib.parse import urlparse, parse_qs
from collections import Counter

import numpy as np


# ---- Email / Text Features ----

PHISHING_KEYWORDS = [
    "urgent", "verify", "account", "suspended", "click here", "confirm",
    "password", "expire", "immediately", "security alert", "unauthorized",
    "update your", "limited time", "act now", "won", "congratulations",
    "claim", "prize", "lottery", "inheritance", "wire transfer", "bitcoin",
    "social security", "irs", "tax refund", "dear customer", "dear user",
]

URGENCY_PATTERNS = [
    r"within \d+ (hour|minute|day)",
    r"expir(e|es|ing|ed)",
    r"immediate(ly)?",
    r"as soon as possible",
    r"asap",
    r"act now",
    r"don'?t delay",
    r"time.?sensitive",
    r"last chance",
    r"final warning",
]

OBFUSCATION_PATTERNS = [
    r"[a-zA-Z]\.[a-zA-Z]\.[a-zA-Z]",
    r"\b[a-zA-Z]{1,2}\d{2,}[a-zA-Z]{1,2}\b",
    r"[^\s]{50,}",
    r"=\?[A-Za-z0-9-]+\?[BQ]\?",
]


def extract_text_features(text: str) -> dict:
    """Extract NLP features from email/message text for phishing detection."""
    text_lower = text.lower()
    words = text_lower.split()
    word_count = len(words) if words else 1

    keyword_hits = sum(1 for kw in PHISHING_KEYWORDS if kw in text_lower)
    urgency_hits = sum(1 for p in URGENCY_PATTERNS if re.search(p, text_lower))
    obfuscation_hits = sum(1 for p in OBFUSCATION_PATTERNS if re.search(p, text))

    urls_in_text = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', text)
    email_addresses = re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', text)

    caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
    special_char_ratio = sum(1 for c in text if not c.isalnum() and not c.isspace()) / max(len(text), 1)
    digit_ratio = sum(1 for c in text if c.isdigit()) / max(len(text), 1)

    sentences = re.split(r'[.!?]+', text)
    avg_sentence_len = np.mean([len(s.split()) for s in sentences if s.strip()]) if sentences else 0

    exclamation_count = text.count("!")
    question_count = text.count("?")
    dollar_count = text.count("$")

    entropy = _text_entropy(text_lower)

    unique_words = len(set(words))
    lexical_diversity = unique_words / word_count if word_count > 0 else 0

    return {
        "keyword_score": keyword_hits / len(PHISHING_KEYWORDS),
        "urgency_score": urgency_hits / len(URGENCY_PATTERNS),
        "obfuscation_score": obfuscation_hits / max(len(OBFUSCATION_PATTERNS), 1),
        "url_count": len(urls_in_text),
        "email_count": len(email_addresses),
        "caps_ratio": caps_ratio,
        "special_char_ratio": special_char_ratio,
        "digit_ratio": digit_ratio,
        "word_count": word_count,
        "avg_sentence_length": avg_sentence_len,
        "exclamation_count": exclamation_count,
        "question_count": question_count,
        "dollar_count": dollar_count,
        "entropy": entropy,
        "lexical_diversity": lexical_diversity,
    }


def _text_entropy(text: str) -> float:
    """Shannon entropy of character distribution -- higher entropy may indicate obfuscation."""
    if not text:
        return 0.0
    freq = Counter(text)
    length = len(text)
    return -sum((c / length) * math.log2(c / length) for c in freq.values() if c > 0)


# ---- URL Features ----

SUSPICIOUS_TLDS = {
    ".tk", ".ml", ".ga", ".cf", ".gq", ".xyz", ".top", ".club",
    ".work", ".date", ".loan", ".racing", ".win", ".bid", ".stream",
}

BRAND_KEYWORDS = [
    "paypal", "apple", "google", "microsoft", "amazon", "netflix",
    "facebook", "instagram", "bank", "secure", "login", "verify",
    "account", "update", "confirm", "signin", "support", "help",
]


def extract_url_features(url: str) -> dict:
    """Extract 25+ features from a URL for phishing detection."""
    try:
        parsed = urlparse(url if "://" in url else f"https://{url}")
    except Exception:
        return _empty_url_features()

    hostname = parsed.hostname or ""
    path = parsed.path or ""
    query = parsed.query or ""
    scheme = parsed.scheme or ""

    url_length = len(url)
    hostname_length = len(hostname)
    path_length = len(path)
    query_length = len(query)

    dot_count = hostname.count(".")
    hyphen_count = hostname.count("-")
    at_count = url.count("@")
    subdomain_count = max(dot_count - 1, 0)

    has_ip = bool(re.match(r'^\d{1,3}(\.\d{1,3}){3}$', hostname))
    has_port = parsed.port is not None and parsed.port not in (80, 443)
    is_https = scheme == "https"

    path_depth = len([p for p in path.split("/") if p])
    query_params = len(parse_qs(query))

    special_in_hostname = sum(1 for c in hostname if not c.isalnum() and c not in ".-")
    digits_in_hostname = sum(1 for c in hostname if c.isdigit())
    digit_ratio_hostname = digits_in_hostname / max(hostname_length, 1)

    tld = "." + hostname.split(".")[-1] if "." in hostname else ""
    suspicious_tld = 1 if tld.lower() in SUSPICIOUS_TLDS else 0

    brand_in_subdomain = sum(
        1 for b in BRAND_KEYWORDS
        if b in hostname.replace(hostname.split(".")[-2] + "." + hostname.split(".")[-1], "").lower()
    ) if dot_count >= 2 else 0

    has_redirect = 1 if "//" in path or "redirect" in url.lower() or "url=" in query.lower() else 0
    has_shortener_pattern = 1 if hostname_length < 8 and path_depth == 1 else 0

    entropy = _text_entropy(url)

    return {
        "url_length": url_length,
        "hostname_length": hostname_length,
        "path_length": path_length,
        "query_length": query_length,
        "dot_count": dot_count,
        "hyphen_count": hyphen_count,
        "at_count": at_count,
        "subdomain_count": subdomain_count,
        "has_ip": int(has_ip),
        "has_port": int(has_port),
        "is_https": int(is_https),
        "path_depth": path_depth,
        "query_params": query_params,
        "special_in_hostname": special_in_hostname,
        "digit_ratio_hostname": digit_ratio_hostname,
        "suspicious_tld": suspicious_tld,
        "brand_in_subdomain": brand_in_subdomain,
        "has_redirect": has_redirect,
        "has_shortener_pattern": has_shortener_pattern,
        "entropy": entropy,
    }


def _empty_url_features() -> dict:
    return {k: 0 for k in [
        "url_length", "hostname_length", "path_length", "query_length",
        "dot_count", "hyphen_count", "at_count", "subdomain_count",
        "has_ip", "has_port", "is_https", "path_depth", "query_params",
        "special_in_hostname", "digit_ratio_hostname", "suspicious_tld",
        "brand_in_subdomain", "has_redirect", "has_shortener_pattern", "entropy",
    ]}


# ---- Behavioral Features ----

def extract_behavioral_features(
    current_message: dict,
    historical_patterns: list[dict] | None = None,
) -> dict:
    """
    Extract behavioral deviation features by comparing current communication
    against historical patterns.
    """
    if not historical_patterns:
        return {
            "time_deviation": 0.0,
            "length_deviation": 0.0,
            "tone_deviation": 0.0,
            "frequency_deviation": 0.0,
            "new_sender": 1.0,
            "pattern_break_score": 0.5,
        }

    hist_lengths = [h.get("length", 0) for h in historical_patterns]
    hist_mean_len = np.mean(hist_lengths) if hist_lengths else 0
    hist_std_len = np.std(hist_lengths) if hist_lengths else 1

    curr_len = current_message.get("length", len(current_message.get("content", "")))
    length_deviation = abs(curr_len - hist_mean_len) / max(hist_std_len, 1)

    known_senders = {h.get("sender", "") for h in historical_patterns}
    new_sender = 0.0 if current_message.get("sender", "") in known_senders else 1.0

    return {
        "time_deviation": 0.0,
        "length_deviation": min(length_deviation, 5.0),
        "tone_deviation": 0.0,
        "frequency_deviation": 0.0,
        "new_sender": new_sender,
        "pattern_break_score": min(length_deviation * 0.3 + new_sender * 0.5, 1.0),
    }


# ---- AI-Generated Text Detection ----

def extract_ai_text_features(text: str) -> dict:
    """
    Statistical features that help distinguish AI-generated text from human text.
    Based on research showing AI text has lower perplexity variance and more
    uniform token distributions.
    """
    words = text.split()
    if len(words) < 5:
        return {"burstiness": 0.5, "perplexity_proxy": 0.5, "repetition_score": 0.0, "uniformity": 0.5}

    word_lengths = [len(w) for w in words]
    sentence_lengths = [len(s.split()) for s in re.split(r'[.!?]+', text) if s.strip()]

    burstiness = float(np.std(sentence_lengths) / max(np.mean(sentence_lengths), 1)) if sentence_lengths else 0
    human_text_typically_has_higher_burstiness = burstiness

    bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words) - 1)]
    bigram_freq = Counter(bigrams)
    repeated_bigrams = sum(1 for v in bigram_freq.values() if v > 1)
    repetition_score = repeated_bigrams / max(len(bigrams), 1)

    word_freq = Counter(words)
    freq_values = sorted(word_freq.values(), reverse=True)
    if len(freq_values) > 1:
        expected_zipf = [freq_values[0] / (i + 1) for i in range(len(freq_values))]
        deviation = np.mean(np.abs(np.array(freq_values) - np.array(expected_zipf))) / max(freq_values[0], 1)
    else:
        deviation = 0

    return {
        "burstiness": human_text_typically_has_higher_burstiness,
        "perplexity_proxy": 1.0 - min(deviation, 1.0),
        "repetition_score": repetition_score,
        "uniformity": 1.0 - min(float(np.std(word_lengths) / max(np.mean(word_lengths), 1)), 1.0),
    }
