"""
Background threat simulation engine.
In production, this would connect to real data sources (email APIs, account webhooks, etc.)
For demo purposes, it generates realistic threat scenarios at intervals.
"""
import asyncio
import uuid
import random
from datetime import datetime, timezone
from typing import Callable

SIMULATED_THREATS = [
    {
        "threat_type": "phishing_attempt",
        "severity": "HIGH",
        "risk_score": 0.82,
        "title": "Phishing email detected in inbox",
        "description": "An email impersonating Chase Bank requested account verification via a suspicious link. The sender domain does not match official Chase domains.",
        "source": "Email Monitor",
        "indicators": {
            "sender_domain_mismatch": True,
            "urgency_language": True,
            "credential_request": True,
            "suspicious_url": "chase-verify-account.tk/login"
        },
        "action_required": "Delete the email immediately. Do not click any links. Report as phishing in your email client."
    },
    {
        "threat_type": "ai_generated_scam",
        "severity": "HIGH",
        "risk_score": 0.76,
        "title": "AI-generated voice scam call detected",
        "description": "An inbound call exhibited hallmarks of AI voice synthesis. The caller claimed to be IRS enforcement and demanded immediate payment via gift cards.",
        "source": "Call Monitor",
        "indicators": {
            "ai_voice_probability": 0.89,
            "government_impersonation": True,
            "unusual_payment_request": True,
            "call_duration": "3m 12s"
        },
        "action_required": "This is a known IRS impersonation scam. Do not call back. Block the number and report to FTC at reportfraud.ftc.gov."
    },
    {
        "threat_type": "account_takeover_attempt",
        "severity": "CRITICAL",
        "risk_score": 0.91,
        "title": "Unusual login attempt from new location",
        "description": "Login attempt to your Google account from Kharkov, Ukraine using an unrecognized device. 3 failed attempts before MFA blocked access.",
        "source": "Account Monitor",
        "indicators": {
            "new_country": "UA",
            "new_device": True,
            "failed_attempts": 3,
            "mfa_blocked": True,
            "time": "2:14 AM local time"
        },
        "action_required": "Change your Google password immediately. Review connected apps and revoke any unfamiliar access tokens."
    },
    {
        "threat_type": "credential_exposure",
        "severity": "MEDIUM",
        "risk_score": 0.58,
        "title": "Email found in data breach database",
        "description": "Your email address was found in the 'TechForums2024' data breach (released March 2024). Hashed passwords and usernames were exposed.",
        "source": "Breach Monitor",
        "indicators": {
            "breach_name": "TechForums2024",
            "data_exposed": ["email", "username", "hashed_password"],
            "breach_date": "March 2024",
            "records_in_breach": "2.1M"
        },
        "action_required": "Update your password for any site where you used the same password. Enable MFA if not already active."
    },
    {
        "threat_type": "sim_swap_indicator",
        "severity": "HIGH",
        "risk_score": 0.79,
        "title": "Potential SIM swap activity detected",
        "description": "Your mobile carrier account logged a device profile change. SIM swap fraud involves transferring your number to an attacker's device.",
        "source": "Identity Monitor",
        "indicators": {
            "carrier_change_detected": True,
            "device_profile_change": True,
            "time": "last 2 hours",
            "mfa_codes_redirected": "possible"
        },
        "action_required": "Call your carrier immediately to verify. Place a SIM lock / port freeze. Temporarily disable SMS-based MFA."
    },
    {
        "threat_type": "social_engineering",
        "severity": "MEDIUM",
        "risk_score": 0.51,
        "title": "Suspicious LinkedIn message detected",
        "description": "A recruitment message contains hallmarks of a 'too good to be true' job offer. AI text analysis indicates 87% probability of AI-generated content.",
        "source": "Communication Monitor",
        "indicators": {
            "ai_generated": True,
            "ai_probability": 0.87,
            "overpromising": True,
            "external_link": True,
            "platform": "LinkedIn"
        },
        "action_required": "Do not click external links in the message. Verify the recruiter's profile independently before responding."
    }
]

_callbacks: list[Callable] = []
_running = False


def register_callback(callback: Callable):
    _callbacks.append(callback)


def unregister_callback(callback: Callable):
    if callback in _callbacks:
        _callbacks.remove(callback)


async def notify_all(event: dict):
    for callback in list(_callbacks):
        try:
            await callback(event)
        except Exception:
            pass


async def run_monitor(interval: int = 8):
    global _running
    _running = True
    seen_indices = set()

    while _running:
        await asyncio.sleep(interval)

        available = [i for i in range(len(SIMULATED_THREATS)) if i not in seen_indices]
        if not available:
            seen_indices.clear()
            available = list(range(len(SIMULATED_THREATS)))

        if random.random() < 0.7:
            idx = random.choice(available)
            seen_indices.add(idx)
            threat_template = SIMULATED_THREATS[idx]

            event = {
                "id": str(uuid.uuid4()),
                **threat_template,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await notify_all(event)


def stop_monitor():
    global _running
    _running = False
