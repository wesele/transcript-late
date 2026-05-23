import sys
import time
import signal
from config import config
from cli_ui import ConsoleUI
from translator import TranslationWorker
from speech_engine import SpeechRecognitionEngine

def main():
    # 1. Parse command-line arguments to load configurations
    config.parse_args()

    # 2. Initialize our premium terminal interface
    ui = ConsoleUI()
    ui.print_startup_info()

    # Unique segment identifier to track incoming audio chunks
    segment_counter = 0

    # 3. Setup Translation background worker
    def on_translation_complete(original, translation, segment_id):
        # Update the pending translation line in-place with the finalized translation
        ui.update_translation_segment(original, translation)

    def on_translation_error(error_msg):
        ui.print_error(f"Translation service error: {error_msg}")

    translator = TranslationWorker(
        on_translation_complete=on_translation_complete,
        on_error=on_translation_error
    )
    translator.start()

    # 4. Setup High-Accuracy Speech Recognition Engine
    def on_stt_status(status_text):
        # Update transient real-time display at bottom of console (e.g. "Processing...")
        if status_text:
            ui.update_hypothesis(status_text)
        else:
            ui.clear_hypothesis()

    def on_stt_recognition(final_text):
        nonlocal segment_counter
        if not final_text.strip():
            return
        
        # Clear hypothesis line immediately upon finalization
        ui.clear_hypothesis()
        
        # 1. IMMEDIATELY print original text on screen to achieve instant response
        ui.print_original_segment(final_text)
        
        # 2. Queue translation to the background worker thread
        segment_counter += 1
        translator.queue_translation(final_text, segment_counter)

    def on_stt_error(error_msg):
        ui.print_error(f"Speech Recognition error: {error_msg}")

    speech_engine = SpeechRecognitionEngine(
        on_hypothesis=on_stt_status,
        on_recognition=on_stt_recognition,
        on_error=on_stt_error
    )
    speech_engine.start()

    # 5. Handle graceful shutdown (Ctrl+C)
    def shutdown_handler(signum, frame):
        print("\n") # Line break
        ui.clear_hypothesis()
        sys.stdout.write("\r") # Reset carriage
        ui.console.print("[bold yellow]⏳ Stopping RTA engines gracefully...[/bold yellow]")
        
        # Stop background engines
        speech_engine.stop()
        translator.stop()
        
        ui.console.print(f"[bold green]✔ Engines stopped. Transcript saved to [underline]{config.log_file}[/underline][/bold green]")
        ui.console.print("[bold cyan]👋 Thank you for using RTA! Goodbye.[/bold cyan]")
        sys.exit(0)

    # Register signals for both normal exit and keyboard interrupts
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    # 6. Main thread keep-alive loop
    try:
        while True:
            # We keep the main thread idle while background SAPI and translation threads work.
            # Using short sleep intervals ensures Ctrl+C interrupts are captured instantly on Windows.
            time.sleep(0.1)
    except KeyboardInterrupt:
        shutdown_handler(None, None)

if __name__ == "__main__":
    main()
