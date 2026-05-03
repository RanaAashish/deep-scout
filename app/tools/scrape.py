"""HTTP fetch + HTML→text with conservative limits (binary URL filtering, timeouts)."""

from __future__ import annotations

import asyncio
import logging
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

CONTENT_LENGTH_LIMIT = 10_000

FETCH_TIMEOUT_SEC = 12.0

BLOCKED_EXTENSIONS = (
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".ppt",
    ".zip",
    ".rar",
    ".7z",
    ".txt",
    ".js",
    ".xml",
    ".css",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".svg",
    ".webp",
    ".mp3",
    ".mp4",
)


def is_valid_url(url: str) -> bool:
    lowered = url.lower()
    return not any(ext in lowered for ext in BLOCKED_EXTENSIONS)


def html_to_text(html_content: str) -> str:
    soup = BeautifulSoup(html_content, "lxml")
    tags = ("h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "blockquote")
    parts: list[str] = []
    for el in soup.find_all(tags):
        t = el.get_text(strip=True)
        if t:
            parts.append(t)
    return "\n".join(parts)


async def fetch_page_text(url: str, *, max_chars: int = CONTENT_LENGTH_LIMIT) -> str:
    if not url or not urlparse(url).scheme.startswith("http"):
        return "Error fetching content: invalid URL"
    if not is_valid_url(url):
        return "Error fetching content: URL contains restricted file extension"

    try:
        logger.info("      [dim]Fetching:[/dim] %s", url)
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=FETCH_TIMEOUT_SEC,
            headers={
                "User-Agent": "shadow-writer/0.1 (+https://github.com/RanaAashish/shadow-writer)"
            },
        ) as client:
            response = await client.get(url)
            if response.status_code != 200:
                logger.warning("      [red]Fetch failed:[/red] HTTP %s", response.status_code)
                return f"Error fetching content: HTTP {response.status_code}"
            raw = response.text
    except Exception as e:
        logger.warning("      [red]Fetch error:[/red] %s", e)
        return f"Error fetching content: {e!s}"

    text = html_to_text(raw)[:max_chars]
    logger.info("      [dim]Extracted %d chars[/dim]", len(text))
    return text if text.strip() else "(No extractable text from page.)"


async def fetch_many_urls(
    urls: list[str], *, max_concurrent: int = 4
) -> dict[str, str]:
    sem = asyncio.Semaphore(max_concurrent)

    async def one(u: str) -> tuple[str, str]:
        async with sem:
            body = await fetch_page_text(u)
            return u, body

    pairs = await asyncio.gather(*[one(u) for u in urls])
    return dict(pairs)
