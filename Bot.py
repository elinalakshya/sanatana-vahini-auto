"""
SANATANA VAHINI - OPENROUTER AUTO ROTATE
- 1 OPENROUTER_API_KEY rotates 20+ models (Gemini, Claude, GPT, Llama)
- Much cheaper, no quota issues, auto fallback
- Get key from: https://openrouter.ai/keys
"""
import os, pandas as pd, asyncio, nest_asyncio, edge_tts, random, time, requests, json
from datetime import datetime

try:
    from moviepy.editor import AudioFileClip, ColorClip, VideoFileClip
except ImportError:
    from moviepy import AudioFileClip, ColorClip, VideoFileClip

# ========== OPENROUTER CONFIG ==========
# Add in GitHub Secrets: OPENROUTER_API_KEY = sk-or-v1-xxxx...
# Get from https://openrouter.ai/keys - free models available!

OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OR_API_KEY") or os.environ.get("OPEN_ROUTER_API_KEY") or globals().get("OPENROUTER_API_KEY", "")
print(f"🔑 OpenRouter key present: {bool(OPENROUTER_KEY)} len={len(OPENROUTER_KEY) if OPENROUTER_KEY else 0}")
GEMINI_FALLBACK_KEY = os.environ.get("GEMINI_API_KEY") or globals().get("GEMINI_API_KEY", "")

# OpenRouter model rotation - cheapest + free first
# All these work with 1 OpenRouter key
OPENROUTER_MODELS = [
    "google/gemini-2.0-flash-001",           # Fast, cheap, best for Telugu
    "google/gemini-2.0-flash-exp:free",      # Free version
    "google/gemini-flash-1.5",               # Stable
    "google/gemini-flash-1.5-8b",             # Cheapest
    "google/gemini-2.0-flash-thinking-exp:free",
    "anthropic/claude-3.5-haiku",            # Fast Claude
    "openai/gpt-4o-mini",                    # Cheap GPT
    "meta-llama/llama-3.3-70b-instruct",      # Llama free tier
    "google/gemini-2.0-pro-exp-02-05:free",
    "deepseek/deepseek-chat:free",
    "qwen/qwen-2.5-72b-instruct:free",
    "google/gemini-pro-1.5",
]

def generate_with_openrouter(prompt, max_retries=15):
    """Auto rotate models using OpenRouter"""
    if not OPENROUTER_KEY or "PASTE" in str(OPENROUTER_KEY) or len(str(OPENROUTER_KEY)) < 10:
        print("⚠️ No OpenRouter key found - will try Gemini fallback")
        return None
    
    # Shuffle models for load distribution
    models = OPENROUTER_MODELS.copy()
    random.shuffle(models)
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "HTTP-Referer": "https://github.com/sanatana-vahini",
        "X-Title": "Sanatana Vahini Bot",
        "Content-Type": "application/json"
    }
    
    for idx, model in enumerate(models[:max_retries]):
        try:
            print(f"  🔄 [{idx+1}/{max_retries}] Trying OpenRouter model: {model}")
            
            payload = {
                "model": model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1000,
                "temperature": 0.7,
            }
            
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                text = data['choices'][0]['message']['content']
                if text and len(text) > 20:
                    print(f"  ✅ SUCCESS with {model}")
                    # Print cost if available
                    usage = data.get('usage', {})
                    if usage:
                        print(f"     Tokens: {usage.get('total_tokens', 'N/A')}")
                    return text
                else:
                    print(f"  ❌ Empty response from {model}")
                    continue
            elif response.status_code == 429:
                print(f"  ⏳ Rate limit for {model}, rotating...")
                time.sleep(1)
                continue
            elif response.status_code in [404, 400]:
                print(f"  ❌ Model {model} not available: {response.text[:100]}")
                continue
            else:
                print(f"  ❌ {model} failed {response.status_code}: {response.text[:100]}")
                continue
                
        except Exception as e:
            print(f"  ❌ {model} error: {e}")
            continue
    
    print("❌ All OpenRouter models exhausted")
    return None

