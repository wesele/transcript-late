import sys
import os
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from config import config

class ConsoleUI:
    def __init__(self):
        self.console = Console()
        self.last_hypothesis_len = 0
        self.has_active_hypothesis = False
        self.log_path = None

    def _get_log_path(self):
        if self.log_path:
            return self.log_path
        if config.log_file:
            self.log_path = config.log_file
            return self.log_path
        date_str = datetime.now().strftime("%Y-%m-%d")
        base = f"transcript_{date_str}"
        path = f"{base}.md"
        if config.new_transcript:
            n = 1
            while os.path.exists(path):
                n += 1
                path = f"{base}_{n}.md"
        self.log_path = path
        return self.log_path

    def print_startup_info(self):
        """Prints the system configuration card on startup."""
        # Create a beautiful configuration card using Rich Panel
        config_text = Text()
        config_text.append("🎙️  Speech STT:     ", style="bold cyan")
        if config.stt_engine == "google":
            config_text.append("Google Speech STT (Cloud/High Accuracy)\n", style="white")
        elif config.stt_engine == "whisper-api":
            config_text.append(f"Whisper API STT ({config.whisper_model})\n", style="white")
        elif config.stt_engine == "whisper-local":
            config_text.append(f"Whisper Local STT (100% Local - {config.whisper_local_size} model)\n", style="white")
        elif config.stt_engine == "nvidia":
            model_name = "Parakeet CTC zh-CN" if "chinese" in config.source_lang.lower() else "Parakeet CTC es"
            config_text.append(f"NVIDIA Riva {model_name} (Cloud/gRPC)\n", style="white")
        elif config.stt_engine == "nvidia-local":
            config_text.append("NVIDIA Parakeet TDT 0.6B (Local/HuggingFace)\n", style="white")
        else:
            config_text.append(f"Vosk Speech STT (100% Local/Offline - {config.vosk_model_size} model)\n", style="white")
        
        config_text.append("🌎  Translation:    ", style="bold cyan")
        config_text.append(f"{config.source_lang} ➡️ {config.target_lang}\n", style="white")
        
        config_text.append("⚙️  Model Backend:  ", style="bold cyan")
        if config.translation_engine == "hy-mt-local":
            config_text.append(f"Hy-MT2 (Local) [{config.hy_mt_model}]\n", style="white")
        else:
            config_text.append(f"{config.model}\n", style="white")
        
        config_text.append("🔗  API Endpoint:   ", style="bold cyan")
        config_text.append(f"{config.base_url}\n", style="white")
        
        config_text.append("📝  Session Log:    ", style="bold cyan")
        config_text.append(f"{self._get_log_path()}\n", style="white")

        config_text.append("🎛️  Sensitivity:    ", style="bold cyan")
        if config.stt_engine in ["google", "whisper-api", "whisper-local", "nvidia", "nvidia-local"]:
            if config.sensitivity >= 5:
                ratio = 1.5 - (config.sensitivity - 5) * 0.09
            else:
                ratio = 1.5 + (5 - config.sensitivity) * 0.625
            config_text.append(f"{config.sensitivity} / 10 (Dynamic Calibrated, Ratio: {ratio:.2f}x)", style="white")
        else:
            config_text.append(f"{config.sensitivity} / 10 (Vosk Native)", style="white")

        panel = Panel(
            config_text,
            title="[bold yellow]RTA - REAL-TIME TRANSLATOR ASSISTANT[/bold yellow]",
            border_style="cyan",
            expand=False,
            padding=(1, 4)
        )
        
        self.console.print(panel)
        if config.stt_engine == "google":
            self.console.print("[bold green]✔ Cloud Google speech recognition activated successfully![/bold green]")
        elif config.stt_engine == "whisper-api":
            self.console.print("[bold green]✔ Cloud Whisper speech recognition activated successfully![/bold green]")
        elif config.stt_engine == "whisper-local":
            self.console.print(f"[bold green]✔ Local offline Whisper ({config.whisper_local_size}) speech recognition activated successfully![/bold green]")
        elif config.stt_engine == "nvidia":
            self.console.print("[bold green]✔ NVIDIA Riva Parakeet CTC cloud speech recognition activated successfully![/bold green]")
        elif config.stt_engine == "nvidia-local":
            self.console.print("[bold green]✔ NVIDIA Parakeet TDT local speech recognition activated successfully![/bold green]")
        else:
            self.console.print(f"[bold green]✔ Local offline Vosk ({config.vosk_model_size}) speech recognition activated successfully![/bold green]")
        self.console.print("[bold yellow]🎙️  Listening... Speak into your microphone (Press Ctrl+C to exit)[/bold yellow]\n")

    def update_hypothesis(self, text):
        """
        Updates the transient real-time speech hypothesis line.
        Uses carriage return to rewrite the line, giving instant feedback.
        """
        if not text.strip():
            return
            
        self.clear_hypothesis()
        
        # Format the live hypothesis in a beautiful greyish color
        # The user requested greyish color for original text
        hypothesis_text = f"🗣️  [Hypothesis] {text}"
        
        # Use rich console print with end="" to output directly with ANSI color codes
        self.console.print(f"\r[grey54]{hypothesis_text}[/grey54]", end="", highlight=False)
        
        self.last_hypothesis_len = len(text) + 15
        self.has_active_hypothesis = True

    def clear_hypothesis(self):
        """Clears the active transient hypothesis line from the console."""
        if self.has_active_hypothesis:
            # Overwrite the line with spaces to erase it completely
            sys.stdout.write(f"\r{' ' * (self.last_hypothesis_len + 10)}\r")
            sys.stdout.flush()
            self.has_active_hypothesis = False

    def print_original_segment(self, original_text):
        """
        Prints the finalized original text immediately in grey.
        Prints a placeholder for the pending translation.
        """
        self.clear_hypothesis()
        
        # 1. Original text line (greyish color, e.g. grey54)
        original_line = Text(f"🗣️  {original_text}", style="grey54")
        self.console.print(original_line)
        
        # 2. Temporary translation line
        self.console.print("[yellow]⏳  Translating...[/yellow]")
        sys.stdout.flush()

    def update_translation_segment(self, original_text, translated_text):
        """
        Replaces the pending translation status with the finalized translation in white.
        """
        self.clear_hypothesis()
        
        # Move cursor up 1 line (\x1b[A), clear the line (\x1b[2K), and reset carriage (\r)
        sys.stdout.write("\x1b[A\x1b[2K\r")
        
        # Print the final translation line in bright white
        prefix = "🇨🇳  " if config.target_lang.lower() == "chinese" else "🌎  "
        translated_line = Text(f"{prefix}{translated_text}", style="white bold")
        self.console.print(translated_line)
        self.console.print("") # Blank line separator
        sys.stdout.flush()
        
        # Save to markdown log
        self._write_to_log(original_text, translated_text)

    def print_error(self, message):
        """Print an error message to the console."""
        self.clear_hypothesis()
        self.console.print(f"[bold red]❌ Error: {message}[/bold red]")

    def _write_to_log(self, original, translation):
        try:
            path = self._get_log_path()
            now = datetime.now()
            file_exists = os.path.exists(path)
            with open(path, "a", encoding="utf-8") as f:
                if not file_exists:
                    f.write(f"# RTA Translation Session Log\n")
                    f.write(f"- **Source Language**: {config.source_lang}\n")
                    f.write(f"- **Target Language**: {config.target_lang}\n")
                    f.write(f"- **Model**: {config.model}\n")
                    f.write(f"- **Date**: {now.strftime('%Y-%m-%d %H:%M:%S')}\n\n---\n\n")

                f.write(f"> **[ {now.strftime('%H:%M:%S')} ]** **{original}**\n")
                f.write(f"> **[ {now.strftime('%H:%M:%S')} ]** *{translation}*\n\n---\n\n")
        except Exception:
            pass
