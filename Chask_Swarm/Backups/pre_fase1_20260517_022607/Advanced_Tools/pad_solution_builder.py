"""
pad_solution_builder.py — Generador de soluciones Dataverse para flujos PAD
============================================================================
Método: Clonar solución real exportada + inyectar Robin code propio.
Validado 2026-05-14: Importación exitosa en Power Automate.

Uso:
    python pad_solution_builder.py --name "Mi Flujo" --robin script.robin --output MiFlujo.zip
"""
import os, json, uuid, zipfile, re, argparse

# Plantilla base: solución real exportada de PAD (TempExport)
TEMPLATE_ZIP = r'C:\Users\fnora\Desktop\Enjambre Datos\TempExport_real.zip'


def build_solution(flow_name: str, robin_code: str, output_path: str,
                   version: str = "1.0.0.0") -> str:
    """Genera una solución Dataverse importable clonando la plantilla real."""

    if not os.path.exists(TEMPLATE_ZIP):
        raise FileNotFoundError(f"Plantilla no encontrada: {TEMPLATE_ZIP}")

    # ── Preparar Definition (formato real: json.dumps + XML-escape) ──
    robin_def = json.dumps(robin_code.replace("\n", "\r\n"), ensure_ascii=False)
    robin_def = robin_def.replace("&", "&amp;").replace(">", "&gt;").replace("<", "&lt;")

    # ── Leer plantilla real ──
    zf_real = zipfile.ZipFile(TEMPLATE_ZIP, 'r')
    cust_xml = zf_real.read('customizations.xml').decode('utf-8-sig')
    sol_xml = zf_real.read('solution.xml').decode('utf-8-sig')
    ct = zf_real.read('[Content_Types].xml')

    # Extraer IDs originales
    wf_match = re.search(r'WorkflowId="\{([^}]+)\}"', cust_xml)
    old_wf_id = wf_match.group(1)
    json_match = re.search(r'<JsonFileName>/Workflows/(.+?)\.json</JsonFileName>', cust_xml)
    old_json_name = json_match.group(1)
    old_json_path = f'Workflows/{old_json_name}.json'
    wf_json = zf_real.read(old_json_path).decode('utf-8')
    zf_real.close()

    # ── Nuevos IDs ──
    new_wf_id = str(uuid.uuid4())
    unique_name = "".join(c for c in flow_name if c.isalnum())[:50]
    new_json_name = f'{unique_name}-{new_wf_id.upper()}'

    # ── Modificar customizations.xml ──
    new_cust = cust_xml
    new_cust = new_cust.replace(old_wf_id, new_wf_id)
    new_cust = new_cust.replace(old_json_name, new_json_name)
    new_cust = re.sub(r'(Name=")[^"]*(")', rf'\g<1>{flow_name}\2', new_cust, count=1)

    # Reemplazar Definition
    old_def = re.search(r'<Definition>(.*?)</Definition>', new_cust, re.DOTALL)
    if old_def:
        new_cust = new_cust[:old_def.start()] + f'<Definition>{robin_def}</Definition>' + new_cust[old_def.end():]

    # Limpiar Dependencies (quitar binarios del flujo original)
    new_cust = re.sub(
        r'<Dependencies>\{[^}]*\}</Dependencies>',
        '<Dependencies>{"childFlows":[],"workQueues":[],"environmentVariables":[],"requiredBinaries":[]}</Dependencies>',
        new_cust)

    # Reemplazar LocalizedNames
    new_cust = re.sub(
        r'(description=")[^"]*(".*?languagecode="1033")',
        rf'\g<1>{flow_name}\2', new_cust)

    # ── Modificar solution.xml ──
    new_sol = sol_xml
    # Reemplazar nombre de solución
    new_sol = re.sub(r'<UniqueName>[^<]+</UniqueName>',
                     f'<UniqueName>{unique_name}</UniqueName>', new_sol)
    new_sol = new_sol.replace(old_wf_id, new_wf_id)
    # Reemplazar LocalizedName de la solución
    new_sol = re.sub(
        r'(<LocalizedName description=")[^"]*(" languagecode="1033")',
        rf'\g<1>{flow_name}\2', new_sol, count=1)
    # Reemplazar version
    new_sol = re.sub(r'<Version>[^<]+</Version>',
                     f'<Version>{version}</Version>', new_sol)

    # ── Crear ZIP ──
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf_new:
        zf_new.writestr('[Content_Types].xml', ct)
        zf_new.writestr('solution.xml', new_sol)
        zf_new.writestr('customizations.xml', new_cust)
        zf_new.writestr(f'Workflows/{new_json_name}.json', wf_json)

    sz = os.path.getsize(output_path)
    print(f"Solucion generada: {output_path} ({sz} bytes)")
    print(f"  Flujo: {flow_name} | ID: {new_wf_id} | Version: {version}")
    return output_path


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Genera soluciones PAD importables")
    p.add_argument("--name", required=True, help="Nombre del flujo")
    p.add_argument("--robin", required=True, help="Ruta al archivo .robin")
    p.add_argument("--output", required=True, help="Ruta del ZIP de salida")
    p.add_argument("--version", default="1.0.0.0", help="Version de la solucion")
    a = p.parse_args()

    with open(a.robin, encoding="utf-8") as f:
        robin = f.read()

    build_solution(a.name, robin, a.output, a.version)
