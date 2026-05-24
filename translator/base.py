from abc import ABC, abstractmethod


class TranslationEngine(ABC):
    @abstractmethod
    def translate(self, text, source_lang, target_lang):
        pass

    def start(self):
        pass

    def stop(self):
        pass
