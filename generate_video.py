import os
import json
import requests
import urllib.parse
from datetime import datetime

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("❌ Error: GEMINI_API_KEY not found!")
    exit(1)

today_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
final_video_name = "video_USA_" + today_date + ".mp4"

print("🤖 Asking Gemini AI for a 2-Minute USA Trending Script...")
ai_prompt = """You are an expert YouTube Shorts scriptwriter for a USA audience. 
Write a script about a highly trending USA topic (Space Mysteries, Future Technology, Area 51, Deep Sea discoveries).
The video must be around 1.5 to 2 minutes long.
Output STRICTLY as a JSON array of objects.
Each object must have:
1. "text": English narration (2-3 engaging sentences per scene).
2. "prompt": A detailed English image prompt for cinematic 8k.
Limit to 10 scenes. Return raw JSON array only, no markdown."""

# URL ko टुकड़ों में लिखा है ताकि कोई brackets न आएँ
part1 = "https://"
part2 = "generativelanguage.googleapis.com"
part3 = "/v1beta/models/gemini-1.5-flash:generateContent?key="
url = part1 + part2 + part3 + api_key

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

for i, scene in enumerate(scenes):
    print("🎬 Processing Scene", i+1, "/", len(scenes))
    img_file = "temp_img_" + str(i) + ".jpg"
    aud_file = "temp_aud_" + str(i) + ".mp3"
    clip_file = "temp_clip_" + str(i) + ".mp4"
    
    safe_prompt = urllib.parse.quote(scene['prompt'] + ", cinematic lighting, 8k")
    
    # Pollinations URL bhi टुकड़ों में लिखा है
    d1 = "https://"
    d2 = "image.pollinations.ai/prompt/"
    img_url = d1 + d2 + safe_prompt + "?width=1080&height=1920&nologo=true"
    
    img_res = requests.get(img_url, headers={'User-Agent': 'Mozilla/5.0'})
    if img_res.status_code == 200:
        with open(img_file, 'wb') as f:
            f.write(img_res.content)
    else:
        continue 
        
    os.system('edge-tts --voice "en-US-ChristopherNeural" --text "' + scene["text"] + '" --write-media ' + aud_file)
    
    ffmpeg_cmd = (
        'ffmpeg -y -loop 1 -framerate 25 -i "' + img_file + '" -i "' + aud_file + '" '
        '-vf "zoompan=z=\'min(zoom+0.0015,1.2)\':d=1000:x=\'iw/2-(iw/zoom/2)\':y=\'ih/2-(ih/zoom/2)\':s=1080x1920" '
        '-c:v libx264 -pix_fmt yuv420p -c:a aac -shortest "' + clip_file + '" -loglevel error'
    )
    os.system(ffmpeg_cmd)
    
    if os.path.exists(clip_file):
        clip_files.append(clip_file)

with open("videos_list.txt", "w") as f:
    for clip in clip_files:
        f.write("file '" + clip + "'\n")

os.system("ffmpeg -f concat -safe 0 -i videos_list.txt -c copy " + final_video_name + " -loglevel error")
print("✅ FINAL VIDEO READY:", final_video_name)

all_videos = sorted([f for f in os.listdir('.') if f.startswith('video_USA') and f.endswith('.mp4')], reverse=True)

html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>AI USA Video Studio</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { background: #0a0a0a; color: white; font-family: sans-serif; margin: 0; padding: 20px; text-align: center; }
        h1 { color: #00e676; }
        .grid { display: flex; flex-wrap: wrap; justify-content: center; gap: 25px; }
        .vid-card { background: #1a1a1a; padding: 15px; border-radius: 15px; width: 320px; border: 1px solid #333; }
        video { width: 100%; border-radius: 10px; background: black; }
        .download-btn { display: block; background: #00e676; color: black; padding: 12px; margin-top: 15px; text-decoration: none; font-weight: bold; border-radius: 8px; }
    </style>
</head>
<body>
    <h1>🇺🇸 Auto AI USA Videos</h1>
    <p>Daily Cinematic Stories</p>
    <div class="grid">
"""

for v in all_videos:
    date_label = v.replace("video_USA_", "").replace(".mp4", "")
    html_content += f'<div class="vid-card"><span>📅 {date_label}</span><video src="{v}" controls preload="metadata"></video><a href="{v}" download class="download-btn">⬇️ Download</a></div>'

html_content += "</div></body></html>"

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)
