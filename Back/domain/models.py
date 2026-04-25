"""
domain/models.py
================
Modelos de datos simplificados para el análisis de perfiles de Instagram.
Eliminada la redundancia y el análisis visual para un formato más limpio.
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Optional

@dataclass
class Metadata:
    scraped_at: str
    target_account: str
    scraper_version: str = "2.1.0"
    posts_requested: int = 0
    posts_obtained: int = 0
    comments_per_post: int = 0
    total_comments_obtained: int = 0
    session_valid: bool = True
    app_id_used: str = ""

@dataclass
class DataQuality:
    first_post_date: str = ""
    last_post_date: str = ""
    posts_requested: int = 0
    posts_obtained: int = 0
    comments_obtained: int = 0

@dataclass
class DeclaredContext:
    language: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    age_range: Optional[str] = None
    education_level: Optional[str] = None
    occupation: Optional[str] = None

@dataclass
class Profile:
    username: str = ""
    full_name: str = ""
    is_private: bool = False
    is_verified: bool = False
    is_business: bool = False
    followers_count: int = 0
    following_count: int = 0
    posts_count: int = 0
    bio: str = ""
    external_url: str = ""
    profile_pic_url: str = ""
    profile_pic_hd_url: str = ""
    declared_context: DeclaredContext = field(default_factory=DeclaredContext)

@dataclass
class TextAnalysis:
    language_detected: Optional[str] = None
    sentiment: Optional[str] = None
    emotion_labels: list[str] = field(default_factory=list)
    topic_tags: list[str] = field(default_factory=list)
    verbosity: Optional[str] = None
    reflexivity: Optional[str] = None
    tone: Optional[str] = None
    confidence: float = 0.0

@dataclass
class DerivedFeatures:
    posting_hour: Optional[int] = None
    posting_day: Optional[str] = None
    caption_length: int = 0
    emoji_density: float = 0.0
    hashtag_density: float = 0.0

@dataclass
class Comment:
    comment_id: str
    username: str
    text: str
    timestamp: str
    is_owner_comment: bool = False

@dataclass
class Post:
    post_id: str
    shortcode: str
    timestamp: str
    type: str
    caption_raw: str
    caption_clean: str
    hashtags: list[str] = field(default_factory=list)
    emojis: list[str] = field(default_factory=list)
    mentions: list[str] = field(default_factory=list)
    engagement: dict = field(default_factory=lambda: {"likes_count": 0, "comments_count": 0})
    text_analysis: TextAnalysis = field(default_factory=TextAnalysis)
    comments_sample: list[Comment] = field(default_factory=list)
    derived_features: DerivedFeatures = field(default_factory=DerivedFeatures)
    display_url: str = "" # Interno

    def to_dict(self):
        return asdict(self)

@dataclass
class ScrapedData:
    metadata: Metadata
    profile: Profile
    data_quality: DataQuality
    posts: list[Post]
    aggregate_features: dict = field(default_factory=dict)
    personality_report: Optional[dict] = None

    def to_dict(self):
        import dataclasses
        def _fix(obj):
            if isinstance(obj, dict): return {str(k): _fix(v) for k, v in obj.items()}
            if isinstance(obj, list): return [_fix(i) for i in obj]
            return obj
        return _fix(dataclasses.asdict(self))
