import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import streamlit as st
from dotenv import load_dotenv
load_dotenv(".env")

from app.sections import split_submission
from app.detection import run_ai_detection
from app.rubric_custom import run_all_custom_checks, validate_custom_check
from app.feedback import generate_session_id, build_session_data, post_feedback_to_github, fetch_feedback_stats
from app.prompts import AI_SENTENCE_STRUCTURE_VERSION, AI_REASONING_DEPTH_VERSION, CUSTOM_RUBRIC_CHECK_VERSION

st.set_page_config(page_title="Rubrix", page_icon="📋", layout="wide", initial_sidebar_state="expanded")

# ── CSS ──────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:ital,wght@0,400;0,500;1,400&family=Fraunces:ital,wght@0,300;0,400;1,300&display=swap');

html, body, [class*="css"] { font-family: 'DM Mono', monospace; }
#MainMenu, footer, .stDeployButton { display: none !important; }

/* ── Color tokens — dark default, light via media query ── */
:root {
    --bg:           #0e0e0e;
    --bg2:          #141414;
    --bg3:          #1a1a1a;
    --border:       #242424;
    --border-accent:#c9a84c33;
    --text:         #d8d6cf;
    --text2:        #777;
    --text3:        #444;
    --accent:       #c9a84c;
    --accent-dim:   #c9a84c0d;
    --flag-bg:      #0e0e0e;
    --flag-border:  #3a1a1a;
    --flag-text:    #c47a7a;
    --ok-bg:        #0e0e0e;
    --ok-border:    #1a3a24;
    --ok-text:      #5a9a72;
    --warn-bg:      #0e0e0e;
    --warn-border:  #3a2e00;
    --warn-text:    #c9a84c;
    --card-shadow:  0 1px 2px rgba(0,0,0,0.3);
}

@media (prefers-color-scheme: light) {
:root {
        --bg:           #fafaf7;
        --bg2:          #f5f4ef;
        --bg3:          #eeede7;
        --border:       #e0ddd5;
        --border-accent:#b8860b22;
        --text:         #1a1a18;
        --text2:        #666;
        --text3:        #aaa;
        --accent:       #b8860b;
        --accent-dim:   #b8860b08;
        --flag-bg:      #fafaf7;
        --flag-border:  #e8c4c4;
        --flag-text:    #7a3a3a;
        --ok-bg:        #fafaf7;
        --ok-border:    #a8d4b8;
        --ok-text:      #2a6a44;
        --warn-bg:      #fafaf7;
        --warn-border:  #d4b870;
        --warn-text:    #7a5a00;
        --card-shadow:  0 1px 2px rgba(0,0,0,0.05);
    }
}

/* ── Typography ── */
h1 {
    font-family: 'Fraunces', serif !important;
    font-size: 2rem !important;
    font-weight: 300 !important;
    letter-spacing: -0.03em;
    color: var(--text) !important;
}
h2, h3 {
    font-family: 'DM Mono', monospace !important;
    font-weight: 500 !important;
    font-size: 0.82rem !important;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--text2) !important;
    border-bottom: 1px solid var(--border);
    padding-bottom: 6px;
    margin-top: 1.8rem !important;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: #080808 !important;
    border-right: 1px solid #1e1e1e !important;
}
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] div,
section[data-testid="stSidebar"] .stMarkdown {
    color: #888 !important;
    font-size: 0.75rem !important;
}
section[data-testid="stSidebar"] input,
section[data-testid="stSidebar"] textarea {
    background: #111 !important;
    border: 1px solid #252525 !important;
    color: #ccc !important;
    font-size: 0.75rem !important;
    border-radius: 2px !important;
    font-family: 'DM Mono', monospace !important;
}
section[data-testid="stSidebar"] .stButton > button {
    background: #111 !important;
    border: 1px solid #2a2a2a !important;
    color: #888 !important;
    font-size: 0.72rem !important;
    border-radius: 2px !important;
    width: 100%;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    border-color: var(--accent) !important;
    color: var(--accent) !important;
}

