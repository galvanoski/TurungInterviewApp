"""
Web scraper module for extracting job descriptions from URLs.
Uses multiple strategies to handle cookie walls, JS-rendered pages, etc.
"""

import json
import re

import cloudscraper
import requests
from bs4 import BeautifulSoup

# Full browser-like headers to avoid being blocked
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,de;q=0.8,es;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}


def fetch_via_jina(url: str) -> str | None:
    """
    Use Jina Reader API to render JS-heavy pages and get clean text.
    Free, no auth required. Handles SPAs and cookie walls.
    """
    try:
        jina_url = f"https://r.jina.ai/{url}"
        resp = requests.get(
            jina_url,
            headers={"Accept": "text/plain", "User-Agent": "Mozilla/5.0"},
            timeout=30,
        )
        resp.raise_for_status()
        text = resp.text.strip()
        if len(text) > 100:
            return text[:8000]
    except Exception:
        pass
    return None


def _extract_json_ld(soup: BeautifulSoup) -> str | None:
    """Extract job description from JSON-LD structured data."""
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
        except (json.JSONDecodeError, TypeError):
            continue

        items = data if isinstance(data, list) else [data]

        for item in items:
            if isinstance(item, dict) and item.get("@graph"):
                items.extend(item["@graph"])

        for item in items:
            if not isinstance(item, dict):
                continue
            if item.get("@type") in ("JobPosting", "jobPosting"):
                parts = []
                if item.get("title"):
                    parts.append(f"Job Title: {item['title']}")
                if item.get("hiringOrganization"):
                    org = item["hiringOrganization"]
                    name = org.get("name", org) if isinstance(org, dict) else org
                    parts.append(f"Company: {name}")
                if item.get("jobLocation"):
                    loc = item["jobLocation"]
                    if isinstance(loc, dict):
                        addr = loc.get("address", {})
                        if isinstance(addr, dict):
                            parts.append(f"Location: {addr.get('addressLocality', '')} {addr.get('addressCountry', '')}")
                    elif isinstance(loc, list):
                        locs = []
                        for l in loc:
                            if isinstance(l, dict):
                                a = l.get("address", {})
                                if isinstance(a, dict):
                                    locs.append(f"{a.get('addressLocality', '')} {a.get('addressCountry', '')}")
                        if locs:
                            parts.append(f"Location: {', '.join(locs)}")
                desc = item.get("description", "")
                if desc:
                    desc_soup = BeautifulSoup(desc, "html.parser")
                    desc_text = desc_soup.get_text(separator="\n", strip=True)
                    parts.append(f"\n{desc_text}")
                if item.get("qualifications"):
                    parts.append(f"\nQualifications: {item['qualifications']}")
                if item.get("skills"):
                    parts.append(f"\nSkills: {item['skills']}")
                if item.get("responsibilities"):
                    parts.append(f"\nResponsibilities: {item['responsibilities']}")

                text = "\n".join(parts).strip()
                if len(text) > 50:
                    return text
    return None


def _extract_meta_tags(soup: BeautifulSoup) -> str | None:
    """Extract job info from Open Graph and meta description tags."""
    parts = []
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        parts.append(f"Title: {og_title['content']}")

    og_desc = soup.find("meta", property="og:description")
    if og_desc and og_desc.get("content"):
        parts.append(og_desc["content"])

    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc and meta_desc.get("content"):
        content = meta_desc["content"]
        if content not in "\n".join(parts):
            parts.append(content)

    text = "\n".join(parts).strip()
    return text if len(text) > 50 else None


def _extract_main_content(soup: BeautifulSoup) -> str:
    """Fallback: extract text from the most likely content areas of the page."""
    for tag in soup(["script", "style", "nav", "footer", "header", "aside",
                     "form", "button", "iframe", "noscript"]):
        tag.decompose()

    selectors = [
        "[class*='job-description']",
        "[class*='jobDescription']",
        "[class*='job-detail']",
        "[class*='jobDetail']",
        "[class*='vacancy']",
        "[class*='posting-description']",
        "[class*='listing-description']",
        "[id*='job-description']",
        "[id*='jobDescription']",
        "article",
        "main",
        "[role='main']",
    ]

    for selector in selectors:
        elements = soup.select(selector)
        if elements:
            text = "\n\n".join(el.get_text(separator="\n", strip=True) for el in elements)
            if len(text) > 100:
                return text[:8000]

    body = soup.find("body")
    if body:
        return body.get_text(separator="\n", strip=True)[:8000]
    return soup.get_text(separator="\n", strip=True)[:8000]


def _fetch_html(url: str) -> str:
    """Fetch HTML using cloudscraper (primary) and requests (fallback)."""
    try:
        scraper = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "windows", "mobile": False}
        )
        resp = scraper.get(url, timeout=30, allow_redirects=True)
        resp.raise_for_status()
        if len(resp.text) > 500:
            return resp.text
    except Exception:
        pass

    session = requests.Session()
    session.headers.update(_HEADERS)
    resp = session.get(url, timeout=25, allow_redirects=True)
    resp.raise_for_status()

    if "cookie" in resp.text.lower()[:2000] and len(resp.text) < 5000:
        resp = session.get(url, timeout=25, allow_redirects=True)

    return resp.text


def scrape_job_url(url: str) -> dict:
    """
    Scrape a job posting URL and extract the description.

    Returns:
        dict with keys: success, text, method, error
    """
    try:
        html = _fetch_html(url)
        soup = BeautifulSoup(html, "html.parser")

        json_ld_text = _extract_json_ld(soup)
        if json_ld_text:
            return {"success": True, "text": json_ld_text, "method": "JSON-LD (structured data)", "error": None}

        meta_text = _extract_meta_tags(soup)
        main_text = _extract_main_content(soup)

        if meta_text and main_text:
            combined = f"{meta_text}\n\n{main_text}"
            return {"success": True, "text": combined[:8000], "method": "Meta tags + HTML content", "error": None}
        elif main_text and len(main_text) > 100:
            return {"success": True, "text": main_text, "method": "HTML content extraction", "error": None}
        elif meta_text:
            return {"success": True, "text": meta_text, "method": "Meta tags only", "error": None}
    except Exception:
        pass

    jina_text = fetch_via_jina(url)
    if jina_text:
        return {"success": True, "text": jina_text, "method": "Jina Reader (JS-rendered)", "error": None}

    return {
        "success": False,
        "text": "",
        "method": "",
        "error": "Could not extract content from this URL. The site may require authentication or advanced bot protection. Try pasting the job description text directly.",
    }
