import re
import json
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv(".env")

client_groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
AI_DETECTION_MODEL = "llama-3.3-70b-versatile"

# ── CHECK 1: Vocabulary & phrase patterns (rule-based) ───────────────────────
# Documented AI writing patterns — no LLM, no opinion, just observable facts.
# TODO: production — expand pattern list from labeled dataset analysis

VERBOSE_FILLERS = [
    r"\bit is worth noting\b",
    r"\bit is important to (consider|note|recognize|acknowledge)\b",
    r"\bin the realm of\b",
    r"\bdelve into\b",
    r"\bfacilitate\b",
    r"\butilize\b",
    r"\bit is crucial to\b",
    r"\bone might argue\b",
    r"\bit could be said\b",
    r"\bthis paper aims to\b",
    r"\bthis study seeks to\b",
    r"\bin order to\b",
    r"\bdue to the fact that\b",
]

AI_TRANSITIONS = [
    r"\bfurthermore\b",
    r"\bmoreover\b",
    r"\bnevertheless\b",
    r"\bin conclusion\b",
    r"\bto summarize\b",
    r"\bin summary\b",
    r"\bladditionally\b",
    r"\bconsequently\b",
]

PASSIVE_VOICE = [
    r"\bit was found that\b",
    r"\bit was observed that\b",
    r"\bit was noted that\b",
    r"\bit can be seen that\b",
    r"\bit should be noted\b",
    r"\bit is suggested that\b",
]

EM_DASH_PATTERN = r"—"


def check_patterns(text: str) -> dict:
    """
    Check 1 — rule-based vocabulary and phrase pattern scan.
    Flags specific documented AI writing patterns.
    Zero API cost. Fully explainable.
    """
    print("  [detection] check 1: vocabulary pattern scan...")
    text_lower = text.lower()
    lines = text.split("\n")

    matched = []

    # Verbose fillers
    for pattern in VERBOSE_FILLERS:
        for i, line in enumerate(lines):
            if re.search(pattern, line.lower()):
                phrase = re.search(pattern, line.lower()).group()
                matched.append({
                    "type": "verbose_filler",
                    "phrase": phrase,
                    "line": line.strip()[:80],
                    "line_num": i + 1
                })

    # AI transitions
    for pattern in AI_TRANSITIONS:
        for i, line in enumerate(lines):
            if re.search(pattern, line.lower()):
                phrase = re.search(pattern, line.lower()).group()
                matched.append({
                    "type": "ai_transition",
                    "phrase": phrase,
                    "line": line.strip()[:80],
                    "line_num": i + 1
                })

    # Passive voice tells
    for pattern in PASSIVE_VOICE:
        for i, line in enumerate(lines):
            if re.search(pattern, line.lower()):
                phrase = re.search(pattern, line.lower()).group()
                matched.append({
                    "type": "passive_voice_tell",
                    "phrase": phrase,
                    "line": line.strip()[:80],
                    "line_num": i + 1
                })

    # Em-dash overuse (more than 2 in the section)
    em_dash_count = text.count("—")
    if em_dash_count > 2:
        matched.append({
            "type": "em_dash_overuse",
            "phrase": f"— used {em_dash_count} times",
            "line": "multiple lines",
            "line_num": 0
        })

    count = len(matched)
    unique_phrases = list({m["phrase"] for m in matched})

    if count >= 5:
        verdict = "likely_ai"
        confidence = min(0.92, 0.60 + count * 0.04)
    elif count >= 2:
        verdict = "possibly_ai"
        confidence = 0.40 + count * 0.06
    else:
        verdict = "likely_human"
        confidence = max(0.10, 0.30 - count * 0.10)

    print(f"  [detection] pattern matches: {count} — verdict: {verdict}")

    return {
        "check": "pattern_scan",
        "check_label": "Vocabulary patterns",
        "check_description": "Flags documented AI writing patterns: verbose fillers, overused transitions, passive voice tells, and em-dash overuse. Based on observable text, not opinion.",
        "verdict": verdict,
        "confidence": round(confidence, 2),
        "match_count": count,
        "matched": matched[:6],
        "unique_phrases": unique_phrases[:5],
        "flagged_sentences": [m["line"] for m in matched[:4] if m["line"] != "multiple lines"],
        "reason": f"Found {count} AI-associated patterns: {', '.join(unique_phrases[:3])}" if matched else "No significant AI patterns detected."
    }


