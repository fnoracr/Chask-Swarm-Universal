import sys
import os
import json
import time
import argparse
import urllib.request
import urllib.error

def send_to_discord(message):
    time.sleep(1) # Simple rate limit
    
    config_path = r"C:\Program Files\Chask_Swarm\Configuracion\channels_config.json"
    if not os.path.exists(config_path):
        sys.stderr.write(f"Error: {config_path} not found.\n")
        sys.exit(1)
        
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception as e:
        sys.stderr.write(f"Error reading config: {e}\n")
        sys.exit(1)
        
    webhook_url = cfg.get("channels", {}).get("discord", {}).get("webhook_url")
    if not webhook_url:
        sys.stderr.write("Error: discord webhook_url not found in config.\n")
        sys.exit(1)
        
    payload = json.dumps({"content": message}).encode("utf-8")
    req = urllib.request.Request(webhook_url, data=payload, headers={"Content-Type": "application/json"})
    
    try:
        with urllib.request.urlopen(req) as response:
            res = response.read().decode("utf-8")
            return res
    except urllib.error.HTTPError as e:
        sys.stderr.write(f"HTTPError {e.code}: {e.read().decode('utf-8', errors='replace')}\n")
        sys.exit(1)
    except urllib.error.URLError as e:
        sys.stderr.write(f"URLError: {e.reason}\n")
        sys.exit(1)

def send_to_web(message):
    time.sleep(1) # Simple rate limit
    url = "http://localhost:7860/web_send"
    payload = json.dumps({"message": message}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    
    try:
        with urllib.request.urlopen(req) as response:
            res = response.read().decode("utf-8")
            return res
    except urllib.error.HTTPError as e:
        sys.stderr.write(f"HTTPError {e.code}: {e.read().decode('utf-8', errors='replace')}\n")
        sys.exit(1)
    except urllib.error.URLError as e:
        sys.stderr.write(f"URLError: {e.reason}\n")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Unified Channel Sender")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    web_parser = subparsers.add_parser("web", help="Send message to local web dashboard")
    web_parser.add_argument("--message", required=True, help="Message to send")
    web_parser.add_argument("--limit", type=int, default=1, help="Rate limit constraint (ignored for simple functionality, enforced internally)")
    web_parser.add_argument("--output", required=True, help="Output file to store result")
    
    discord_parser = subparsers.add_parser("discord", help="Send message to Discord webhook")
    discord_parser.add_argument("--message", required=True, help="Message to send")
    discord_parser.add_argument("--limit", type=int, default=1, help="Rate limit constraint (ignored for simple functionality, enforced internally)")
    discord_parser.add_argument("--output", required=True, help="Output file to store result")
    
    args = parser.parse_args()
    
    if args.command == "web":
        res = send_to_web(args.message)
    elif args.command == "discord":
        res = send_to_discord(args.message)
        
    try:
        out_data = json.loads(res) if res else {"status": "ok"}
    except:
        out_data = {"status": "ok", "raw": res}
        
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(out_data, f, indent=2)
        
    print(f"Success! Data written to: {args.output}")

if __name__ == "__main__":
    main()
