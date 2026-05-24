from openai import OpenAI
from config import config
from .base import TranslationEngine


class CloudAPIEngine(TranslationEngine):
    def start(self):
        self.client = OpenAI(base_url=config.base_url, api_key=config.api_key)

    def translate(self, text, source_lang, target_lang):
        if "hy-mt" in config.model.lower():
            system_prompt = "You are a professional simultaneous interpreter. Translate the text accurately. Output ONLY the translated text without explanations."
            user_content = f"Translate the following text from {source_lang} to {target_lang}:\n\n{text}"
        else:
            system_prompt = (
                f"You are a professional real-time simultaneous interpreter. "
                f"Translate the following text from {source_lang} to {target_lang}. "
                f"Output ONLY the direct translation. Do not add any introductory phrases, explanations, "
                f"notes, quote marks, or markdown blocks. Keep the exact meaning, tone, and punctuation of the original text."
            )
            user_content = text

        response = self.client.chat.completions.create(
            model=config.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=0.3,
            timeout=10.0,
        )
        return response.choices[0].message.content.strip()
