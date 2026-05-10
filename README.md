🎙️ AI Media Translator
A powerful toolset to translate any audio into Vietnamese subtitles using Whisper (via Groq) and Gemini 2.0 Flash (via OpenRouter).

🚀 Features
This project offers two distinct ways to translate content:

Live Translator (live_translator.py):

Captures system audio in real-time.

Displays a floating, transparent overlay on your screen.

~3s latency – perfect for live streams, meetings, or games.

YouTube Video Processor (yt_video_translator.py):

Downloads videos directly from YouTube links (720p).

Uses context-aware AI to translate the entire video at once.

Generates a high-quality .mp4 file with Bilingual Letterboxing (Original text and Vietnamese subtitles placed in a black bar below the video).

🛠️ Requirements
Python 3.10+

FFmpeg: Required for audio extraction and video merging.

API Keys:

Groq Cloud (Whisper-v3)

OpenRouter (Gemini 2.0 Flash)

📥 Installation
Bash

# Clone the repository

git clone https://github.com/yourusername/ai-media-translator.git
cd ai-media-translator

# Install dependencies (using uv for speed)

uv pip install -r requirements.txt
⚙️ Configuration
Open both .py files and insert your API keys:

Python
GROQ_API_KEY = "your_groq_key"
OPENROUTER_API_KEY = "your_openrouter_key"
🎮 Usage
Option A: Live Screen Translation
Best for live content where you need immediate subtitles.

Bash
uv run live_translator.py
Option B: YouTube Subtitle Burn-in
Best for watching foreign videos with perfect, non-blocking bilingual subtitles.

Bash
uv run yt_translator.py
Paste the YouTube URL.

Enter a Project Folder name.

Enter the Output File name.

Wait for the AI to "cook" your video!

📂 Project Structure
Plaintext
.
├── live_translator.py # Real-time system audio overlay
├── yt_translator.py # YouTube downloader & subtitle burner
├── requirements.txt # Project dependencies
└── README.md # Documentation
📝 License
MIT License - Feel free to use and modify!