/* ── Primary button ── */
.stButton > button[kind="primary"] {
    background: var(--accent) !important;
    color: #000 !important;
    border: none !important;
    border-radius: 2px !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.08em;
    padding: 10px 22px !important;
    text-transform: uppercase;
    box-shadow: 0 0 12px var(--accent-dim);
}
.stButton > button[kind="primary"]:hover {
    opacity: 0.88 !important;
    box-shadow: 0 0 20px var(--border-accent) !important;
}
.stButton > button:not([kind="primary"]) {
    background: var(--bg2) !important;
    border: 1px solid var(--border) !important;
    color: var(--text2) !important;
    border-radius: 2px !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.75rem !important;
}
.stButton > button:not([kind="primary"]):hover {
    border-color: var(--accent) !important;
    color: var(--accent) !important;
}

/* ── Cards ── */
.rubrix-card {
    border: 1px solid var(--border);
    border-radius: 3px;
    padding: 14px 16px;
    background: transparent;
    margin-bottom: 8px;
}
.rubrix-card-accent {
    border: 1px solid var(--border-accent);
    border-radius: 3px;
    padding: 14px 16px;
    background: transparent;
    margin-bottom: 8px;
}
.check-card {
    border: 1px solid var(--border);
    border-radius: 3px;
    padding: 12px 14px;
    background: transparent;
    height: 100%;
}
.check-card:hover {
    border-color: var(--border-accent);
}

/* ── Badges ── */
.badge {
    display: inline-block;
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem;
    font-weight: 500;
    padding: 3px 9px;
    border-radius: 2px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}
.badge-ai      { background: var(--flag-bg);  color: var(--flag-text); border: 1px solid var(--flag-border); }
.badge-maybe   { background: var(--warn-bg);  color: var(--warn-text); border: 1px solid var(--warn-border); }
.badge-human   { background: var(--ok-bg);    color: var(--ok-text);   border: 1px solid var(--ok-border);   }
.badge-met     { background: var(--ok-bg);    color: var(--ok-text);   border: 1px solid var(--ok-border);   }
.badge-partial { background: var(--warn-bg);  color: var(--warn-text); border: 1px solid var(--warn-border); }
.badge-missing { background: var(--flag-bg);  color: var(--flag-text); border: 1px solid var(--flag-border); }
.badge-beta    { background: transparent;     color: var(--text3);     border: 1px solid var(--border);      }
.badge-unknown { background: var(--bg3);      color: var(--text3);     border: 1px solid var(--border);      }

/* ── Flagged sentence highlight ── */
.flagged-sentence {
    border-left: 2px solid var(--flag-border);
    background: transparent;
    padding: 5px 12px;
    font-size: 0.77rem;
    color: var(--text2);
    border-radius: 0;
    margin: 4px 0;
    font-style: italic;
    line-height: 1.55;
}

/* ── Section nav label ── */
.section-nav {
    font-size: 0.68rem;
    color: var(--text3);
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 6px;
}

/* ── Check labels ── */
.check-label {
    font-size: 0.65rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--text3);
    margin-bottom: 7px;
}
.check-reason {
    font-size: 0.72rem;
    color: var(--text2);
    margin-top: 7px;
    line-height: 1.55;
    border-top: 1px solid var(--border);
    padding-top: 6px;
}
.conf-text {
    font-size: 0.65rem;
    color: var(--text3);
    margin-top: 3px;
}

/* ── Overall verdict card ── */
.verdict-bar {
    border: 1px solid var(--border);
    border-left: 2px solid var(--border-accent);
    border-radius: 0 3px 3px 0;
    padding: 10px 16px;
    background: transparent;
    margin-bottom: 14px;
    display: flex;
    align-items: center;
    gap: 12px;
}

