"""
ML model definitions and inference for threat detection.
Includes phishing classifier, URL analyzer, anomaly detector, and AI text detector.
"""

import os
import json
from pathlib import Path

import numpy as np
import joblib
from sklearn.ensemble import GradientBoostingClassifier, IsolationForest, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

from app.ml.feature_extraction import (
    extract_text_features,
    extract_url_features,
    extract_behavioral_features,
    extract_ai_text_features,
)

MODELS_DIR = Path(__file__).parent / "trained_models"


class PhishingClassifier:
    """Gradient Boosting classifier for phishing email/message detection."""

    def __init__(self):
        self.model: Pipeline | None = None
        self.feature_names = list(extract_text_features("sample").keys())

    def train(self, X: np.ndarray, y: np.ndarray):
        self.model = Pipeline([
            ("scaler", StandardScaler()),
            ("clf", GradientBoostingClassifier(
                n_estimators=200,
                max_depth=5,
                learning_rate=0.1,
                subsample=0.8,
                random_state=42,
            )),
        ])
        self.model.fit(X, y)

    def predict(self, text: str) -> dict:
        features = extract_text_features(text)
        feature_vector = np.array([list(features.values())]).reshape(1, -1)

        if self.model is None:
            return self._rule_based_predict(features)

        prob = self.model.predict_proba(feature_vector)[0]
        is_phishing = int(prob[1] > 0.5)
        return {
            "is_phishing": bool(is_phishing),
            "confidence": float(max(prob)),
            "phishing_probability": float(prob[1]),
            "features": features,
        }

    def _rule_based_predict(self, features: dict) -> dict:
        """Fallback rule-based detection when no trained model is available."""
        score = 0.0
        score += features["keyword_score"] * 0.35
        score += features["urgency_score"] * 0.25
        score += features["obfuscation_score"] * 0.15
        score += min(features["url_count"] * 0.05, 0.15)
        score += features["caps_ratio"] * 0.05 if features["caps_ratio"] > 0.3 else 0
        score += features["special_char_ratio"] * 0.05 if features["special_char_ratio"] > 0.15 else 0
        score = min(score, 1.0)
        return {
            "is_phishing": score > 0.5,
            "confidence": max(score, 1 - score),
            "phishing_probability": score,
            "features": features,
        }

    def save(self, path: Path | None = None):
        path = path or MODELS_DIR / "phishing_classifier.joblib"
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, path)

    def load(self, path: Path | None = None):
        path = path or MODELS_DIR / "phishing_classifier.joblib"
        if path.exists():
            self.model = joblib.load(path)
            return True
        return False


class URLThreatAnalyzer:
    """Random Forest classifier for phishing URL detection."""

    def __init__(self):
        self.model: Pipeline | None = None
        self.feature_names = list(extract_url_features("https://example.com").keys())

    def train(self, X: np.ndarray, y: np.ndarray):
        self.model = Pipeline([
            ("scaler", StandardScaler()),
            ("clf", RandomForestClassifier(
                n_estimators=300,
                max_depth=10,
                min_samples_split=5,
                random_state=42,
                n_jobs=-1,
            )),
        ])
        self.model.fit(X, y)

    def predict(self, url: str) -> dict:
        features = extract_url_features(url)
        feature_vector = np.array([list(features.values())]).reshape(1, -1)

        if self.model is None:
            return self._rule_based_predict(features)

        prob = self.model.predict_proba(feature_vector)[0]
        return {
            "is_threat": bool(prob[1] > 0.5),
            "confidence": float(max(prob)),
            "threat_probability": float(prob[1]),
            "features": features,
        }

    def _rule_based_predict(self, features: dict) -> dict:
        score = 0.0
        score += 0.2 if features["has_ip"] else 0
        score += 0.15 if features["suspicious_tld"] else 0
        score += 0.15 if features["brand_in_subdomain"] else 0
        score += 0.1 if not features["is_https"] else 0
        score += 0.1 if features["has_redirect"] else 0
        score += min(features["subdomain_count"] * 0.05, 0.15)
        score += 0.1 if features["url_length"] > 75 else 0
        score += 0.05 if features["has_port"] else 0
        score = min(score, 1.0)
        return {
            "is_threat": score > 0.5,
            "confidence": max(score, 1 - score),
            "threat_probability": score,
            "features": features,
        }

    def save(self, path: Path | None = None):
        path = path or MODELS_DIR / "url_analyzer.joblib"
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, path)

    def load(self, path: Path | None = None):
        path = path or MODELS_DIR / "url_analyzer.joblib"
        if path.exists():
            self.model = joblib.load(path)
            return True
        return False


