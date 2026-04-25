"""
application/personality_analysis.py
===================================
UseCase encargado de realizar el análisis profundo de personalidad (OCEAN).
"""

import logging
from domain.models import ScrapedData

logger = logging.getLogger(__name__)

class PersonalityAnalysisUseCase:
    def __init__(self, ai_client):
        self.ai_client = ai_client

    def execute(self, scraped_data: ScrapedData) -> dict:
        """Realiza el análisis Big Five basado en bio, posts y comentarios."""
        logger.info(f"🧬 Iniciando análisis para: {scraped_data.profile.username}")
        
        posts_context = []
        for p in scraped_data.posts[:10]:  
            posts_context.append({
                "caption": p.caption_raw,
                "engagement": p.engagement,
                "timestamp": p.timestamp,
                "comments_sample": [c.text for c in p.comments_sample[:10]]
            })

        try:
            return self.ai_client.analyze_personality_ocean(
                profile_bio=scraped_data.profile.bio,
                posts_data=posts_context
            )
        except Exception as e:
            logger.error(f"❌ Error en análisis de personalidad: {e}")
            return {"error": str(e)}
