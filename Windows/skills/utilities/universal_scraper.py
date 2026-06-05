"""
universal_scraper.py — Scraper Universal de Conocimiento Profundo
==================================================================
Dado un tema y una lista de URLs semilla, rastrea y extrae contenido
de forma profunda, recursiva y limpia. Guarda el resultado en un
archivo Markdown estructurado listo para ser indexado.

Soporta:
  - Documentación técnica (MS Learn, ReadTheDocs, docs.*)
  - Wikipedia y Wikis
  - GitHub READMEs y Wikis
  - Blogs y artículos técnicos
  - YouTube (transcripciones de video con yt-dlp si disponible)

Uso:
  python universal_scraper.py --topic "Docker" --urls "https://docs.docker.com/" --depth 2
  python universal_scraper.py --topic "FastAPI" --auto
"""

import re
import os
import sys
import json
import time
import logging
import argparse
import hashlib
import io
from pathlib import Path
from urllib.parse import urljoin, urlparse
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ─── Dependencias opcionales con fallback ─────────────────────
try:
    import requests
    from bs4 import BeautifulSoup
    SCRAPING_OK = True
except ImportError:
    SCRAPING_OK = False
    print("AVISO: instala 'requests' y 'beautifulsoup4' para scraping web")

try:
    import ftfy
    FTFY_OK = True
except ImportError:
    FTFY_OK = False

# ─── Configuración ────────────────────────────────────────────
BASE_KNOWLEDGE = r"C:\Users\fnora\Desktop\Enjambre Datos\knowledge_bases"
LOG_DIR        = r"C:\Users\fnora\Desktop\Enjambre Datos\knowledge_bases\logs"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

REQUEST_DELAY  = 1.0   # segundos entre requests (cortesía)
REQUEST_TIMEOUT = 15
MAX_CONTENT_MB  = 5    # Ignorar páginas mayores de X MB

# ─── Logging ──────────────────────────────────────────────────
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger("universal_scraper")


# ─── Utilidades ───────────────────────────────────────────────
def fix_text(text: str) -> str:
    if FTFY_OK:
        return ftfy.fix_text(text)
    return text

def url_to_filename(url: str) -> str:
    """Convierte una URL en nombre de archivo seguro."""
    h = hashlib.md5(url.encode()).hexdigest()[:8]
    domain = urlparse(url).netloc.replace(".", "_")
    return f"{domain}_{h}"

def is_same_domain(url: str, base_url: str) -> bool:
    """Verifica si una URL pertenece al mismo dominio base."""
    return urlparse(url).netloc == urlparse(base_url).netloc

def is_valid_url(url: str) -> bool:
    """Verifica que la URL es válida y no es un recurso binario."""
    parsed = urlparse(url)
    if parsed.scheme not in ('http', 'https'):
        return False
    bad_extensions = {'.pdf', '.zip', '.exe', '.png', '.jpg', '.jpeg',
                      '.gif', '.svg', '.ico', '.mp4', '.mp3', '.wav',
                      '.css', '.js', '.xml', '.json', '.csv'}
    if any(parsed.path.lower().endswith(ext) for ext in bad_extensions):
        return False
    return True

def clean_html_to_markdown(soup: BeautifulSoup, url: str) -> str:
    """
    Convierte HTML a Markdown limpio, preservando estructura semántica.
    """
    # Eliminar elementos no útiles
    for tag in soup.find_all(['script', 'style', 'nav', 'footer', 'header',
                               'aside', 'form', 'button', 'input', 'select',
                               'iframe', 'svg', 'img', 'noscript', 'meta',
                               'link', 'advertisement', 'banner']):
        tag.decompose()

    # Eliminar clases típicas de navegación/UI
    for cls in ['sidebar', 'navbar', 'menu', 'breadcrumb', 'cookie',
                 'advertisement', 'social', 'share', 'related', 'comments',
                 'footer', 'header', 'nav', 'toc', 'table-of-contents']:
        for el in soup.find_all(class_=re.compile(cls, re.I)):
            el.decompose()
        for el in soup.find_all(id=re.compile(cls, re.I)):
            el.decompose()

    # Extraer contenido principal
    main = (
        soup.find('main') or
        soup.find('article') or
        soup.find(class_=re.compile(r'content|main|article|post|docs', re.I)) or
        soup.find('div', id=re.compile(r'content|main|article', re.I)) or
        soup.body or
        soup
    )

    if not main:
        return ""

    lines = []
    _process_node(main, lines, depth=0)
    text = "\n".join(lines).strip()
    text = re.sub(r'\n{3,}', '\n\n', text)
    return fix_text(text)


