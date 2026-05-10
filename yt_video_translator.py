import os
import subprocess
import requests
import yt_dlp
from groq import Groq

# --- API CONFIGURATION ---
# Replace with your actual keys 
GROQ_API_KEY = ""
OPENROUTER_API_KEY = ""

client = Groq(api_key=GROQ_API_KEY)

def download_youtube_video(url, folder_path):
    print("\n🎬 Step 1: Downloading Video & Audio from YouTube...")
    ydl_opts = {
        'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best',
        'outtmpl': os.path.join(folder_path, "temp_video_merge.%(ext)s"),
        'merge_output_format': 'mp4',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '128'
        }],
        'keepvideo': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    
    video_path = os.path.join(folder_path, "temp_video_merge.mp4")
    audio_path = os.path.join(folder_path, "temp_video_merge.mp3")
    return video_path, audio_path

def format_time(seconds):
    """Converts seconds to SRT time format (HH:MM:SS,mmm)"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def transcribe_and_translate(audio_file, folder_path):
    print("🤖 Step 2: Transcribing audio with Groq (Whisper-v3)...")
    with open(audio_file, "rb") as file:
        transcription = client.audio.transcriptions.create(
            file=(audio_file, file.read()),
            model="whisper-large-v3",
            response_format="verbose_json",
        )
    
    segments = transcription.segments
    # Prepare text for context-aware translation
    lines_to_translate = [f"{i} | {seg['text'].strip()}" for i, seg in enumerate(segments)]
    full_text = "\n".join(lines_to_translate)
    
    print("🧠 Step 3: Translating with Gemini 2.0 Flash (Context-Aware)...")
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
    prompt = (
    "You are a professional subtitle translator. Translate the following lines from their source language into natural Vietnamese. "
    "STRICT RULE: Keep the format '{Index} | {Translation}'. Do not add any explanations or notes.\n\n" + full_text
    )
    
    res = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json={
            "model": "google/gemini-2.0-flash-001",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2
        },
        timeout=60
    )
    
    translated_text = res.json()['choices'][0]['message']['content']
    translated_lines = translated_text.strip().split('\n')
    
    trans_dict = {}
    for line in translated_lines:
        if "|" in line:
            parts = line.split("|", 1)
            try: 
                idx = int(parts[0].strip())
                trans_dict[idx] = parts[1].strip()
            except: pass

    print("✍️ Step 4: Generating Bilingual SRT file...")
    srt_path = os.path.join(folder_path, "bilingual_sub.srt")
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments):
            start = format_time(seg['start'])
            end = format_time(seg['end'])
            original = seg['text'].strip()
            translated = trans_dict.get(i, "[Translation Missing]")
            # Stack Original (Top) and Translated (Bottom)
            f.write(f"{i+1}\n{start} --> {end}\n{original}\n{translated}\n\n")

    return srt_path

def merge_subtitles_to_video(video_file, srt_file, output_file):
    print("🎥 Step 5: Applying Letterboxing & Hardcoding Subtitles with FFmpeg...")
    
    # Handle Windows path formatting for FFmpeg
    srt_abs_path = os.path.abspath(srt_file).replace("\\", "/")
    if srt_abs_path[1] == ':':
        srt_abs_path = srt_abs_path[0] + "\\:" + srt_abs_path[2:]

    # Subtitle Styling
    style = (
        "FontSize=15,"
        "PrimaryColour=&H00FFFFFF,"      # White
        "OutlineColour=&H00000000,"      # Black
        "BorderStyle=1,"
        "Outline=0.5,"
        "Alignment=2,"                   # Bottom Center
        "MarginV=10"                     # Vertical margin within the pad
    )

    # Complex Filter: 
    # 1. Add 120px black bar at the bottom (pad)
    # 2. Overlay subtitles on the new expanded frame
    video_filter = f"pad=iw:ih+120:0:0:black,subtitles='{srt_abs_path}':force_style='{style}'"

    command = [
        "ffmpeg", "-y", "-i", video_file,
        "-vf", video_filter,
        "-c:v", "libx264",
        "-c:a", "aac",
        "-map", "0:v",
        "-map", "0:a",
        output_file
    ]
    
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

def main():
    # User Inputs (CLI UI)
    print("========================================")
    print("   AI YOUTUBE TRANSLATOR (CLI VERSION)  ")
    print("========================================")
    url = input("🔗 Enter YouTube URL: ")
    folder_name = input("📁 Enter Project Folder Name: ")
    video_name = input("🎞️ Enter Output Video Name (e.g., final_video): ")
    
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    
    v_tmp, a_tmp, s_tmp = "", "", ""
    
    try:
        # Processing Pipeline
        v_tmp, a_tmp = download_youtube_video(url, folder_name)
        s_tmp = transcribe_and_translate(a_tmp, folder_name)
        
        final_output = os.path.join(folder_name, f"{video_name}.mp4")
        merge_subtitles_to_video(v_tmp, s_tmp, final_output)
        
        print(f"\n✅ SUCCESS! Process completed.")
        print(f"📍 Final Video: {final_output}")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
    finally:
        # Cleanup temporary files
        print("🧹 Cleaning up temporary assets...")
        for f in [v_tmp, a_tmp, s_tmp]:
            if f and os.path.exists(f):
                try: os.remove(f)
                except: pass
        print("✨ Done.")

if __name__ == "__main__":
    main()