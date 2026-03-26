import os
from dotenv import load_dotenv
from groq import Groq
from openai import OpenAI

load_dotenv(".env")

def test_groq():
    print("→ Testing Groq...")
    api_key = os.getenv("GROQ_API_KEY")
    print(f"  key loaded: {'YES' if api_key else 'NO'}")
    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": "Say OK"}],
        max_tokens=5
    )
    result = response.choices[0].message.content.strip()
    print(f"✓ Groq ping OK — response: '{result}'")
    print(f"  model: {response.model}")

def test_openai():
    print("→ Testing OpenAI...")
    api_key = os.getenv("OPENAI_API_KEY")
    print(f"  key loaded: {'YES' if api_key else 'NO'}")
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say OK"}],
            max_tokens=5
        )
        result = response.choices[0].message.content.strip()
        print(f"✓ OpenAI ping OK — response: '{result}'")
        print(f"  model: {response.model}")
    except Exception as e:
        print(f"⚠ OpenAI not available: {e}")
        print(f"  → Add credits at platform.openai.com/settings/billing")
        print(f"  → Not needed until Task T-10, continuing...")

if __name__ == "__main__":
    print("=" * 40)
    print("SMOKE TEST — API connectivity")
    print("=" * 40)
    test_groq()
    test_openai()
    print("=" * 40)
    print("✓ All systems go. Ready to build.")
    print("=" * 40)