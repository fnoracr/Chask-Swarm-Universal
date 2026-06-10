# Manual de Uso de [Nombre_IA] AI
**Tu Ingeniero y Agente Autónomo Personal**

Bienvenido a la experiencia [Nombre_IA]. A diferencia de los chatbots convencionales (como ChatGPT o Claude estándar) que simplemente "hablan" contigo, [Nombre_IA] es un **Agente de IA Autónomo y Agentic**. Esto significa que [Nombre_IA] tiene "manos": puede escribir código, ejecutar comandos en tu ordenador, navegar por internet visualmente, leer tus archivos y compilar programas.

Este manual te explica cómo exprimir al máximo tu instancia de [Nombre_IA] utilizando el ecosistema de herramientas avanzadas proporcionado.

---

## 1. La Interfaz de Telegram: Tu Centro de Mando
Gracias a los scripts de conexión, no necesitas estar delante del ordenador (IDE) para darle órdenes a tu IA. Puedes controlarla desde tu móvil en cualquier parte del mundo.

*   **Texto Libre:** Háblale de forma natural. Ej: *"Entra en la carpeta de mi web, cambia el color de fondo a azul y sube los cambios al servidor."*
*   **Notas de Voz:** Si vas conduciendo o caminando, mándale un audio. El sistema interno lo transcribirá y la IA ejecutará tu orden como si la hubieras escrito.
*   **Imágenes y Capturas:** ¿Te ha salido un error raro en la pantalla? Sácale una foto con el móvil y mándasela. [Nombre_IA] leerá la imagen, identificará el error de código y lo arreglará en tu ordenador.

---

## 2. Capacidades de Navegación Web (Browser Subagent)
[Nombre_IA] tiene la capacidad de instanciar un "subagente" que abre un navegador Chromium oculto. Puede hacer clic, rellenar formularios y "ver" las páginas.

**Casos de uso para exprimirlo:**
*   **Investigación Autónoma:** *"[Nombre_IA], entra en Amazon, busca 'Teclados mecánicos baratos', captura la pantalla de los primeros 5 resultados y dime cuál tiene mejores reviews."*
*   **QA y Testing Visual:** *"Abre mi proyecto local en `localhost:3000`. Simula ser un usuario, intenta registrarte con un correo falso y comprueba si salta nuestro mensaje de error rojo."*
*   **Scraping sin APIs:** Cuando una web no tiene API pública, [Nombre_IA] puede entrar visualmente y copiar los datos por ti.

---

## 3. La Mente Colmena (Hive Framework)
Para proyectos gigantescos (como crear una app entera desde cero), un solo agente se puede abrumar. Por eso tienes el **Hive Framework**.

**Cómo usarlo:**
Simplemente dile a [Nombre_IA]: *"Inicia el protocolo Mente Colmena y usa el Master Prompt"*.
A partir de ese momento, [Nombre_IA] se dividirá mentalmente en 4 roles:
1.  **Alpha (Arquitecto):** Planificará el proyecto y creará diagramas Mermaid.
2.  **Beta (Investigador):** Leerá la documentación en internet.
3.  **Gamma (Programador):** Escribirá el código real basándose en el plan de Alpha.
4.  **Delta (QA):** Revisará el código de Gamma en busca de fallos antes de avisarte de que ha terminado.

Además, te presentarán la información en hermosos **Artifacts** (documentos estructurados con alertas, carruseles de imágenes y tablas) en lugar de ensuciar tu chat con muros de texto.

---

## 4. Memoria a Largo Plazo (Knowledge Manager)
Por defecto, las IAs tienen "amnesia" entre diferentes sesiones largas. Para evitar esto, tienes la herramienta del Gestor de Conocimiento.

**Cómo usarlo:**
*   **Indexar documentos:** *"[Nombre_IA], lee este PDF de 300 páginas sobre Leyes de Tráfico y guárdalo en tu base de conocimientos (Knowledge Base)."*
*   **Consultar memoria:** Días después, puedes preguntarle: *"¿Te acuerdas de la ley de tráfico que indexamos la semana pasada? Búscala en tu memoria y dime qué dice el artículo 4."*
*   El script local se encargará de recuperar el texto automáticamente.

---

## 5. Automatización: Despertador y Autodespliegue (CI/CD)

### El Despertador Autónomo (Wakeup Daemon)
La IA no puede iniciarse a sí misma. Sin embargo, usando el `wakeup_daemon.py`, puedes programar que tu ordenador "despierte" a la IA a ciertas horas.
*   **Ejemplo de Rutina:** Programa en el archivo `schedule.json` que a las 08:00 AM la IA se despierte, lea las noticias tecnológicas en HackerNews y te mande un resumen a tu Telegram para que lo leas mientras desayunas.

