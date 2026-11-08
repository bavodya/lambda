import os
import time
from dotenv import load_dotenv
from google import genai

load_dotenv()

_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
MODEL_FAST = os.getenv("GEMINI_MODEL_FAST", "gemini-3.5-flash-lite")


def call_llm(prompt, fast=False, retries=3):
    model = MODEL_FAST if fast else MODEL
    last_error = None
    for attempt in range(retries):
        try:
            response = _client.models.generate_content(model=model, contents=prompt)
            return response.text
        except Exception as e:
            last_error = e
            wait = 5 * (attempt + 1)
            print(f"  LLM недоступна ({e}), повтор через {wait} с...")
            time.sleep(wait)
    raise last_error