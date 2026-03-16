import os

import httpx


def enhance_digest(prompt: str, fallback: str) -> str:
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        return fallback

    payload = {
        'contents': [
            {
                'parts': [
                    {
                        'text': (
                            'Rewrite the following family digest so it sounds warm, concise, and actionable. '
                            'Keep it under 160 words.\n\n'
                            + prompt
                        )
                    }
                ]
            }
        ]
    }
    url = (
        'https://generativelanguage.googleapis.com/v1beta/models/'
        'gemini-2.0-flash:generateContent'
    )
    try:
        response = httpx.post(url, params={'key': api_key}, json=payload, timeout=8.0)
        response.raise_for_status()
        body = response.json()
        return body['candidates'][0]['content']['parts'][0]['text'].strip()
    except Exception:
        return fallback
