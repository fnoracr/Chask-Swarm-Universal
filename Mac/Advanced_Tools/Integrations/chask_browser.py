"""
chask_browser.py — Control Total de Navegador via Playwright
=============================================================
Wrapper unificado para que Enjambre controle Chrome/Firefox/WebKit
con API limpia, modo headless o visible, y conexion a Chrome existente.

Uso desde CLI:
  python chask_browser.py go "https://google.com"
  python chask_browser.py screenshot "https://example.com" --output captura.png
  python chask_browser.py extract "https://example.com" "h1"

Uso desde codigo:
  from chask_browser import [Nombre_IA]Browser
  async with [Nombre_IA]Browser() as browser:
      await browser.go("https://google.com")
      text = await browser.extract("h1")
"""
import asyncio
import argparse
import json
import os
import sys
import io

# Fix encoding para consola Windows
if sys.stdout and hasattr(sys.stdout, 'buffer'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except:
        pass

from playwright.async_api import async_playwright

# Configuration
DEFAULT_HEADLESS = True
DEFAULT_TIMEOUT = 30000  # 30s
SCREENSHOTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "browser_screenshots")


class [Nombre_IA]Browser:
    """Control total de navegador con API limpia."""

    def __init__(self, headless=DEFAULT_HEADLESS, browser_type="chromium"):
        self.headless = headless
        self.browser_type = browser_type
        self._pw = None
        self._browser = None
        self._context = None
        self._page = None

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, *args):
        await self.close()

    async def start(self):
        """Inicia el navegador."""
        self._pw = await async_playwright().start()
        launcher = getattr(self._pw, self.browser_type)
        self._browser = await launcher.launch(headless=self.headless)
        self._context = await self._browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        )
        self._page = await self._context.new_page()
        self._page.set_default_timeout(DEFAULT_TIMEOUT)
        return self

    async def connect_to_existing(self, cdp_url="http://localhost:9222"):
        """Conecta a un Chrome ya abierto (con sus cookies y sesiones)."""
        self._pw = await async_playwright().start()
        self._browser = await self._pw.chromium.connect_over_cdp(cdp_url)
        contexts = self._browser.contexts
        if contexts:
            self._context = contexts[0]
            pages = self._context.pages
            self._page = pages[0] if pages else await self._context.new_page()
        else:
            self._context = await self._browser.new_context()
            self._page = await self._context.new_page()
        return self

    async def close(self):
        """Cierra todo limpiamente."""
        if self._browser:
            await self._browser.close()
        if self._pw:
            await self._pw.stop()

    # ── Navegacion ──────────────────────────────────────────
    async def go(self, url, wait_until="domcontentloaded"):
        """Navega a una URL."""
        await self._page.goto(url, wait_until=wait_until)
        return self._page.url

    async def back(self):
        await self._page.go_back()

    async def forward(self):
        await self._page.go_forward()

    async def reload(self):
        await self._page.reload()

    # ── Interaccion ─────────────────────────────────────────
    async def click(self, selector, timeout=5000):
        """Click en un elemento por selector CSS."""
        await self._page.click(selector, timeout=timeout)

    async def type(self, selector, text, delay=50):
        """Escribe texto en un campo."""
        await self._page.fill(selector, "")
        await self._page.type(selector, text, delay=delay)

    async def fill(self, selector, text):
        """Rellena un campo de forma instantanea (sin simular teclas)."""
        await self._page.fill(selector, text)

    async def press(self, key):
        """Presiona una tecla (Enter, Tab, etc.)."""
        await self._page.keyboard.press(key)

    async def select(self, selector, value):
        """Selecciona opcion en un <select>."""
        await self._page.select_option(selector, value)

    # ── Extraccion ──────────────────────────────────────────
    async def extract(self, selector, attribute=None):
        """Extrae texto o atributo de un elemento."""
        el = await self._page.query_selector(selector)
        if not el:
            return None
        if attribute:
            return await el.get_attribute(attribute)
        return await el.inner_text()

    async def extract_all(self, selector):
        """Extrae texto de TODOS los elementos que coincidan."""
        elements = await self._page.query_selector_all(selector)
        return [await el.inner_text() for el in elements]

    async def extract_html(self, selector=None):
        """Extrae el HTML de un elemento o de toda la pagina."""
        if selector:
            el = await self._page.query_selector(selector)
            return await el.inner_html() if el else None
        return await self._page.content()

    # ── Capturas ────────────────────────────────────────────
    async def screenshot(self, path=None, full_page=False):
        """Captura pantalla."""
        if not path:
            os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
            from datetime import datetime
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = os.path.join(SCREENSHOTS_DIR, f"capture_{ts}.png")
        await self._page.screenshot(path=path, full_page=full_page)
        return path

    # ── JavaScript ──────────────────────────────────────────
    async def run_js(self, code):
        """Ejecuta JavaScript arbitrario en la pagina."""
        return await self._page.evaluate(code)

    # ── Esperas ─────────────────────────────────────────────
    async def wait_for(self, selector, timeout=10000):
        """Espera a que un elemento aparezca."""
        await self._page.wait_for_selector(selector, timeout=timeout)

    async def wait_for_navigation(self, timeout=30000):
        """Espera a que termine la navegacion."""
        await self._page.wait_for_load_state("networkidle", timeout=timeout)

    # ── Utilidades ──────────────────────────────────────────
    async def get_url(self):
        return self._page.url

    async def get_title(self):
        return await self._page.title()

    async def get_cookies(self):
        return await self._context.cookies()

    async def set_cookies(self, cookies):
        await self._context.add_cookies(cookies)

    async def pdf(self, path):
        """Genera PDF de la pagina actual (solo Chromium)."""
        await self._page.pdf(path=path)
        return path

    async def new_tab(self, url=None):
        """Abre una nueva pestana."""
        self._page = await self._context.new_page()
        if url:
            await self._page.goto(url)
        return self._page

    async def tabs(self):
        """Lista de pestanas abiertas."""
        return self._context.pages

    async def switch_tab(self, index):
        """Cambia a una pestana por indice."""
        pages = self._context.pages
        if 0 <= index < len(pages):
            self._page = pages[index]
            await self._page.bring_to_front()


