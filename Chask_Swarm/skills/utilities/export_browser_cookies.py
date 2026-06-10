#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
export_browser_cookies.py — Extractor Automático de Cookies de Navegador
========================================================================
Detecta e intenta extraer de forma automática y local las cookies de YouTube 
encriptadas en Google Chrome y Microsoft Edge en Windows usando DPAPI.
Permite iniciar la descarga de vídeos sin interacción del usuario.

Diseñado por Enjambre para el ecosistema Chask Swarm.
"""

import os
import sys
import json
import base64
import shutil
import sqlite3
import win32crypt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

BASE_DIR = r"C:\Program Files\Chask_Swarm"
DEFAULT_OUTPUT = os.path.join(r"C:\Users\fnora\Desktop\Enjambre Datos", "youtube_cookies.txt")

def get_chrome_key(local_state_path: str) -> bytes | None:
    """Extrae y desencripta la clave maestra AES de Chrome con DPAPI."""
    if not os.path.exists(local_state_path):
        return None
    try:
        with open(local_state_path, "r", encoding="utf-8") as f:
            local_state = json.load(f)
        encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
        # Quitar prefijo DPAPI (primeros 5 bytes)
        encrypted_key = encrypted_key[5:]
        # Desencriptar usando DPAPI Windows
        decrypted_key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
        return decrypted_key
    except Exception as e:
        print(f"[Error] No se pudo obtener la clave maestra AES: {e}")
        return None

def decrypt_cookie_value(encrypted_val: bytes, key: bytes) -> str:
    """Desencripta un valor de cookie cifrado con AES-GCM (Chrome 80+)."""
    try:
        # Chrome usa el prefijo v10 o v11 (3 bytes)
        prefix = encrypted_val[:3]
        if prefix in (b'v10', b'v11'):
            iv = encrypted_val[3:15]
            ciphertext = encrypted_val[15:]
            aesgcm = AESGCM(key)
            decrypted = aesgcm.decrypt(iv, ciphertext, None)
            return decrypted.decode('utf-8', errors='replace')
        else:
            # Fallback a DPAPI tradicional (versiones antiguas)
            return win32crypt.CryptUnprotectData(encrypted_val, None, None, None, 0)[1].decode('utf-8', errors='replace')
    except Exception:
        return ""

def dump_cookies_netscape(db_path: str, local_state_path: str, output_path: str) -> bool:
    """Extrae las cookies de YouTube y las guarda en formato Netscape."""
    if not os.path.exists(db_path) or not os.path.exists(local_state_path):
        return False
        
    key = get_chrome_key(local_state_path)
    if not key:
        return False

    # Crear copia temporal de la base de datos para no bloquear el navegador activo
    temp_db = os.path.join(os.environ["TEMP"], "temp_cookies.db")
    try:
        shutil.copyfile(db_path, temp_db)
    except Exception as e:
        print(f"[Error] No se pudo duplicar el archivo de cookies: {e}")
        return False

    try:
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # Consultar cookies asociadas a YouTube
        query = """
        SELECT host_key, path, is_secure, expires_utc, name, value, encrypted_value 
        FROM cookies 
        WHERE host_key LIKE '%youtube.com%' OR host_key LIKE '%google.com%'
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        
        cookies_written = 0
        with open(output_path, "w", encoding="utf-8") as f:
            # Cabecera Netscape Cookies
            f.write("# Netscape HTTP Cookie File\n")
            f.write("# http://curl.haxx.se/rfc/cookie_spec.html\n")
            f.write("# This is a generated file! Do not edit.\n\n")
            
            for row in rows:
                host, path, secure, expires, name, val, enc_val = row
                
                # Desencriptar si tiene valor encriptado
                decrypted_val = ""
                if enc_val:
                    decrypted_val = decrypt_cookie_value(enc_val, key)
                else:
                    decrypted_val = val
                    
                if not decrypted_val:
                    continue
                    
                # Formatear al formato Netscape
                # domain - FALSE/TRUE - path - FALSE/TRUE - expiration - name - value
                is_domain = "TRUE" if host.startswith(".") else "FALSE"
                is_secure = "TRUE" if secure else "FALSE"
                
                # Convertir timestamp de Chrome (microsegundos desde 1601) a Unix Epoch
                expires_unix = 0
                if expires > 0:
                    expires_unix = int((expires / 1000000) - 11644473600)
                    if expires_unix < 0:
                        expires_unix = 0
                
                line = f"{host}\t{is_domain}\t{path}\t{is_secure}\t{expires_unix}\t{name}\t{decrypted_val}\n"
                f.write(line)
                cookies_written += 1
                
        conn.close()
        try:
            os.remove(temp_db)
        except Exception:
            pass
            
        if cookies_written > 0:
            print(f"[Éxito] Se extrajeron e indexaron {cookies_written} cookies en {output_path}")
            return True
        return False
    except Exception as e:
        print(f"[Error] Excepción durante la lectura de la BD de cookies: {e}")
        if os.path.exists(temp_db):
            try:
                conn.close()
                os.remove(temp_db)
            except Exception: pass
        return False

def main():
    print("=== EXTRACTOR AUTOMÁTICO DE COOKIES ACADÉMICAS DE YOUTUBE ===")
    
    # Rutas estándar de Chrome y Edge en Windows
    user_profile = os.environ["USERPROFILE"]
    
    browsers = [
        {
            "name": "Google Chrome",
            "db": os.path.join(user_profile, r"AppData\Local\Google\Chrome\User Data\Default\Network\Cookies"),
            "state": os.path.join(user_profile, r"AppData\Local\Google\Chrome\User Data\Local State")
        },
        {
            "name": "Microsoft Edge",
            "db": os.path.join(user_profile, r"AppData\Local\Microsoft\Edge\User Data\Default\Network\Cookies"),
            "state": os.path.join(user_profile, r"AppData\Local\Microsoft\Edge\User Data\Local State")
        }
    ]
    
    success = False
    for browser in browsers:
        print(f"Buscando sesión activa en {browser['name']}...")
        if os.path.exists(browser["db"]):
            if dump_cookies_netscape(browser["db"], browser["state"], DEFAULT_OUTPUT):
                success = True
                break
        else:
            print(f"  -> No se encontró base de datos para {browser['name']}")

    if success:
        print(f"\n[FINALIZADO] Archivo generado de forma segura en: {DEFAULT_OUTPUT}")
        print("Ahora puedes correr tu indexador sin configurar contraseñas ni 2FA.")
    else:
        print("\n[Fallo] No se pudieron extraer cookies automáticamente.")
        print("Asegúrate de tener Chrome o Edge cerrados, o exporta el archivo cookies.txt usando la extensión del navegador.")

if __name__ == "__main__":
    main()