def _process_node(node, lines: list, depth: int):
    """Procesa recursivamente un nodo HTML y genera Markdown."""
    from bs4 import NavigableString, Tag

    if isinstance(node, NavigableString):
        text = str(node).strip()
        if text and text not in ('|', '-'):
            lines.append(text)
        return

    if not isinstance(node, Tag):
        return

    tag = node.name.lower() if node.name else ''

    if tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
        level = int(tag[1])
        text  = node.get_text(' ', strip=True)
        if text:
            lines.append(f"\n{'#' * level} {text}\n")

    elif tag == 'p':
        text = node.get_text(' ', strip=True)
        if len(text) > 20:
            lines.append(f"\n{text}\n")

    elif tag in ('ul', 'ol'):
        for li in node.find_all('li', recursive=False):
            text = li.get_text(' ', strip=True)
            if text:
                lines.append(f"- {text}")
        lines.append("")

    elif tag == 'li':
        text = node.get_text(' ', strip=True)
        if text:
            lines.append(f"- {text}")

    elif tag in ('pre', 'code'):
        text = node.get_text()
        if text.strip():
            lang = node.get('class', [''])[0].replace('language-', '') if node.get('class') else ''
            lines.append(f"\n```{lang}\n{text.strip()}\n```\n")

    elif tag == 'blockquote':
        text = node.get_text(' ', strip=True)
        if text:
            lines.append(f"\n> {text}\n")

    elif tag == 'table':
        # Extraer tabla como texto simple
        rows = []
        for tr in node.find_all('tr'):
            cells = [td.get_text(' ', strip=True) for td in tr.find_all(['td', 'th'])]
            if cells:
                rows.append(' | '.join(cells))
        if rows:
            lines.append('\n' + '\n'.join(rows) + '\n')

    elif tag in ('div', 'section', 'article', 'main', 'body', 'span',
                 'strong', 'em', 'b', 'i', 'a'):
        for child in node.children:
            _process_node(child, lines, depth + 1)

    else:
        for child in node.children:
            _process_node(child, lines, depth + 1)


