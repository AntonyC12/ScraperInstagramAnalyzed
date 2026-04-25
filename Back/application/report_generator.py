"""
application/report_generator.py
==============================
Servicio encargado de generar el informe académico en PDF.
"""

import logging
from typing import Any
from datetime import datetime
from pathlib import Path
from fpdf import FPDF

logger = logging.getLogger(__name__)

class PersonalityReportPDF(FPDF):
    def header(self):
        self.set_font("helvetica", "B", 16)
        self.set_text_color(41, 128, 185) 
        self.cell(190, 10, "INFORME PSICOLÓGICO DIGITAL - BIG FIVE (OCEAN)", ln=1, align="C")
        self.set_font("helvetica", "I", 10)
        self.set_text_color(127, 140, 141)
        self.cell(190, 10, f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=1, align="C")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(149, 165, 166)
        self.cell(0, 10, f"Página {self.page_no()}/{{nb}} - Análisis Académico", align="C")

    def chapter_title(self, title, color=(44, 62, 80)):
        self.set_font("helvetica", "B", 12)
        self.set_fill_color(*color)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, f"  {title}", ln=1, fill=True)
        self.ln(5)
        # Reset color to dark gray after title
        self.set_text_color(44, 62, 80)

    def trait_row(self, label, score, interpretation, evidence):
        self.set_x(10)
        self.set_font("helvetica", "B", 11)
        self.set_text_color(52, 73, 94)
        self.cell(190, 8, f"{label}: {int(score*100)}%", ln=1)
        
        x_start, y_start = self.get_x(), self.get_y()
        self.set_fill_color(236, 240, 241)
        self.rect(x_start, y_start, 100, 3, "F")
        fill_width = score * 100
        color = (46, 204, 113) if score > 0.7 else (241, 196, 15) if score > 0.4 else (231, 76, 60)
        self.set_fill_color(*color)
        self.rect(x_start, y_start, fill_width, 3, "F")
        self.ln(6)
        
        self.set_x(10)
        self.set_font("helvetica", "", 10)
        self.set_text_color(44, 62, 80)
        self.multi_cell(190, 6, f"Interpretación: {interpretation}")
        
        self.set_x(10)
        self.set_font("helvetica", "I", 9)
        self.set_text_color(127, 140, 141)
        ev_text = ", ".join(evidence) if isinstance(evidence, list) else str(evidence)
        self.multi_cell(190, 5, f"Evidencia: {ev_text}")
        self.ln(5)

class ReportGeneratorUseCase:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _clean_text(self, text: Any) -> str:
        """Limpia texto para compatibilidad con fuentes estándar de PDF (latin-1)."""
        if not text: return "N/A"
        # Convertir a latin-1 para soportar tildes y ñ en helvetica estándar
        try:
            return str(text).encode("latin-1", "replace").decode("latin-1")
        except:
            return "".join(c for c in str(text) if ord(c) < 128)

    def execute(self, data: dict) -> str:
        username = data.get("profile", {}).get("username", "unknown")
        file_path = self.output_dir / f"Reporte_Personalidad_{username}.pdf"

        pdf = PersonalityReportPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        w_util = 190
        # Color base oscuro
        pdf.set_text_color(44, 62, 80)

        # 1. Perfil
        pdf.chapter_title("1. INFORMACIÓN DEL PERFIL")
        profile = data.get("profile", {})
        pdf.set_font("helvetica", "", 11)
        pdf.set_x(10)
        pdf.cell(w_util, 8, f"Usuario: @{self._clean_text(profile.get('username'))}", ln=1)
        pdf.cell(w_util, 8, f"Nombre: {self._clean_text(profile.get('full_name'))}", ln=1)
        pdf.cell(w_util, 8, f"Seguidores: {profile.get('followers_count')} | Seguidos: {profile.get('following_count')}", ln=1)
        pdf.multi_cell(w_util, 8, f"Bio: {self._clean_text(profile.get('bio'))}")
        pdf.ln(5)

        # 2. OCEAN
        pdf.chapter_title("2. ANÁLISIS DE RASGOS (BIG FIVE)")
        personality = data.get("personality_report", {})
        pdf.set_font("helvetica", "I", 10)
        pdf.set_x(10)
        pdf.multi_cell(w_util, 6, self._clean_text(personality.get("summary", "")))
        pdf.ln(5)

        traits = personality.get("traits", {})
        ocean_map = {
            "openness": "Apertura", 
            "conscientiousness": "Responsabilidad", 
            "extraversion": "Extraversión", 
            "agreeableness": "Amabilidad", 
            "neuroticism": "Neuroticismo"
        }

        for key, label in ocean_map.items():
            trait = traits.get(key, {})
            pdf.trait_row(
                label, 
                trait.get("score", 0), 
                self._clean_text(trait.get("interpretation", "N/A")), 
                [self._clean_text(e) for e in trait.get("evidence", [])]
            )

        # 3. Notas
        pdf.set_x(10)
        pdf.chapter_title("3. NOTAS ACADÉMICAS", color=(52, 73, 94))
        pdf.set_font("helvetica", "", 10)
        pdf.multi_cell(w_util, 6, f"Notas: {self._clean_text(personality.get('academic_notes'))}")
        pdf.ln(3)
        for b in personality.get("potential_biases", []):
            pdf.set_x(10)
            pdf.multi_cell(w_util, 6, f" - {self._clean_text(b)}")

        pdf.output(str(file_path))
        return str(file_path)
