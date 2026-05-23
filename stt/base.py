from abc import ABC, abstractmethod


class STTEngine(ABC):
    def __init__(self, on_hypothesis=None, on_recognition=None, on_error=None):
        self.on_hypothesis = on_hypothesis
        self.on_recognition = on_recognition
        self.on_error = on_error
        self.is_listening = False

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    @staticmethod
    def map_language(source_lang, engine_type, model_size="small"):
        lang = source_lang.lower().strip()

        if engine_type == "google":
            if "chinese" in lang or "zh" in lang or "cn" in lang:
                return "zh-CN"
            elif "spanish" in lang or "es" in lang:
                return "es-ES"
            elif "japanese" in lang or "ja" in lang or "jp" in lang:
                return "ja-JP"
            elif "german" in lang or "de" in lang:
                return "de-DE"
            elif "french" in lang or "fr" in lang:
                return "fr-FR"
            return "en-US"

        elif engine_type == "vosk":
            if "chinese" in lang or "zh" in lang or "cn" in lang:
                return "vosk-model-small-cn-0.22" if model_size == "small" else "vosk-model-cn-0.22"
            elif "spanish" in lang or "es" in lang:
                return "vosk-model-small-es-0.42" if model_size == "small" else "vosk-model-es-0.42"
            elif "japanese" in lang or "ja" in lang or "jp" in lang:
                return "vosk-model-small-ja-0.22" if model_size == "small" else "vosk-model-ja-0.22"
            elif "german" in lang or "de" in lang:
                return "vosk-model-small-de-0.15" if model_size == "small" else "vosk-model-de-0.21"
            elif "french" in lang or "fr" in lang:
                return "vosk-model-small-fr-0.22" if model_size == "small" else "vosk-model-fr-0.22"
            return "vosk-model-small-en-us-0.15" if model_size == "small" else "vosk-model-en-us-0.22"

        elif engine_type == "whisper":
            if "chinese" in lang or "zh" in lang or "cn" in lang:
                return "zh"
            elif "spanish" in lang or "es" in lang:
                return "es"
            elif "japanese" in lang or "ja" in lang or "jp" in lang:
                return "ja"
            elif "german" in lang or "de" in lang:
                return "de"
            elif "french" in lang or "fr" in lang:
                return "fr"
            return "en"

        return None

    @staticmethod
    def map_nvidia(source_lang):
        lang = source_lang.lower().strip()
        if "chinese" in lang or "zh" in lang or "cn" in lang:
            return "9add5ef7-322e-47e0-ad7a-5653fb8d259b", "zh-CN"
        elif "spanish" in lang or "es" in lang:
            return "a9eeee8f-b509-4712-b19d-194361fa5f31", "es-US"
        return "9add5ef7-322e-47e0-ad7a-5653fb8d259b", "zh-CN"
