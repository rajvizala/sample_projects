"""
Training script for ThreatLens ML models.
Generates synthetic training data based on real-world phishing patterns and
trains all model components.

Usage:
    python -m app.ml.train_models
"""

import numpy as np
from pathlib import Path

from app.ml.feature_extraction import (
    extract_text_features,
    extract_url_features,
    extract_ai_text_features,
)
from app.ml.models import (
    PhishingClassifier,
    URLThreatAnalyzer,
    AnomalyDetector,
    AITextDetector,
)

LEGITIMATE_EMAILS = [
    "Hi team, please find the quarterly report attached. Let me know if you have questions.",
    "Meeting rescheduled to 3pm tomorrow. Same conference room. Thanks!",
    "Great job on the presentation today. The client was really impressed with the demo.",
    "Can you review the pull request I submitted? It fixes the authentication bug we discussed.",
    "Reminder: office will be closed next Monday for the holiday. Enjoy the long weekend!",
    "The new feature deployment went smoothly. All metrics looking good in production.",
    "Let's sync up about the Q3 roadmap. Does Thursday at 2pm work for everyone?",
    "Thanks for sending the invoice. Payment will be processed within 30 days as per our terms.",
    "Welcome to the team! Your onboarding documents are in the shared drive folder.",
    "The API documentation has been updated. Check the wiki for the latest endpoints.",
    "Coffee chat tomorrow? Would love to hear about your experience at the conference.",
    "Budget approval came through for the new server infrastructure. Procurement starts next week.",
    "Happy birthday! The team got you a gift card. Check your desk when you get in.",
    "Sprint retrospective notes are posted in Confluence. Action items assigned.",
    "Your subscription renewal is coming up in 60 days. No action needed right now.",
    "The performance review cycle starts next month. Please update your self-assessment.",
    "Lunch and learn on Friday about the new testing framework. Pizza provided!",
    "Your flight to the conference is booked. Itinerary details in your email.",
    "The CI pipeline is green again after the hotfix. All tests passing.",
    "Project kickoff meeting scheduled for Monday. Agenda attached for review.",
]

PHISHING_EMAILS = [
    "URGENT: Your account has been suspended! Click here immediately to verify your identity and restore access before permanent deletion.",
    "Congratulations! You've won $1,000,000 in the international lottery. Click here to claim your prize immediately!",
    "Your PayPal account has been limited. Verify your information within 24 hours or your account will be permanently closed.",
    "SECURITY ALERT: Unauthorized login detected on your account. Click here NOW to secure your account immediately!",
    "Dear Customer, your bank account will be suspended unless you verify your identity. Click the link below within 2 hours.",
    "Act now! Your social security number has been compromised. Call this number immediately to prevent identity theft.",
    "Your Apple ID has expired. Update your payment information immediately or lose access to all Apple services.",
    "FINAL WARNING: Your email storage is full. Click here to upgrade for free or all emails will be deleted.",
    "You have a pending wire transfer of $50,000. Confirm your account details to receive the funds.",
    "IRS Tax Refund: You are eligible for a $3,500 refund. Submit your information to claim within 48 hours.",
    "Your Netflix subscription payment failed! Update your billing info now to avoid service interruption.",
    "ALERT: Someone is using your identity! Click here to verify yourself and stop the unauthorized activity.",
    "Dear valued customer, confirm your password to continue using your Microsoft account. Expires in 1 hour!",
    "Bitcoin investment opportunity! Guaranteed 500% returns. Limited spots available. Invest now!",
    "Your Amazon order #4829 cannot be delivered. Update your address immediately or it will be returned.",
    "URGENT: Your computer has been infected! Call our support line immediately for free virus removal.",
    "Dear user, your account security is at risk. Download this attachment to run a security scan now.",
    "Inheritance notification: You are the beneficiary of $2.5 million. Reply with your bank details.",
    "Your Google account will be deleted in 24 hours. Click here to verify and prevent deletion!",
    "EXCLUSIVE: Work from home and earn $5000/week! No experience needed. Apply now before spots fill up!",
]

