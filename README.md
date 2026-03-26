# Rubrix

**Research paper and document checker powered by cascade inference.**

AI detection · custom rubric checks · section-by-section evaluation · feedback loop

→ [Live demo]() · [GitHub](https://github.com/ussruthilaya-lang/Rubrix)

---

## What it does

Rubrix takes a research paper or project document and evaluates it section by section across two dimensions:

**AI detection** — three independent checks run on each section:
- Vocabulary pattern scan (rule-based, zero API cost) — flags documented AI phrases like "it is worth noting", "furthermore", passive voice tells, em-dash overuse
- Sentence uniformity (Llama 70B) — checks for uniform sentence length, missing personal voice, generic paragraph openers
- Structural tells (Llama 70B) — checks for mechanical transitions, conclusion restating introduction, equal hedging on all claims

Every verdict names the exact pattern that triggered it. Not a black-box score — specific, explainable, actionable.

**Custom rubric checks** — two slots the user defines. Defaults are "Clarity of Argument" and "Evidence Quality". User can change both the category and description. Input is validated against prompt injection, length limits, and multi-criterion abuse before hitting the pipeline.

**Section-by-section** — detects section boundaries from headings, evaluates one section at a time, up to 3 free. User confirms before proceeding to the next. After 3: "this tool is in beta — your feedback shapes what gets built next."

**Feedback loop** — after each run, collects three signals: AI detection accuracy (yes/no), fix suggestion usefulness (yes/no), free text. Stored as GitHub Issues with prompt version labels. Used to track quality improvements across prompt versions.

---

## Why I built it

This is a demo app for user testing, built to showcase production ML engineering patterns in a scoped, deployable project.

The target user is a student submitting a research paper who wants to know if their paper will pass review — not just a score, but specific, fixable feedback.

The product constraint I set myself: every verdict must be explainable. A student should be able to read the output and understand exactly why something was flagged and how to fix it. This ruled out black-box classifiers and forced every LLM prompt to return specific evidence, not just a label.

---

## Architecture

```
Input (paste / PDF)
    ↓
Section splitter        — heading detection → token split fallback
    ↓
┌─────────────────────────────────────────────┐
│  AI Detection (per section)                 │
│  Check 1: Pattern scan      (rule-based)    │
│  Check 2: Sentence uniformity (Llama 70B)   │
│  Check 3: Structural tells   (Llama 70B)    │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│  Custom Rubric (per section)                │
│  2 user-defined criteria  (Llama 70B)       │
│  Input validated before hitting pipeline    │
└─────────────────────────────────────────────┘
    ↓
Results display — flagged sentences highlighted inline
    ↓
Feedback collector → GitHub Issues (versioned by prompt)
```

The standard rubric pipeline (20-criterion cascade) is also implemented in `app/inference.py` using a 3-stage model cascade: Llama 8B for bulk scoring → Llama 70B recheck on low-confidence results → GPT-4o-mini for fix generation (gated behind user confirmation). Not exposed in the current UI but fully functional.

---

## Stack

| Component | Choice | Why |
|---|---|---|
| Stage 1 model | Groq Llama 3.1 8B | Fast, free, bulk scoring |
| Stage 2/Detection | Groq Llama 3.3 70B | Better nuance, still free |
| Stage 3 | GPT-4o-mini | Fix generation, ~$0.004/run |
| Embeddings | all-MiniLM-L6-v2 | No API cost, right size |
| Vector store | FAISS IndexFlatL2 | Exact search at rubric scale |
| UI | Streamlit | Fast to ship, good enough |
| Feedback | GitHub Issues API | Free, versioned, queryable by label |
| Hosting | HuggingFace Spaces | Free, public URL, zero DevOps |

---

## Key engineering decisions

**Cascade inference over single-model.** Small model handles breadth (20 criteria in one call), strong model handles precision (only re-evaluates low-confidence results). This is how production AI systems control cost — not a workaround.

**RAG for rubric matching.** Criterion descriptions are embedded with sentence-transformers and indexed in FAISS. Submission text is matched semantically before any LLM sees it. "We evaluated using accuracy and F1" correctly retrieves the "Evaluation methodology" criterion with no keyword overlap.

**Rule-based check first.** AI detection Check 1 uses zero API calls — just regex against documented patterns. This is intentional: the most reliable signal is the cheapest one. LLMs handle what rules can't.

**Prompt versioning from day one.** Every prompt has a version constant in `app/prompts.py`. Every feedback GitHub Issue is labeled with the prompt versions that ran. When a prompt is refined, the version bumps and the feedback data separates cleanly. This makes the improvement loop measurable: "v1.0 got 60% positive on fix suggestions, v1.2 got 78%."

**Input validation as a security layer.** Custom rubric descriptions are validated against a blocklist (injection keywords), a length limit (200 chars), and a structural check (max 2 "and"s, no semicolons). Built before it was a problem, not after.

**Honest beta framing.** The 3-section limit is real, not a fake paywall. The message is "this tool is in beta — your feedback shapes what gets built next." This produces better feedback signal than a hard paywall and is more credible to users.

---

## How to run

**Prerequisites:** Python 3.11, Groq API key (free at console.groq.com)

```bash
git clone https://github.com/ussruthilaya-lang/Rubrix
cd rubric-checker

py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1        # Windows
# source .venv/bin/activate       # Mac/Linux

pip install -r requirements.txt
```

Create `.env` (use Python to avoid encoding issues on Windows):

```python
python -c "
with open('.env', 'w', encoding='utf-8') as f:
    f.write('GROQ_API_KEY=your_key_here\n')
    f.write('OPENAI_API_KEY=your_key_here\n')   # optional, needed for Stage 3
    f.write('GITHUB_TOKEN=your_token_here\n')    # optional, for feedback collection
    f.write('GITHUB_REPO=ussruthilaya-lang/Rubrix\n')
"
```

Build the rubric index (one-time):

```bash
python scripts/build_rubric.py
python scripts/build_embeddings.py
python scripts/build_index.py
```

Run:

```bash
streamlit run app/main.py
```

Smoke test APIs:

```bash
python scripts/smoke_test.py
```

**Mock mode** — toggle in the sidebar to run the full UI without any API calls. Uses pre-built fixture data in `tests/mock_data.py`.

---

## Project structure

```
rubric-checker/
├── app/
│   ├── main.py           # Streamlit UI
│   ├── detection.py      # AI detection — 3 checks
│   ├── sections.py       # Section splitter
│   ├── rubric_custom.py  # Custom rubric validator + runner
│   ├── inference.py      # Cascade pipeline — stages 1, 2, 3
│   ├── assembler.py      # Result assembler + best-match pointer
│   ├── prompts.py        # All prompts with version constants
│   └── feedback.py       # GitHub Issues feedback collector
├── data/
│   ├── rubric.json       # 20-criterion rubric (swappable)
│   ├── rubric.index      # FAISS index
│   └── rubric_meta.json  # Index metadata
├── scripts/
│   ├── build_rubric.py
│   ├── build_embeddings.py
│   ├── build_index.py
│   ├── smoke_test.py
│   └── prompt_version_check.py
└── tests/
    ├── mock_data.py
    ├── test_retrieval.py
    └── test_cascade.py
```

---

## What's production-ready vs demo

This is intentionally a demo app. The production gaps are marked with `# TODO: production` throughout the codebase. Key ones:

- Prompts need calibration against a labeled dataset before production use
- AI detection confidence thresholds are heuristic, not empirically validated
- Section splitter relies on keyword matching — ML boundary detection would be more robust
- Feedback stats fetch hits the GitHub API on every load — needs a TTL cache
- No rate limiting on the Streamlit app — would need middleware in production
- FAISS index is rebuilt manually — production would auto-rebuild on rubric changes

The pipeline architecture, prompt versioning system, feedback loop, and input validation are all production patterns implemented correctly. The prompts themselves are v1.0 placeholders pending user testing data.

---

## Learnings

**On cascade inference:** Building this clarified why production AI systems route across models rather than using one model for everything. Cost control isn't just about price per token — it's about spending precision where precision matters and using speed where speed is enough.

**On RAG at small scale:** FAISS IndexFlatL2 with 20 vectors is exact search with sub-millisecond latency. The tendency to reach for approximate search or managed vector databases at every scale is a mistake. Match the tool to the problem size.

**On explainability as a design constraint:** Deciding early that every verdict must name a specific pattern forced better prompt engineering. "This looks AI" is not a useful output. "This sentence uses a mechanical transition pattern" is. The constraint improved the product.

**On feedback loops:** Collecting feedback with prompt version labels from day one means the improvement cycle is measurable. Without version labels, you can't know whether a prompt change helped or hurt.

**On honest product scoping:** The hardest decisions were what to cut. Novelty checking, full-paper evaluation, a recommendation engine — all scoped out because they couldn't be done reliably with the available tools. A tool that does three things well and explains them clearly is more useful than a tool that does ten things poorly.

---

*Built by Sruthilaya — [LinkedIn](https://www.linkedin.com/in/sruthilaya-sundaram-306/)*