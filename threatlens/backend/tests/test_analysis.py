"""Tests for ThreatLens analysis pipeline."""

import pytest
from app.ml.feature_extraction import (
    extract_text_features,
    extract_url_features,
    extract_ai_text_features,
    extract_behavioral_features,
)
from app.ml.models import (
    PhishingClassifier,
    URLThreatAnalyzer,
    AnomalyDetector,
    AITextDetector,
    ThreatScorer,
)


class TestTextFeatureExtraction:
    def test_legitimate_email(self):
        features = extract_text_features("Hi team, the quarterly report is ready for review.")
        assert features["keyword_score"] < 0.1
        assert features["urgency_score"] == 0

    def test_phishing_email(self):
        features = extract_text_features(
            "URGENT: Your account has been suspended! Verify immediately "
            "or your account will expire. Click here to confirm your password."
        )
        assert features["keyword_score"] > 0.1
        assert features["urgency_score"] > 0

    def test_feature_keys(self):
        features = extract_text_features("test input")
        expected_keys = {
            "keyword_score", "urgency_score", "obfuscation_score",
            "url_count", "email_count", "caps_ratio", "special_char_ratio",
            "digit_ratio", "word_count", "avg_sentence_length",
            "exclamation_count", "question_count", "dollar_count",
            "entropy", "lexical_diversity",
        }
        assert set(features.keys()) == expected_keys


class TestURLFeatureExtraction:
    def test_legitimate_url(self):
        features = extract_url_features("https://www.google.com/search?q=test")
        assert features["is_https"] == 1
        assert features["suspicious_tld"] == 0
        assert features["has_ip"] == 0

    def test_phishing_url(self):
        features = extract_url_features("http://paypa1-secure.login-verify.tk/account")
        assert features["suspicious_tld"] == 1
        assert features["is_https"] == 0

    def test_ip_url(self):
        features = extract_url_features("http://192.168.1.100:8080/login")
        assert features["has_ip"] == 1
        assert features["has_port"] == 1


class TestAITextDetection:
    def test_human_text(self):
        features = extract_ai_text_features(
            "lol that's hilarious. Did you see what Sarah posted? I literally can't "
            "even. also reminder we need to finish the project by friday or prof is gonna kill us haha"
        )
        assert features["burstiness"] >= 0

    def test_ai_text(self):
        features = extract_ai_text_features(
            "The integration of artificial intelligence into modern business processes represents "
            "a transformative shift in operational efficiency. By leveraging machine learning "
            "algorithms and natural language processing capabilities, organizations can streamline "
            "workflows and enhance decision-making processes."
        )
        assert "uniformity" in features


class TestBehavioralFeatures:
    def test_new_sender(self):
        features = extract_behavioral_features(
            {"content": "test", "sender": "unknown@evil.com"},
            [{"sender": "friend@company.com", "length": 50}],
        )
        assert features["new_sender"] == 1.0

    def test_known_sender(self):
        features = extract_behavioral_features(
            {"content": "test", "sender": "friend@company.com"},
            [{"sender": "friend@company.com", "length": 50}],
        )
        assert features["new_sender"] == 0.0


class TestPhishingClassifier:
    def test_rule_based_phishing(self):
        clf = PhishingClassifier()
        result = clf.predict(
            "URGENT: Your account has been suspended! Click here to verify "
            "your password immediately or your account will expire."
        )
        assert result["phishing_probability"] > 0.1

    def test_rule_based_legitimate(self):
        clf = PhishingClassifier()
        result = clf.predict("Hi, the meeting is at 3pm tomorrow. See you there.")
        assert result["phishing_probability"] < 0.3


class TestURLAnalyzer:
    def test_rule_based_safe(self):
        analyzer = URLThreatAnalyzer()
        result = analyzer.predict("https://www.google.com")
        assert result["threat_probability"] < 0.5

    def test_rule_based_threat(self):
        analyzer = URLThreatAnalyzer()
        result = analyzer.predict("http://192.168.1.100:8080/paypal-login.php")
        assert result["threat_probability"] > 0.2


class TestThreatScorer:
    def test_high_threat(self):
        scorer = ThreatScorer()
        result = scorer.score(
            phishing_result={"phishing_probability": 0.9},
            url_result={"threat_probability": 0.8},
            anomaly_result={"anomaly_score": 0.7},
            ai_text_result={"ai_probability": 0.6},
        )
        assert result["threat_score"] > 60
        assert result["severity"] in ("high", "critical")

    def test_low_threat(self):
        scorer = ThreatScorer()
        result = scorer.score(
            phishing_result={"phishing_probability": 0.1},
            url_result={"threat_probability": 0.05},
        )
        assert result["threat_score"] < 20

    def test_empty_input(self):
        scorer = ThreatScorer()
        result = scorer.score()
        assert result["threat_score"] == 0
        assert result["severity"] == "low"
