import os
import json
import uuid
import urllib.request
import urllib.error
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(".env")

# TODO: production — move to environment-specific config
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")
GITHUB_API = "https://api.github.com"

# Prompt versions imported at runtime
# TODO: production — auto-inject from prompt registry


def generate_session_id() -> str:
    return str(uuid.uuid4())[:8]


def build_session_data(
    session_id: str,
    sections_evaluated: int,
    custom_checks: list,
    ai_results: list,
    rubric_summary: dict,
    stage3_used: bool,
    prompt_versions: dict
) -> dict:
    """
    Build clean session data dict.
    No submission text, no PII — only signal.
    """
    if ai_results:
        flagged = sum(
            1 for r in ai_results
            if r.get("overall_verdict") in ("likely_ai", "possibly_ai")
        )
        ai_summary = f"{flagged}/{len(ai_results)} sections flagged"
    else:
        ai_summary = "not run"

    rubric_summary_str = (
        f"MET:{rubric_summary.get('met', 0)} "
        f"PARTIAL:{rubric_summary.get('partial', 0)} "
        f"MISSING:{rubric_summary.get('missing', 0)}"
    )

    c1 = custom_checks[0] if len(custom_checks) > 0 else {}
    c2 = custom_checks[1] if len(custom_checks) > 1 else {}

    return {
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "prompt_versions": prompt_versions,
        "section_count_evaluated": sections_evaluated,
        "custom_check_1_category": c1.get("category", ""),
        "custom_check_1_description": c1.get("description", "")[:100],
        "custom_check_2_category": c2.get("category", ""),
        "custom_check_2_description": c2.get("description", "")[:100],
        "ai_check_result_summary": ai_summary,
        "rubric_scores_summary": rubric_summary_str,
        "stage3_used": stage3_used,
    }


def post_feedback_to_github(session_data: dict, feedback: dict) -> dict:
    """
    Post feedback as a GitHub issue.
    Title: [feedback] session_id date
    Body: JSON with all session data + feedback signals
    Labels: prompt version tags
    """
    if not GITHUB_TOKEN or not GITHUB_REPO:
        print("  [feedback] GitHub not configured — logging locally only")
        _log_locally(session_data, feedback)
        return {"success": False, "reason": "not configured"}

    title = f"[feedback] {session_data['session_id']} — {session_data['timestamp'][:10]}"

    # Build issue body as readable JSON
    body_data = {
        **session_data,
        "feedback_ai_check_accurate": feedback.get("ai_check_accurate", ""),
        "feedback_fix_useful": feedback.get("fix_useful", ""),
        "feedback_free_text": feedback.get("free_text", "")[:300]
    }

    # Labels for filtering by prompt version
    prompt_versions = session_data.get("prompt_versions", {})
    labels = ["user-feedback"]
    for key, version in prompt_versions.items():
        labels.append(f"{key}-{version}")

    issue_payload = {
        "title": title,
        "body": f"```json\n{json.dumps(body_data, indent=2)}\n```",
        "labels": labels
    }

    url = f"{GITHUB_API}/repos/{GITHUB_REPO}/issues"
    data = json.dumps(issue_payload).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
            "User-Agent": "rubric-checker"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            issue_url = result.get("html_url", "")
            print(f"  [feedback] ✓ issue created: {issue_url}")
            return {"success": True, "url": issue_url}
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"  [feedback] ✗ GitHub error {e.code}: {error_body[:100]}")
        _log_locally(session_data, feedback)
        return {"success": False, "reason": f"HTTP {e.code}"}
    except Exception as e:
        print(f"  [feedback] ✗ error: {e}")
        _log_locally(session_data, feedback)
        return {"success": False, "reason": str(e)}


def _log_locally(session_data: dict, feedback: dict):
    """
    Fallback — write to local JSON file if GitHub unavailable.
    Used during local dev without token configured.
    """
    os.makedirs("data/feedback_local", exist_ok=True)
    filename = f"data/feedback_local/{session_data['session_id']}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump({**session_data, **feedback}, f, indent=2)
    print(f"  [feedback] logged locally: {filename}")


def fetch_feedback_stats() -> dict:
    """
    Fetch feedback issues from GitHub and compute stats.
    Returns summary for display in UI.
    TODO: production — cache this with TTL so we don't hit API on every page load
    """
    if not GITHUB_TOKEN or not GITHUB_REPO:
        return {"total": 0, "note": "GitHub not configured"}

    url = f"{GITHUB_API}/repos/{GITHUB_REPO}/issues?labels=user-feedback&state=open&per_page=100"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "rubric-checker"
        }
    )

    try:
        with urllib.request.urlopen(req) as response:
            issues = json.loads(response.read().decode())

        total = len(issues)
        ai_accurate = 0
        fix_useful = 0

        for issue in issues:
            body = issue.get("body", "")
            try:
                json_str = body.replace("```json", "").replace("```", "").strip()
                data = json.loads(json_str)
                if data.get("feedback_ai_check_accurate") == "yes":
                    ai_accurate += 1
                if data.get("feedback_fix_useful") == "yes":
                    fix_useful += 1
            except Exception:
                continue

        return {
            "total": total,
            "ai_accurate": ai_accurate,
            "ai_accurate_pct": round(ai_accurate / total * 100) if total else 0,
            "fix_useful": fix_useful,
            "fix_useful_pct": round(fix_useful / total * 100) if total else 0,
        }

    except Exception as e:
        print(f"  [feedback] stats fetch error: {e}")
        return {"total": 0, "note": str(e)}


if __name__ == "__main__":
    print("=" * 40)
    print("T-19 (revised): Testing GitHub feedback")
    print("=" * 40)

    session_id = generate_session_id()
    print(f"✓ session_id: {session_id}")

    session_data = build_session_data(
        session_id=session_id,
        sections_evaluated=2,
        custom_checks=[
            {"category": "Research Contribution",
             "description": "Paper presents a novel finding."},
            {"category": "Methodology Rigor",
             "description": "Methodology is reproducible."}
        ],
        ai_results=[
            {"overall_verdict": "likely_ai"},
            {"overall_verdict": "likely_human"}
        ],
        rubric_summary={"met": 14, "partial": 2, "missing": 4},
        stage3_used=False,
        prompt_versions={
            "ai_sentence": "v1.0",
            "ai_reasoning": "v1.0",
            "custom_rubric": "v1.0"
        }
    )
    print("✓ session data built")

    result = post_feedback_to_github(session_data, {
        "ai_check_accurate": "yes",
        "fix_useful": "no",
        "free_text": "AI detection was correct but fix suggestions were too generic."
    })

    if result["success"]:
        print(f"✓ issue posted: {result['url']}")
    else:
        print(f"⚠ fallback to local: {result['reason']}")

    stats = fetch_feedback_stats()
    print(f"\n--- STATS ---")
    print(f"  total feedback: {stats.get('total', 0)}")
    if stats.get('total', 0) > 0:
        print(f"  AI accurate: {stats['ai_accurate_pct']}%")
        print(f"  fix useful:  {stats['fix_useful_pct']}%")

    print("\n" + "=" * 40)
    print("✓ T-19 complete")
    print("=" * 40)