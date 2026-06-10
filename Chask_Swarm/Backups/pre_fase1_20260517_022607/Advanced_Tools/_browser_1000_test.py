"""Browser Pool Test: 1000 pruebas con un solo arranque de Chromium."""
import asyncio, time, json, sys
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from playwright.async_api import async_playwright

N = 1000

async def run():
    ok = 0
    fail = 0
    errors = {}
    times = []

    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=True)
    print(f"[POOL] Browser lanzado 1 vez. Ejecutando {N} tests con new_context()...")

    for i in range(N):
        t0 = time.time()
        try:
            ctx = await browser.new_context()
            page = await ctx.new_page()
            await page.goto("about:blank", wait_until="domcontentloaded")
            await page.title()
            await ctx.close()
            ok += 1
        except Exception as e:
            fail += 1
            err = str(e)[:80]
            errors[err] = errors.get(err, 0) + 1
        elapsed = time.time() - t0
        times.append(elapsed)
        if (i + 1) % 200 == 0:
            avg_so_far = sum(times) / len(times) * 1000
            print(f"  Progreso: {i+1}/{N} | OK={ok} FAIL={fail} | avg={avg_so_far:.1f}ms")

    await browser.close()
    await pw.stop()

    avg = sum(times) / len(times) * 1000
    print(f"RESULTADO: {ok}/{N} ({ok/N*100:.2f}%) | avg={avg:.1f}ms")

    from scipy import stats as sp
    k, n = ok, N
    lo95 = float(sp.beta.ppf(0.025, k, n - k + 1)) if k > 0 else 0.0
    hi95 = float(sp.beta.ppf(0.975, k + 1, n - k)) if k < n else 1.0
    lo99 = float(sp.beta.ppf(0.005, k, n - k + 1)) if k > 0 else 0.0
    hi99 = float(sp.beta.ppf(0.995, k + 1, n - k)) if k < n else 1.0
    pval = float(sp.binomtest(k, n, 0.99, alternative="greater").pvalue)

    print(f"CI95=[{lo95*100:.2f}%, {hi95*100:.2f}%]")
    print(f"CI99=[{lo99*100:.2f}%, {hi99*100:.2f}%]")
    h05 = "Rechazar H0" if pval < 0.05 else "No rechazar H0"
    h01 = "Rechazar H0" if pval < 0.01 else "No rechazar H0"
    print(f"H0(p>0.99 alpha=5%): {h05} (p={pval:.8f})")
    print(f"H0(p>0.99 alpha=1%): {h01}")

    data = {"ok": k, "n": n, "avg_ms": round(avg, 2),
            "ci95": [round(lo95, 6), round(hi95, 6)],
            "ci99": [round(lo99, 6), round(hi99, 6)],
            "pvalue": round(pval, 8), "errors": errors,
            "h0_alpha05": h05, "h0_alpha01": h01}
    out = __import__('os').path.join(__import__('os').path.dirname(__import__('os').path.abspath(__file__)), "browser_1000_results.json")
    with open(out, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Resultados guardados en: {out}")

if __name__ == "__main__":
    asyncio.run(run())
