MOCK_STAGE1_RESULTS = [
    {"id": "C01", "status": "MET",     "confidence": 1.00, "evidence": "This paper investigates automated essay scoring"},
    {"id": "C02", "status": "PARTIAL", "confidence": 0.60, "evidence": "research questions implied but not explicit"},
    {"id": "C03", "status": "MET",     "confidence": 1.00, "evidence": "Prior work includes Shermis 2013 and Taghipour 2016"},
    {"id": "C04", "status": "MET",     "confidence": 1.00, "evidence": "addresses the gap by applying pre-trained language models"},
    {"id": "C05", "status": "MET",     "confidence": 1.00, "evidence": "We fine-tuned BERT-base on the ASAP dataset"},
    {"id": "C06", "status": "PARTIAL", "confidence": 0.60, "evidence": "methodology described but justification weak"},
    {"id": "C07", "status": "MET",     "confidence": 1.00, "evidence": "accuracy and quadratic weighted kappa (QWK)"},
    {"id": "C08", "status": "MET",     "confidence": 1.00, "evidence": "ASAP dataset, grades 7-10, split 80/10/10"},
    {"id": "C09", "status": "MET",     "confidence": 1.00, "evidence": "baseline SVM model which achieved 79%"},
    {"id": "C10", "status": "MET",     "confidence": 1.00, "evidence": "87% accuracy and QWK of 0.82"},
    {"id": "C11", "status": "MISSING", "confidence": 0.00, "evidence": "none found"},
    {"id": "C12", "status": "PARTIAL", "confidence": 0.60, "evidence": "limitations not explicitly discussed"},
    {"id": "C13", "status": "MISSING", "confidence": 0.00, "evidence": "none found"},
    {"id": "C14", "status": "MET",     "confidence": 1.00, "evidence": "demonstrates transformers are effective for AES"},
    {"id": "C15", "status": "MET",     "confidence": 1.00, "evidence": "Our work differs in using transformer architecture"},
    {"id": "C16", "status": "PARTIAL", "confidence": 0.80, "evidence": "results reported but interpretation thin"},
    {"id": "C17", "status": "MET",     "confidence": 1.00, "evidence": "Future work will explore larger models"},
    {"id": "C18", "status": "MET",     "confidence": 1.00, "evidence": "abstract covers problem, approach, results"},
    {"id": "C19", "status": "MET",     "confidence": 1.00, "evidence": "paper is written clearly"},
    {"id": "C20", "status": "MET",     "confidence": 1.00, "evidence": "references follow consistent format"},
]

MOCK_STAGE2_RESULTS = [
    {"id": "C01", "status": "MET",     "confidence": 1.00, "evidence": "This paper investigates automated essay scoring"},
    {"id": "C02", "status": "MISSING", "confidence": 0.80, "evidence": "no explicit research questions stated"},
    {"id": "C03", "status": "MET",     "confidence": 1.00, "evidence": "Prior work includes Shermis 2013 and Taghipour 2016"},
    {"id": "C04", "status": "MET",     "confidence": 1.00, "evidence": "addresses the gap by applying pre-trained language models"},
    {"id": "C05", "status": "MET",     "confidence": 1.00, "evidence": "We fine-tuned BERT-base on the ASAP dataset"},
    {"id": "C06", "status": "PARTIAL", "confidence": 0.60, "evidence": "methodology described but justification weak"},
    {"id": "C07", "status": "MET",     "confidence": 1.00, "evidence": "accuracy and quadratic weighted kappa (QWK)"},
    {"id": "C08", "status": "MET",     "confidence": 1.00, "evidence": "ASAP dataset, grades 7-10, split 80/10/10"},
    {"id": "C09", "status": "MET",     "confidence": 1.00, "evidence": "baseline SVM model which achieved 79%"},
    {"id": "C10", "status": "MET",     "confidence": 1.00, "evidence": "87% accuracy and QWK of 0.82"},
    {"id": "C11", "status": "MISSING", "confidence": 0.90, "evidence": "none found"},
    {"id": "C12", "status": "MISSING", "confidence": 0.80, "evidence": "no explicit limitations section"},
    {"id": "C13", "status": "MISSING", "confidence": 0.90, "evidence": "none found"},
    {"id": "C14", "status": "MET",     "confidence": 1.00, "evidence": "demonstrates transformers are effective for AES"},
    {"id": "C15", "status": "MET",     "confidence": 1.00, "evidence": "Our work differs in using transformer architecture"},
    {"id": "C16", "status": "PARTIAL", "confidence": 0.70, "evidence": "results reported but interpretation thin"},
    {"id": "C17", "status": "MET",     "confidence": 1.00, "evidence": "Future work will explore larger models"},
    {"id": "C18", "status": "MET",     "confidence": 1.00, "evidence": "abstract covers problem, approach, results"},
    {"id": "C19", "status": "MET",     "confidence": 1.00, "evidence": "paper is written clearly"},
    {"id": "C20", "status": "MET",     "confidence": 1.00, "evidence": "references follow consistent format"},
]

MOCK_FIXES = {
    "C02": {
        "what_is_missing": "No explicit research questions or hypotheses are stated anywhere in the paper.",
        "how_to_fix": "Add a numbered list of research questions at the end of the introduction section.",
        "example_fix": "This study addresses: (1) Can BERT achieve human-level accuracy on AES? (2) Does domain adaptation improve cross-prompt generalization?"
    },
    "C06": {
        "what_is_missing": "The choice of fine-tuning BERT is not justified over alternative approaches.",
        "how_to_fix": "Add one sentence explaining why BERT was chosen over other transformer models for this task.",
        "example_fix": "We selected BERT-base over GPT-2 due to its bidirectional context modeling, which better captures essay coherence."
    },
    "C11": {
        "what_is_missing": "No statistical significance tests are reported for the accuracy improvement claims.",
        "how_to_fix": "Add a paired t-test result comparing your model to the SVM baseline.",
        "example_fix": "The improvement over the SVM baseline was statistically significant (paired t-test, p < 0.01, n=1000)."
    },
    "C12": {
        "what_is_missing": "No limitations section exists and generalizability constraints are not discussed.",
        "how_to_fix": "Add a short limitations paragraph acknowledging dataset scope and potential biases.",
        "example_fix": "This study is limited to English essays from grades 7-10; generalizability to other languages or grade levels requires further validation."
    },
    "C13": {
        "what_is_missing": "Ethical implications of automated essay scoring are not addressed.",
        "how_to_fix": "Add a sentence acknowledging potential bias in automated scoring and its impact on students.",
        "example_fix": "Automated scoring systems may reflect biases present in training data; we recommend human oversight for high-stakes assessment decisions."
    },
    "C16": {
        "what_is_missing": "Results are reported but not interpreted in the context of the research goals.",
        "how_to_fix": "Add a sentence connecting the QWK score to what it means for practical essay scoring use.",
        "example_fix": "A QWK of 0.82 indicates strong agreement with human raters, suggesting the model is suitable for formative feedback applications."
    },
}

MOCK_STAGE3_RESULTS = []
for r in MOCK_STAGE2_RESULTS:
    row = dict(r)
    if r["id"] in MOCK_FIXES:
        row["fix"] = MOCK_FIXES[r["id"]]
    else:
        row["fix"] = None
    MOCK_STAGE3_RESULTS.append(row)