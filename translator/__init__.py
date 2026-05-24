import threading
import queue
import time
from config import config
from .base import TranslationEngine
from .cloud_api import CloudAPIEngine
from .hy_mt_local import HyMTLocalEngine


def create_engine():
    if config.translation_engine == "cloud-api":
        return CloudAPIEngine()
    elif config.translation_engine == "hy-mt-local":
        return HyMTLocalEngine()
    raise ValueError(f"Unknown translation engine: {config.translation_engine}")


class TranslationWorker:
    def __init__(self, on_translation_complete=None, on_error=None):
        self.input_queue = queue.Queue()
        self.on_translation_complete = on_translation_complete
        self.on_error = on_error
        self.engine = None
        self.thread = None
        self.running = False

    def start(self):
        self.engine = create_engine()
        self.engine.start()
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        self.input_queue.put(None)
        self.engine.stop()
        if self.thread:
            self.thread.join(timeout=1.0)

    def queue_translation(self, text, segment_id):
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
                translated_text = self._translate(original_text)
                if self.on_translation_complete:
                    self.on_translation_complete(original_text, translated_text, segment_id)
                self.input_queue.task_done()
            except Exception as e:
                if self.on_error:
                    self.on_error(str(e))
                time.sleep(1.0)

    def _translate(self, text):
        if config.source_lang.lower().strip() == config.target_lang.lower().strip():
            return text

        is_whisper_local = config.stt_engine == "whisper-local"
        target_is_english = config.target_lang.lower().strip() in ("english", "en")
        if is_whisper_local and target_is_english:
            return text

        llm_source_lang = "English" if is_whisper_local else config.source_lang
        return self.engine.translate(text, llm_source_lang, config.target_lang)
