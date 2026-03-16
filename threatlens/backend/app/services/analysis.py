"""
Core analysis service that orchestrates ML models for threat detection.
"""

import time
import hashlib
import re
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.ml.models import (
    PhishingClassifier,
    URLThreatAnalyzer,
    AnomalyDetector,
    AITextDetector,
    ThreatScorer,
)
from app.models.threat import Threat, AnalysisLog
from app.schemas.threat import (
    AnalysisResponse,
    ThreatIndicator,
    EmailAnalysisRequest,
    URLAnalysisRequest,
    MessageAnalysisRequest,
)


class AnalysisService:
    def __init__(self):
        self.phishing_clf = PhishingClassifier()
        self.url_analyzer = URLThreatAnalyzer()
        self.anomaly_detector = AnomalyDetector()
        self.ai_detector = AITextDetector()
        self.threat_scorer = ThreatScorer()

        self.phishing_clf.load()
        self.url_analyzer.load()
        self.anomaly_detector.load()
        self.ai_detector.load()

    def analyze_email(self, request: EmailAnalysisRequest, db: Session) -> AnalysisResponse:
        start = time.time()
        full_text = f"{request.subject} {request.body}"

        phishing_result = self.phishing_clf.predict(full_text)
        ai_result = self.ai_detector.predict(full_text)

        url_result = None
        urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', full_text)
        if urls:
            url_scores = [self.url_analyzer.predict(u) for u in urls]
            worst = max(url_scores, key=lambda x: x["threat_probability"])
            url_result = worst

        anomaly_result = self.anomaly_detector.predict(
            {"content": full_text, "sender": request.sender}
        )

        scored = self.threat_scorer.score(
            phishing_result=phishing_result,
            url_result=url_result,
            anomaly_result=anomaly_result,
            ai_text_result=ai_result,
        )

        indicators = self._build_indicators(phishing_result, url_result, anomaly_result, ai_result)
        processing_time = (time.time() - start) * 1000

        threat_id = None
        if scored["threat_score"] > 20:
            threat = Threat(
                threat_type=scored["threat_type"],
                severity=scored["severity"],
                threat_score=scored["threat_score"],
                source_type="email",
                source_content=f"From: {request.sender}\nSubject: {request.subject}\n\n{request.body[:500]}",
                analysis_summary=self._generate_summary(scored, indicators),
                recommended_action=scored["recommended_action"],
                phishing_score=phishing_result.get("phishing_probability", 0),
                anomaly_score=anomaly_result.get("anomaly_score", 0),
                ai_generated_score=ai_result.get("ai_probability", 0),
                url_threat_score=url_result.get("threat_probability", 0) if url_result else 0,
                metadata_json={"sender": request.sender, "urls_found": len(urls)},
            )
            db.add(threat)
            db.commit()
            db.refresh(threat)
            threat_id = threat.id

        self._log_analysis(db, "email", full_text, scored["threat_score"] > 20, processing_time)

        return AnalysisResponse(
            threat_detected=scored["threat_score"] > 20,
            threat_score=scored["threat_score"],
            severity=scored["severity"],
            threat_type=scored["threat_type"],
            indicators=indicators,
            analysis_summary=self._generate_summary(scored, indicators),
            recommended_action=scored["recommended_action"],
            threat_id=threat_id,
            processing_time_ms=round(processing_time, 2),
        )

    def analyze_url(self, request: URLAnalysisRequest, db: Session) -> AnalysisResponse:
        start = time.time()

        url_result = self.url_analyzer.predict(request.url)

        phishing_result = None
        ai_result = None
        if request.context:
            phishing_result = self.phishing_clf.predict(request.context)
            ai_result = self.ai_detector.predict(request.context)

        scored = self.threat_scorer.score(
            phishing_result=phishing_result,
            url_result=url_result,
            ai_text_result=ai_result,
        )

        indicators = self._build_indicators(phishing_result, url_result, None, ai_result)
        processing_time = (time.time() - start) * 1000

        threat_id = None
        if scored["threat_score"] > 20:
            threat = Threat(
                threat_type=scored["threat_type"],
                severity=scored["severity"],
                threat_score=scored["threat_score"],
                source_type="url",
                source_content=request.url,
                analysis_summary=self._generate_summary(scored, indicators),
                recommended_action=scored["recommended_action"],
                phishing_score=phishing_result.get("phishing_probability", 0) if phishing_result else 0,
                url_threat_score=url_result.get("threat_probability", 0),
                metadata_json={"url": request.url, "context": request.context},
            )
            db.add(threat)
            db.commit()
            db.refresh(threat)
            threat_id = threat.id

        self._log_analysis(db, "url", request.url, scored["threat_score"] > 20, processing_time)

        return AnalysisResponse(
            threat_detected=scored["threat_score"] > 20,
            threat_score=scored["threat_score"],
            severity=scored["severity"],
            threat_type=scored["threat_type"],
            indicators=indicators,
            analysis_summary=self._generate_summary(scored, indicators),
            recommended_action=scored["recommended_action"],
            threat_id=threat_id,
            processing_time_ms=round(processing_time, 2),
        )

    def analyze_message(self, request: MessageAnalysisRequest, db: Session) -> AnalysisResponse:
        start = time.time()

        phishing_result = self.phishing_clf.predict(request.content)
        ai_result = self.ai_detector.predict(request.content)

        urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', request.content)
        url_result = None
        if urls:
            url_scores = [self.url_analyzer.predict(u) for u in urls]
            url_result = max(url_scores, key=lambda x: x["threat_probability"])

        anomaly_result = self.anomaly_detector.predict(
            {"content": request.content, "sender": request.sender_id or "unknown"}
        )

        scored = self.threat_scorer.score(
            phishing_result=phishing_result,
            url_result=url_result,
            anomaly_result=anomaly_result,
            ai_text_result=ai_result,
        )

        indicators = self._build_indicators(phishing_result, url_result, anomaly_result, ai_result)
        processing_time = (time.time() - start) * 1000

        threat_id = None
        if scored["threat_score"] > 20:
            threat = Threat(
                threat_type=scored["threat_type"],
                severity=scored["severity"],
                threat_score=scored["threat_score"],
                source_type="message",
                source_content=request.content[:500],
                analysis_summary=self._generate_summary(scored, indicators),
                recommended_action=scored["recommended_action"],
                phishing_score=phishing_result.get("phishing_probability", 0),
                anomaly_score=anomaly_result.get("anomaly_score", 0),
                ai_generated_score=ai_result.get("ai_probability", 0),
                url_threat_score=url_result.get("threat_probability", 0) if url_result else 0,
                metadata_json={"channel": request.channel, "sender_id": request.sender_id},
            )
            db.add(threat)
            db.commit()
            db.refresh(threat)
            threat_id = threat.id

        self._log_analysis(db, "message", request.content, scored["threat_score"] > 20, processing_time)

        return AnalysisResponse(
            threat_detected=scored["threat_score"] > 20,
            threat_score=scored["threat_score"],
            severity=scored["severity"],
            threat_type=scored["threat_type"],
            indicators=indicators,
            analysis_summary=self._generate_summary(scored, indicators),
            recommended_action=scored["recommended_action"],
            threat_id=threat_id,
            processing_time_ms=round(processing_time, 2),
        )

    def _build_indicators(
        self,
        phishing: dict | None,
        url: dict | None,
        anomaly: dict | None,
        ai_text: dict | None,
    ) -> list[ThreatIndicator]:
        indicators = []
        if phishing:
            indicators.append(ThreatIndicator(
                name="Phishing Content",
                score=round(phishing.get("phishing_probability", 0) * 100, 1),
                details=self._phishing_details(phishing),
            ))
        if url:
            indicators.append(ThreatIndicator(
                name="Malicious URL",
                score=round(url.get("threat_probability", 0) * 100, 1),
                details=self._url_details(url),
            ))
        if anomaly:
            indicators.append(ThreatIndicator(
                name="Behavioral Anomaly",
                score=round(anomaly.get("anomaly_score", 0) * 100, 1),
                details=self._anomaly_details(anomaly),
            ))
        if ai_text:
            indicators.append(ThreatIndicator(
                name="AI-Generated Content",
                score=round(ai_text.get("ai_probability", 0) * 100, 1),
                details=self._ai_details(ai_text),
            ))
        return indicators

    def _phishing_details(self, result: dict) -> str:
        features = result.get("features", {})
        parts = []
        if features.get("keyword_score", 0) > 0.1:
            parts.append("suspicious keywords detected")
        if features.get("urgency_score", 0) > 0.1:
            parts.append("urgency language present")
        if features.get("url_count", 0) > 0:
            parts.append(f"{features['url_count']} embedded URLs")
        return "; ".join(parts) if parts else "No significant phishing indicators"

    def _url_details(self, result: dict) -> str:
        features = result.get("features", {})
        parts = []
        if features.get("has_ip"):
            parts.append("IP address used instead of domain")
        if features.get("suspicious_tld"):
            parts.append("suspicious top-level domain")
        if features.get("brand_in_subdomain"):
            parts.append("brand name in subdomain (impersonation)")
        if not features.get("is_https"):
            parts.append("no HTTPS encryption")
        return "; ".join(parts) if parts else "No significant URL threats"

    def _anomaly_details(self, result: dict) -> str:
        features = result.get("features", {})
        parts = []
        if features.get("new_sender", 0) > 0.5:
            parts.append("unknown sender")
        if features.get("length_deviation", 0) > 2:
            parts.append("unusual message length")
        if features.get("pattern_break_score", 0) > 0.5:
            parts.append("communication pattern deviation")
        return "; ".join(parts) if parts else "Normal communication patterns"

    def _ai_details(self, result: dict) -> str:
        features = result.get("features", {})
        parts = []
        if features.get("burstiness", 1) < 0.3:
            parts.append("low sentence variance (typical of AI)")
        if features.get("uniformity", 0) > 0.7:
            parts.append("high word-length uniformity")
        if features.get("repetition_score", 0) > 0.1:
            parts.append("repetitive phrasing detected")
        return "; ".join(parts) if parts else "Text appears human-written"

    def _generate_summary(self, scored: dict, indicators: list[ThreatIndicator]) -> str:
        high_indicators = [i for i in indicators if i.score > 50]
        if not high_indicators:
            return f"Analysis complete. Threat score: {scored['threat_score']}/100. No significant threats detected."

        names = [i.name for i in high_indicators]
        return (
            f"Threat detected with score {scored['threat_score']}/100 ({scored['severity']} severity). "
            f"Primary concerns: {', '.join(names)}. {scored['recommended_action']}"
        )

    def _log_analysis(self, db: Session, input_type: str, content: str, threat: bool, time_ms: float):
        log = AnalysisLog(
            input_type=input_type,
            input_hash=hashlib.sha256(content.encode()).hexdigest()[:16],
            threat_detected=int(threat),
            processing_time_ms=time_ms,
        )
        db.add(log)
        db.commit()


_service: AnalysisService | None = None


def get_analysis_service() -> AnalysisService:
    global _service
    if _service is None:
        _service = AnalysisService()
    return _service
