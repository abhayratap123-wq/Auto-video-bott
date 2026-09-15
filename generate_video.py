import os
import json
import time
import requests
import urllib.parse
from datetime import datetime

# 1. API Setup
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("❌ Error: GEMINI_API_KEY not found in GitHub Secrets!")
    exit(1)

today_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
final_video_name = "video_USA_" + today_date + ".mp4"

# 2. USA Audience Script (2 Minutes Length)
print("🤖 Asking Gemini AI for a 2-Minute USA Trending Script...")
ai_prompt = """You are an expert YouTube Shorts scriptwriter for a USA audience. 
Write a script about a highly trending USA topic (e.g., Space Mysteries, Future Technology, Area 51, Deep Sea discoveries).
The video must be around 1.5 to 2 minutes long.
Output STRICTLY as a JSON array of objects.
Each object must have:
1. "text": English narration (Make it 2-3 engaging sentences per scene so the duration is long).
2. "prompt": A highly detailed English image generation prompt for a realistic cinematic 8k image.
Limit to 10 to 12 scenes. Do NOT wrap it in markdown block (like ```json), just return the raw JSON array."""

# FIXED: gemini-3.8-flash was consistently overloaded (503) for several minutes straight.
# Instead of depending on one single model, try a short list of models in order —
# if one is down, move to the next instead of failing the whole run.
MODELS_TO_TRY = ["gemini-3.6-flash", "gemini-2.5-flash", "gemini-3.7-flash"]

payload = {
    "contents": [{"parts": [{"text": ai_prompt}]}],
    # FIXED: forces Gemini to return syntactically valid JSON only, instead of
    # just hoping the prompt instructions are followed. This is what was causing
    # the "Unterminated string" parsing error (an unescaped character in the raw text reply).
    "generationConfig": {"responseMimeType": "application/json"}
}

scenes = None
attempts_per_model = 3

for model_name in MODELS_TO_TRY:
    url = "https://generativelanguage.googleapis.com/v1beta/models/" + model_name + ":generateContent?key=" + api_key
    wait_seconds = 15
    print(f"🔧 Trying model: {model_name}")

    for attempt in range(1, attempts_per_model + 1):
        data = None
        try:
            response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=60)
            data = response.json()
        except Exception as e:
            print(f"⚠️ Request failed ({model_name}, attempt {attempt}/{attempts_per_model}):", e)

        if data and "candidates" in data:
            try:
                json_text = data['candidates'][0]['content']['parts'][0]['text'].strip()
                if json_text.startswith("```json"):
                    json_text = json_text[7:-3].strip()
                elif json_text.startswith("```"):
                    json_text = json_text[3:-3].strip()
                scenes = json.loads(json_text)
                print(f"✅ {model_name} generated", len(scenes), "scenes successfully!")
                break  # success, stop retrying this model
            except Exception as e:
                print(f"⚠️ Parsing failed ({model_name}, attempt {attempt}/{attempts_per_model}):", e)
        else:
            print(f"⚠️ API error ({model_name}, attempt {attempt}/{attempts_per_model}):", data)

        if attempt < attempts_per_model:
            print(f"⏳ Retrying in {wait_seconds}s...")
            time.sleep(wait_seconds)
            wait_seconds = min(wait_seconds * 2, 90)

    if scenes:
        break  # this model worked, no need to try the next one
    print(f"❌ {model_name} did not work after {attempts_per_model} attempts. Trying next model...")

if not scenes:
    print("❌ All models failed. No scenes generated.")
    exit(1)

clip_files = []

