# translation.py
import os
import requests
from config import Config


class TranslationService:
    def __init__(self):
        self.api_key = Config.DEEPL_API_KEY
        self.url = "https://api-free.deepl.com/v2/translate"
        self.cache = {}

    def translate(
        self, text: str, source_lang: str = None, target_lang: str = "SV"
    ) -> str:
        """
        Translate text from source_lang to target_lang using DeepL.
        Returns the translated text or raises an exception if it fails.
        """
        if not text:
            return ""

        # Check if we have a valid API key
        if not self.api_key:
            raise ValueError(
                "DeepL API key is not set. Please configure DEEPL_API_KEY."
            )

        cache_key = (text, source_lang or "", target_lang)
        if cache_key in self.cache:
            return self.cache[cache_key]

        data = {"auth_key": self.api_key, "text": text, "target_lang": target_lang}
        if source_lang:
            data["source_lang"] = source_lang

        resp = requests.post(self.url, data=data)
        if resp.status_code != 200:
            raise RuntimeError(
                f"DeepL Translation failed: {resp.status_code} - {resp.text}"
            )

        result_json = resp.json()
        if "translations" not in result_json or not result_json["translations"]:
            raise RuntimeError("DeepL response is missing 'translations' data.")

        translated = result_json["translations"][0]["text"]
        self.cache[cache_key] = translated
        return translated
