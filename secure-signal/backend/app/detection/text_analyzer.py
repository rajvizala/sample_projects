"""
Statistical AI-generated text detector using perplexity and burstiness analysis.
Implements the approach from "DetectGPT" and related research — no API calls needed.
"""
import re
import math
import string
from collections import Counter
from typing import TypedDict


class TextAnalysis(TypedDict):
    ai_probability: float
    perplexity_score: float
    burstiness_score: float
    avg_sentence_length: float
    vocabulary_richness: float
    repetition_score: float
    reasoning: list[str]


def _tokenize(text: str) -> list[str]:
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    return text.split()


def _get_sentences(text: str) -> list[str]:
    sentences = re.split(r"[.!?]+", text)
    return [s.strip() for s in sentences if len(s.strip()) > 5]


def _compute_perplexity_proxy(tokens: list[str]) -> float:
    """
    Proxy for perplexity using unigram distribution entropy.
    AI text tends to have lower entropy (more predictable word distribution).
    """
    if len(tokens) < 10:
        return 50.0

    freq = Counter(tokens)
    total = len(tokens)
    probs = [count / total for count in freq.values()]
    entropy = -sum(p * math.log2(p) for p in probs if p > 0)
    normalized = entropy / math.log2(max(len(freq), 2))
    return round(normalized * 100, 2)


def _compute_burstiness(sentences: list[str]) -> float:
    """
    Burstiness measures variance in sentence length.
    Human text has higher burstiness (varied rhythm), AI text is more uniform.
    """
    if len(sentences) < 3:
        return 50.0

    lengths = [len(s.split()) for s in sentences]
    mean = sum(lengths) / len(lengths)
    variance = sum((l - mean) ** 2 for l in lengths) / len(lengths)
    std_dev = math.sqrt(variance)
    cv = (std_dev / mean) * 100 if mean > 0 else 0
    return round(min(cv, 100), 2)


def _compute_repetition(tokens: list[str]) -> float:
    """Measures n-gram repetition — AI text often repeats phrases."""
    if len(tokens) < 10:
        return 0.0

    bigrams = [f"{tokens[i]}_{tokens[i+1]}" for i in range(len(tokens) - 1)]
    if not bigrams:
        return 0.0
    bigram_freq = Counter(bigrams)
    repeated = sum(1 for count in bigram_freq.values() if count > 1)
    return round((repeated / len(bigrams)) * 100, 2)


def _vocabulary_richness(tokens: list[str]) -> float:
    """Type-token ratio — higher = more diverse vocabulary."""
    if not tokens:
        return 0.0
    unique = len(set(tokens))
    return round((unique / len(tokens)) * 100, 2)


def analyze_text_for_ai(text: str) -> TextAnalysis:
    """
    Analyze text for probability of AI generation using statistical signals.
    Returns a score between 0 (definitely human) and 1 (likely AI-generated).
    """
    tokens = _tokenize(text)
    sentences = _get_sentences(text)

    if len(tokens) < 10:
        return TextAnalysis(
            ai_probability=0.0,
            perplexity_score=50.0,
            burstiness_score=50.0,
            avg_sentence_length=0.0,
            vocabulary_richness=0.0,
            repetition_score=0.0,
            reasoning=["Text too short for reliable analysis"]
        )

    perplexity = _compute_perplexity_proxy(tokens)
    burstiness = _compute_burstiness(sentences)
    repetition = _compute_repetition(tokens)
    vocab_richness = _vocabulary_richness(tokens)
    avg_sentence_len = len(tokens) / max(len(sentences), 1)

    reasoning = []
    ai_signals = 0

    if perplexity < 45:
        ai_signals += 2
        reasoning.append(f"Low vocabulary entropy ({perplexity:.0f}/100) — predictable word distribution typical of LLMs")

    if burstiness < 25:
        ai_signals += 2
        reasoning.append(f"Low sentence length variance ({burstiness:.0f}%) — AI text tends toward uniform rhythm")

    if repetition > 15:
        ai_signals += 1
        reasoning.append(f"High bigram repetition ({repetition:.0f}%) — repeated phrase patterns detected")

    if 15 <= avg_sentence_len <= 22:
        ai_signals += 1
        reasoning.append(f"Sentence length ({avg_sentence_len:.1f} words avg) falls in typical LLM output range")

    if vocab_richness > 75:
        reasoning.append(f"High vocabulary diversity ({vocab_richness:.0f}%) — consistent with human writing")
        ai_signals -= 1

    if not reasoning:
        reasoning.append("No strong AI-generation signals detected — text appears human-authored")

    ai_probability = min(max(ai_signals / 6.0, 0.0), 1.0)

    return TextAnalysis(
        ai_probability=round(ai_probability, 3),
        perplexity_score=perplexity,
        burstiness_score=burstiness,
        avg_sentence_length=round(avg_sentence_len, 1),
        vocabulary_richness=vocab_richness,
        repetition_score=repetition,
        reasoning=reasoning
    )