# ── CHECK 2: Sentence uniformity (Llama 70B) ─────────────────────────────────
# Checks for uniform sentence length, lack of personal voice, generic openers.
# Shows specific sentences that triggered the verdict.
# TODO: production — calibrate confidence against labeled academic writing dataset

SENTENCE_UNIFORMITY_PROMPT = """You are a writing analyst checking for AI-generated text patterns.

Analyze this text section for sentence uniformity and voice.

Check specifically for:
1. Uniform sentence length — do most sentences run 18-25 words with little variation?
2. Missing personal voice — does the writing avoid first-person positions like "we chose X because Y" or "we were surprised to find"?
3. Generic paragraph openers — does each paragraph start with an obvious topic sentence stating the main point immediately?
4. Missing qualifications — does the writing avoid phrases like "in our experience", "unexpectedly", "contrary to our initial hypothesis"?

SECTION HEADING: {heading}
SECTION TEXT:
{content}

Respond with a JSON object with exactly these fields:
- verdict: one of "likely_ai", "possibly_ai", or "likely_human"
- confidence: float 0.0 to 1.0
- flagged_sentences: list of up to 3 exact sentences from the text that show uniform structure or missing voice
- reason: one specific sentence explaining what triggered the verdict (name the exact pattern)

Respond with ONLY the JSON object, no other text."""


def check_sentence_uniformity(heading: str, content: str) -> dict:
    """
    Check 2 — LLM analysis of sentence structure uniformity and personal voice.
    Shows specific flagged sentences so verdict is explainable.
    """
    print("  [detection] check 2: sentence uniformity (Llama 70B)...")

    prompt = SENTENCE_UNIFORMITY_PROMPT.format(
        heading=heading,
        content=content[:2000]
    )

    try:
        response = client_groq.chat.completions.create(
            model=AI_DETECTION_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.1
        )
        raw = response.choices[0].message.content.strip()

        if raw.startswith("```"):
            raw = re.sub(r'^```[a-z]*\n?', '', raw)
            raw = re.sub(r'\n?```$', '', raw)
            raw = raw.strip()

        result = json.loads(raw)
        result["check"] = "sentence_uniformity"
        result["check_label"] = "Sentence uniformity"
        result["check_description"] = "Checks for uniform sentence length, missing personal voice, and generic paragraph openers — specific structural tells of AI-generated academic text."
        print(f"  [detection] sentence uniformity: {result['verdict']} (conf={result['confidence']:.2f})")
        return result

    except Exception as e:
        print(f"  [detection] check 2 error: {e}")
        return {
            "check": "sentence_uniformity",
            "check_label": "Sentence uniformity",
            "check_description": "Checks for uniform sentence length and missing personal voice.",
            "verdict": "unknown",
            "confidence": 0.0,
            "flagged_sentences": [],
            "reason": f"Check unavailable: {str(e)[:60]}"
        }


# ── CHECK 3: Structural tells (Llama 70B) ─────────────────────────────────────
# Checks for observable structural patterns — not "original thought" judgment.
# Conclusion restates intro, abstract over-promises, mechanical transitions.
# TODO: production — test against confirmed AI vs human papers, calibrate thresholds

STRUCTURAL_TELLS_PROMPT = """You are a writing analyst checking for AI-generated text patterns.

Analyze this text section for structural tells of AI writing.

Check specifically for:
1. Conclusion restates introduction — does the conclusion just echo the opening without adding new insight?
2. Abstract over-promises — does the abstract claim broader impact than the content delivers?
3. Mechanical transitions — phrases like "The next section discusses", "This section presents", "As mentioned above"
4. Equal hedging on all claims — does the writing hedge every statement equally rather than distinguishing strong findings from uncertain ones?

SECTION HEADING: {heading}
SECTION TEXT:
{content}

Respond with a JSON object with exactly these fields:
- verdict: one of "likely_ai", "possibly_ai", or "likely_human"
- confidence: float 0.0 to 1.0
- flagged_sentences: list of up to 3 exact sentences from the text that show structural tells
- reason: one specific sentence explaining what triggered the verdict (name the exact structural pattern)

Respond with ONLY the JSON object, no other text."""


