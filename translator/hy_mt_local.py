import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from config import config
from .base import TranslationEngine


class HyMTLocalEngine(TranslationEngine):
    def __init__(self):
        self.tokenizer = None
        self.model = None

    def start(self):
        model_name = config.hy_mt_model
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            dtype=torch.bfloat16,
            trust_remote_code=True,
        )
        self.model.eval()

    def translate(self, text, source_lang, target_lang):
        if source_lang.lower().strip() == target_lang.lower().strip():
            return text

        prompt = f"Translate the following text into {target_lang}, without additional explanation:\n\n{text}"
        messages = [{"role": "user", "content": prompt}]
        inputs = self.tokenizer.apply_chat_template(
            messages, add_generation_prompt=True, return_tensors="pt"
        )

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=200,
                temperature=0.7,
                top_p=0.6,
                top_k=20,
                repetition_penalty=1.05,
            )

        response = self.tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True
        )
        return response.strip()
