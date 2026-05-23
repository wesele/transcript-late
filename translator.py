import threading
import queue
import time
from openai import OpenAI
from config import config

class TranslationWorker:
    def __init__(self, on_translation_complete=None, on_error=None):
        """
        Background worker that processes translation requests.
        
        :param on_translation_complete: Callback function taking (original_text, translated_text)
        :param on_error: Callback function taking (error_message)
        """
        self.input_queue = queue.Queue()
        self.on_translation_complete = on_translation_complete
        self.on_error = on_error
        self.client = None
        self.thread = None
        self.running = False

    def start(self):
        """Start the background translation thread."""
        # Initialize OpenAI client with specified base URL and API Key
        self.client = OpenAI(
            base_url=config.base_url,
            api_key=config.api_key
        )
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop the background translation thread."""
        self.running = False
        # Put None in queue to unblock the worker thread
        self.input_queue.put(None)
        if self.thread:
            self.thread.join(timeout=1.0)

    def queue_translation(self, text, segment_id):
        """Queue a new text block for translation."""
        self.input_queue.put((text, segment_id))

    def _run(self):
        while self.running:
            try:
                item = self.input_queue.get()
                if item is None:
                    break
                
                original_text, segment_id = item
                if not original_text.strip():
                    self.input_queue.task_done()
                    continue

                # Run translation call
                translated_text = self._translate(original_text)
                
                if self.on_translation_complete:
                    self.on_translation_complete(original_text, translated_text, segment_id)
                
                self.input_queue.task_done()
            except Exception as e:
                if self.on_error:
                    self.on_error(str(e))
                # Avoid tight loop in case of persistent errors
                time.sleep(1.0)

    def _translate(self, text):
        """Synchronously calls translation model to translate the text."""
        # Bypass LLM if source and target are the same
        if config.source_lang.lower().strip() == config.target_lang.lower().strip():
            return text
            
        # Bypass LLM if using whisper-local (which outputs English) and target language is English
        is_whisper_local = config.stt_engine == "whisper-local"
        target_is_english = config.target_lang.lower().strip() in ["english", "en"]
        if is_whisper_local and target_is_english:
            return text

        # Determine source language for LLM prompt.
        # If whisper-local is used, the input text has already been translated to English.
        llm_source_lang = "English" if is_whisper_local else config.source_lang

        # Prepare system prompt to ensure precise translation and no filler text
        if "hy-mt" in config.model.lower():
            # Optimized prompt style for Tencent Hy-MT translation models
            system_prompt = "You are a professional simultaneous interpreter. Translate the text accurately. Output ONLY the translated text without explanations."
            user_content = f"Translate the following text from {llm_source_lang} to {config.target_lang}:\n\n{text}"
        else:
            system_prompt = (
                f"You are a professional real-time simultaneous interpreter. "
                f"Translate the following text from {llm_source_lang} to {config.target_lang}. "
                f"Output ONLY the direct translation. Do not add any introductory phrases, explanations, "
                f"notes, quote marks, or markdown blocks. Keep the exact meaning, tone, and punctuation of the original text."
            )
            user_content = text
        
        try:
            response = self.client.chat.completions.create(
                model=config.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.3,
                timeout=10.0 # Fast timeout for real-time responsiveness
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            # Return error description as part of the output so the user sees it in translation field
            return f"[Translation Error: {e}]"