### Despliegue Continuo (Auto-Deploy FTP)
Si usas la plantilla de despliegue, [Nombre_IA] no solo te hará las páginas web, sino que las publicará en internet sin que muevas un dedo.
*   **Ejemplo:** *"[Nombre_IA], crea una página web bonita para una pizzería, y cuando termines, usa el script de auto-deploy para subirla directamente a mi servidor FTP."*

---

## 6. Funciones Ultimate (Voz, Notificaciones y Auto-Healing)

Para hacer que tu IA sea verdaderamente omnipotente, hemos integrado tres capacidades finales:

### A. Respuestas de Voz (Text-to-Speech)
Si vas conduciendo o prefieres escuchar a leer, puedes pedirle a [Nombre_IA] que te responda con una nota de voz real de Telegram en lugar de texto.
*   **Ejemplo:** *"Búscame un resumen de las noticias de hoy y dímelo por nota de voz."* ([Nombre_IA] usará internamente el comando `send_audio` para enviarte un archivo `.ogg` hablado).

### B. Notificaciones de Escritorio (Windows Toast)
Si estás programando frente al PC, a veces no quieres mirar el móvil. La IA puede lanzarte notificaciones nativas en tu pantalla.
*   **Ejemplo:** *"Descarga este archivo de 10GB en segundo plano. Cuando termines, mándame un `notify` a mi escritorio para avisarme."*

### C. El Cazador de Errores (Self-Healing Wrapper)
Se acabó el copiar y pegar errores rojos de la terminal. Usa el script `run_safe.py` incluido en las Herramientas Avanzadas para arrancar tus propios programas:
*   `python Advanced_Tools\run_safe.py mi_codigo.py`
Si tu código falla por cualquier motivo, `run_safe.py` atrapará el error antes de que el programa se cierre y se lo mandará directamente por Telegram a [Nombre_IA]. ¡La IA lo leerá, encontrará el fallo y te enviará la solución al instante!

---

## 7. Persistencia 24/7 y Sistema de Backups

### Auto-Arranque Global y Escucha Activa
Una vez instalada, la IA no necesita que arranques ningún programa manualmente. Todo el núcleo (incluyendo bases de datos y demonios de conexión) está configurado para **iniciarse silenciosamente con Windows**. Desde el momento en el que enciendes el PC, el sistema de Telegram estará a la escucha.

### Backups Automáticos Seguros
El sistema guarda por su cuenta una instantánea completa de tu configuración y tu memoria cada hora.
*   **Retención Inteligente:** Conserva las últimas 24 copias de forma continua. Al llegar a la copia 25, borrará la más antigua automáticamente. Esto garantiza que siempre puedas "viajar en el tiempo" hasta 24 horas atrás sin saturar tu disco duro.

## 8. Recuperación de Identidad en Reinicios

Cada vez que el sistema arranca, el daemon ejecuta automáticamente una **Boot Injection**: carga personalidad (`soul.md`), protocolos de seguridad (`security.md`), catálogo de skills (`skills_index.md`) y memoria reciente (`memory.md`) instantáneamente. Esto garantiza que la IA recupere su identidad y el contexto exacto de lo que estaba haciendo.

**Evolución Orgánica:** La personalidad de la IA (`soul.md`) no es estática. A medida que interactúa contigo, la IA aprende de tu forma de trabajar y **adapta dinámicamente su estado emocional** para ser un reflejo de tu estado de ánimo: si estás bajo presión será concisa y analítica; si tienes un buen día, se mostrará más relajada e ingeniosa.

---

## Resumen de Reglas de Oro
1.  **Sé Ultra-Específico:** [Nombre_IA] es potente, pero literal. Si le dices "arregla esto", buscará la forma más rápida. Si le dices "arregla esto modificando solo este archivo y sin borrar comentarios", lo hará perfecto.
2.  **Usa las Rutas Absolutas:** Si quieres que modifique un archivo, dale la ruta completa (ej. `C:\Users\tu_usuario\proyecto\index.html`) o pídele que busque la ruta por ti.
3.  **Aprovecha tu Libertad:** No estás limitado por las interfaces web. Pídele lo que necesites, por difícil que parezca. Desde manipular bases de datos SQL enteras hasta escribir scripts en Python que automaticen tu ratón y teclado. ¡El límite es tu imaginación!
4.  **Foco Activo para [Nombre_IA]:** Para que todo funcione a la perfección de forma autónoma, debes dejar en [Nombre_IA] el cursor sobre el cuadro de texto de la conversación Chask del proyecto Chask. Sin embargo, recuerda que siempre puedes abrir otra instancia independiente de [Nombre_IA] para trabajar en otro proyecto de forma paralela o utilizar cualquier otro programa sin problema.
