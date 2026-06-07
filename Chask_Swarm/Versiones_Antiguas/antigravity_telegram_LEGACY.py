import sys
import time
import requests
import json
import os
import speech_recognition as sr
from pydub import AudioSegment

CONFIG_PATH = r"C:\Program Files\Chask_Swarm\agents_config.json"
STATE_FILE = r"C:\Program Files\Chask_Swarm\telegram_state.txt"
MEDIA_DIR = r"C:\Program Files\Chask_Swarm\telegram_media"

# Setup ffmpeg for pydub
ffmpeg_path = r"C:\Program Files\Chask_Swarm\ffmpeg.exe"
AudioSegment.converter = ffmpeg_path
AudioSegment.ffprobe = ffmpeg_path

if not os.path.exists(MEDIA_DIR):
    os.makedirs(MEDIA_DIR)

def get_config():
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)['credentials']

def get_last_update_id():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return int(f.read().strip())
    return 0

def save_last_update_id(update_id):
    with open(STATE_FILE, 'w') as f:
        f.write(str(update_id))

def send_message(text):
    creds = get_config()
    token = creds['telegram_bot']
    admin_id = creds['telegram_admin']
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": admin_id, "text": text}
    requests.post(url, json=payload)

def download_telegram_file(token, file_id, ext):
    url = f"https://api.telegram.org/bot{token}/getFile?file_id={file_id}"
    resp = requests.get(url).json()
    if resp.get('ok'):
        file_path = resp['result']['file_path']
        download_url = f"https://api.telegram.org/file/bot{token}/{file_path}"
        file_data = requests.get(download_url).content
        local_path = os.path.join(MEDIA_DIR, f"{file_id}.{ext}")
        with open(local_path, 'wb') as f:
            f.write(file_data)
        return local_path
    return None

def transcribe_audio(file_path):
    try:
        wav_path = file_path.replace('.ogg', '.wav')
        audio = AudioSegment.from_ogg(file_path)
        audio.export(wav_path, format="wav")
        
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language="es-ES")
            return text
    except Exception as e:
        return f"[Error en transcripción de voz: {e}]"

def process_message(update, token):
    if 'message' not in update: return ""
    msg = update['message']
    
    final_text = []
    
    if 'photo' in msg:
        # Get highest resolution photo
        photo = msg['photo'][-1]
        local_path = download_telegram_file(token, photo['file_id'], 'jpg')
        caption = msg.get('caption', '')
        if local_path:
            final_text.append(f"[IMAGEN ADJUNTA: {local_path}]")
        if caption:
            final_text.append(caption)
            
    if 'voice' in msg:
        voice = msg['voice']
        local_path = download_telegram_file(token, voice['file_id'], 'ogg')
        if local_path:
            transcription = transcribe_audio(local_path)
            final_text.append(f"[MENSAJE DE VOZ]: {transcription}")
            
    if 'text' in msg:
        final_text.append(msg['text'])
        
    return "\n".join(final_text).strip()

def get_updates_and_wait():
    creds = get_config()
    token = creds['telegram_bot']
    admin_id = creds['telegram_admin']
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    
    last_update_id = get_last_update_id()
    
    if last_update_id == 0:
        resp = requests.get(url).json()
        if resp.get('result'):
            last_update_id = resp['result'][-1]['update_id']
            save_last_update_id(last_update_id)

    while True:
        try:
            resp = requests.get(f"{url}?offset={last_update_id + 1}&timeout=30", timeout=35).json()
            for update in resp.get('result', []):
                last_update_id = update['update_id']
                save_last_update_id(last_update_id)
                if 'message' in update and str(update['message']['chat']['id']) == admin_id:
                    text = process_message(update, token)
                    if text:
                        print(f"INSTRUCTION_RECEIVED: {text}", flush=True)
                        return text
        except Exception as e:
            time.sleep(2)

def check_messages_non_blocking():
    """Read pending messages from the daemon's queue file instead of polling Telegram directly.
    This prevents race conditions where two processes compete for the same getUpdates response."""
    pending_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pending_messages.json")
    try:
        if os.path.exists(pending_file):
            with open(pending_file, "r", encoding="utf-8") as f:
                messages = json.load(f)
            # Find first pending message
            for msg in messages:
                if msg.get("status") == "pending":
                    print(f"INSTRUCTION_RECEIVED: {msg['text']}", flush=True)
                    return msg['text']
    except Exception as e:
        print(f"ERROR_READING_QUEUE: {e}", flush=True)
    print("NO_MESSAGES", flush=True)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "send":
            text = " ".join(sys.argv[2:])
            send_message(text)
        elif command == "ask":
            text = " ".join(sys.argv[2:])
            send_message(text)
            get_updates_and_wait()
        elif command == "listen":
            get_updates_and_wait()
        elif command == "check":
            check_messages_non_blocking()
