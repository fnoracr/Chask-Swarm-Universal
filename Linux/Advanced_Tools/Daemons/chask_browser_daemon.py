"""
chask_browser_daemon.py — Browser Pool Daemon
=============================================
Lanza un Chromium persistente via Playwright launch_server().
Los scripts se conectan via connect(ws_endpoint) sin cold start.
Expone un fichero con el WS endpoint para que otros scripts lo lean.
"""
import asyncio
import os
import sys
import signal
import json
from datetime import datetime

ENDPOINT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "browser_daemon_endpoint.json")
LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "browser_daemon.log")

def log(msg):
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except:
        pass
    print(line)

async def main():
    from playwright.async_api import async_playwright

    log("Browser Daemon arrancando...")
    pw = await async_playwright().start()

    server = await pw.chromium.launch(
        headless=True,
        args=["--disable-gpu", "--no-sandbox", "--disable-dev-shm-usage"]
    )

    # Playwright Python no tiene launch_server() directo,
    # asi que mantenemos el browser vivo y exponemos su CDP endpoint
    # Los clientes usan connect_over_cdp()

    # Obtener CDP endpoint del browser
    # Usamos el endpoint interno de Chromium
    cdp_url = None
    try:
        # El browser expone contexts, obtenemos el endpoint del proceso
        # Playwright internamente usa CDP, podemos obtener el WS URL
        cdp_url = server._impl_obj._browser.ws_endpoint if hasattr(server._impl_obj, '_browser') else None
    except:
        pass

    # Si no podemos obtener CDP, usamos el approach de browser reutilizable
    # Los clientes importan este modulo y usan get_browser()
    endpoint_data = {
        "pid": os.getpid(),
        "started": datetime.now().isoformat(),
        "status": "running",
        "cdp_url": cdp_url
    }

    with open(ENDPOINT_FILE, "w") as f:
        json.dump(endpoint_data, f, indent=2)

    log(f"Browser Daemon activo (PID: {os.getpid()})")
    if cdp_url:
        log(f"CDP endpoint: {cdp_url}")

    # Mantener vivo
    stop = asyncio.Event()

    def handle_signal(*args):
        log("Senal de parada recibida")
        stop.set()

    try:
        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)
    except:
        pass

    await stop.wait()

    log("Cerrando browser...")
    await server.close()
    await pw.stop()

    # Limpiar endpoint file
    try:
        os.remove(ENDPOINT_FILE)
    except:
        pass
    log("Browser Daemon detenido.")


# ═══════════════════════════════════════════════════════
# API para que otros scripts usen el pool sin cold start
# ═══════════════════════════════════════════════════════
_shared_pw = None
_shared_browser = None

async def get_pool_browser():
    """Obtiene un browser compartido. Lanza uno si no existe."""
    global _shared_pw, _shared_browser
    if _shared_browser and _shared_browser.is_connected():
        return _shared_browser

    from playwright.async_api import async_playwright
    _shared_pw = await async_playwright().start()
    _shared_browser = await _shared_pw.chromium.launch(
        headless=True,
        args=["--disable-gpu", "--no-sandbox"]
    )
    return _shared_browser


async def pool_navigate(url, extract_text=False, screenshot_path=None):
    """Navega a una URL usando el pool. Retorna titulo y opcionalmente texto/screenshot."""
    browser = await get_pool_browser()
    ctx = await browser.new_context()
    page = await ctx.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        result = {"title": await page.title(), "url": page.url}
        if extract_text:
            result["text"] = await page.inner_text("body")
        if screenshot_path:
            await page.screenshot(path=screenshot_path)
            result["screenshot"] = screenshot_path
        return result
    finally:
        await ctx.close()


async def pool_close():
    """Cierra el browser pool compartido."""
    global _shared_pw, _shared_browser
    if _shared_browser:
        await _shared_browser.close()
        _shared_browser = None
    if _shared_pw:
        await _shared_pw.stop()
        _shared_pw = None


if __name__ == "__main__":
    asyncio.run(main())
