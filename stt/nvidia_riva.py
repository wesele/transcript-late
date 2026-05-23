import riva.client
import riva.client.proto.riva_asr_pb2
from config import config
from ._segment_base import SegmentSTTEngine
from .base import STTEngine


class NvidiaRivaEngine(SegmentSTTEngine):
    def __init__(self, on_hypothesis=None, on_recognition=None, on_error=None):
        super().__init__(on_hypothesis, on_recognition, on_error)
        self.nvidia_asr_service = None

    def _start_listening(self):
        if self.on_hypothesis:
            self.on_hypothesis("Initializing NVIDIA Riva Parakeet CTC client...")
        try:
            self._init_client()
        except Exception as e:
            if self.on_error:
                self.on_error(f"Failed to initialize NVIDIA Riva client: {e}")
            return
        super()._start_listening()

    def _init_client(self):
        if self.nvidia_asr_service is not None:
            return
        api_key = config.nvidia_key
        function_id, _ = STTEngine.map_nvidia(config.source_lang)

        metadata_args = None
        if config.nvidia_server == "grpc.nvcf.nvidia.com:443":
            if not api_key:
                raise ValueError("NVIDIA API key missing. Set RTA_NVIDIA_KEY env var or pass --nvidia-key.")
            metadata_args = [
                ["function-id", function_id],
                ["authorization", f"Bearer {api_key}"],
            ]

        auth = riva.client.Auth(
            uri=config.nvidia_server,
            use_ssl=config.nvidia_use_ssl,
            metadata_args=metadata_args,
        )
        self.nvidia_asr_service = riva.client.ASRService(auth)

    def transcribe(self, audio_data) -> str:
        self._init_client()

        raw_data = audio_data.get_raw_data(convert_rate=16000, convert_width=2)
        _, language_code = STTEngine.map_nvidia(config.source_lang)

        streaming_config = riva.client.StreamingRecognitionConfig(
            config=riva.client.RecognitionConfig(
                encoding=riva.client.AudioEncoding.LINEAR_PCM,
                sample_rate_hertz=16000,
                language_code=language_code,
                max_alternatives=1,
                enable_automatic_punctuation=True,
                audio_channel_count=1,
            ),
            interim_results=False,
        )

        def audio_generator():
            yield riva.client.proto.riva_asr_pb2.StreamingRecognizeRequest(streaming_config=streaming_config)
            yield riva.client.proto.riva_asr_pb2.StreamingRecognizeRequest(audio_content=raw_data)

        responses = self.nvidia_asr_service.stub.StreamingRecognize(
            audio_generator(),
            metadata=self.nvidia_asr_service.auth.get_auth_metadata(),
            timeout=60,
        )

        for response in responses:
            if response.results:
                for result in response.results:
                    if result.is_final:
                        text = result.alternatives[0].transcript.strip()
                        if text:
                            return text
        return ""
