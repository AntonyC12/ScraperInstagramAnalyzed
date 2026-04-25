"""
Back/tests/test_personality_logic.py
====================================
Prueba unitaria para validar el análisis de personalidad Big Five con Groq.
"""

import sys
import os
import json
import logging

# Añadir el path raíz
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from application.personality_analysis import PersonalityAnalysisUseCase
from infrastructure.ai.groq_client import GroqClient
from domain.models import ScrapedData, Post, Profile
from config.settings import Settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_personality_flow():
    settings = Settings()
    if not settings.groq_api_key:
        logger.error("❌ GROQ_API_KEY no encontrada")
        return

    # Mock de datos
    profile = Profile(
        username="test_user",
        bio="Explorador de datos y entusiasta de la IA. Siempre aprendiendo."
    )
    posts = [
        Post(
            post_id="1", shortcode="A", timestamp="2024-01-01T12:00:00Z", type="image",
            caption_raw="Hoy aprendí algo nuevo sobre redes neuronales! #AI",
            caption_clean="Hoy aprendí algo nuevo sobre redes neuronales!",
            engagement={"likes_count": 100, "comments_count": 10}
        ),
        Post(
            post_id="2", shortcode="B", timestamp="2024-01-02T12:00:00Z", type="image",
            caption_raw="Disfrutando de un café mientras programo. #codinglife",
            caption_clean="Disfrutando de un café mientras programo.",
            engagement={"likes_count": 80, "comments_count": 5}
        )
    ]

    scraped_data = ScrapedData(
        metadata=None,
        profile=profile,
        data_quality=None,
        posts=posts
    )

    client = GroqClient(settings.groq_api_key, model_name=settings.groq_model)
    use_case = PersonalityAnalysisUseCase(client)
    
    logger.info("🚀 Iniciando prueba de análisis de personalidad con Groq...")
    report = use_case.execute(scraped_data)

    if "traits" in report:
        logger.info("✅ Reporte generado exitosamente.")
        print(f"Resumen: {report.get('summary', 'N/A')}")
    else:
        logger.error(f"❌ Error: {report.get('error', 'Desconocido')}")

if __name__ == "__main__":
    test_personality_flow()
