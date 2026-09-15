import os
import json
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

# URL 100% FIXED
url = "[https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=](https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=)" + api_key
payload = {"contents": [{"parts": [{"text": ai_prompt}]}]}

try:
    response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
    data = response.json()
    
    if "candidates" not in data:
        print("❌ API Error:", data)
        exit(1)
        
    json_text = data['candidates'][0]['content']['parts'][0]['text'].strip()
    
    if json_text.startswith("```json"):
        json_text = json_text[7:-3].strip()
    elif json_text.startswith("```"):
        json_text = json_text[3:-3].strip()
        
    scenes = json.loads(json_text)
    print("✅ Gemini generated", len(scenes), "scenes successfully!")
except Exception as e:
    print("❌ API Error or Parsing Failed:", e)
    exit(1)

clip_files = []

# 3. Generate Image, Voice & Apply CINEMATIC ZOOM (Motion)
print("🚀 Starting Video Generation Process...")
for i, scene in enumerate(scenes):
    print("🎬 Processing Scene", i+1, "/", len(scenes), "...")
    img_file = "temp_img_" + str(i) + ".jpg"
    aud_file = "temp_aud_" + str(i) + ".mp3"
    clip_file = "temp_clip_" + str(i) + ".mp4"
    
    # A. Download High Quality Portrait Image (1080x1920)
    safe_prompt = urllib.parse.quote(scene['prompt'] + ", highly detailed, cinematic lighting, 8k")
    img_url = "[https://image.pollinations.ai/prompt/](https://image.pollinations.ai/prompt/)" + safe_prompt + "?width=1080&height=1920&nologo=true"
    
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
