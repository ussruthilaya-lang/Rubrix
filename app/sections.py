import re

# PROMPT_VERSION: not applicable — rule-based only, no LLM
# TODO: production — add ML-based section boundary detection for papers with non-standard headings

SECTION_KEYWORDS = [
    "abstract", "introduction", "background", "related work",
    "literature review", "methodology", "methods", "approach",
    "experimental setup", "experiments", "results", "findings",
    "discussion", "analysis", "evaluation", "conclusion",
    "conclusions", "future work", "references", "appendix"
]

MAX_SECTIONS = 3
MAX_TOKENS_PER_SECTION = 800  # approx 600 words
CHARS_PER_TOKEN = 4  # rough estimate


def _estimate_tokens(text: str) -> int:
    return len(text) // CHARS_PER_TOKEN


def _detect_heading(line: str) -> bool:
    """Return True if line looks like a section heading."""
    line_clean = line.strip().lower()
    # Headings are short — reject long lines immediately
    if len(line.strip()) > 60:
        return False

    # Remove numbering like "1.", "2.1", "III."
    line_clean = re.sub(r'^[\d\.\s]+', '', line_clean)
    line_clean = re.sub(r'^[ivxlcdm]+\.\s*', '', line_clean)

    for keyword in SECTION_KEYWORDS:
        if line_clean.startswith(keyword):
            return True
    return False


def _split_by_headings(text: str) -> list:
    """Split text into sections using heading detection."""
    lines = text.split('\n')
    sections = []
    current_heading = "Preamble"
    current_lines = []

    for line in lines:
        if _detect_heading(line) and line.strip():
            if current_lines:
                content = '\n'.join(current_lines).strip()
                if content:
                    sections.append({
                        "heading": current_heading,
                        "content": content,
                        "tokens": _estimate_tokens(content),
                        "method": "heading_detection"
                    })
            current_heading = line.strip()
            current_lines = []
        else:
            current_lines.append(line)

    # Don't forget the last section
    if current_lines:
        content = '\n'.join(current_lines).strip()
        if content:
            sections.append({
                "heading": current_heading,
                "content": content,
                "tokens": _estimate_tokens(content),
                "method": "heading_detection"
            })

    return sections


def _split_by_tokens(text: str) -> list:
    """Fallback: split by token count when no headings found."""
    chunk_size = MAX_TOKENS_PER_SECTION * CHARS_PER_TOKEN
    chunks = []
    start = 0
    idx = 1

    while start < len(text):
        end = start + chunk_size
        # Try to break at a paragraph boundary
        if end < len(text):
            newline_pos = text.rfind('\n\n', start, end)
            if newline_pos > start:
                end = newline_pos

        content = text[start:end].strip()
        if content:
            chunks.append({
                "heading": f"Section {idx}",
                "content": content,
                "tokens": _estimate_tokens(content),
                "method": "token_split"
            })
        start = end
        idx += 1

    return chunks


def split_submission(text: str) -> dict:
    """
    Main entry point. Split submission into sections.
    Returns dict with sections list and metadata.
    """
    print("\n[sections] splitting submission...")
    print(f"  input length: {len(text):,} chars (~{_estimate_tokens(text):,} tokens)")

    # Try heading detection first
    sections = _split_by_headings(text)
    method = "heading_detection"

    if len(sections) < 2:
        print("  [sections] few headings found — falling back to token split")
        sections = _split_by_tokens(text)
        method = "token_split"

    # Log what we found
    print(f"  [sections] detected {len(sections)} sections via {method}:")
    for i, s in enumerate(sections):
        print(f"    {i+1}. '{s['heading']}' — {s['tokens']} tokens")

    # Cap at MAX_SECTIONS
    total_found = len(sections)
    sections = sections[:MAX_SECTIONS]

    if total_found > MAX_SECTIONS:
        print(f"  [sections] capped at {MAX_SECTIONS} — {total_found - MAX_SECTIONS} sections require paid plan")

    return {
        "sections": sections,
        "total_found": total_found,
        "total_returned": len(sections),
        "capped": total_found > MAX_SECTIONS,
        "method": method
    }


if __name__ == "__main__":
    print("=" * 40)
    print("T-16: Testing section splitter")
    print("=" * 40)

    # Test 1 — paper with clear headings
    test_paper = """
Abstract
This paper investigates transformer-based models for automated essay scoring.
We fine-tuned BERT on 50,000 essays achieving 87% accuracy vs 79% SVM baseline.

1. Introduction
Automated essay scoring has been a long-standing NLP challenge. Hand-crafted
features fail to capture semantic meaning. This work addresses the gap by
applying pre-trained language models. We evaluate on the ASAP benchmark dataset.

2. Related Work
Prior work includes Shermis (2013) using regression and Taghipour (2016) with
LSTMs. Our work differs by using transformer architecture with domain adaptation.
Several recent works have explored BERT for scoring but none applied domain-specific
fine-tuning on grade-stratified data as we do here.

3. Methodology
We fine-tuned BERT-base on the ASAP dataset containing essays from grades 7-10.
The dataset was split 80/10/10 for train/validation/test. We used accuracy and
quadratic weighted kappa as evaluation metrics. Training ran for 5 epochs with
learning rate 2e-5 and batch size 32.

4. Results
Our model achieved 87% accuracy and QWK of 0.82. The baseline SVM achieved 79%.
Results show consistent improvement across all essay prompts. Table 1 shows
per-prompt breakdown.

5. Conclusion
Transformers are effective for AES. Future work will explore larger models
and cross-domain generalization. We will release code and models publicly.
"""

    result = split_submission(test_paper)
    print(f"\n✓ sections returned: {result['total_returned']}/{result['total_found']}")
    print(f"  capped: {result['capped']}")
    print(f"  method: {result['method']}")

    print("\n--- SECTION PREVIEW ---")
    for i, s in enumerate(result["sections"]):
        print(f"\nSection {i+1}: {s['heading']}")
        print(f"  tokens: {s['tokens']}")
        print(f"  preview: {s['content'][:80]}...")

    print("\n" + "=" * 40)

    # Test 2 — no headings (token split fallback)
    print("\nTest 2 — no headings:")
    no_heading_text = "This is a paragraph. " * 200
    result2 = split_submission(no_heading_text)
    print(f"✓ sections returned: {result2['total_returned']} via {result2['method']}")

    print("\n" + "=" * 40)
    print("✓ T-16 complete — section splitter ready")
    print("=" * 40)