/* ── Missing block ── */
.missing-block {
    border-left: 2px solid var(--warn-border);
    background: transparent;
    border-radius: 0;
    padding: 8px 14px;
    margin: 6px 0;
}
.missing-title {
    font-size: 0.63rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text3);
    margin-bottom: 3px;
}
.missing-text {
    font-size: 0.76rem;
    color: var(--text2);
    line-height: 1.5;
}
.evidence-text {
    font-size: 0.68rem;
    color: var(--text3);
    margin-top: 5px;
}

/* ── Metrics ── */
[data-testid="stMetric"] {
    background: var(--bg2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 3px !important;
    padding: 12px 16px !important;
    box-shadow: var(--card-shadow);
}
[data-testid="stMetricLabel"] {
    font-size: 0.65rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    color: var(--text3) !important;
}
[data-testid="stMetricValue"] {
    font-size: 1.6rem !important;
    font-weight: 500 !important;
    color: var(--accent) !important;
}

/* ── Expander ── */
.streamlit-expanderHeader {
    font-size: 0.75rem !important;
    background: var(--bg2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 2px !important;
    color: var(--text2) !important;
}

/* ── Progress ── */
.stProgress > div > div {
    background: var(--accent) !important;
    border-radius: 1px !important;
}
.stProgress > div {
    background: var(--bg3) !important;
    border-radius: 1px !important;
    height: 2px !important;
}

/* ── Divider ── */
hr {
    border: none !important;
    border-top: 1px solid var(--border) !important;
    margin: 20px 0 !important;
}

/* ── Inputs ── */
.stTextArea textarea {
    border-radius: 2px !important;
    font-size: 0.80rem !important;
    font-family: 'DM Mono', monospace !important;
    border-color: var(--border) !important;
    background: var(--bg2) !important;
    color: var(--text) !important;
}
.stTextInput input {
    border-radius: 2px !important;
    font-size: 0.80rem !important;
    font-family: 'DM Mono', monospace !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab"] {
    font-size: 0.75rem !important;
    font-family: 'DM Mono', monospace !important;
    letter-spacing: 0.06em !important;
}
.stTabs [data-baseweb="tab-highlight"] {
    background: var(--accent) !important;
    height: 2px !important;
}

/* ── Radio ── */
.stRadio label { font-size: 0.75rem !important; }

/* ── Caption ── */
.stCaption { font-size: 0.70rem !important; color: var(--text3) !important; }

/* ── Alerts ── */
.stAlert {
    border-radius: 2px !important;
    font-size: 0.78rem !important;
    font-family: 'DM Mono', monospace !important;
}

/* ── Toggle ── */
.stToggle label { font-size: 0.75rem !important; }

/* ── Info box custom ── */
.info-box {
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    background: var(--accent-dim);
    border-radius: 0 3px 3px 0;
    padding: 10px 14px;
    font-size: 0.75rem;
    color: var(--text2);
    margin: 8px 0;
    line-height: 1.5;
}

/* ── Section detected list ── */
.section-item {
    font-size: 0.73rem;
    color: var(--text2);
    padding: 3px 0;
    border-bottom: 1px solid var(--border);
}
.section-item:last-child { border-bottom: none; }
</style>""", unsafe_allow_html=True)

# ── Theme toggle ─────────────────────────────────────────
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

# ── Session state ────────────────────────────────────────
for key, default in [
    ("session_id", None),
    ("ready", False),
    ("current_section", 0),
    ("all_sections", []),
    ("section_results", []),
    ("feedback_submitted", False),
]:
    if key not in st.session_state:
        st.session_state[key] = default

if st.session_state.session_id is None:
    st.session_state.session_id = generate_session_id()

# ── Default custom checks ────────────────────────────────
DEFAULT_CUSTOM_CHECKS = [
    {
        "category": "Clarity of Argument",
        "description": "The main argument is clearly stated and consistently supported throughout the section."
    },
    {
        "category": "Evidence Quality",
        "description": "Claims are supported by specific data, citations, or examples rather than general assertions."
    }
]

# ── Sidebar ──────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        "<div style='font-family:Fraunces,serif;font-size:1.3rem;font-weight:300;"
        "color:#e8e6df;letter-spacing:-0.02em;margin-bottom:2px'>rubrix</div>"
        "<div style='font-size:0.68rem;color:#555;letter-spacing:0.1em;"
        "text-transform:uppercase'>research checker · beta</div>",
        unsafe_allow_html=True
    )
    st.markdown("---")

    use_mock = st.toggle("Mock mode", value=False, help="Run without API calls")

    st.markdown("---")
    st.markdown(
        "<div style='font-size:0.68rem;text-transform:uppercase;"
        "letter-spacing:0.1em;color:#555;margin-bottom:8px'>Custom checks</div>",
        unsafe_allow_html=True
    )
    st.caption("Describe what to check. Max 200 chars. One criterion each.")

    custom_checks = []
    for i, default in enumerate(DEFAULT_CUSTOM_CHECKS):
        st.markdown(
            f"<div style='font-size:0.65rem;color:#444;text-transform:uppercase;"
            f"letter-spacing:0.08em;margin-top:10px'>Check {i+1}</div>",
            unsafe_allow_html=True
        )
        category = st.text_input(
            f"Category {i+1}",
            value=default["category"],
            key=f"cat_{i}",
            max_chars=50,
            label_visibility="collapsed"
        )
        description = st.text_area(
            f"Description {i+1}",
            value=default["description"],
            key=f"desc_{i}",
            max_chars=200,
            height=65,
            label_visibility="collapsed"
        )
        validation = validate_custom_check(category, description)
        if not validation["valid"]:
            st.error(validation["error"])
        else:
            st.markdown(
                "<div style='font-size:0.65rem;color:#4a7c59'>✓ valid</div>",
                unsafe_allow_html=True
            )
            custom_checks.append({"category": category, "description": description})

    st.markdown("---")
    st.markdown(
        "<div style='font-size:0.68rem;text-transform:uppercase;"
        "letter-spacing:0.1em;color:#555;margin-bottom:8px'>Impact</div>",
        unsafe_allow_html=True
    )
    if st.button("Load stats", use_container_width=True):
        with st.spinner(""):
            stats = fetch_feedback_stats()
        if stats.get("total", 0) > 0:
            st.metric("Sessions", stats["total"])
            st.metric("AI accurate", f"{stats['ai_accurate_pct']}%")
            st.metric("Fixes useful", f"{stats['fix_useful_pct']}%")
        else:
            st.caption("No feedback collected yet.")

# ── Header ───────────────────────────────────────────────
col_h, col_badge = st.columns([4, 1])
with col_h:
    st.markdown(
        "<h1>Paper checker</h1>"
        "<p style='font-size:0.78rem;color:#888;margin-top:-8px;"
        "font-family:DM Mono,monospace;letter-spacing:0.04em'>"
        "AI detection · custom rubric · section-by-section</p>",
        unsafe_allow_html=True
    )
with col_badge:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(
        "<span class='badge badge-beta'>BETA</span>",
        unsafe_allow_html=True
    )

st.markdown("---")

# ── INPUT ────────────────────────────────────────────────
if not st.session_state.ready:
    st.markdown(
        "<div class='section-nav'>Input — text only, no images</div>",
        unsafe_allow_html=True
    )

    tab1, tab2 = st.tabs(["Paste text", "Upload PDF"])
    submission_text = ""

    with tab1:
        submission_text = st.text_area(
            "Submission",
            height=200,
            placeholder="Paste your research paper, project document, or report here...",
            label_visibility="collapsed",
            key="paste_input"
        )
        if submission_text:
            st.caption(f"{len(submission_text):,} characters")

    with tab2:
        uploaded = st.file_uploader("PDF", type=["pdf"], label_visibility="collapsed")
        if uploaded:
            import PyPDF2
            reader = PyPDF2.PdfReader(uploaded)
            pages = [p.extract_text() for p in reader.pages if p.extract_text()]
            submission_text = "\n".join(pages)
            st.caption(f"{len(reader.pages)} pages · {len(submission_text):,} chars")

    if submission_text:
        split_result = split_submission(submission_text)
        sections = split_result["sections"]
        st.session_state.all_sections = sections

        st.markdown("---")
        st.markdown(
            "<div class='section-nav'>Detected sections</div>",
            unsafe_allow_html=True
        )
        for s in sections:
            st.markdown(
                f"<div style='font-size:0.75rem;color:#888;padding:2px 0'>"
                f"· {s['heading']} <span style='color:#555'>({s['tokens']} tokens)</span></div>",
                unsafe_allow_html=True
            )
        if split_result["capped"]:
            st.markdown(
                f"<div style='font-size:0.72rem;color:#666;margin-top:4px'>"
                f"+ {split_result['total_found'] - split_result['total_returned']} more sections · paid plan</div>",
                unsafe_allow_html=True
            )

        st.markdown("<br>", unsafe_allow_html=True)
        col_run, col_info = st.columns([1, 3])
        with col_run:
            run_disabled = len(custom_checks) == 0
            if st.button("run →", type="primary", disabled=run_disabled, use_container_width=True):
                st.session_state.ready = True
                st.session_state.current_section = 0
                st.session_state.section_results = []
                st.session_state.feedback_submitted = False
                st.rerun()
        with col_info:
            if run_disabled:
                st.warning("Fix custom check errors in sidebar first.")
            else:
                st.caption(f"Will evaluate {len(sections)} section{'s' if len(sections) != 1 else ''}  ·  AI detection + {len(custom_checks)} custom checks")


# ── PIPELINE ─────────────────────────────────────────────
if st.session_state.ready and st.session_state.all_sections:
    sections = st.session_state.all_sections
    idx = st.session_state.current_section
    MAX_FREE = 3

    if idx < len(sections) and idx < MAX_FREE:
        section = sections[idx]

        # Progress
        st.progress((idx) / min(len(sections), MAX_FREE))
        st.markdown(
            f"<div class='section-nav'>"
            f"Section {idx+1} of {min(len(sections), MAX_FREE)} · {section['heading']}"
            f"</div>",
            unsafe_allow_html=True
        )
        st.markdown("---")

        # Run checks
        with st.spinner("Running AI detection..."):
            if use_mock:
                ai_results = [{
                    "section_index": idx + 1,
                    "heading": section["heading"],
                    "overall_verdict": "likely_ai",
                    "average_confidence": 0.85,
                    "checks": [
                        {
                            "check": "pattern_scan",
                            "check_label": "Vocabulary patterns",
                            "check_description": "Flags documented AI writing patterns.",
                            "verdict": "likely_ai",
                            "confidence": 0.88,
                            "unique_phrases": ["furthermore", "it is worth noting"],
                            "flagged_sentences": [
                                "Furthermore, it is important to consider our approach.",
                                "It is worth noting this paper aims to facilitate evaluation."
                            ],
                            "reason": "Found 7 AI-associated patterns: furthermore, it is worth noting."
                        },
                        {
                            "check": "sentence_uniformity",
                            "check_label": "Sentence uniformity",
                            "check_description": "Checks sentence length variation and personal voice.",
                            "verdict": "likely_ai",
                            "confidence": 0.80,
                            "flagged_sentences": [
                                "This paper aims to investigate the utilization of transformer-based models."
                            ],
                            "reason": "Uniform sentence length and no first-person voice detected."
                        },
                        {
                            "check": "structural_tells",
                            "check_label": "Structural tells",
                            "check_description": "Checks for mechanical transitions and structural patterns.",
                            "verdict": "possibly_ai",
                            "confidence": 0.65,
                            "flagged_sentences": [
                                "The next section discusses the methodology in detail."
                            ],
                            "reason": "Mechanical transition detected: 'The next section discusses'."
                        }
                    ]
                }]
            else:
                ai_results = run_ai_detection([section])

        with st.spinner("Running custom checks..."):
            if use_mock:
                custom_results = [{
                    "section_index": 1,
                    "heading": section["heading"],
                    "checks": [
                        {
                            "category": c["category"],
                            "status": "PARTIAL",
                            "confidence": 0.65,
                            "evidence": "Some evidence present but incomplete.",
                            "what_is_missing": "The argument is stated but not consistently maintained."
                        }
                        for c in custom_checks
                    ]
                }]
            else:
                custom_results = run_all_custom_checks([section], custom_checks)

        # Store
        if len(st.session_state.section_results) <= idx:
            st.session_state.section_results.append({
                "section": section,
                "ai_results": ai_results,
                "custom_results": custom_results,
            })

        # ── AI Detection display ──────────────────────────
        st.markdown("### AI detection")
        st.markdown(
            "<div style='font-size:0.72rem;color:#666;margin-bottom:12px'>"
            "Three independent checks — vocabulary patterns (rule-based), "
            "sentence uniformity, and structural tells. Each verdict is explained."
            "</div>",
            unsafe_allow_html=True
        )

        for r in ai_results:
            verdict = r["overall_verdict"]
            badge_cls = "badge-ai" if verdict == "likely_ai" else "badge-maybe" if verdict == "possibly_ai" else "badge-human"
            verdict_label = verdict.replace("_", " ").upper()

            st.markdown(
                f"<div class='verdict-bar'>"
                f"<span class='badge {badge_cls}'>{verdict_label}</span>"
                f"<span style='font-size:0.72rem;color:var(--text3)'>"
                f"avg confidence {r['average_confidence']:.0%} · 3 independent checks</span>"
                f"</div>",
                unsafe_allow_html=True
            )


            # 3 check cards
            cols = st.columns(3)
            for j, check in enumerate(r.get("checks", [])):
                with cols[j]:
                    v = check.get("verdict", "unknown")
                    bc = "badge-ai" if v == "likely_ai" else "badge-maybe" if v == "possibly_ai" else "badge-human" if v == "likely_human" else "badge-beta"
                    st.markdown(
                        f"<div class='check-card'>"
                        f"<div class='check-label'>{check.get('check_label', check['check'])}</div>"
                        f"<span class='badge {bc}'>{v.replace('_', ' ').upper()}</span>"
                        f"<div class='conf-text'>conf {check.get('confidence', 0):.0%}</div>"
                        f"<div class='check-reason'>{check.get('reason', '')}</div>"
                        f"</div>",
                        unsafe_allow_html=True
                    )

            # Flagged sentences — highlighted inline
            all_flagged = []
            for check in r.get("checks", []):
                for sent in check.get("flagged_sentences", []):
                    if sent and sent not in all_flagged:
                        all_flagged.append(sent)

            if all_flagged:
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown(
                    "<div class='section-nav'>Flagged sentences</div>",
                    unsafe_allow_html=True
                )
                for sent in all_flagged[:5]:
                    st.markdown(
                        f"<div class='flagged-sentence'>{sent}</div>",
                        unsafe_allow_html=True
                    )
                st.markdown(
                    "<div style='font-size:0.68rem;color:#555;margin-top:6px'>"
                    "These sentences show patterns associated with AI-generated text. "
                    "Rewrite them in your own voice with specific evidence.</div>",
                    unsafe_allow_html=True
                )

        st.markdown("---")

        # ── Custom checks display ─────────────────────────
        st.markdown("### Custom checks")

        for section_result in custom_results:
            cols = st.columns(len(section_result["checks"]))
            for j, check in enumerate(section_result["checks"]):
                with cols[j]:
                    status = check["status"]
                    bc = "badge-met" if status == "MET" else "badge-partial" if status == "PARTIAL" else "badge-missing"
                    st.markdown(
                        f"<div class='check-card'>"
                        f"<div class='check-label'>{check['category']}</div>"
                        f"<span class='badge {bc}'>{status}</span>"
                        f"<div class='conf-text'>conf {check['confidence']:.0%}</div>"
                        f"</div>",
                        unsafe_allow_html=True
                    )

            # Show flagged/missing inline
        for check in section_result["checks"]:
            if check["status"] in ("PARTIAL", "MISSING") and check.get("what_is_missing"):
                evidence_html = (
                    f'<div style="font-size:0.72rem;color:#888;margin-top:6px">'
                    f'Evidence found: {check["evidence"]}</div>'
                ) if check.get("evidence") and check["evidence"] != "none found" else ""

                st.markdown(
                        f"<div class='missing-block'>"
                        f"<div class='missing-title'>{check['category']} — what's missing</div>"
                        f"<div class='missing-text'>{check['what_is_missing']}</div>"
                        f"{evidence_html}"
                        f"</div>",
                        unsafe_allow_html=True
                    )

        st.markdown("---")

        # ── Navigation ────────────────────────────────────
        next_idx = idx + 1
        if next_idx < len(sections) and next_idx < MAX_FREE:
            next_section = sections[next_idx]
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button(
                    f"next section →",
                    type="primary",
                    use_container_width=True
                ):
                    st.session_state.current_section += 1
                    st.rerun()
            with col2:
                st.caption(
                    f"Next: {next_section['heading']} · "
                    f"{MAX_FREE - next_idx} free evaluation{'s' if MAX_FREE - next_idx != 1 else ''} remaining"
                )
        elif next_idx >= MAX_FREE and next_idx < len(sections):
            st.markdown(
                "<div class='rubrix-card' style='text-align:center'>"
                "<div style='font-size:0.78rem;color:#888;margin-bottom:8px'>"
                "3 free section evaluations used.</div>"
                "<div style='font-size:0.72rem;color:#555'>"
                "This tool is in beta. Your feedback helps decide what gets built next.</div>"
                "</div>",
                unsafe_allow_html=True
            )
            st.markdown(
                "[⭐ Follow on GitHub](https://github.com/ussruthilaya-lang/Rubrix)"
            )
        else:
            st.success("All sections evaluated.")

    # ── Feedback ──────────────────────────────────────────
    if st.session_state.section_results and not st.session_state.feedback_submitted:
        st.markdown("---")
        st.markdown("### Feedback")
        st.caption("Helps improve the tool. Takes 20 seconds.")

        c1, c2 = st.columns(2)
        with c1:
            ai_accurate = st.radio(
                "AI detection accurate?",
                ["yes", "no", "not sure"],
                horizontal=True
            )
        with c2:
            fix_useful = st.radio(
                "Custom checks useful?",
                ["yes", "no", "not applicable"],
                horizontal=True
            )
        free_text = st.text_area(
            "Other feedback",
            placeholder="What worked? What didn't? What would you change?",
            height=65,
            label_visibility="collapsed"
        )

        if st.button("submit feedback →", type="primary"):
            all_ai = []
            for sr in st.session_state.section_results:
                all_ai.extend(sr["ai_results"])

            session_data = build_session_data(
                session_id=st.session_state.session_id,
                sections_evaluated=len(st.session_state.section_results),
                custom_checks=custom_checks,
                ai_results=all_ai,
                rubric_summary={"met": 0, "partial": 0, "missing": 0},
                stage3_used=False,
                prompt_versions={
                    "ai_sentence": AI_SENTENCE_STRUCTURE_VERSION,
                    "ai_reasoning": AI_REASONING_DEPTH_VERSION,
                    "custom_rubric": CUSTOM_RUBRIC_CHECK_VERSION
                }
            )
            with st.spinner(""):
                result = post_feedback_to_github(session_data, {
                    "ai_check_accurate": ai_accurate,
                    "fix_useful": fix_useful,
                    "free_text": free_text
                })
            st.session_state.feedback_submitted = True
            st.rerun()

    elif st.session_state.feedback_submitted:
        st.markdown("---")
        st.success("Feedback submitted. Thank you for helping improve Rubrix.")
        if st.button("← new evaluation", type="primary"):
            for key in ["ready", "current_section", "all_sections",
                       "section_results", "feedback_submitted", "session_id"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()