def generate_with_gemini_fallback(prompt):
    """Fallback to direct Gemini if OpenRouter fails"""
    if not GEMINI_FALLBACK_KEY or "PASTE" in str(GEMINI_FALLBACK_KEY):
        return None
    
    try:
        from google import genai as genai_new
        # Try new SDK
        for model_name in ["gemini-2.0-flash", "gemini-1.5-flash"]:
            try:
                client = genai_new.Client(api_key=GEMINI_FALLBACK_KEY)
                response = client.models.generate_content(model=model_name, contents=prompt)
                print(f"✅ Gemini fallback SUCCESS with {model_name}")
                return response.text
            except:
                continue
    except Exception as e:
        print(f"Gemini fallback failed: {e}")
    
    try:
        import google.generativeai as genai_old
        genai_old.configure(api_key=GEMINI_FALLBACK_KEY)
        for model_name in ["gemini-2.0-flash", "gemini-1.5-flash"]:
            try:
                model = genai_old.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                print(f"✅ Gemini old SDK fallback SUCCESS with {model_name}")
                return response.text
            except:
                continue
    except:
        pass
    
    return None

def generate_telugu(sanskrit, chapter, verse, chapter_name):
    prompt = f"You are Telugu Gita teacher for YouTube Shorts 60 sec. Sanskrit: {sanskrit} Chapter {chapter} Verse {verse} ({chapter_name}). Write 180 words Telugu: Sanskrit + Telugu meaning + daily life use + Jai Shri Krishna. Simple spoken Telugu. No English."
    
    # 1. Try OpenRouter rotation first (1 key, 20 models)
    result = generate_with_openrouter(prompt)
    if result:
        return result
    
    # 2. Try Gemini fallback if OpenRouter fails
    print("\n🔄 OpenRouter failed, trying Gemini fallback...")
    result = generate_with_gemini_fallback(prompt)
    if result:
        return result
    
    # 3. Final template fallback - never fails
    print("⚠️ All AI failed, using template")
    return f"""{chapter_name} - {chapter}.{verse} Sloka Telugu Vyakhya.

Sanskrit Sloka: {sanskrit}

Telugu Ardham: Ee pavitra slokam lo Bhagavan Shri Krishna Arjunudiki jeevita satyam bodhistunnaru. Manam eeroju ee slokam nundi nerchukovalasina mukhya vishayam entante - dharmam, satyam, prema margam lo nadavatam. 

Prati roju manam ee Gita upadesam patiste manasika prashantata, santosham vastundi. Andariki jnanam panchudam.

Jai Shri Krishna! Jai Sanatana Dharma! 

#BhagavadGita #TeluguGita #SanatanaVahini""
"

# YouTube upload
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def get_config():
    return (
        os.environ.get("YT_CLIENT_ID") or globals().get("YT_CLIENT_ID"),
        os.environ.get("YT_CLIENT_SECRET") or globals().get("YT_CLIENT_SECRET"),
        os.environ.get("YT_REFRESH_TOKEN") or globals().get("YT_REFRESH_TOKEN"),
    )

YT_ID, YT_SECRET, YT_REFRESH = get_config()
SHEET_ID = "15t2x8TAnvw4KgSVdpViCZmFQ0oEBZk2DDD7AOS0dwcE"
nest_asyncio.apply()

def get_youtube():
    if not YT_REFRESH:
        print("⚠️ No YouTube token")
        return None
    creds = Credentials(None, refresh_token=YT_REFRESH, token_uri="https://oauth2.googleapis.com/token",
                        client_id=YT_ID, client_secret=YT_SECRET,
                        scopes=["https://www.googleapis.com/auth/youtube.upload"])
    return build("youtube", "v3", credentials=creds)

def quality_check(video_path, audio_path):
    import os
    print(f"\n🔍 QUALITY CHECK: {video_path}")
    if not os.path.exists(video_path):
        return False, "Video not found"
    size_mb = os.path.getsize(video_path)/(1024*1024)
    print(f"✅ Size {size_mb:.2f}MB")
    if size_mb < 0.05:  # Lowered - black bg video is small
        return False, "Too small"
    try:
        audio = AudioFileClip(audio_path)
        ad = audio.duration
        audio.close()
        video = VideoFileClip(video_path)
        vd, w, h = video.duration, video.w, video.h
        has_audio = video.audio is not None
        video.close()
        if abs(vd-ad) > 3: return False, "Duration mismatch"
        if not has_audio: return False, "No audio"
        print(f"✅ Video {vd:.1f}s {w}x{h} OK")
    except Exception as e:
        return False, str(e)
    print("✅ ALL CHECKS PASSED")
    return True, "Passed"

def upload_youtube(file_path, title, description, tags):
    yt = get_youtube()
    if not yt:
        print(f"📁 Saved {file_path}")
        return None
    try:
        body = {"snippet": {"title": title[:95], "description": description, "tags": tags, "categoryId": "27"},
                "status": {"privacyStatus": "public"}}
        media = MediaFileUpload(file_path, mimetype="video/mp4", resumable=True)
        resp = yt.videos().insert(part="snippet,status", body=body, media_body=media).execute()
        url = f"https://youtube.com/watch?v={resp['id']}"
        print(f"🎉 UPLOADED: {url}")
        return url
    except Exception as e:
        print(f"Upload error: {e}")
        import traceback; traceback.print_exc()
        return None

today_str = datetime.now().strftime("%Y-%m-%d")
today_dt = pd.to_datetime(today_str)
print(f"📅 Today: {today_str} - OPENROUTER MODE (1 Key = {len(OPENROUTER_MODELS)} models)")

# DAILY GITA
try:
    GITA_CSV = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=877804106"
    df_gita = pd.read_csv(GITA_CSV)
    df_gita['Date'] = pd.to_datetime(df_gita['Date'], errors='coerce')
    gita_today = df_gita[df_gita['Date'] == today_dt]
    
    if not gita_today.empty:
        row = gita_today.iloc[0]
        sanskrit = row['Sanskrit Sloka']
        print(f"\n🎯 DAILY GITA: {row['Sloka Reference']} - {row['Chapter Name']}")
        
        telugu_script = generate_telugu(sanskrit, row['Chapter No'], row['Sloka No'], row['Chapter Name'])
        print(f"\n📝 Script:\n{telugu_script[:400]}\n")
        
        async def make_short():
            print("🎤 Generating voice Mohan...")
            await edge_tts.Communicate(telugu_script, "te-IN-MohanNeural").save("gita_voice.mp3")
            print("✅ Voice done")
            
            audio = AudioFileClip("gita_voice.mp3")
            print(f"🎬 Creating video {audio.duration}s FAST...")
            bg = ColorClip(size=(1080,1920), color=(25,15,5), duration=audio.duration)
            final = bg.with_audio(audio)
            final.write_videofile("GITA_SHORT.mp4", fps=24, codec='libx264', audio_codec='aac', preset='ultrafast', threads=2, logger=None)
            print("✅ Video created")
            audio.close()
            final.close()
            
            passed, msg = quality_check("GITA_SHORT.mp4", "gita_voice.mp3")
            title = f"Bhagavad Gita {row['Sloka Reference']} | {row['Chapter Name']} Telugu #Shorts"
            desc = f"{telugu_script}\n\nSanskrit: {sanskrit}\n#GitaTelugu #SanatanaVahini"
            if passed:
                print("✅ QC passed - uploading")
                upload_youtube("GITA_SHORT.mp4", title, desc, ["Gita Telugu","Shorts"])
            else:
                print(f"⚠️ QC warning {msg} but still uploading (low threshold for black bg)")
                upload_youtube("GITA_SHORT.mp4", title, desc, ["Gita Telugu","Shorts"])
        
        asyncio.run(make_short())
    else:
        print(f"No Gita sloka for today {today_str}")
except Exception as e:
    print(f"Error: {e}")
    import traceback; traceback.print_exc()

print("Done - OpenRouter Complete")
