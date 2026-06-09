from __future__ import annotations

import json
import os
import time
from typing import Any
import dotenv

try:
    from google import genai
    from google.genai import types
    from google.genai.errors import APIError
except ImportError:
    genai = None
    types = None
    APIError = Exception

dotenv.load_dotenv()


class MangaTranslationEngine:
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        """
        Initializes the Gemini client using environment variables.
        """
        if genai is None or types is None:
            raise ImportError(
                "google-genai is required. Please run: pip install google-genai"
            )

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables.")

        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        GLOSSARY = {
            "達坂さん": "Aisaka-san",
            "逢坂さん": "Aisaka-san",
            "高須君": "Takasu-kun",
            "竜児": "Ryuuji",
        }

        self.system_prompt = (
            "You are an expert Japanese-to-English manga scanlation translator.\n"
            "Translate the provided list of sequential speech bubble texts.\n\n"
            "Guidelines:\n"
            "1. Maintain the natural flow, emotional intensity, and character voices of the scene.\n"
            "2. Resolve missing pronouns by analyzing the reading sequence flow.\n"
            "3. Keep translations concise so they fit comfortably inside bubble boundaries.\n"
            f"4. STRICTLY adhere to this terminology glossary mapping: {json.dumps(GLOSSARY, ensure_ascii=False)}\n"
            "5. Return the output STRICTLY as a valid JSON array matching the exact input structure, "
            "replacing the text with English. Do not add markdown code blocks or prose."
        )

    def translate_page_bubbles(
        self,
        bubble_metadata: list[dict[str, Any]],
        max_retries: int = 5,
        initial_delay: float = 2.0,
    ) -> list[dict[str, Any]]:
        """
        Sends sequential bubble data to the Gemini API with automatic exponential backoff
        retries to handle 503 server demand spikes gracefully.
        """
        if not bubble_metadata:
            return []

        input_data_str = json.dumps(bubble_metadata, ensure_ascii=False, indent=2)
        delay = initial_delay

        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=input_data_str,
                    config=types.GenerateContentConfig(
                        system_instruction=self.system_prompt,
                        response_mime_type="application/json",
                    ),
                )

                if not response.text:
                    raise ValueError("Received an empty response from the Gemini API.")

                return json.loads(response.text)

            except (APIError, Exception) as e:
                error_msg = str(e)
                is_server_busy = (
                    "503" in error_msg
                    or "high demand" in error_msg.lower()
                    or "UNAVAILABLE" in error_msg
                )

                if is_server_busy and attempt < max_retries - 1:
                    print(
                        f"[Attempt {attempt + 1}/{max_retries}] Gemini Server busy (503). Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                    delay *= 2
                else:
                    print(f"Gemini API translation pipeline failed permanently: {e}")
                    return bubble_metadata

        return bubble_metadata


if __name__ == "__main__":
    mock_sorted_pipeline_data = [
        {
            "bubble_id": 0,
            "bbox": {"x1": 365, "y1": 49, "x2": 409, "y2": 138},
            "original_text": "きゃっ",
            "area_px": 2493,
        },
        {
            "bubble_id": 1,
            "bbox": {"x1": 464, "y1": 244, "x2": 666, "y2": 585},
            "original_text": "勝手な事ほざいてんじゃないわよ！！",
            "area_px": 40638,
        },
        {
            "bubble_id": 2,
            "bbox": {"x1": 524, "y1": 757, "x2": 660, "y2": 914},
            "original_text": "いきなりどうしちゃったの逢坂さん．．．こわいっ",
            "area_px": 15358,
        },
    ]

    translator = MangaTranslationEngine()

    print("Dispatching payload to Gemini...")
    results = translator.translate_page_bubbles(mock_sorted_pipeline_data)

    print("\nFinal API Translated Payload Output:")
    print(json.dumps(results, ensure_ascii=False, indent=2))
