"""
domain/analyzers.py
===================
Análisis avanzado de contenido, conducta temporal e interacción social.
Limpieza de código para eliminar placeholders y métricas no utilizadas.
"""

from __future__ import annotations
import re
import logging
from collections import Counter
from datetime import datetime
from typing import TYPE_CHECKING
import emoji as emoji_lib

if TYPE_CHECKING:
    from domain.models import Comment, Post, TextAnalysis, DerivedFeatures

logger = logging.getLogger(__name__)

_HASHTAG_RE = re.compile(r"#(\w+)", re.UNICODE)
_MENTION_RE = re.compile(r"@(\w+)", re.UNICODE)

_THEMES = {
    "vida personal": ["yo", "mi", "me", "siento", "hoy", "día", "personal"],
    "trabajo/estudio": ["trabajo", "universidad", "estudio", "proyecto", "oficina"],
    "ocio/viajes": ["viaje", "playa", "vacaciones", "descanso", "trip"],
    "familia": ["familia", "mamá", "papá", "hijos"],
    "espiritualidad": ["dios", "fe", "gracias", "bendición"],
    "deporte/gym": ["gym", "entreno", "deporte", "fitness"],
}

_EMOTIONAL_WORDS = {
    "alegría": ["feliz", "alegre", "contento", "bien", "happy"],
    "tristeza": ["triste", "mal", "solo", "sad"],
    "amor": ["amor", "quiero", "amo", "love", "❤️"],
    "orgullo": ["orgulloso", "logré", "meta"],
}

def extract_hashtags(text: str) -> list[str]:
    return [m.lower() for m in _HASHTAG_RE.findall(text or "")]

def extract_emojis(text: str) -> list[str]:
    return [token["emoji"] for token in emoji_lib.emoji_list(text or "")]

def extract_mentions(text: str) -> list[str]:
    return [m.lower() for m in _MENTION_RE.findall(text or "")]

class DomainAnalyzer:
    """Orquestador de análisis de dominio."""

    @staticmethod
    def analyze_text(post: Post) -> TextAnalysis:
        from domain.models import TextAnalysis
        text = post.caption_raw.lower()
        
        pos_words = ["feliz", "bien", "gracias", "amor", "excelente", "top", "lindo", "bella"]
        neg_words = ["triste", "mal", "error", "odio", "feo", "lluvia", "erizo"]
        
        pos = sum(1 for w in pos_words if w in text)
        neg = sum(1 for w in neg_words if w in text)
        sentiment = "positivo" if pos > neg else "negativo" if neg > pos else "neutro"
        
        emotions = [e for e, words in _EMOTIONAL_WORDS.items() if any(w in text for w in words)]
        tone = "emocional" if len(post.emojis) > 1 or pos > 0 else "informal" if any(x in text for x in ["jaja", "lol"]) else "neutro"
        verbosity = "extenso" if len(text.split()) > 30 else "moderado" if len(text.split()) > 10 else "breve"
        
        return TextAnalysis(
            language_detected="es",
            sentiment=sentiment,
            emotion_labels=emotions,
            topic_tags=[t for t, k in _THEMES.items() if any(w in text for w in k)],
            verbosity=verbosity,
            reflexivity="impulsivo" if "!" in text or "?" in text else "neutro",
            tone=tone,
            confidence=0.75
        )

    @staticmethod
    def calculate_derived(post: Post) -> DerivedFeatures:
        from domain.models import DerivedFeatures
        try:
            dt = datetime.fromisoformat(post.timestamp.replace("Z", "+00:00"))
            hour, day = dt.hour, dt.strftime("%A")
        except:
            hour, day = None, None
            
        words = post.caption_raw.split()
        return DerivedFeatures(
            posting_hour=hour,
            posting_day=day,
            caption_length=len(post.caption_raw),
            emoji_density=len(post.emojis) / len(words) if words else 0,
            hashtag_density=len(post.hashtags) / len(words) if words else 0
        )

    @staticmethod
    def build_aggregate_features(posts: list[Post]) -> dict:
        if not posts: return {}
        
        hours = [p.derived_features.posting_hour for p in posts if p.derived_features.posting_hour is not None]
        days = [p.derived_features.posting_day for p in posts if p.derived_features.posting_day is not None]
        h_dist, d_dist = Counter(hours), Counter(days)
        
        timestamps = []
        for p in posts:
            try:
                timestamps.append(datetime.fromisoformat(p.timestamp.replace("Z", "+00:00")))
            except: pass
        
        freq = 0.0
        if len(timestamps) > 1:
            timestamps.sort()
            deltas = [(timestamps[i+1] - timestamps[i]).days for i in range(len(timestamps)-1)]
            freq = sum(deltas) / len(deltas)

        return {
            "posting_frequency_days": round(freq, 2),
            "most_active_hour": h_dist.most_common(1)[0][0] if h_dist else None,
            "most_active_day": d_dist.most_common(1)[0][0] if d_dist else None,
            "avg_likes_per_post": round(sum(p.engagement["likes_count"] for p in posts) / len(posts), 1),
            "avg_comments_per_post": round(sum(p.engagement["comments_count"] for p in posts) / len(posts), 1),
            "style": {
                "avg_caption_length": round(sum(p.derived_features.caption_length for p in posts) / len(posts), 1),
                "avg_hashtags": round(sum(len(p.hashtags) for p in posts) / len(posts), 1),
                "avg_emojis": round(sum(len(p.emojis) for p in posts) / len(posts), 1),
            }
        }
