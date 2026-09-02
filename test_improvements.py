import html
import re
from typing import List, Tuple
from bs4 import BeautifulSoup

def clean_pure_text(text: str) -> str:
    """
    Strips all part dividers (e.g. '━━━━━━━━━━━━━━━━ Part 7 ━━━━━━━━━━━━━━━━'),
    dashes, equal signs, stray ADVERTISEMENT markers, and formats clean continuous paragraphs.
    """
    if not text:
        return ""

    lines = text.splitlines()
    cleaned_lines = []
    
    # Patterns to remove
    divider_pattern = re.compile(r"^[━\-=_\*~#\s]*(Part\s+\d+|Chapter\s+\d+|Section\s+\d+)?[━\-=_\*~#\s]*$", re.IGNORECASE)
    ad_line_pattern = re.compile(r"^(advertisement|sponsored|read\s+more|click\s+here|share\s+on|written\s+by|author\s+bio|leave\s+a\s+reply|source:|photo\s+by)[\s\:\.\-]*$", re.IGNORECASE)
    pure_symbol_line = re.compile(r"^[━\-=_\*~#\s]{3,}$")

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if cleaned_lines and cleaned_lines[-1] != "":
                cleaned_lines.append("")
            continue

        # Check if line is a divider or ad marker
        if divider_pattern.match(stripped) and (len(stripped) > 5 or "part" in stripped.lower()):
            continue
        if ad_line_pattern.match(stripped):
            continue
        if pure_symbol_line.match(stripped):
            continue
        if re.match(r"^part\s+\d+[\s\:\.\-]*$", stripped, re.IGNORECASE):
            continue

        cleaned_lines.append(stripped)

    # Join and normalize multiple blank lines
    result = "\n".join(cleaned_lines)
    result = re.sub(r"\n{3,}", "\n\n", result).strip()
    return result

def extract_from_soup_improved(soup: BeautifulSoup) -> Tuple[str, List[str]]:
    # Extract Title
    title = ""
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        title = og_title["content"].strip()

    if not title and soup.title:
        title = soup.title.get_text(strip=True)

    if not title:
        h1 = soup.find("h1")
        if h1:
            title = h1.get_text(strip=True)

    # Locate Article Body Container
    content_area = (
        soup.find("div", class_=re.compile(r"(entry-content|post-content|article-content|story-content|elementor-widget-theme-post-content)"))
        or soup.find("article")
        or soup.find("main")
    )
    if not content_area:
        return title, []

    container = BeautifulSoup(str(content_area), "html.parser")

    # Decompose script, style, ads, social, author, header, footer, etc.
    for tag in container.find_all([
        "script", "style", "ins", "nav", "aside", "figure", "iframe", "noscript",
        "form", "button", "svg", "header", "footer", "select", "option"
    ]):
        tag.decompose()

    # Safely decompose widgets without deleting parent wrappers
    for tag in list(container.find_all(class_=re.compile(r"(banner|social-share|share-box|author-box|author-bio|widget-area|comments-area|nav-links|wp-block-buttons|disclaimer)", re.IGNORECASE))):
        # Don't decompose if it contains the main body (> 4 paragraphs)
        if len(tag.find_all("p")) < 4:
            tag.decompose()

    for tag in list(container.find_all(id=re.compile(r"(social-share|author-bio|comments|disclaimer)", re.IGNORECASE))):
        if len(tag.find_all("p")) < 4:
            tag.decompose()

    paragraphs = []
    for el in container.find_all(["p", "blockquote"]):
        txt = el.get_text(separator=" ", strip=True)
        if not txt:
            continue

        lower = txt.lower()
        if len(txt) < 20 and any(k in lower for k in ["next", "continue", "page", "part", "prev", "previous", "share", "read next"]):
            continue
        if any(lower.startswith(bad) for bad in ["advertisement", "read more", "click here", "author bio", "written by", "subscribe to", "share on", "sponsored", "leave a reply"]):
            continue
        if "is a contributor who enjoys writing" in lower or "contributor who enjoys writing about" in lower:
            continue

        paragraphs.append(txt)

    return title, paragraphs
