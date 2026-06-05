"""
computer_use.py — Control Unificado del Sistema Operativo
==========================================================
API limpia para que Enjambre controle CUALQUIER aplicacion del sistema:
- Apps Win32 nativas: via SendMessage/PostMessage
- Apps modernas (WPF/UWP): via UI Automation (UIA)
- Apps Electron/Chromium: via UIA + clipboard
- Office (Word/Excel/PPT): via COM Automation
- Navegadores: via Playwright (delega a chask_browser.py)

Uso:
  from computer_use import ComputerUse
  cu = ComputerUse()
  cu.find_window("Notepad")
  cu.type_text("Hola mundo")
  cu.click_element("Guardar")
"""
import os
import sys
import time
import json
import ctypes
import ctypes.wintypes
from datetime import datetime

# UIA
try:
    import uiautomation as auto
    HAS_UIA = True
except ImportError:
    HAS_UIA = False

# Clipboard
try:
    import pyperclip
    HAS_CLIPBOARD = True
except ImportError:
    HAS_CLIPBOARD = False

# Win32
user32 = ctypes.windll.user32

# Directorio de mapas de apps
APP_MAPS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_maps")
os.makedirs(APP_MAPS_DIR, exist_ok=True)


class ComputerUse:
    """Control unificado de aplicaciones del sistema operativo."""

    def __init__(self):
        self._window = None
        self._hwnd = None
        self._app_map = None

    # ══════════════════════════════════════════════════════
    # VENTANAS
    # ══════════════════════════════════════════════════════
    def find_window(self, name, exact=False):
        """Encuentra una ventana por nombre (parcial o exacto)."""
        if not HAS_UIA:
            return False
        if exact:
            self._window = auto.WindowControl(searchDepth=1, Name=name)
        else:
            self._window = auto.WindowControl(searchDepth=1, SubName=name)

        if self._window.Exists(3):
            self._hwnd = self._window.NativeWindowHandle
            return True
        return False

    def list_windows(self):
        """Lista todas las ventanas visibles del escritorio."""
        if not HAS_UIA:
            return []
        desktop = auto.GetRootControl()
        windows = []
        for w in desktop.GetChildren():
            if w.ControlType == auto.ControlType.WindowControl:
                try:
                    name = w.Name
                    if name and name.strip():
                        windows.append({
                            "name": name,
                            "hwnd": w.NativeWindowHandle,
                            "class": w.ClassName,
                            "rect": str(w.BoundingRectangle) if w.BoundingRectangle else ""
                        })
                except:
                    pass
        return windows

    def activate_window(self):
        """Trae la ventana al frente."""
        if self._hwnd:
            user32.ShowWindow(self._hwnd, 9)  # SW_RESTORE
            time.sleep(0.1)
            user32.SetForegroundWindow(self._hwnd)
            time.sleep(0.3)

    # ══════════════════════════════════════════════════════
    # ELEMENTOS UI (via UIA)
    # ══════════════════════════════════════════════════════
    def find_element(self, name=None, control_type=None, automation_id=None, depth=20):
        """Busca un elemento UI dentro de la ventana activa."""
        if not self._window:
            return None
        kwargs = {"searchDepth": depth}
        if name:
            kwargs["Name"] = name
        if automation_id:
            kwargs["AutomationId"] = automation_id

        if control_type == "button":
            return self._window.ButtonControl(**kwargs)
        elif control_type == "edit":
            return self._window.EditControl(**kwargs)
        elif control_type == "text":
            return self._window.TextControl(**kwargs)
        elif control_type == "list":
            return self._window.ListControl(**kwargs)
        elif control_type == "menu":
            return self._window.MenuControl(**kwargs)
        elif control_type == "menuitem":
            return self._window.MenuItemControl(**kwargs)
        else:
            # Busqueda generica
            return self._window.Control(**kwargs)

    def click_element(self, name=None, control_type=None, automation_id=None):
        """Click en un elemento por nombre o ID."""
        el = self.find_element(name, control_type, automation_id)
        if el and el.Exists(2):
            try:
                # Intentar InvokePattern primero (no necesita foco)
                el.GetInvokePattern().Invoke()
                return True
            except:
                pass
            try:
                el.Click()
                return True
            except:
                pass
        return False

    def type_in_element(self, name=None, text="", automation_id=None):
        """Escribe texto en un campo de texto."""
        el = self.find_element(name, "edit", automation_id)
        if el and el.Exists(2):
            try:
                # Intentar ValuePattern primero (no necesita foco)
                vp = el.GetValuePattern()
                vp.SetValue(text)
                return True
            except:
                pass
            try:
                # Fallback: click + clipboard
                el.Click()
                time.sleep(0.2)
                if HAS_CLIPBOARD:
                    pyperclip.copy(text)
                    import pyautogui
                    pyautogui.hotkey('ctrl', 'v')
                    return True
            except:
                pass
        return False

    # ══════════════════════════════════════════════════════
    # MAPEO DE APPS
    # ══════════════════════════════════════════════════════
    def scan_app(self, name, max_depth=10):
        """Escanea la estructura UI de una aplicacion y la guarda como mapa."""
        if not self.find_window(name):
            return None

        app_map = {
            "app_name": name,
            "scanned_at": datetime.now().isoformat(),
            "hwnd": self._hwnd,
            "elements": []
        }

        def _scan(control, depth=0):
            if depth > max_depth:
                return
            try:
                info = {
                    "name": control.Name or "",
                    "type": control.ControlTypeName,
                    "automation_id": control.AutomationId or "",
                    "class": control.ClassName or "",
                    "depth": depth
                }
                rect = control.BoundingRectangle
                if rect:
                    info["rect"] = {
                        "left": rect.left, "top": rect.top,
                        "right": rect.right, "bottom": rect.bottom
                    }

                # Verificar patrones disponibles
                patterns = []
                try:
                    control.GetInvokePattern()
                    patterns.append("Invoke")
                except:
                    pass
                try:
                    control.GetValuePattern()
                    patterns.append("Value")
                except:
                    pass
                try:
                    control.GetTogglePattern()
                    patterns.append("Toggle")
                except:
                    pass
                try:
                    control.GetSelectionPattern()
                    patterns.append("Selection")
                except:
                    pass
                info["patterns"] = patterns

                if info["name"] or info["automation_id"]:
                    app_map["elements"].append(info)

                for child in control.GetChildren():
                    _scan(child, depth + 1)
            except:
                pass

        _scan(self._window)

        # Guardar mapa
        safe_name = "".join(c if c.isalnum() else "_" for c in name.lower())
        map_path = os.path.join(APP_MAPS_DIR, f"{safe_name}.json")
        with open(map_path, "w", encoding="utf-8") as f:
            json.dump(app_map, f, indent=2, ensure_ascii=False)

        self._app_map = app_map
        return app_map

    def load_app_map(self, name):
        """Carga un mapa de app previamente escaneado."""
        safe_name = "".join(c if c.isalnum() else "_" for c in name.lower())
        map_path = os.path.join(APP_MAPS_DIR, f"{safe_name}.json")
        if os.path.exists(map_path):
            with open(map_path, "r", encoding="utf-8") as f:
                self._app_map = json.load(f)
            return self._app_map
        return None

    # ══════════════════════════════════════════════════════
    # COM AUTOMATION (Office)
    # ══════════════════════════════════════════════════════
    def office_word(self, action, **kwargs):
        """Control de Microsoft Word via COM."""
        try:
            import win32com.client
            word = win32com.client.Dispatch("Word.Application")
            word.Visible = True

            if action == "open":
                doc = word.Documents.Open(kwargs.get("path"))
                return True
            elif action == "new":
                doc = word.Documents.Add()
                return True
            elif action == "write":
                sel = word.Selection
                sel.TypeText(kwargs.get("text", ""))
                return True
            elif action == "save":
                word.ActiveDocument.Save()
                return True
            elif action == "save_as":
                word.ActiveDocument.SaveAs2(kwargs.get("path"))
                return True
        except Exception as e:
            print(f"[COM] Error Word: {e}")
        return False

    def office_excel(self, action, **kwargs):
        """Control de Microsoft Excel via COM."""
        try:
            import win32com.client
            excel = win32com.client.Dispatch("Excel.Application")
            excel.Visible = True

            if action == "open":
                wb = excel.Workbooks.Open(kwargs.get("path"))
                return True
            elif action == "new":
                wb = excel.Workbooks.Add()
                return True
            elif action == "write_cell":
                sheet = excel.ActiveSheet
                sheet.Cells(kwargs.get("row", 1), kwargs.get("col", 1)).Value = kwargs.get("value", "")
                return True
            elif action == "read_cell":
                sheet = excel.ActiveSheet
                return sheet.Cells(kwargs.get("row", 1), kwargs.get("col", 1)).Value
            elif action == "save":
                excel.ActiveWorkbook.Save()
                return True
        except Exception as e:
            print(f"[COM] Error Excel: {e}")
        return False


# ── CLI ─────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Computer Use — Control del SO")
    sub = parser.add_subparsers(dest="cmd")

    p_list = sub.add_parser("list", help="Listar ventanas")
    p_scan = sub.add_parser("scan", help="Escanear app")
    p_scan.add_argument("app", help="Nombre de la ventana")
    p_scan.add_argument("--depth", type=int, default=10)

    args = parser.parse_args()
    cu = ComputerUse()

    if args.cmd == "list":
        windows = cu.list_windows()
        for w in windows:
            print(f"  [{w['hwnd']}] {w['name']} ({w['class']})")

    elif args.cmd == "scan":
        result = cu.scan_app(args.app, max_depth=args.depth)
        if result:
            print(f"[OK] {len(result['elements'])} elementos encontrados")
            for el in result["elements"][:20]:
                patterns = ", ".join(el.get("patterns", []))
                print(f"  [{el['type']}] {el['name'][:40]} | ID={el['automation_id']} | {patterns}")
        else:
            print(f"[ERROR] No se encontro ventana: {args.app}")
    else:
        parser.print_help()
