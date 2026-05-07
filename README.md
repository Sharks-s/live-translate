# live-translate

Translate anything playing on your screen in real-time. Powered by Whisper + Gemini. (~3s latency)

## What it does

Captures your system audio → transcribes with Whisper → translates via Gemini → shows as a floating overlay with the original text and translation side by side.

Works with any audio source — videos, meetings, podcasts, etc.

## Requirements

- Python 3.8+
- Two free API keys:
  - **Groq** (Whisper) → https://console.groq.com
  - **OpenRouter** (Gemini) → https://openrouter.ai

## Setup

```bash
git clone https://github.com/yourusername/live-translate
cd live-translate
uv venv && uv pip install -r requirements.txt
```

Open `main.py` and add your keys:

```python
GROQ_API_KEY = "your_groq_api_key_here"
OPENROUTER_API_KEY = "your_openrouter_api_key_here"
```

## Run

```bash
uv run main.py
```

## Change language

Edit this line in `main.py`:

```python
"content": "Translate to natural Vietnamese. Return ONLY the translation, no explanation."
```
