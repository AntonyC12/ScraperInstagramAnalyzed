"""
application/scrape_profile.py
==============================
Orquestador simplificado del flujo de scraping y análisis académico.
"""

from __future__ import annotations
import logging
from datetime import datetime, timezone
from config.settings import Settings
from domain.models import ScrapedData, Metadata, DataQuality
from domain.analyzers import DomainAnalyzer
from infrastructure.auth.cookie_session import get_session_data
from infrastructure.instagram.http_client import build_session
from infrastructure.instagram.profile_fetcher import fetch_profile
from infrastructure.instagram.posts_fetcher import fetch_posts
from infrastructure.instagram.comments_fetcher import fetch_all_post_comments
from infrastructure.persistence.json_writer import save_to_json
from application.personality_analysis import PersonalityAnalysisUseCase
from application.report_generator import ReportGeneratorUseCase

logger = logging.getLogger(__name__)

SCRAPER_VERSION = "2.1.0"

class ScrapeProfileUseCase:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        from infrastructure.ai.groq_client import GroqClient
        self.ai_client = GroqClient(settings.groq_api_key, model_name=settings.groq_model)

    def execute(self) -> ScrapedData:
        s = self.settings
        target = s.target_account

        logger.info("==============================================================")
        logger.info(f"  🕵️  Instagram Scraper & Analyzer v{SCRAPER_VERSION}")
        logger.info("==============================================================")

        # 1. Sesión
        session_data = get_session_data(
            target_username=target,
            cookies_dict=s.as_cookies_dict(),
            app_id_override=s.ig_app_id,
            headless=s.playwright_headless,
            cookies_path=s.cookies_file,
            save_cookies=True,
        )
        http_session = build_session(session_data["cookies"], session_data["app_id"])

        # 2. Perfil
        profile, user_id, end_cursor, initial_edges = fetch_profile(http_session, target)
        
        # 3. Contexto (Groq)
        if s.groq_api_key:
            logger.info(f"🤖 Infiriendo contexto con GROQ...")
            context_data = self.ai_client.infer_context_and_demographics(profile.bio, [])
            profile.declared_context.language = context_data.get("language")
            profile.declared_context.country = context_data.get("country")
            profile.declared_context.city = context_data.get("city")
            profile.declared_context.age_range = context_data.get("age_range")
            profile.declared_context.occupation = context_data.get("occupation")

        # 4. Posts y Comentarios
        posts = fetch_posts(http_session, user_id, initial_edges, end_cursor, s.posts_limit)
        fetch_all_post_comments(http_session, posts, target, s.comments_limit)
        total_comments = sum(len(p.comments_sample) for p in posts)

        # 5. Análisis de Texto
        logger.info(f"🔬 Analizando {len(posts)} posts...")
        for post in posts:
            post.text_analysis = DomainAnalyzer.analyze_text(post)
            post.derived_features = DomainAnalyzer.calculate_derived(post)

        # 6. Personalidad
        logger.info("🧬 Generando análisis Big Five...")
        personality_service = PersonalityAnalysisUseCase(self.ai_client)
        personality_report = personality_service.execute(
            ScrapedData(
                metadata=None, profile=profile, data_quality=None, posts=posts
            )
        )
        if personality_report:
            personality_report["disclaimer"] = "Propósito académico, no diagnóstico médico."

        # 7. Ensamblar
        scraped_data = ScrapedData(
            metadata=Metadata(
                scraped_at=datetime.now(tz=timezone.utc).isoformat(),
                target_account=target,
                scraper_version=SCRAPER_VERSION,
                posts_requested=s.posts_limit,
                posts_obtained=len(posts),
                comments_per_post=s.comments_limit,
                total_comments_obtained=total_comments,
                session_valid=session_data.get("is_logged_in", False),
                app_id_used=session_data["app_id"]
            ),
            profile=profile,
            data_quality=DataQuality(
                first_post_date=posts[-1].timestamp if posts else "",
                last_post_date=posts[0].timestamp if posts else "",
                posts_requested=s.posts_limit,
                posts_obtained=len(posts),
                comments_obtained=total_comments
            ),
            posts=posts,
            aggregate_features=DomainAnalyzer.build_aggregate_features(posts),
            personality_report=personality_report
        )

        # 8. Persistir
        repo_dir = s.back_dir / "repositories"
        repo_dir.mkdir(parents=True, exist_ok=True)
        json_path = repo_dir / f"{target}_scrapy.json"
        save_to_json(scraped_data, json_path)

        # 9. Reporte PDF
        report_service = ReportGeneratorUseCase(s.back_dir / "reports")
        pdf_path = report_service.execute(scraped_data.to_dict())
        
        logger.info(f"✅ Completado. JSON: {json_path} | PDF: {pdf_path}")
        return scraped_data