# ── CLI ─────────────────────────────────────────────────────
async def cli_main():
    parser = argparse.ArgumentParser(description="Enjambre Browser — Control Total via Playwright")
    sub = parser.add_subparsers(dest="cmd")

    p_go = sub.add_parser("go", help="Navegar a una URL")
    p_go.add_argument("url")
    p_go.add_argument("--visible", action="store_true")

    p_ss = sub.add_parser("screenshot", help="Captura de pantalla")
    p_ss.add_argument("url")
    p_ss.add_argument("--output", default=None)
    p_ss.add_argument("--full", action="store_true")

    p_ex = sub.add_parser("extract", help="Extraer texto de un selector")
    p_ex.add_argument("url")
    p_ex.add_argument("selector")

    p_js = sub.add_parser("js", help="Ejecutar JavaScript")
    p_js.add_argument("url")
    p_js.add_argument("code")

    args = parser.parse_args()

    if not args.cmd:
        parser.print_help()
        return

    headless = not getattr(args, "visible", False)
    async with [Nombre_IA]Browser(headless=headless) as browser:
        if args.cmd == "go":
            url = await browser.go(args.url)
            title = await browser.get_title()
            print(f"[OK] {title} ({url})")

        elif args.cmd == "screenshot":
            await browser.go(args.url)
            path = await browser.screenshot(path=args.output, full_page=args.full)
            print(f"[OK] Screenshot guardado en: {path}")

        elif args.cmd == "extract":
            await browser.go(args.url)
            text = await browser.extract(args.selector)
            print(f"[OK] Texto extraido:\n{text}")

        elif args.cmd == "js":
            await browser.go(args.url)
            result = await browser.run_js(args.code)
            print(f"[OK] Resultado: {result}")


if __name__ == "__main__":
    asyncio.run(cli_main())
""",
"description": "chask_browser.py — Control total de navegador para Enjambre"
"""
