import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
MODEL_FAST = os.getenv("GEMINI_MODEL_FAST", "gemini-3.5-flash-lite")


def call_llm(prompt, fast=False):
    model = MODEL_FAST if fast else MODEL
    response = _client.models.generate_content(model=model, contents=prompt)
    return response.text
