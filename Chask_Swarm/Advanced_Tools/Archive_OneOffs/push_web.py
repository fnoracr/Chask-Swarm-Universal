import sys, requests, os

def push(message):
    url = "http://localhost:7860/web_send"
    try:
        requests.post(url, json={"message": message}, timeout=5)
        print("[WebPush] OK")
    except Exception as e:
        print(f"[WebPush] Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        msg = " ".join(sys.argv[1:])
        push(msg)
