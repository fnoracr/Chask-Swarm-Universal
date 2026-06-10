"""
chask_test_battery.py — Bateria de Tests Masiva del Enjambre
============================================================
1000 pruebas por capacidad. Genera informe HTML con intervalos
de confianza y contrastes de hipotesis.
"""
import os, sys, io, json, time, math, subprocess, traceback
from datetime import datetime
from collections import defaultdict

if sys.stdout and hasattr(sys.stdout, 'buffer'):
    try: sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except: pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS_DIR)
REPORT_PATH = os.path.join(os.path.expanduser("~"), "Desktop", "chask_test_report.html")
LOG_FILE = os.path.join(BASE_DIR, "test_battery.log")
RESULTS_FILE = os.path.join(TOOLS_DIR, "test_results.json")
N = 1000  # tests por capacidad

def log(msg):
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f: f.write(line+"\n")
    except: pass
    print(line)

# ══════════════════════════════════════════════════════════
# ESTADISTICA
# ══════════════════════════════════════════════════════════
def clopper_pearson(k, n, alpha):
    """Intervalo de confianza exacto de Clopper-Pearson."""
    from scipy import stats as sp
    if n == 0: return (0, 1)
    lo = sp.beta.ppf(alpha/2, k, n-k+1) if k > 0 else 0.0
    hi = sp.beta.ppf(1-alpha/2, k+1, n-k) if k < n else 1.0
    return (lo, hi)

def binomial_test(k, n, p0, alternative='greater'):
    """Test binomial: H0: p <= p0 vs H1: p > p0."""
    from scipy import stats as sp
    result = sp.binomtest(k, n, p0, alternative=alternative)
    return result.pvalue

def compute_stats(k, n):
    """Calcula todas las estadisticas para k exitos de n pruebas."""
    p_hat = k/n if n > 0 else 0
    ci95 = clopper_pearson(k, n, 0.05)
    ci99 = clopper_pearson(k, n, 0.01)
    pval_05 = binomial_test(k, n, 0.99)
    pval_01 = binomial_test(k, n, 0.99)
    return {
        "n": n, "k": k, "p_hat": round(p_hat, 6),
        "ci95": (round(ci95[0],6), round(ci95[1],6)),
        "ci99": (round(ci99[0],6), round(ci99[1],6)),
        "h0_p99_alpha05": "Rechazar H0" if pval_05 < 0.05 else "No rechazar H0",
        "h0_p99_alpha01": "Rechazar H0" if pval_01 < 0.01 else "No rechazar H0",
        "pvalue": round(pval_05, 8)
    }

# ══════════════════════════════════════════════════════════
# CAPTURA DE ESTADO DEL SISTEMA
# ══════════════════════════════════════════════════════════
def capture_system_state():
    state = {"ts": datetime.now().isoformat()}
    # Procesos python
    try:
        out = subprocess.check_output('wmic process where "name=\'python.exe\' or name=\'pythonw.exe\'" get CommandLine /FORMAT:LIST',
            shell=True, text=True, stderr=subprocess.DEVNULL, timeout=5)
        state["python_procs"] = len([l for l in out.split("\n") if "CommandLine=" in l and l.strip().endswith(".py")])
    except: state["python_procs"] = -1
    # Qdrant
    try:
        import urllib.request
        r = urllib.request.urlopen("http://localhost:6333/collections", timeout=3)
        state["qdrant"] = "online" if r.status == 200 else "offline"
    except: state["qdrant"] = "offline"
    # Charm
    try:
        import uiautomation as auto
        w = auto.WindowControl(searchDepth=1, SubName='Charm')
        state["charm"] = "open" if w.Exists(1) else "closed"
    except: state["charm"] = "unknown"
    return state

# ══════════════════════════════════════════════════════════
# TESTS
# ══════════════════════════════════════════════════════════
def test_qdrant_log(i):
    """Test: escribir una operacion en Qdrant."""
    try:
        from chask_operational_memory import OperationalMemory
        mem = OperationalMemory()
        if not mem.client: return False, "Sin conexion"
        mem.log_operation(f"test_battery_{i}", approach="auto-test", result="success",
                          keywords=["test"], project="test_battery")
        return True, "OK"
    except Exception as e: return False, str(e)[:100]

def test_qdrant_recall(i):
    """Test: buscar en Qdrant."""
    try:
        from chask_operational_memory import OperationalMemory
        mem = OperationalMemory()
        if not mem.client: return False, "Sin conexion"
        results = mem.recall(f"test query {i}", limit=1)
        return True, f"{len(results)} resultados"
    except Exception as e: return False, str(e)[:100]

