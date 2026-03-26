import os
import json
from dotenv import load_dotenv
from groq import Groq
from openai import OpenAI, RateLimitError

load_dotenv(".env")

client_groq = Groq(api_key=os.getenv("GROQ_API_KEY"))

STAGE1_MODEL = "llama-3.1-8b-instant"
STAGE2_MODEL = "llama-3.3-70b-versatile"
CONFIDENCE_THRESHOLD = 0.75


def stage1_score(submission_text: str, rubric: list) -> list:
    """
    Stage 1: Score all 20 criteria with Llama 8B.
    Returns list of result dicts.
    """
    print("\n[Stage 1] Scoring all criteria with Llama 8B...")

    criteria_block = "\n".join([
        f"{c['id']}: {c['name']} — {c['description']}"
        for c in rubric
    ])

    prompt = f"""You are an expert academic reviewer. Evaluate the submission below against each rubric criterion.

SUBMISSION:
{submission_text[:6000]}

RUBRIC CRITERIA:
{criteria_block}

For each criterion, respond with a JSON array. Each element must have exactly these fields:
- id: the criterion ID (e.g. C01)
- status: one of MET, PARTIAL, or MISSING
- confidence: a float between 0.0 and 1.0
- evidence: a short quote or phrase from the submission that supports your decision (or "none found" if missing)

Respond with ONLY the JSON array, no other text.
"""

    response = client_groq.chat.completions.create(
        model=STAGE1_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000,
        temperature=0.1
    )

    raw = response.choices[0].message.content.strip()

    # Parse JSON response
    try:
        results = json.loads(raw)
    except json.JSONDecodeError:
        # Try to extract JSON array if model added extra text
        import re
        match = re.search(r'\[.*\]', raw, re.DOTALL)
        if match:
            results = json.loads(match.group())
        else:
            print("  [Stage 1] ERROR: could not parse response")
            print(f"  raw response: {raw[:200]}")
            return []

    # Log each result
    for r in results:
        flag = "⚠" if r["status"] in ("PARTIAL", "MISSING") or r["confidence"] < CONFIDENCE_THRESHOLD else "✓"
        print(f"  {flag} {r['id']}: {r['status']} (conf={r['confidence']:.2f})")

    met = sum(1 for r in results if r["status"] == "MET")
    partial = sum(1 for r in results if r["status"] == "PARTIAL")
    missing = sum(1 for r in results if r["status"] == "MISSING")
    low_conf = sum(1 for r in results if r["confidence"] < CONFIDENCE_THRESHOLD)

    print(f"\n  [Stage 1] complete — MET: {met}, PARTIAL: {partial}, MISSING: {missing}")
    print(f"  [Stage 1] low confidence (<{CONFIDENCE_THRESHOLD}): {low_conf} — flagging for Stage 2")

    return results

def stage2_recheck(submission_text: str, rubric: list, stage1_results: list) -> list:
    """
    Stage 2: Recheck low-confidence and non-MET criteria with Llama 70B.
    Returns updated full results list.
    """
    # Find criteria to escalate
    rubric_map = {c["id"]: c for c in rubric}
    to_escalate = [
        r for r in stage1_results
        if r["status"] in ("PARTIAL", "MISSING") or r["confidence"] < CONFIDENCE_THRESHOLD
    ]

    if not to_escalate:
        print("\n[Stage 2] No criteria to escalate — all high confidence")
        return stage1_results

    print(f"\n[Stage 2] Escalating {len(to_escalate)} criteria to Llama 70B...")
    for r in to_escalate:
        print(f"  → {r['id']}: {r['status']} (conf={r['confidence']:.2f})")

    criteria_block = "\n".join([
        f"{r['id']}: {rubric_map[r['id']]['name']} — {rubric_map[r['id']]['description']}"
        for r in to_escalate
    ])

    prompt = f"""You are a senior academic reviewer. Re-evaluate ONLY the following criteria against the submission.
These were flagged as uncertain by a preliminary review.

SUBMISSION:
{submission_text[:6000]}

CRITERIA TO RE-EVALUATE:
{criteria_block}

For each criterion respond with a JSON array with exactly these fields:
- id: criterion ID
- status: MET, PARTIAL, or MISSING
- confidence: float 0.0 to 1.0
- evidence: short quote from submission or "none found"

Be more thorough than the preliminary review. Look carefully for implicit mentions.
Respond with ONLY the JSON array, no other text.
"""

    response = client_groq.chat.completions.create(
        model=STAGE2_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000,
        temperature=0.1
    )

    raw = response.choices[0].message.content.strip()

    try:
        updated = json.loads(raw)
    except json.JSONDecodeError:
        import re
        match = re.search(r'\[.*\]', raw, re.DOTALL)
        if match:
            updated = json.loads(match.group())
        else:
            print("  [Stage 2] ERROR: could not parse response — keeping Stage 1 results")
            return stage1_results

    # Merge updated results back into full results list
    updated_map = {r["id"]: r for r in updated}
    final_results = []
    for r in stage1_results:
        if r["id"] in updated_map:
            new = updated_map[r["id"]]
            old_status = r["status"]
            new_status = new["status"]
            change = f"  ✓ upgraded: {old_status} → {new_status}" if old_status != new_status else "  → unchanged"
            print(f"  [Stage 2] {r['id']}: {old_status}(conf={r['confidence']:.2f}) → {new_status}(conf={new['confidence']:.2f}){change if old_status != new_status else ''}")
            final_results.append(new)
        else:
            final_results.append(r)

    still_flagged = [r for r in final_results if r["status"] in ("PARTIAL", "MISSING")]
    print(f"\n  [Stage 2] complete — {len(still_flagged)} criteria still need fixes → escalating to Stage 3")

    return final_results

