import soundcard as sc
import numpy as np
import io
import threading
import queue
import requests
import tkinter as tk
from scipy.io import wavfile
from groq import Groq

# --- CONFIGURATION ---
# Get your free Groq API key at: https://console.groq.com
GROQ_API_KEY = "your_groq_api_key_here"

# Get your OpenRouter API key at: https://openrouter.ai
OPENROUTER_API_KEY = "your_openrouter_api_key_here"

SAMPLE_RATE = 16000
CHUNK_DURATION = 3  # seconds per audio chunk — increase if transcription feels choppy

client = Groq(api_key=GROQ_API_KEY)
audio_queue = queue.Queue()


# --- SUBTITLE OVERLAY WINDOW ---
class SubtitleOverlay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎙 Live Subtitle")
        self.root.attributes("-topmost", True)   # Always on top
        self.root.attributes("-alpha", 0.92)     # Slight transparency
        self.root.configure(bg="#1a1a2e")
        self.root.geometry("900x160")
        self.root.resizable(True, True)

        outer = tk.Frame(self.root, bg="#2d2d4e", padx=2, pady=2)
        outer.pack(fill="both", expand=True, padx=8, pady=8)

        inner = tk.Frame(outer, bg="#1a1a2e")
        inner.pack(fill="both", expand=True)

        # Original transcribed text (smaller, muted)
        self.original_label = tk.Label(
            inner,
            text="",
            font=("Segoe UI", 15),
            fg="#9090cc",
            bg="#1a1a2e",
            wraplength=860,
            justify="center"
        )
        self.original_label.pack(expand=True, fill="both", padx=12, pady=(10, 2))

        # Translated text (larger, highlighted)
        self.translated_label = tk.Label(
            inner,
            text="Waiting for audio...",
            font=("Segoe UI", 26, "bold"),
            fg="#ffe066",
            bg="#1a1a2e",
            wraplength=860,
            justify="center"
        )
        self.translated_label.pack(expand=True, fill="both", padx=12, pady=(2, 10))

        self.root.bind("<Configure>", self._on_resize)

    def _on_resize(self, event):
        w = self.root.winfo_width() - 40
        self.original_label.config(wraplength=w)
        self.translated_label.config(wraplength=w)

    def update(self, original, translated):
        self.original_label.config(text=original)
        self.translated_label.config(text=translated or "...")


# --- TRANSLATION ---
def translate(text):
    """
    Translates the transcribed text using OpenRouter (Gemini 2.0 Flash).
    To change the target language, edit the system prompt below.
    Example: "Translate to natural Japanese. Return ONLY the translation."
    """
    if not text.strip() or text.strip() == ".":
        return ""
    try:
        res = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
            json={
                "model": "google/gemini-2.0-flash-001",
                "messages": [
                    {
                        "role": "system",
                        # --- Change target language here ---
                        "content": "Translate to natural Vietnamese. Return ONLY the translation, no explanation."
                    },
                    {"role": "user", "content": text}
                ]
            },
            timeout=5
        )
        return res.json()['choices'][0]['message']['content'].strip()
    except:
        return None


# --- AUDIO PROCESSING ---
def process_audio(audio_data):
    """Transcribes audio using Whisper via Groq, then translates the result."""
    try:
        buf = io.BytesIO()
        wavfile.write(buf, SAMPLE_RATE, audio_data.astype(np.float32))
        buf.seek(0)

        # Whisper auto-detects language — works with Japanese, Korean, Chinese, English, etc.
        original = client.audio.transcriptions.create(
            file=("audio.wav", buf),
            model="whisper-large-v3",
            response_format="text",
        ).strip()

        if len(original) > 1:
            translated = translate(original)
            overlay.root.after(0, overlay.update, original, translated or "")
    except:
        pass


# --- BACKGROUND WORKER ---
def worker():
    """Processes audio chunks from the queue one at a time."""
    while True:
        data = audio_queue.get()
        if data is None:
            break
        process_audio(data)
        audio_queue.task_done()


# --- AUDIO CAPTURE LOOP ---
def main_logic():
    """
    Captures system audio (loopback) in chunks and queues them for processing.
    Requires a loopback-capable audio device.
    - Windows: works out of the box with most drivers
    - Linux: requires PulseAudio or PipeWire with a monitor source
    - macOS: requires a virtual audio driver (e.g. BlackHole)
    """
    speaker = sc.default_speaker()
    threading.Thread(target=worker, daemon=True).start()
    buf = []

    with sc.get_microphone(id=str(speaker.name), include_loopback=True).recorder(samplerate=SAMPLE_RATE) as mic:
        while True:
            data = mic.record(numframes=4000)
            buf.append(data)
            if sum(len(d) for d in buf) >= SAMPLE_RATE * CHUNK_DURATION:
                chunk = np.concatenate(buf)
                audio = np.mean(chunk, axis=1) if chunk.ndim > 1 else chunk
                # Skip silent chunks to avoid unnecessary API calls
                if np.max(np.abs(audio)) > 0.02:
                    audio_queue.put(audio)
                buf.clear()


# --- ENTRY POINT ---
threading.Thread(target=main_logic, daemon=True).start()
overlay = SubtitleOverlay()
overlay.root.mainloop()