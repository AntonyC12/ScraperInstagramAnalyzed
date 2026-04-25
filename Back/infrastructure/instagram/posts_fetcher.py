"""
infrastructure/instagram/posts_fetcher.py
==========================================
Extrae publicaciones de una cuenta de Instagram.
"""

from __future__ import annotations
import logging
import time
import random
from datetime import datetime, timezone
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from domain.models import Post
from domain.analyzers import extract_hashtags, extract_emojis, extract_mentions

logger = logging.getLogger(__name__)

def _unix_to_iso(ts: int) -> str:
    if not ts: return ""
    try:
        return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
    except:
        return ""

def _parse_post_node(node: dict) -> Post:
    caption_edges = node.get("edge_media_to_caption", {}).get("edges", [])
    caption = caption_edges[0].get("node", {}).get("text", "") if caption_edges else ""
    
    return Post(
        post_id=str(node.get("id", "")),
        shortcode=node.get("shortcode", ""),
        timestamp=_unix_to_iso(node.get("taken_at_timestamp", 0)),
        type=node.get("__typename", "GraphImage"),
        caption_raw=caption,
        caption_clean=caption,
        hashtags=extract_hashtags(caption),
        emojis=extract_emojis(caption),
        mentions=extract_mentions(caption),
        engagement={
            "likes_count": node.get("edge_media_preview_like", {}).get("count", 0),
            "comments_count": node.get("edge_media_to_comment", {}).get("count", 0)
        },
        display_url=node.get("display_url", "")
    )

def _parse_rest_item(item: dict) -> Post:
    caption = (item.get("caption") or {}).get("text", "")
    m_type = item.get("media_type")
    typename = "GraphImage" if m_type == 1 else "GraphVideo" if m_type == 2 else "GraphSidecar"

    return Post(
        post_id=str(item.get("pk", "")),
        shortcode=item.get("code", ""),
        timestamp=_unix_to_iso(item.get("taken_at", 0)),
        type=typename,
        caption_raw=caption,
        caption_clean=caption,
        hashtags=extract_hashtags(caption),
        emojis=extract_emojis(caption),
        mentions=extract_mentions(caption),
        engagement={
            "likes_count": item.get("like_count", 0),
            "comments_count": item.get("comment_count", 0)
        },
        display_url=item.get("image_versions2", {}).get("candidates", [{}])[0].get("url", "")
    )

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=5, max=60),
    retry=retry_if_exception_type((requests.exceptions.RequestException,)),
    reraise=True,
)
def _fetch_page_rest(session: requests.Session, user_id: str, max_id: str = "") -> tuple[list[Post], str, bool]:
    url = f"https://www.instagram.com/api/v1/feed/user/{user_id}/"
    params = {"count": 12}
    if max_id: params["max_id"] = max_id
    resp = session.get(url, params=params, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    posts = [_parse_rest_item(it) for it in data.get("items", [])]
    return posts, data.get("next_max_id", ""), data.get("more_available", False)

def fetch_posts(session: requests.Session, user_id: str, initial_edges: list, initial_cursor: str, limit: int = 10) -> list[Post]:
    all_posts = []
    if initial_edges:
        all_posts.extend([_parse_post_node(e["node"]) for e in initial_edges if "node" in e])
    
    max_id = initial_cursor
    has_next = (bool(max_id) or not all_posts) and len(all_posts) < limit

    while has_next and len(all_posts) < limit:
        time.sleep(random.uniform(2, 4))
        try:
            new_posts, max_id, has_next = _fetch_page_rest(session, user_id, max_id)
            if not new_posts: break
            all_posts.extend(new_posts)
        except: break
            
    return all_posts[:limit]