def stage3_generate_fixes(submission_text: str, rubric: list, stage2_results: list) -> list:
    """
    Stage 3: Generate fix suggestions for PARTIAL and MISSING criteria using GPT-4o-mini.
    Only called after explicit user confirmation.
    Returns updated results list with fix text added.
    """
    from openai import OpenAI
    import os

    client_openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    rubric_map = {c["id"]: c for c in rubric}
    to_fix = [r for r in stage2_results if r["status"] in ("PARTIAL", "MISSING")]

    if not to_fix:
        print("\n[Stage 3] Nothing to fix — all criteria MET")
        return stage2_results

    print(f"\n[Stage 3] Generating fixes for {len(to_fix)} criteria with GPT-4o-mini...")
    total_tokens = 0

    fixed_map = {}
    for r in to_fix:
        criterion = rubric_map[r["id"]]
        print(f"  → {r['id']}: {criterion['name']} ({r['status']})...")

        prompt = f"""You are an expert academic writing coach.

A research paper submission was evaluated against this rubric criterion and found to be {r['status']}.

CRITERION: {criterion['name']}
CRITERION DESCRIPTION: {criterion['description']}

SUBMISSION EXCERPT (relevant section):
{submission_text[:3000]}

EVIDENCE FOUND (or lack thereof): {r.get('evidence', 'none found')}

Respond with a JSON object with exactly these fields:
- what_is_missing: one sentence describing specifically what is absent or incomplete
- how_to_fix: one concrete sentence the author can add or change to meet this criterion
- example_fix: a short example sentence (max 30 words) showing what good text looks like

Respond with ONLY the JSON object, no other text."""

        response = client_openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.2
        )

        raw = response.choices[0].message.content.strip()
        tokens_used = response.usage.total_tokens
        total_tokens += tokens_used

        try:
            response = client_openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.2
            )
            raw = response.choices[0].message.content.strip()
            tokens_used = response.usage.total_tokens
            total_tokens += tokens_used

            try:
                fix = json.loads(raw)
            except json.JSONDecodeError:
                import re
                match = re.search(r'\{.*\}', raw, re.DOTALL)
                fix = json.loads(match.group()) if match else {
                    "what_is_missing": "Could not parse fix",
                    "how_to_fix": "Please review manually",
                    "example_fix": ""
                }

            fixed_map[r["id"]] = fix
            cost = tokens_used * 0.00000015
            print(f"  ✓ {r['id']}: fix generated — tokens: {tokens_used} (~${cost:.5f})")

        except openai.RateLimitError:
            print(f"  ⚠ {r['id']}: OpenAI quota exceeded — add credits at platform.openai.com/settings/billing")
            fixed_map[r["id"]] = {
                "what_is_missing": "Fix generation requires OpenAI credits",
                "how_to_fix": "Add credits at platform.openai.com/settings/billing",
                "example_fix": ""
            }
        except Exception as e:
            print(f"  ⚠ {r['id']}: Stage 3 error — {str(e)[:80]}")
            fixed_map[r["id"]] = {
                "what_is_missing": "Fix generation unavailable",
                "how_to_fix": "Please review manually",
                "example_fix": ""
            }

    # Merge fixes back into results
    final_results = []
    for r in stage2_results:
        if r["id"] in fixed_map:
            r["fix"] = fixed_map[r["id"]]
        else:
            r["fix"] = None
        final_results.append(r)

    total_cost = total_tokens * 0.00000015
    print(f"\n  [Stage 3] complete — total tokens: {total_tokens}, estimated cost: ~${total_cost:.4f}")

    return final_results

if __name__ == "__main__":
    print("=" * 40)
    print("T-09: Testing Stage 1 + Stage 2")
    print("=" * 40)

    sample_submission = """
    Abstract:
    This paper investigates the use of transformer-based models for automated essay scoring.
    We propose a fine-tuned BERT model trained on 50,000 student essays. Our model achieves
    87% accuracy on the test set, outperforming the baseline SVM model which achieved 79%.

    1. Introduction
    Automated essay scoring (AES) has been a long-standing challenge in NLP. Existing approaches
    rely on hand-crafted features which fail to capture semantic meaning. This work addresses
    the gap by applying pre-trained language models to the task.

    2. Related Work
    Prior work includes (Shermis 2013) who used regression models, and (Taghipour 2016) who
    applied LSTMs. Our work differs in using transformer architecture with domain adaptation.

    3. Methodology
    We fine-tuned BERT-base on the ASAP dataset containing essays from grades 7-10.
    The dataset was split 80/10/10 for train/validation/test. We used accuracy and
    quadratic weighted kappa (QWK) as evaluation metrics.

    4. Results
    Our model achieved 87% accuracy and QWK of 0.82. The baseline SVM achieved 79% accuracy.
    Results show consistent improvement across all essay prompts.

    5. Conclusion
    This work demonstrates transformers are effective for AES. Future work will explore
    larger models and cross-domain generalization.
    """

    with open("data/rubric.json", encoding="utf-8") as f:
        rubric = json.load(f)

    stage1_results = stage1_score(sample_submission, rubric)
    final_results = stage2_recheck(sample_submission, rubric, stage1_results)

    print(f"\n✓ final results — {len(final_results)} criteria")
    met = sum(1 for r in final_results if r["status"] == "MET")
    partial = sum(1 for r in final_results if r["status"] == "PARTIAL")
    missing = sum(1 for r in final_results if r["status"] == "MISSING")
    print(f"  MET: {met} | PARTIAL: {partial} | MISSING: {missing}")
    print("=" * 40)
    print("✓ T-09 complete — Stage 2 recheck ready")
    print("=" * 40)