# 3. Generate Image, Voice & Apply CINEMATIC ZOOM (Motion)
print("🚀 Starting Video Generation Process...")
for i, scene in enumerate(scenes):
    print("🎬 Processing Scene", i+1, "/", len(scenes), "...")
    img_file = "temp_img_" + str(i) + ".jpg"
    aud_file = "temp_aud_" + str(i) + ".mp3"
    clip_file = "temp_clip_" + str(i) + ".mp4"

    # A. Download High Quality Portrait Image (1080x1920) — FIXED: removed stray markdown-link brackets
    safe_prompt = urllib.parse.quote(scene['prompt'] + ", highly detailed, cinematic lighting, 8k")
    img_url = "https://image.pollinations.ai/prompt/" + safe_prompt + "?width=1080&height=1920&nologo=true"

    img_response = requests.get(img_url, headers={'User-Agent': 'Mozilla/5.0'})
    if img_response.status_code == 200:
        with open(img_file, 'wb') as f:
            f.write(img_response.content)
    else:
        print("⚠️ Image download failed for scene", i+1, ". Skipping.")
        continue

    # B. Generate Voice (USA Accent)
    os.system('edge-tts --voice "en-US-ChristopherNeural" --text "' + scene["text"] + '" --write-media ' + aud_file)

    # C. FFMPEG MAGIC: Add Cinematic Zoom (Motion)
    print("🎥 Applying Cinematic Zoom Effect...")
    ffmpeg_cmd = (
        'ffmpeg -y -loop 1 -framerate 25 -i "' + img_file + '" -i "' + aud_file + '" '
        '-vf "zoompan=z=\'min(zoom+0.0015,1.2)\':d=1000:x=\'iw/2-(iw/zoom/2)\':y=\'ih/2-(ih/zoom/2)\':s=1080x1920" '
        '-c:v libx264 -pix_fmt yuv420p -c:a aac -shortest "' + clip_file + '" -loglevel error'
    )
    os.system(ffmpeg_cmd)

    if os.path.exists(clip_file):
        clip_files.append(clip_file)

# 4. Merge All Clips into the Final 2-Minute Video
print("🔗 Combining all scenes into Final Video...")
with open("videos_list.txt", "w") as f:
    for clip in clip_files:
        f.write("file '" + clip + "'\n")

os.system("ffmpeg -f concat -safe 0 -i videos_list.txt -c copy " + final_video_name + " -loglevel error")
print("✅ FINAL VIDEO READY:", final_video_name)

# 5. Clean & Beautiful HTML Generation
all_videos = sorted([f for f in os.listdir('.') if f.startswith('video_USA') and f.endswith('.mp4')], reverse=True)

html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>AI USA Video Studio</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { background: #0a0a0a; color: white; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; text-align: center; }
        h1 { color: #00e676; margin-bottom: 5px; }
        p { color: #aaa; margin-bottom: 30px; }
        .grid { display: flex; flex-wrap: wrap; justify-content: center; gap: 25px; }
        .vid-card { background: #1a1a1a; padding: 15px; border-radius: 15px; width: 320px; box-shadow: 0 10px 20px rgba(0,0,0,0.5); border: 1px solid #333; }
        video { width: 100%; border-radius: 10px; background: black; }
        .download-btn { display: block; background: #00e676; color: black; padding: 12px; margin-top: 15px; text-decoration: none; font-weight: bold; border-radius: 8px; transition: 0.3s; }
        .download-btn:hover { background: #00c853; color: white; }
        .date-label { color: #ffeb3b; font-size: 14px; margin-bottom: 10px; display: block; }
    </style>
</head>
<body>
    <h1>🇺🇸 Auto AI USA Videos</h1>
    <p>Daily 2-Minute Cinematic Stories | Auto-Updates at 11:00 PM</p>
    <div class="grid">
"""

if not all_videos:
    html_content += "<h3>No videos generated yet.</h3>"
else:
    for v in all_videos:
        date_label = v.replace("video_USA_", "").replace(".mp4", "")
        html_content += f'<div class="vid-card"><span class="date-label">📅 {date_label}</span><video src="{v}" controls preload="metadata"></video><a href="{v}" download class="download-btn">⬇️ Download High Quality</a></div>'

html_content += """
    </div>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("🌐 Clean Webpage Updated Successfully!")
