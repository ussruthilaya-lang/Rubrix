# PROMPT_VERSION REGISTRY
# When you change a prompt: bump its version, keep the old one commented out
# Feedback rows record prompt_version so you can track quality over time

# ── AI Detection ─────────────────────────────────────────────────────────────

AI_SENTENCE_STRUCTURE_VERSION = "v1.0"
AI_SENTENCE_STRUCTURE = """You are an expert in academic writing analysis.

Analyze the following text section for AI-generated writing patterns.
Focus ONLY on sentence structure — look for:
- Uniform sentence length with little variation
- Lack of personal voice or first-person reasoning
- Over-formal transitions ("Furthermore", "Moreover", "It is worth noting")
- Hedging clusters ("it is important to consider", "one might argue")
- Repetitive syntactic patterns across consecutive sentences

SECTION HEADING: {heading}
SECTION TEXT:
{content}

Respond with a JSON object with exactly these fields:
- verdict: "likely_ai", "possibly_ai", or "likely_human"
- confidence: float 0.0 to 1.0
- flagged_sentences: list of up to 3 sentences that triggered the verdict (exact quotes)
- reason: one sentence explaining the verdict

Respond with ONLY the JSON object, no other text.
"""

AI_REASONING_DEPTH_VERSION = "v1.0"
AI_REASONING_DEPTH = """You are an expert academic reviewer assessing originality of thought.

Analyze the following text section for depth of reasoning.
Focus ONLY on whether arguments show original thinking or surface-level summarization:
- AI tends to restate known facts without taking a position
- AI tends to list points without building an argument
- Humans tend to show uncertainty, make trade-offs, defend choices
- Look for: "we chose X over Y because", "this surprised us", "contrary to our expectation"

SECTION HEADING: {heading}
SECTION TEXT:
{content}

Respond with a JSON object with exactly these fields:
- verdict: "likely_ai", "possibly_ai", or "likely_human"
- confidence: float 0.0 to 1.0
- flagged_sentences: list of up to 3 sentences that triggered the verdict (exact quotes)
- reason: one sentence explaining the verdict

Respond with ONLY the JSON object, no other text.
"""

# ── Custom Rubric ─────────────────────────────────────────────────────────────

CUSTOM_RUBRIC_CHECK_VERSION = "v1.0"
CUSTOM_RUBRIC_CHECK = """You are an expert academic reviewer.

Evaluate the following section against a custom rubric criterion defined by the user.

SECTION HEADING: {heading}
SECTION TEXT:
{content}

CUSTOM CRITERION CATEGORY: {category}
CUSTOM CRITERION DESCRIPTION: {description}

Respond with a JSON object with exactly these fields:
- status: "MET", "PARTIAL", or "MISSING"
- confidence: float 0.0 to 1.0
- evidence: short quote from the text that supports your decision, or "none found"
- what_is_missing: one sentence if PARTIAL or MISSING, else empty string

Respond with ONLY the JSON object, no other text.
"""