LEGITIMATE_URLS = [
    "https://www.google.com/search?q=weather",
    "https://github.com/microsoft/vscode/issues",
    "https://docs.python.org/3/library/json.html",
    "https://stackoverflow.com/questions/tagged/python",
    "https://www.amazon.com/dp/B09V3KXJPB",
    "https://mail.google.com/mail/u/0/#inbox",
    "https://www.linkedin.com/feed/",
    "https://calendar.google.com/calendar/r",
    "https://www.nytimes.com/2024/01/15/technology/ai.html",
    "https://en.wikipedia.org/wiki/Machine_learning",
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "https://stripe.com/docs/api/charges",
    "https://www.notion.so/workspace/dashboard",
    "https://app.slack.com/client/T024BE7LD",
    "https://zoom.us/j/1234567890",
]

PHISHING_URLS = [
    "http://paypa1-secure.login-verify.tk/account/update",
    "http://192.168.1.100:8080/bankofamerica/login.php",
    "http://secure-apple.com.verify-account.ml/id/login",
    "http://microsoft-365-update.xyz/office/verify?user=target",
    "http://amaz0n-support.club/order/confirm/payment",
    "http://netflix-billing.top/update/payment?ref=user123",
    "http://google-security-alert.ga/account/verify/2fa",
    "https://login-facebook.security-check.cf/auth/verify",
    "http://verify-your-paypal.bid/signin?dispatch=confirm",
    "http://139.59.22.100/chase-bank/online/login.html",
    "http://secure.banklogin.stream/customer/verification",
    "http://instagram-help.win/support/account-recovery",
    "http://www.goog1e.com/accounts/signin/v2/challenge",
    "http://apple-support-verify.date/help/account",
    "http://amazn-prime.loan/membership/renew?act=urgent",
]

HUMAN_TEXTS = [
    "So I was thinking about what happened yesterday and honestly... it's been bugging me. "
    "Like, the whole meeting felt off? Not sure if anyone else noticed but the VP seemed really "
    "distracted. Maybe it's the Q4 numbers. Anyway, wanted to grab coffee and chat about it.",
    "lol that's hilarious. Did you see what Sarah posted? I literally can't even. "
    "also reminder we need to finish the project by friday or prof is gonna kill us haha",
    "Hey! Running about 10 min late. Traffic on 95 is INSANE today. "
    "Can you order me the usual? Thanks!!",
    "I don't know... I've been going back and forth on this decision for weeks now. "
    "Part of me wants to take the job in Seattle but then there's the whole thing with "
    "the apartment lease and moving costs. Ugh, adulting is hard.",
]

AI_GENERATED_TEXTS = [
    "In the ever-evolving landscape of digital security, it is imperative that organizations "
    "adopt a comprehensive approach to threat mitigation. The implementation of robust security "
    "protocols serves as the foundation for protecting sensitive data and maintaining operational "
    "integrity across all organizational levels and departments.",
    "The integration of artificial intelligence into modern business processes represents a "
    "transformative shift in operational efficiency. By leveraging machine learning algorithms "
    "and natural language processing capabilities, organizations can streamline workflows, "
    "enhance decision-making processes, and achieve unprecedented levels of productivity.",
    "Sustainable development goals require a multifaceted approach that encompasses environmental "
    "stewardship, social responsibility, and economic viability. Through the implementation of "
    "comprehensive strategies and the adoption of innovative technologies, communities can "
    "achieve meaningful progress toward a more sustainable future.",
    "The advancement of quantum computing technology presents both significant opportunities "
    "and challenges for the field of cryptography. As quantum processors continue to increase "
    "in capability and reliability, the development of post-quantum cryptographic algorithms "
    "becomes increasingly critical for maintaining the security of digital communications.",
]


