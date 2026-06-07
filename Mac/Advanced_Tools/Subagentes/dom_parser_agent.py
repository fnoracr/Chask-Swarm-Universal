import re

class AgenticDOMParser:
    """
    Subagente encargado de convertir un DOM complejo (HTML)
    en un árbol semántico simplificado (Markdown-like) para consumo
    eficiente por modelos de lenguaje, ahorrando tokens y reduciendo
    alucinaciones al navegar por DrissionPage o Playwright.
    """
    def __init__(self):
        self.ignore_tags = ['script', 'style', 'svg', 'path', 'noscript', 'meta', 'link', 'iframe']

    def parse_html(self, html_content: str) -> str:
        """
        Limpia el HTML crudo y lo convierte en un formato texto legible para el agente.
        """
        # Eliminar comentarios
        html_content = re.sub(r'<!--.*?-->', '', html_content, flags=re.DOTALL)
        
        # Eliminar tags ignorados con su contenido
        for tag in self.ignore_tags:
            html_content = re.sub(f'<{tag}[^>]*>.*?</{tag}>', '', html_content, flags=re.IGNORECASE | re.DOTALL)
            html_content = re.sub(f'<{tag}[^>]*/>', '', html_content, flags=re.IGNORECASE)
            
        # Extraer elementos interactivos con atributos clave (id, href, class, value, placeholder)
        # Esto es un simplificador rudo, en un caso real se usaría BeautifulSoup.
        
        # Simplificar tags a algo leíble
        # Ejemplo: <a href="link">texto</a> -> [LINK: texto](link)
        html_content = re.sub(r'<a[^>]+href=["\'](.*?)["\'][^>]*>(.*?)</a>', r'[LINK: \2](\1)', html_content, flags=re.IGNORECASE | re.DOTALL)
        
        # <button id="btn">texto</button> -> [BUTTON id="btn"]: texto
        html_content = re.sub(r'<button[^>]*id=["\'](.*?)["\'][^>]*>(.*?)</button>', r'[BUTTON id="\1"]: \2', html_content, flags=re.IGNORECASE | re.DOTALL)
        
        # Inputs
        html_content = re.sub(r'<input[^>]*placeholder=["\'](.*?)["\'][^>]*>', r'[INPUT placeholder="\1"]', html_content, flags=re.IGNORECASE)
        
        # Eliminar el resto de tags HTML dejando solo texto
        semantic_text = re.sub(r'<[^>]+>', '\n', html_content)
        
        # Limpiar saltos de línea y espacios en blanco excesivos
        semantic_text = re.sub(r'\n\s*\n', '\n', semantic_text).strip()
        
        return semantic_text

    def parse_drission_page(self, page) -> str:
        """
        Toma una instancia de ChromiumPage (DrissionPage) y procesa su DOM.
        """
        try:
            return self.parse_html(page.html)
        except Exception as e:
            return f"Error parseando página: {e}"

if __name__ == "__main__":
    parser = AgenticDOMParser()
    sample_html = '''
    <html><body>
        <script>alert(1);</script>
        <div class="header">
            <a href="/login">Iniciar Sesión</a>
        </div>
        <main>
            <h1>Bienvenido</h1>
            <input type="text" placeholder="Buscar propiedades...">
            <button id="submitBtn">Buscar</button>
            <svg><path d="M10 10"/></svg>
        </main>
    </body></html>
    '''
    print("Test de Parseo Semántico:")
    print("-------------------------")
    print(parser.parse_html(sample_html))
    print("-------------------------")
