import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv(".env")
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

prompt = """Analyze this text for AI writing patterns.

SECTION HEADING: Abstract
SECTION TEXT:
It is worth noting that this paper aims to investigate transformer models.
Furthermore, it is important to consider our approach seeks to facilitate evaluation.

Respond with a JSON object with exactly these fields:
- verdict: "likely_ai", "possibly_ai", or "likely_human"
- confidence: float 0.0 to 1.0
- flagged_sentences: list of up to 3 flagged sentences
- reason: one sentence explaining the verdict

Respond with ONLY the JSON object, no other text."""

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": prompt}],
    max_tokens=400,
    temperature=0.1
)

print("=== RAW RESPONSE ===")
print(repr(response.choices[0].message.content))
print("=== FINISH REASON ===")
print(response.choices[0].finish_reason)
print("=== USAGE ===")
print(response.usage)