import os
import json
import argparse


_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


def _load_config():
    try:
        with open(_CONFIG_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


_ENV_MAP = {
    "api_key": "LONGCAT_API_KEY",
    "base_url": "LONGCAT_BASE_URL",
    "model": "LONGCAT_MODEL",
    "stt_engine": "RTA_STT_ENGINE",
    "vosk_model_size": "RTA_VOSK_MODEL_SIZE",
    "whisper_key": "RTA_WHISPER_KEY",
    "whisper_url": "RTA_WHISPER_URL",
    "whisper_model": "RTA_WHISPER_MODEL",
    "whisper_local_size": "RTA_WHISPER_LOCAL_SIZE",
    "nvidia_key": "RTA_NVIDIA_KEY",
    "nvidia_server": "RTA_NVIDIA_SERVER",
    "nvidia_use_ssl": "RTA_NVIDIA_USE_SSL",
    "sensitivity": "RTA_SENSITIVITY",
}


_DEFAULTS = {
    "api_key": "ak_2US0cb4253bq8Co7qk4zC7cX4mD64",
    "base_url": "https://api.longcat.chat/openai/v1/",
    "model": "LongCat-Flash-Lite",
    "source_lang": "English",
    "target_lang": "Chinese",
    "stt_engine": "nvidia-local",
    "vosk_model_size": "small",
    "whisper_key": "",
    "whisper_url": "https://api.openai.com/v1/",
    "whisper_model": "whisper-1",
    "whisper_local_size": "base",
    "nvidia_key": "",
    "nvidia_server": "grpc.nvcf.nvidia.com:443",
    "nvidia_use_ssl": True,
    "sensitivity": 8,
    "new_transcript": False,
    "log_file": None,
}


class Config:
    def __init__(self):
        file_cfg = _load_config()
        for key, default in _DEFAULTS.items():
            value = file_cfg.get(key, default)
            if key in _ENV_MAP:
                env_val = os.environ.get(_ENV_MAP[key])
                if env_val is not None:
                    if key == "nvidia_use_ssl":
                        value = env_val.lower() in ("true", "1", "yes")
                    elif key == "sensitivity":
                        value = int(env_val)
                    else:
                        value = env_val
            setattr(self, key, value)

    def parse_args(self):
        """Parse CLI args to override configuration."""
        parser = argparse.ArgumentParser(description="RTA - Real-time Speech Translator")

        parser.add_argument("--source", type=str, default=self.source_lang,
                            help=f"Source language (default: {self.source_lang})")
        parser.add_argument("--target", type=str, default=self.target_lang,
                            help=f"Target translation language (default: {self.target_lang})")
        parser.add_argument("--key", type=str, default=self.api_key,
                            help="OpenAI-compatible translation API Key")
        parser.add_argument("--url", type=str, default=self.base_url,
                            help="OpenAI-compatible translation API Base URL")
        parser.add_argument("--model", type=str, default=self.model,
                            help="Translation Model name")
        parser.add_argument("--stt", type=str, default=self.stt_engine,
                            choices=["google", "vosk", "whisper-api", "whisper-local", "nvidia", "nvidia-local"],
                            help=f"Speech-to-Text engine (default: {self.stt_engine})")
        parser.add_argument("--stt-model-size", type=str, default=self.vosk_model_size,
                            choices=["small", "large"],
                            help=f"Model size for Vosk (default: {self.vosk_model_size})")
        parser.add_argument("--whisper-key", type=str, default=self.whisper_key)
        parser.add_argument("--whisper-url", type=str, default=self.whisper_url)
        parser.add_argument("--whisper-model", type=str, default=self.whisper_model)
        parser.add_argument("--whisper-local-size", type=str, default=self.whisper_local_size,
                            choices=["tiny", "base", "small", "medium", "large"])
        parser.add_argument("--nvidia-key", type=str, default=self.nvidia_key)
        parser.add_argument("--nvidia-server", type=str, default=self.nvidia_server)
        parser.add_argument("--nvidia-no-ssl", action="store_true")
        parser.add_argument("--sensitivity", type=int, default=self.sensitivity)
        parser.add_argument("-n", "--new", action="store_true", default=self.new_transcript,
                            help="Force new transcript file (add sequence number if today's file exists)")
        parser.add_argument("--log", type=str, default=None,
                            help="Manual transcript filename (overrides auto-naming)")

        args = parser.parse_args()

        self.source_lang = args.source
        self.target_lang = args.target
        self.api_key = args.key
        self.base_url = args.url
        self.model = args.model
        self.stt_engine = args.stt
        self.vosk_model_size = args.stt_model_size
        self.whisper_key = args.whisper_key
        self.whisper_url = args.whisper_url
        self.whisper_model = args.whisper_model
        self.whisper_local_size = args.whisper_local_size
        self.nvidia_key = args.nvidia_key
        self.nvidia_server = args.nvidia_server
        self.nvidia_use_ssl = not args.nvidia_no_ssl
        self.sensitivity = max(1, min(10, args.sensitivity))
        self.new_transcript = args.new
        self.log_file = args.log


config = Config()
