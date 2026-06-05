# [Nombre_IA] IDE - Atajos de Teclado (Keybindings)

Este archivo sirve como referencia de memoria para que [Nombre_IA] ([Nombre_IA]) pueda interactuar con la interfaz del propio IDE simulando pulsaciones de teclado mediante VBScript o herramientas similares.

## Ventanas y Paneles
- **Toggle Sidebar** (Alternar barra lateral): `Ctrl + B`
- **Toggle Auxiliary Pane** (Alternar panel auxiliar): `Ctrl + Shift + B`
- **New Editor Window** (Nueva ventana del editor): `Ctrl + Shift + N`

## Navegación
- **Go Back** (Ir atrás): `Ctrl + [`
- **Go Forward** (Ir adelante): `Ctrl + ]`
- **Close Tab** (Cerrar pestaña): `Ctrl + W`

## Conversaciones y Proyectos
- **New Conversation** (Nueva conversación): `Ctrl + N`
- **Open Conversation History** (Abrir historial): `Ctrl + Y`
- **Select Next Conversation** (Conversación siguiente): `Alt + Flecha Abajo` (↓)
- **Select Previous Conversation** (Conversación anterior): `Alt + Flecha Arriba` (↑)
- **Open Conversation Picker** (Buscador de conversaciones): `Ctrl + K`
- **Open Project Picker** (Buscador de proyectos): `Ctrl + Shift + K`

## Acciones e Interfaz
- **Focus Input** (Fijar cursor en caja de texto): `Ctrl + L`
- **Open Settings** (Abrir configuración): `Ctrl + ,`
- **Scheduled Tasks** (Tareas programadas): `Ctrl + U`
- **Open Launchpad** (Abrir Launchpad): (Sin atajo por defecto, requiere interacción UI)
- **Open Keyboard Shortcuts** (Ver atajos): `Ctrl + ?`
- **Provide Feedback** (Dar feedback): (Sin atajo por defecto)
- **Copy conversation markdown** (Copiar markdown): (Sin atajo por defecto)
- **Toggle Model Selector** (Alternar modelo AI): `Ctrl + /`
- **Toggle Voice Recording** (Alternar grabación de voz): `Ctrl + M`
- **File Picker** (Selector de archivos): `Ctrl + P`
- **Open Command Palette** (Paleta de comandos): `Ctrl + Shift + P`

---
*Nota para VBScript (SendKeys)*: 
- `Ctrl` = `^`
- `Shift` = `+`
- `Alt` = `%`
- `Enter` = `~` o `{ENTER}`
- `Flecha Abajo` = `{DOWN}`
- `Flecha Arriba` = `{UP}`
- `Esc` = `{ESC}`

Ejemplo de flujo para abrir "[Nombre_IA] Telegram": `^k` -> `[Nombre_IA] Telegram` -> `{ENTER}` -> `^l`