def test_qdrant_stats(i):
    """Test: obtener estadisticas de Qdrant."""
    try:
        from chask_operational_memory import OperationalMemory
        mem = OperationalMemory()
        if not mem.client: return False, "Sin conexion"
        s = mem.stats()
        return len(s) > 0, f"{len(s)} colecciones"
    except Exception as e: return False, str(e)[:100]

def test_window_list(i):
    """Test: listar ventanas del sistema."""
    try:
        from computer_use import ComputerUse
        cu = ComputerUse()
        windows = cu.list_windows()
        return len(windows) > 0, f"{len(windows)} ventanas"
    except Exception as e: return False, str(e)[:100]

def test_window_find(i):
    """Test: encontrar ventana Charm."""
    try:
        from computer_use import ComputerUse
        cu = ComputerUse()
        found = cu.find_window("Charm")
        return found, "Encontrada" if found else "No encontrada"
    except Exception as e: return False, str(e)[:100]

def test_injector_find(i):
    """Test: localizar chat input en Charm (sin inyectar)."""
    try:
        import uiautomation as auto
        w = auto.WindowControl(searchDepth=1, SubName='Charm')
        if not w.Exists(1): return False, "Ventana no encontrada"
        ci = w.EditControl(searchDepth=100, Name='Message input')
        return ci.Exists(1), "Input encontrado" if ci.Exists(0) else "Input no visible"
    except Exception as e: return False, str(e)[:100]

def test_file_read(i):
    """Test: leer memory.md."""
    try:
        p = os.path.join(BASE_DIR, "memory.md")
        with open(p, "r", encoding="utf-8") as f: content = f.read()
        return len(content) > 0, f"{len(content)} bytes"
    except Exception as e: return False, str(e)[:100]

def test_file_write(i):
    """Test: escribir/leer fichero temporal."""
    try:
        p = os.path.join(TOOLS_DIR, f"_test_tmp_{i}.txt")
        with open(p, "w") as f: f.write(f"test_{i}")
        with open(p, "r") as f: content = f.read()
        os.remove(p)
        return content == f"test_{i}", "OK"
    except Exception as e: return False, str(e)[:100]

def test_browser_headless(i):
    """Test: navegacion headless con Playwright."""
    try:
        import asyncio
        from chask_browser import NoraBrowser
        async def _t():
            async with NoraBrowser(headless=True) as b:
                await b.go("about:blank")
                return True
        return asyncio.run(_t()), "OK"
    except Exception as e: return False, str(e)[:100]

def test_watchdog_qdrant(i):
    """Test: verificar que Qdrant responde."""
    try:
        import urllib.request
        r = urllib.request.urlopen("http://localhost:6333/collections", timeout=3)
        return r.status == 200, f"HTTP {r.status}"
    except Exception as e: return False, str(e)[:100]

def test_watchdog_processes(i):
    """Test: detectar procesos del enjambre."""
    try:
        out = subprocess.check_output(
            'wmic process where "name=\'python.exe\' or name=\'pythonw.exe\'" get CommandLine /FORMAT:LIST',
            shell=True, text=True, stderr=subprocess.DEVNULL, timeout=5)
        found = "unified_daemon" in out.lower()
        return found, "Daemon detectado" if found else "Daemon NO detectado"
    except Exception as e: return False, str(e)[:100]

# ══════════════════════════════════════════════════════════
# RUNNER
# ══════════════════════════════════════════════════════════
ALL_TESTS = {
    "Qdrant: Log Operacion": test_qdrant_log,
    "Qdrant: Recall Semantico": test_qdrant_recall,
    "Qdrant: Estadisticas": test_qdrant_stats,
    "UIA: Listar Ventanas": test_window_list,
    "UIA: Encontrar Charm": test_window_find,
    "Injector: Localizar Chat Input": test_injector_find,
    "IO: Leer memory.md": test_file_read,
    "IO: Escritura/Lectura Temp": test_file_write,
    "Browser: Navegacion Headless": test_browser_headless,
    "Watchdog: Health Qdrant": test_watchdog_qdrant,
    "Watchdog: Detectar Daemon": test_watchdog_processes,
}

# Browser tests limitados a 100 por velocidad (cada uno tarda ~1s)
LIMITS = {"Browser: Navegacion Headless": 100}

