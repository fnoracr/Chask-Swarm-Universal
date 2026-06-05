import os
import json
import socket
import threading
import sys
from qdrant_client import QdrantClient

# [Nombre_IA] Edu Daemon
HOST = "0.0.0.0"
PORT = 51401

def check_compliance(text):
    # Basic local compliance check for sharing to P2P network
    # As requested by the user: "determinar si tiene o no contenido no admisible (sexo, drogas, racismo, etc)"
    bad_words = ["sexo explicito", "droga ilegal", "racismo", "odio", "violencia extrema"]
    for w in bad_words:
        if w in text.lower():
            return False
    return True

def handle_client(conn, addr):
    try:
        data = conn.recv(8192).decode('utf-8')
        if not data: return
        
        request = json.loads(data)
        action = request.get("action")
        topic_id = request.get("topic_id")
        
        if action == "DOWNLOAD_TOPIC":
            print(f"[P2P] Peer {addr} solicito el tema {topic_id}")
            try:
                client = QdrantClient("localhost", port=6333)
                records, _ = client.scroll(
                    collection_name=topic_id,
                    limit=1000,
                    with_payload=True,
                    with_vectors=False
                )
                
                lessons = []
                for r in records:
                    content = r.payload.get("content", "")
                    if not check_compliance(content):
                        conn.sendall(json.dumps({"success": False, "error": "Compliance Check Failed: Contenido Inadmisible"}).encode('utf-8'))
                        return
                    lessons.append(r.payload)
                    
                response = {"success": True, "topic_id": topic_id, "lessons": lessons}
                
                # We chunk the send if it's too big, but for now standard send
                payload = json.dumps(response).encode('utf-8')
                # Send size first
                conn.sendall(str(len(payload)).zfill(10).encode('utf-8'))
                conn.sendall(payload)
                print(f"[P2P] Tema {topic_id} enviado a {addr} con exito.")
            except Exception as e:
                conn.sendall(json.dumps({"success": False, "error": str(e)}).encode('utf-8'))
            
    except Exception as e:
        print(f"P2P Error: {e}")
    finally:
        conn.close()

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"[Colmena] Colmena P2P Education Daemon escuchando en {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_client, args=(conn, addr)).start()

if __name__ == "__main__":
    start_server()
