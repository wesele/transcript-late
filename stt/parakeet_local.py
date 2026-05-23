import numpy as np
import torch
from transformers import AutoModelForTDT, AutoProcessor
from ._segment_base import SegmentSTTEngine


class NvidiaLocalEngine(SegmentSTTEngine):
    MODEL_NAME = "nvidia/parakeet-tdt-0.6b-v3"

    def __init__(self, on_hypothesis=None, on_recognition=None, on_error=None):
        super().__init__(on_hypothesis, on_recognition, on_error)
        self.model = None
        self.processor = None

    def _start_listening(self):
        if self.on_hypothesis:
            self.on_hypothesis(f"Loading NVIDIA Parakeet TDT model ({self.MODEL_NAME})...")
        try:
            self._load_model()
        except Exception as e:
            if self.on_error:
                self.on_error(f"Failed to load NVIDIA Parakeet TDT model: {e}")
            return
        super()._start_listening()

    def _load_model(self):
        if self.model is not None:
            return
        self.processor = AutoProcessor.from_pretrained(self.MODEL_NAME, local_files_only=True)
        self.model = AutoModelForTDT.from_pretrained(self.MODEL_NAME, local_files_only=True)
        self.model.eval()

    def transcribe(self, audio_data) -> str:
        if self.model is None:
            return ""

        raw_data = audio_data.get_raw_data(convert_rate=16000, convert_width=2)
        audio_np = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32) / 32768.0

        if len(audio_np) == 0:
            return ""

        inputs = self.processor(audio_np, sampling_rate=16000, return_tensors="pt")

        with torch.no_grad():
            output = self.model.generate(inputs["input_features"], max_new_tokens=100)

        transcription = self.processor.batch_decode(output.sequences, skip_special_tokens=True)[0]
        return transcription.strip()
