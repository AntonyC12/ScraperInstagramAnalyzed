"""
Back/tests/test_report_only.py
==============================
Genera el PDF a partir de un JSON existente para validar el diseño.
"""
import json
import sys
from pathlib import Path

# Asegurar que Back/ esté en el path
_back_dir = Path(__file__).parent.parent
if str(_back_dir) not in sys.path:
    sys.path.insert(0, str(_back_dir))

from application.report_generator import ReportGeneratorUseCase

def test_generate_pdf():
    json_path = _back_dir / "repositories" / "erikavelez_scrapy.json"
    if not json_path.exists():
        print(f"[-] No se encuentra el archivo JSON en {json_path}")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"[+] Cargando datos de: {data['profile']['username']}")
    
    report_service = ReportGeneratorUseCase(_back_dir / "reports")
    pdf_path = report_service.execute(data)
    
    print(f"[+] PDF generado en: {pdf_path}")

if __name__ == "__main__":
    test_generate_pdf()