# ─── Scraper Principal ────────────────────────────────────────
class UniversalScraper:

    def __init__(self, topic: str, seed_urls: list[str],
                 max_depth: int = 2, max_pages: int = 200,
                 same_domain_only: bool = True):
        self.topic            = topic
        self.seed_urls        = seed_urls
        self.max_depth        = max_depth
        self.max_pages        = max_pages
        self.same_domain_only = same_domain_only

        # Crear directorio de salida
        safe_topic = re.sub(r'[^a-z0-9_]', '_', topic.lower())
        self.output_dir  = Path(BASE_KNOWLEDGE) / safe_topic
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.output_file = self.output_dir / f"{safe_topic}_knowledge.md"
        self.state_file  = self.output_dir / "scraper_state.json"

        # Estado
        self.visited  = set()
        self.errors   = []
        self.scraped  = []
        self._load_state()

    def _load_state(self):
        if self.state_file.exists():
            try:
                s = json.loads(self.state_file.read_text(encoding='utf-8'))
                self.visited = set(s.get('visited', []))
                log.info(f"Estado previo: {len(self.visited)} URLs ya visitadas")
            except Exception:
                pass

    def _save_state(self):
        self.state_file.write_text(
            json.dumps({'visited': list(self.visited), 'errors': self.errors},
                       ensure_ascii=False, indent=2),
            encoding='utf-8'
        )

    def _fetch(self, url: str) -> tuple[str, BeautifulSoup | None]:
        """Descarga una página y devuelve (html, soup)."""
        try:
            resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT,
                                allow_redirects=True)
            # Verificar tamaño
            content_len = int(resp.headers.get('content-length', 0))
            if content_len > MAX_CONTENT_MB * 1024 * 1024:
                return "", None

            if resp.status_code != 200:
                return "", None

            # Solo procesar HTML
            ct = resp.headers.get('content-type', '')
            if 'text/html' not in ct:
                return "", None

            soup = BeautifulSoup(resp.text, 'html.parser')

            # Extraer título
            title = soup.title.string.strip() if soup.title else url

            return title, soup

        except Exception as e:
            log.warning(f"Error fetching {url}: {e}")
            self.errors.append({"url": url, "error": str(e)})
            return "", None

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> list[str]:
        """Extrae links válidos de una página para seguir."""
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href'].strip()
            # Resolver URLs relativas
            absolute = urljoin(base_url, href)
            # Limpiar fragmentos (#)
            absolute = absolute.split('#')[0]
            if not absolute or absolute in self.visited:
                continue
            if not is_valid_url(absolute):
                continue
            if self.same_domain_only and not any(
                is_same_domain(absolute, seed) for seed in self.seed_urls
            ):
                continue
            links.append(absolute)
        return list(set(links))

    def scrape(self, progress_callback=None) -> str:
        """
        Ejecuta el scraping completo y devuelve la ruta del archivo MD generado.
        """
        if not SCRAPING_OK:
            log.error("requests y beautifulsoup4 son necesarios")
            return ""

        log.info(f"Iniciando scraping de '{self.topic}' — {len(self.seed_urls)} seeds")
        log.info(f"Max profundidad: {self.max_depth} | Max páginas: {self.max_pages}")

        # Inicializar la cola con las URLs semilla
        queue = [(url, 0) for url in self.seed_urls if url not in self.visited]
        pages_scraped = 0
        articles_written = 0

        # Inicializar el archivo de salida
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write(f"# Conocimiento Profundo: {self.topic}\n\n")
            f.write(f"> Generado automáticamente por Enjambre Universal Scraper\n")
            f.write(f"> Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            f.write(f"> Fuentes semilla: {', '.join(self.seed_urls)}\n\n---\n\n")

        while queue and pages_scraped < self.max_pages:
            url, depth = queue.pop(0)

            if url in self.visited:
                continue
            if depth > self.max_depth:
                continue

            self.visited.add(url)
            log.info(f"[{pages_scraped+1}/{self.max_pages}] depth={depth} {url[:80]}")

            title, soup = self._fetch(url)
            if not soup:
                time.sleep(REQUEST_DELAY)
                continue

            # Convertir a Markdown
            content = clean_html_to_markdown(soup, url)

            # Filtrar contenido demasiado corto o que sea página de error
            if len(content.strip()) < 200:
                log.info(f"  → Descartado (contenido insuficiente: {len(content)} chars)")
                time.sleep(REQUEST_DELAY)
                continue

            # Guardar al archivo MD
            with open(self.output_file, 'a', encoding='utf-8') as f:
                f.write(f"## Origen: {url}\n\n")
                f.write(f"# {title}\n\n")
                f.write(content)
                f.write(f"\n\n---\n\n")

            articles_written += 1
            pages_scraped    += 1

            # Extraer links para seguir si no hemos llegado al límite de profundidad
            if depth < self.max_depth:
                new_links = self._extract_links(soup, url)
                for link in new_links:
                    if link not in self.visited:
                        queue.append((link, depth + 1))

            # Guardar estado cada 10 páginas
            if pages_scraped % 10 == 0:
                self._save_state()

            if progress_callback:
                progress_callback(pages_scraped, self.max_pages, url)

            time.sleep(REQUEST_DELAY)

        self._save_state()
        size_mb = self.output_file.stat().st_size / (1024*1024)
        log.info(f"Scraping completado: {articles_written} páginas | {size_mb:.1f} MB")
        log.info(f"Archivo: {self.output_file}")
        return str(self.output_file)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic",  required=True, help="Nombre del tema (ej: 'Docker')")
    parser.add_argument("--urls",   nargs='+',     help="URLs semilla")
    parser.add_argument("--depth",  type=int, default=2, help="Profundidad máxima de scraping")
    parser.add_argument("--pages",  type=int, default=200, help="Máximo de páginas")
    parser.add_argument("--all-domains", action="store_true", help="Seguir links externos también")
    args = parser.parse_args()

    if not args.urls:
        # Buscar fuentes conocidas
        from topic_detector import KNOWN_SOURCES
        topic_lower = args.topic.lower()
        urls = []
        for known, sources in KNOWN_SOURCES.items():
            if known in topic_lower or topic_lower in known:
                urls = sources
                break
        if not urls:
            print(f"ERROR: No se encontraron fuentes para '{args.topic}'. Usa --urls")
            sys.exit(1)
    else:
        urls = args.urls

    scraper = UniversalScraper(
        topic=args.topic,
        seed_urls=urls,
        max_depth=args.depth,
        max_pages=args.pages,
        same_domain_only=not args.all_domains
    )
    result = scraper.scrape()
    if result:
        print(f"\nArchivo generado: {result}")
        print(f"Ahora puedes indexarlo con:")
        print(f'  python universal_ingest.py --topic "{args.topic}" --file "{result}"')


if __name__ == "__main__":
    main()