class AnomalyDetector:
    """Isolation Forest for behavioral anomaly detection in communication patterns."""

    def __init__(self):
        self.model: IsolationForest | None = None
        self.scaler: StandardScaler | None = None

    def train(self, X: np.ndarray, contamination: float = 0.1):
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        self.model = IsolationForest(
            n_estimators=200,
            contamination=contamination,
            max_features=0.8,
            random_state=42,
        )
        self.model.fit(X_scaled)

    def predict(self, current_message: dict, historical_patterns: list[dict] | None = None) -> dict:
        features = extract_behavioral_features(current_message, historical_patterns)
        feature_vector = np.array([list(features.values())]).reshape(1, -1)

        if self.model is None or self.scaler is None:
            anomaly_score = features["pattern_break_score"]
            return {
                "is_anomaly": anomaly_score > 0.6,
                "anomaly_score": anomaly_score,
                "features": features,
            }

        X_scaled = self.scaler.transform(feature_vector)
        raw_score = self.model.decision_function(X_scaled)[0]
        normalized_score = 1 - (raw_score + 0.5)
        normalized_score = float(np.clip(normalized_score, 0, 1))

        return {
            "is_anomaly": normalized_score > 0.6,
            "anomaly_score": normalized_score,
            "features": features,
        }

    def save(self, path: Path | None = None):
        path = path or MODELS_DIR / "anomaly_detector.joblib"
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"model": self.model, "scaler": self.scaler}, path)

    def load(self, path: Path | None = None):
        path = path or MODELS_DIR / "anomaly_detector.joblib"
        if path.exists():
            data = joblib.load(path)
            self.model = data["model"]
            self.scaler = data["scaler"]
            return True
        return False


class AITextDetector:
    """Detects AI-generated text using statistical features."""

    def __init__(self):
        self.model: Pipeline | None = None

    def train(self, X: np.ndarray, y: np.ndarray):
        self.model = Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(C=1.0, random_state=42, max_iter=1000)),
        ])
        self.model.fit(X, y)

    def predict(self, text: str) -> dict:
        features = extract_ai_text_features(text)
        feature_vector = np.array([list(features.values())]).reshape(1, -1)

        if self.model is None:
            return self._rule_based_predict(features)

        prob = self.model.predict_proba(feature_vector)[0]
        return {
            "is_ai_generated": bool(prob[1] > 0.5),
            "confidence": float(max(prob)),
            "ai_probability": float(prob[1]),
            "features": features,
        }

    def _rule_based_predict(self, features: dict) -> dict:
        score = 0.0
        if features["burstiness"] < 0.3:
            score += 0.3
        if features["uniformity"] > 0.7:
            score += 0.3
        if features["repetition_score"] > 0.1:
            score += 0.2
        score += (1 - features["perplexity_proxy"]) * 0.2
        score = min(score, 1.0)
        return {
            "is_ai_generated": score > 0.5,
            "confidence": max(score, 1 - score),
            "ai_probability": score,
            "features": features,
        }

    def save(self, path: Path | None = None):
        path = path or MODELS_DIR / "ai_text_detector.joblib"
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, path)

    def load(self, path: Path | None = None):
        path = path or MODELS_DIR / "ai_text_detector.joblib"
        if path.exists():
            self.model = joblib.load(path)
            return True
        return False


class ThreatScorer:
    """
    Composite threat scorer that combines outputs from all detectors
    into a unified threat assessment.
    """

    WEIGHTS = {
        "phishing": 0.35,
        "url_threat": 0.25,
        "anomaly": 0.20,
        "ai_generated": 0.20,
    }

    SEVERITY_THRESHOLDS = {
        "critical": 0.85,
        "high": 0.65,
        "medium": 0.40,
        "low": 0.20,
    }

    ACTIONS = {
        "critical": "Immediately block sender and report. Do not click any links or download attachments. Change passwords for any referenced accounts.",
        "high": "Exercise extreme caution. Verify sender through an independent channel before taking any action. Report if confirmed suspicious.",
        "medium": "Be cautious. Verify the sender identity independently. Do not share personal information or click unfamiliar links.",
        "low": "Low risk detected. Continue with normal caution. Monitor for follow-up suspicious activity.",
    }

    def score(
        self,
        phishing_result: dict | None = None,
        url_result: dict | None = None,
        anomaly_result: dict | None = None,
        ai_text_result: dict | None = None,
    ) -> dict:
        scores = {}
        if phishing_result:
            scores["phishing"] = phishing_result.get("phishing_probability", 0)
        if url_result:
            scores["url_threat"] = url_result.get("threat_probability", 0)
        if anomaly_result:
            scores["anomaly"] = anomaly_result.get("anomaly_score", 0)
        if ai_text_result:
            scores["ai_generated"] = ai_text_result.get("ai_probability", 0)

        if not scores:
            return {"threat_score": 0, "severity": "low", "recommended_action": self.ACTIONS["low"]}

        total_weight = sum(self.WEIGHTS[k] for k in scores)
        composite = sum(scores[k] * self.WEIGHTS[k] for k in scores) / total_weight

        composite = float(np.clip(composite * 100, 0, 100))

        severity = "info"
        for level, threshold in self.SEVERITY_THRESHOLDS.items():
            if composite / 100 >= threshold:
                severity = level
                break

        action = self.ACTIONS.get(severity, self.ACTIONS["low"])

        threat_type = "unknown"
        if scores:
            dominant = max(scores, key=scores.get)
            type_map = {
                "phishing": "phishing",
                "url_threat": "malicious_url",
                "anomaly": "behavioral_anomaly",
                "ai_generated": "ai_impersonation",
            }
            threat_type = type_map.get(dominant, "unknown")

        return {
            "threat_score": round(composite, 1),
            "severity": severity,
            "threat_type": threat_type,
            "recommended_action": action,
            "component_scores": scores,
        }