def run_all_tests():
    log("=" * 60)
    log(f"BATERIA DE TESTS MASIVA — {len(ALL_TESTS)} capacidades x {N} pruebas")
    log("=" * 60)

    initial_state = capture_system_state()
    log(f"Estado inicial: {json.dumps(initial_state, ensure_ascii=False)}")

    all_results = {}
    grand_start = time.time()

    for test_name, test_fn in ALL_TESTS.items():
        limit = LIMITS.get(test_name, N)
        log(f"\n--- {test_name} ({limit} pruebas) ---")
        successes = 0
        failures = 0
        errors = defaultdict(int)
        times = []

        for i in range(limit):
            t0 = time.time()
            try:
                ok, detail = test_fn(i)
            except Exception as e:
                ok, detail = False, str(e)[:100]
            elapsed = time.time() - t0
            times.append(elapsed)

            if ok:
                successes += 1
            else:
                failures += 1
                errors[detail] += 1

            if (i+1) % 200 == 0:
                log(f"  Progreso: {i+1}/{limit} | OK={successes} FAIL={failures}")

        avg_time = sum(times)/len(times) if times else 0
        stats = compute_stats(successes, limit)

        all_results[test_name] = {
            "successes": successes, "failures": failures, "total": limit,
            "avg_time_ms": round(avg_time*1000, 2),
            "top_errors": dict(sorted(errors.items(), key=lambda x: -x[1])[:5]),
            "stats": stats
        }
        log(f"  RESULTADO: {successes}/{limit} ({stats['p_hat']*100:.2f}%) | "
            f"CI95={stats['ci95']} | CI99={stats['ci99']} | "
            f"H0(p>0.99 @5%)={stats['h0_p99_alpha05']}")

    final_state = capture_system_state()
    elapsed_total = round(time.time() - grand_start, 1)
    log(f"\nTiempo total: {elapsed_total}s")
    log(f"Estado final: {json.dumps(final_state, ensure_ascii=False)}")

    # Guardar resultados raw
    payload = {
        "timestamp": datetime.now().isoformat(),
        "initial_state": initial_state,
        "final_state": final_state,
        "elapsed_s": elapsed_total,
        "results": all_results
    }
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    # Generar HTML
    generate_html_report(payload)

    # Enviar resumen por Telegram
    send_telegram_summary(payload)

    log("BATERIA COMPLETADA")