def check_structural_tells(heading: str, content: str) -> dict:
    """
    Check 3 — LLM analysis of structural patterns.
    Replaces 'reasoning depth' with observable structural tells.
    Explainable: shows exact sentences, names exact patterns.
    """
    print("  [detection] check 3: structural tells (Llama 70B)...")

    prompt = STRUCTURAL_TELLS_PROMPT.format(
        heading=heading,
        content=content[:2000]
    )

    try:
        response = client_groq.chat.completions.create(
            model=AI_DETECTION_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.1
        )
        raw = response.choices[0].message.content.strip()

        if raw.startswith("```"):
            raw = re.sub(r'^```[a-z]*\n?', '', raw)
            raw = re.sub(r'\n?```$', '', raw)
            raw = raw.strip()

        result = json.loads(raw)
        result["check"] = "structural_tells"
        result["check_label"] = "Structural tells"
        result["check_description"] = "Checks for mechanical transitions, conclusion restating introduction, and equal hedging on all claims — observable structural patterns common in AI-generated text."
        print(f"  [detection] structural tells: {result['verdict']} (conf={result['confidence']:.2f})")
        return result

    except Exception as e:
        print(f"  [detection] check 3 error: {e}")
        return {
            "check": "structural_tells",
            "check_label": "Structural tells",
            "check_description": "Checks for mechanical transitions and structural patterns.",
            "verdict": "unknown",
            "confidence": 0.0,
            "flagged_sentences": [],
            "reason": f"Check unavailable: {str(e)[:60]}"
        }


# ── Aggregator ────────────────────────────────────────────────────────────────

def run_ai_detection(sections: list) -> list:
    """
    Run all 3 checks on each section.
    Returns list of per-section detection results.
    """
    print("\n[detection] running AI detection on all sections...")
    all_results = []

    for i, section in enumerate(sections):
        print(f"\n  [detection] section {i+1}: '{section['heading']}'")
        heading = section["heading"]
        content = section["content"]

        check1 = check_patterns(content)
        check2 = check_sentence_uniformity(heading, content)
        check3 = check_structural_tells(heading, content)

        verdicts = [check1["verdict"], check2["verdict"], check3["verdict"]]
        likely_ai = verdicts.count("likely_ai")
        possibly_ai = verdicts.count("possibly_ai")

        if likely_ai >= 2:
            overall = "likely_ai"
        elif likely_ai >= 1 or possibly_ai >= 2:
            overall = "possibly_ai"
        else:
            overall = "likely_human"

        valid_confs = [
            c["confidence"] for c in [check1, check2, check3]
            if c["verdict"] != "unknown" and c["confidence"] > 0
        ]
        avg_conf = round(sum(valid_confs) / len(valid_confs), 2) if valid_confs else 0.0

        print(f"  [detection] overall: {overall} (avg_conf={avg_conf:.2f})")

        all_results.append({
            "section_index": i + 1,
            "heading": heading,
            "overall_verdict": overall,
            "average_confidence": avg_conf,
            "checks": [check1, check2, check3]
        })

    return all_results


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from app.sections import split_submission

    print("=" * 40)
    print("Testing revised AI detection")
    print("=" * 40)

    test_text = """
Abstract
It is worth noting that this paper aims to investigate the utilization of
transformer-based models for automated essay scoring. Furthermore, it is
important to consider that our approach seeks to facilitate more accurate
evaluation. Moreover, in the realm of natural language processing, this
study seeks to delve into the challenges of automated scoring. The results
demonstrate significant improvements. It was found that accuracy increased.
It was observed that the baseline was exceeded. In conclusion, this work
facilitates better outcomes.

1. Introduction
It is crucial to acknowledge that automated essay scoring has been a
long-standing challenge. One might argue that hand-crafted features
fail to capture semantic meaning. Furthermore, this paper aims to
address this gap by utilizing pre-trained language models.
In summary, we believe this work will facilitate better scoring systems.
The next section discusses the related work in detail.
As mentioned above, the problem is significant.
"""

    split = split_submission(test_text)
    results = run_ai_detection(split["sections"])

    print("\n--- RESULTS ---")
    for r in results:
        print(f"\nSection: {r['heading']}")
        print(f"  overall: {r['overall_verdict']} (conf={r['average_confidence']})")
        for check in r["checks"]:
            print(f"  {check['check_label']}: {check['verdict']}")
            if check.get("flagged_sentences"):
                print(f"    flagged: {check['flagged_sentences'][0][:70]}...")
            if check.get("reason"):
                print(f"    reason: {check['reason'][:80]}")

    print("\n✓ detection rewrite complete")