def generate_training_data():
    """Generate feature matrices and labels from sample data."""
    print("Generating training data...")

    text_features, text_labels = [], []
    for email in LEGITIMATE_EMAILS:
        text_features.append(list(extract_text_features(email).values()))
        text_labels.append(0)
    for email in PHISHING_EMAILS:
        text_features.append(list(extract_text_features(email).values()))
        text_labels.append(1)

    rng = np.random.RandomState(42)
    for _ in range(200):
        base = text_features[rng.randint(0, len(LEGITIMATE_EMAILS))]
        noise = rng.normal(0, 0.05, len(base))
        text_features.append(list(np.clip(np.array(base) + noise, 0, None)))
        text_labels.append(0)
    for _ in range(200):
        base = text_features[len(LEGITIMATE_EMAILS) + rng.randint(0, len(PHISHING_EMAILS))]
        noise = rng.normal(0, 0.05, len(base))
        text_features.append(list(np.clip(np.array(base) + noise, 0, None)))
        text_labels.append(1)

    url_features, url_labels = [], []
    for url in LEGITIMATE_URLS:
        url_features.append(list(extract_url_features(url).values()))
        url_labels.append(0)
    for url in PHISHING_URLS:
        url_features.append(list(extract_url_features(url).values()))
        url_labels.append(1)

    for _ in range(200):
        base = url_features[rng.randint(0, len(LEGITIMATE_URLS))]
        noise = rng.normal(0, 0.1, len(base))
        url_features.append(list(np.clip(np.array(base) + noise, 0, None)))
        url_labels.append(0)
    for _ in range(200):
        base = url_features[len(LEGITIMATE_URLS) + rng.randint(0, len(PHISHING_URLS))]
        noise = rng.normal(0, 0.1, len(base))
        url_features.append(list(np.clip(np.array(base) + noise, 0, None)))
        url_labels.append(1)

    ai_features, ai_labels = [], []
    for text in HUMAN_TEXTS:
        ai_features.append(list(extract_ai_text_features(text).values()))
        ai_labels.append(0)
    for text in AI_GENERATED_TEXTS:
        ai_features.append(list(extract_ai_text_features(text).values()))
        ai_labels.append(1)

    for _ in range(100):
        base = ai_features[rng.randint(0, len(HUMAN_TEXTS))]
        noise = rng.normal(0, 0.05, len(base))
        ai_features.append(list(np.clip(np.array(base) + noise, 0, None)))
        ai_labels.append(0)
    for _ in range(100):
        base = ai_features[len(HUMAN_TEXTS) + rng.randint(0, len(AI_GENERATED_TEXTS))]
        noise = rng.normal(0, 0.05, len(base))
        ai_features.append(list(np.clip(np.array(base) + noise, 0, None)))
        ai_labels.append(1)

    normal_behavior = rng.normal(loc=[0.0, 0.0, 0.0, 0.0, 0.0, 0.2], scale=0.15, size=(300, 6))
    normal_behavior = np.clip(normal_behavior, 0, 1)

    return {
        "text": (np.array(text_features), np.array(text_labels)),
        "url": (np.array(url_features), np.array(url_labels)),
        "ai": (np.array(ai_features), np.array(ai_labels)),
        "behavior": normal_behavior,
    }


def train_all_models():
    """Train and save all ML models."""
    data = generate_training_data()

    print("Training phishing classifier...")
    phishing_clf = PhishingClassifier()
    X_text, y_text = data["text"]
    phishing_clf.train(X_text, y_text)
    phishing_clf.save()
    print(f"  Trained on {len(y_text)} samples ({sum(y_text)} phishing, {len(y_text) - sum(y_text)} legitimate)")

    print("Training URL threat analyzer...")
    url_analyzer = URLThreatAnalyzer()
    X_url, y_url = data["url"]
    url_analyzer.train(X_url, y_url)
    url_analyzer.save()
    print(f"  Trained on {len(y_url)} samples ({sum(y_url)} malicious, {len(y_url) - sum(y_url)} safe)")

    print("Training anomaly detector...")
    anomaly_det = AnomalyDetector()
    anomaly_det.train(data["behavior"], contamination=0.1)
    anomaly_det.save()
    print(f"  Trained on {len(data['behavior'])} behavioral samples")

    print("Training AI text detector...")
    ai_detector = AITextDetector()
    X_ai, y_ai = data["ai"]
    ai_detector.train(X_ai, y_ai)
    ai_detector.save()
    print(f"  Trained on {len(y_ai)} samples ({sum(y_ai)} AI-generated, {len(y_ai) - sum(y_ai)} human)")

    print(f"\nAll models saved to {MODELS_DIR}/")
    print("Training complete.")


if __name__ == "__main__":
    train_all_models()
