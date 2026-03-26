import openai
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.inference import stage1_score, stage2_recheck, stage3_generate_fixes

def assemble_results(rubric: list, final_results: list) -> dict:
    """
    Merge rubric metadata with pipeline results.
    Find best-match (highest confidence MET) criterion.
    Return clean output structure for the UI.
    """
    rubric_map = {c["id"]: c for c in rubric}

    rows = []
    for r in final_results:
        criterion = rubric_map[r["id"]]
        fix = r.get("fix") or {}
        rows.append({
            "id": r["id"],
            "name": criterion["name"],
            "status": r["status"],
            "confidence": r["confidence"],
            "evidence": r.get("evidence", "none found"),
            "rubric_text": criterion["description"],
            "what_is_missing": fix.get("what_is_missing", ""),
            "how_to_fix": fix.get("how_to_fix", ""),
            "example_fix": fix.get("example_fix", ""),
            "is_best_match": False
        })

    # Find highest confidence MET criterion — this is the "learn from" pointer
    met_rows = [r for r in rows if r["status"] == "MET"]
    if met_rows:
        best = max(met_rows, key=lambda r: r["confidence"])
        for r in rows:
            if r["id"] == best["id"]:
                r["is_best_match"] = True
                break
        print(f"  [assembler] best match: {best['id']} — {best['name']} (conf={best['confidence']:.2f})")

    # Summary stats
    summary = {
        "total": len(rows),
        "met": sum(1 for r in rows if r["status"] == "MET"),
        "partial": sum(1 for r in rows if r["status"] == "PARTIAL"),
        "missing": sum(1 for r in rows if r["status"] == "MISSING"),
        "best_match_id": best["id"] if met_rows else None,
        "best_match_name": best["name"] if met_rows else None,
    }

    print(f"  [assembler] summary — MET: {summary['met']} | PARTIAL: {summary['partial']} | MISSING: {summary['missing']}")

    return {"summary": summary, "rows": rows}


if __name__ == "__main__":
    import json
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    USE_MOCK = True  # ← flip to False only when testing with real API

    print("=" * 40)
    print(f"T-11: Testing assembler ({'MOCK' if USE_MOCK else 'LIVE API'})")
    print("=" * 40)

    with open("data/rubric.json", encoding="utf-8") as f:
        rubric = json.load(f)

    if USE_MOCK:
        from tests.mock_data import MOCK_STAGE3_RESULTS
        print("[mock] using mock pipeline results — no API calls")
        final_results = MOCK_STAGE3_RESULTS
    else:
        from app.inference import stage1_score, stage2_recheck, stage3_generate_fixes
        sample_submission = """
        This paper investigates transformer-based models for automated essay scoring.
        We fine-tuned BERT-base on the ASAP dataset (80/10/10 split).
        Our model achieved 87% accuracy vs SVM baseline of 79%.
        Future work will explore larger models.
        """
        stage1 = stage1_score(sample_submission, rubric)
        stage2 = stage2_recheck(sample_submission, rubric, stage1)
        final_results = stage3_generate_fixes(sample_submission, rubric, stage2)

    output = assemble_results(rubric, final_results)

    print("\n--- SUMMARY ---")
    s = output["summary"]
    print(f"  Total: {s['total']} | MET: {s['met']} | PARTIAL: {s['partial']} | MISSING: {s['missing']}")
    print(f"  Best match: {s['best_match_id']} — {s['best_match_name']}")

    print("\n--- SAMPLE ROWS ---")
    for row in output["rows"][:4]:
        star = " ★ LEARN FROM THIS" if row["is_best_match"] else ""
        print(f"\n  {row['id']} — {row['name']}{star}")
        print(f"  status: {row['status']} | conf: {row['confidence']}")
        if row["what_is_missing"]:
            print(f"  missing: {row['what_is_missing']}")
        if row["how_to_fix"]:
            print(f"  fix:     {row['how_to_fix']}")

    print("\n" + "=" * 40)
    print("✓ T-11 complete — assembler ready")
    print("=" * 40)