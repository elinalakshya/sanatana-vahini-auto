"""
SANATANA VAHINI - FAST OPTIMIZED - Linked Colab + GitHub Auto
Fixed: Fast video generation (ultrafast preset)
"""
import os, pandas as pd, asyncio, nest_asyncio, edge_tts
from datetime import datetime

try:
    import google.generativeai as genai
    from moviepy.editor import AudioFileClip, ColorClip
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "google-generativeai", "edge-tts", "moviepy", "pandas", "nest-asyncio", "google-api-python-client", "google-auth"])
    import google.generativeai as genai
    from moviepy.editor import AudioFileClip, ColorClip
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

def get_config():
    return (
        os.environ.get("GEMINI_API_KEY") or globals().get("GEMINI_API_KEY"),
        os.environ.get("YT_CLIENT_ID") or globals().get("YT_CLIENT_ID"),
        os.environ.get("YT_CLIENT_SECRET") or globals().get("YT_CLIENT_SECRET"),
        os.environ.get("YT_REFRESH_TOKEN") or globals().get("YT_REFRESH_TOKEN"),
    )

GEMINI_KEY, YT_ID, YT_SECRET, YT_REFRESH = get_config()
SHEET_ID = "15t2x8TAnvw4KgSVdpViCZmFQ0oEBZk2DDD7AOS0dwcE"
nest_asyncio.apply()

if GEMINI_KEY and "PASTE" not in GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None
    print("⚠️ Gemini key missing")

def get_youtube():
    if not YT_REFRESH:
        print("⚠️ No YouTube token")
        return None
    creds = Credentials(None, refresh_token=YT_REFRESH, token_uri="https://oauth2.googleapis.com/token",
                        client_id=YT_ID, client_secret=YT_SECRET,
                        scopes=["https://www.googleapis.com/auth/youtube.upload"])
    return build("youtube", "v3", credentials=creds)

def quality_check(video_path, audio_path, is_short=False):
    import os
    print(f"\n🔍 QUALITY CHECK: {video_path}")
    if not os.path.exists(video_path):
        return False, "Video not found"
    size_mb = os.path.getsize(video_path)/(1024*1024)
    if size_mb < 0.5:
        return False, f"Too small {size_mb:.2f}MB"
    print(f"✅ Size {size_mb:.2f}MB")
    try:
        from moviepy.editor import VideoFileClip, AudioFileClip
        audio = AudioFileClip(audio_path)
        ad = audio.duration
        audio.close()
        if ad < 20: return False, f"Audio short {ad}s"
        print(f"✅ Audio {ad:.1f}s")
        video = VideoFileClip(video_path)
        vd, w, h = video.duration, video.w, video.h
        has_audio = video.audio is not None
        video.close()
        if abs(vd-ad) > 3: return False, f"Duration mismatch"
        if not has_audio: return False, "No audio"
        print(f"✅ Video {vd:.1f}s {w}x{h} audio OK")
    except Exception as e:
        return False, f"Check error {e}"
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
print(f"📅 Today: {today_str}")

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
        
        if model:
            prompt = f"You are Telugu Gita teacher for YouTube Shorts 60 sec. Sanskrit: {sanskrit} Chapter {row['Chapter No']} Verse {row['Sloka No']}. Write 180 words Telugu: Sanskrit + Telugu meaning + daily use + Jai Shri Krishna. Simple Telugu."
            telugu_script = model.generate_content(prompt).text
        else:
            telugu_script = f"{row['Chapter Name']} {row['Sloka Reference']} - {sanskrit}. Meaning in Telugu: This sloka teaches dharma..."
        
        print(telugu_script[:200])
        
        async def make_short():
            print("🎤 Generating voice Mohan...")
            await edge_tts.Communicate(telugu_script, "te-IN-MohanNeural").save("gita_voice.mp3")
            print("✅ Voice done")
            
            audio = AudioFileClip("gita_voice.mp3")
            print(f"🎬 Creating video duration {audio.duration}s (FAST mode ultrafast)...")
            bg = ColorClip(size=(1080,1920), color=(25,15,5), duration=audio.duration)
            final = bg.set_audio(audio)
            # FAST PRESET - 10x faster
            final.write_videofile("GITA_SHORT.mp4", fps=24, codec='libx264', audio_codec='aac', preset='ultrafast', threads=2, logger=None)
            print("✅ Video created")
            audio.close()
            final.close()
            
            passed, msg = quality_check("GITA_SHORT.mp4", "gita_voice.mp3", is_short=True)
            if passed:
                title = f"Bhagavad Gita {row['Sloka Reference']} | {row['Chapter Name']} Telugu #Shorts"
                desc = f"{telugu_script}\n\nSanskrit: {sanskrit}\n#GitaTelugu #SanatanaVahini"
                upload_youtube("GITA_SHORT.mp4", title, desc, ["Gita Telugu","Shorts"])
            else:
                print(f"❌ QC Failed {msg}")
        
        asyncio.run(make_short())
    else:
        print("No Gita sloka today in sheet")
except Exception as e:
    print(f"Error in Gita daily: {e}")
    import traceback; traceback.print_exc()

# WEEKLY FULL
try:
    MAIN_CSV = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
    df_main = pd.read_csv(MAIN_CSV)
    df_main['Release Date'] = pd.to_datetime(df_main['Release Date'], errors='coerce')
    weekly_today = df_main[df_main['Release Date'] == today_dt]
    
    if not weekly_today.empty:
        fr = weekly_today.iloc[0]
        print(f"\n🎯 WEEKLY FULL TODAY: {fr['Video ID']} - {fr['Video Topic']}")
        # Full video logic can be added here
    else:
        print("No full video today - only daily short")
except Exception as e:
    print(f"Error weekly: {e}")