# ══════════════════════════════════════════════════════════
# HTML REPORT
# ══════════════════════════════════════════════════════════
def generate_html_report(data):
    results = data["results"]
    rows = ""
    for name, r in results.items():
        s = r["stats"]
        phat = s["p_hat"]
        color = "#00ff88" if phat >= 0.99 else "#ffaa00" if phat >= 0.95 else "#ff4444"
        bar_w = int(phat * 100)
        h0_05_color = "#00ff88" if "Rechazar" in s["h0_p99_alpha05"] else "#ff4444"
        h0_01_color = "#00ff88" if "Rechazar" in s["h0_p99_alpha01"] else "#ff4444"
        top_err = "<br>".join(f"{v}x: {k[:50]}" for k,v in r["top_errors"].items()) or "—"

        rows += f"""<tr>
<td>{name}</td>
<td><strong>{r['successes']}</strong>/{r['total']}</td>
<td><div style="background:#333;border-radius:4px;overflow:hidden;height:20px">
  <div style="background:{color};width:{bar_w}%;height:100%;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:bold">{phat*100:.2f}%</div>
</div></td>
<td>[{s['ci95'][0]*100:.2f}%, {s['ci95'][1]*100:.2f}%]</td>
<td>[{s['ci99'][0]*100:.2f}%, {s['ci99'][1]*100:.2f}%]</td>
<td style="color:{h0_05_color}">{s['h0_p99_alpha05']}</td>
<td style="color:{h0_01_color}">{s['h0_p99_alpha01']}</td>
<td>{s['pvalue']}</td>
<td>{r['avg_time_ms']:.1f}ms</td>
<td class="err">{top_err}</td>
</tr>"""

    # Initial/Final state
    ist = data["initial_state"]
    fst = data["final_state"]

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Enjambre Test Battery Report</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#0a0a1a;color:#e0e0e0;font-family:'Segoe UI',system-ui,sans-serif;padding:30px}}
h1{{text-align:center;font-size:2.2em;background:linear-gradient(135deg,#00d4ff,#7b2ff7);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:5px}}
.subtitle{{text-align:center;color:#888;margin-bottom:30px}}
.card{{background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:20px;margin-bottom:20px;backdrop-filter:blur(10px)}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th{{background:rgba(123,47,247,0.2);padding:10px 8px;text-align:left;border-bottom:2px solid #7b2ff7}}
td{{padding:8px;border-bottom:1px solid rgba(255,255,255,0.06)}}
tr:hover{{background:rgba(255,255,255,0.03)}}
.err{{font-size:11px;color:#ff8888;max-width:200px;word-break:break-all}}
.state-grid{{display:grid;grid-template-columns:1fr 1fr;gap:20px}}
.state-card{{background:rgba(0,212,255,0.05);border:1px solid rgba(0,212,255,0.2);border-radius:8px;padding:15px}}
.state-card h3{{color:#00d4ff;margin-bottom:10px}}
.legend{{margin-top:20px;padding:15px;background:rgba(255,255,255,0.03);border-radius:8px;font-size:12px;color:#aaa}}
.badge{{display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:bold}}
.badge-ok{{background:#00ff8822;color:#00ff88;border:1px solid #00ff88}}
.badge-warn{{background:#ffaa0022;color:#ffaa00;border:1px solid #ffaa00}}
.badge-fail{{background:#ff444422;color:#ff4444;border:1px solid #ff4444}}
</style>
</head>
<body>
<h1>Enjambre (Chask Swarm) — Test Battery Report</h1>
<p class="subtitle">Generado: {data['timestamp'][:19]} | Duracion: {data['elapsed_s']}s | {len(results)} capacidades testadas</p>

<div class="state-grid">
<div class="state-card"><h3>Estado Inicial</h3>
<p>Procesos Python: {ist.get('python_procs','?')}</p>
<p>Qdrant: <span class="badge {'badge-ok' if ist.get('qdrant')=='online' else 'badge-fail'}">{ist.get('qdrant','?')}</span></p>
<p>Charm: <span class="badge {'badge-ok' if ist.get('charm')=='open' else 'badge-warn'}">{ist.get('charm','?')}</span></p>
</div>
<div class="state-card"><h3>Estado Final</h3>
<p>Procesos Python: {fst.get('python_procs','?')}</p>
<p>Qdrant: <span class="badge {'badge-ok' if fst.get('qdrant')=='online' else 'badge-fail'}">{fst.get('qdrant','?')}</span></p>
<p>Charm: <span class="badge {'badge-ok' if fst.get('charm')=='open' else 'badge-warn'}">{fst.get('charm','?')}</span></p>
</div>
</div>

<div class="card" style="margin-top:20px">
<h2 style="margin-bottom:15px">Resultados por Capacidad</h2>
<table>
<tr><th>Capacidad</th><th>OK/Total</th><th>Tasa de Exito</th><th>IC 95%</th><th>IC 99%</th>
<th>H0: p&gt;0.99 (a=5%)</th><th>H0: p&gt;0.99 (a=1%)</th><th>p-value</th><th>Tiempo Medio</th><th>Errores</th></tr>
{rows}
</table>
</div>

<div class="legend">
<strong>Metodologia:</strong> Intervalo de confianza exacto de Clopper-Pearson (binomial). Contraste: H0: p &le; 0.99 vs H1: p &gt; 0.99.
"Rechazar H0" significa que hay evidencia estadistica de que la probabilidad de exito supera 0.99 al nivel de significacion indicado.
Browser tests limitados a 100 por tiempo de ejecucion (~1s/test).
</div>
</body></html>"""

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(html)
    log(f"[HTML] Informe guardado en: {REPORT_PATH}")

def send_telegram_summary(data):
    results = data["results"]
    lines = ["[TEST BATTERY] Informe completado\n"]
    for name, r in results.items():
        s = r["stats"]
        emoji = "[OK]" if s["p_hat"] >= 0.99 else "[WARN]" if s["p_hat"] >= 0.95 else "[FAIL]"
        lines.append(f"{emoji} {name}: {s['p_hat']*100:.1f}% ({r['successes']}/{r['total']})")
    lines.append(f"\nTiempo total: {data['elapsed_s']}s")
    lines.append(f"Informe HTML en el escritorio.")
    msg = "\n".join(lines)
    try:
        tg = os.path.join(BASE_DIR, "charm_telegram.py")
        subprocess.run([sys.executable, tg, "send", msg], capture_output=True, timeout=15)
    except: pass

if __name__ == "__main__":
    run_all_tests()
