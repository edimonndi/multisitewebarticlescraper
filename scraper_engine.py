import html
import re
import threading
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple
from urllib.parse import parse_qs, unquote, urlencode, urljoin, urlparse, urlunparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

UNICODE_REPLACEMENTS = {
    "\u2018": "'", "\u2019": "'", "\u201a": "'", "\u201b": "'",
    "\u201c": '"', "\u201d": '"', "\u201e": '"', "\u201f": '"',
    "\u2014": "—", "\u2013": "–", "\u2026": "...", "\u00a0": " ",
    "\ufeff": "", "\u200b": "", "\u200e": "", "\u200f": ""
}

DISCARD_STARTS = (
    "advertisement", "read more", "click here", "author bio", "written by",
    "subscribe to", "share on", "source:", "photo by", "image by",
    "sponsored", "leave a reply", "comment", "related stories", "trending now",
    "follow us", "disclaimer:"
)


def create_resilient_session() -> requests.Session:
    """Creates a fresh requests Session with retry adapter for high connection reliability."""
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)
    retries = Retry(
        total=2,
        backoff_factor=0.3,
        status_forcelist=[500, 502, 503, 504],
        raise_on_status=False
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def clean_pure_text(text: str) -> str:
    """
    Cleans story text by stripping:
    - Pure symbol divider lines (e.g. '━━━━━━━━━━━━━━━━', '================', '----------------')
    - Scraper-generated part divider banners (e.g. '━━━━━━━━━━━━━━━━ Part 7 ━━━━━━━━━━━━━━━━', '--- Part 2 ---')
    - Metadata lines (e.g. 'Source: https://...', 'Total Parts: 3 | Total Words: ...')
    - Bottom navigation cues (e.g. '-END OF PART 2 - PRESS NEXT PART IN BOTTOM...')
    - Ad markers (e.g. 'ADVERTISEMENT', 'SPONSORED')
    PRESERVES:
    - All story section titles and chapter headers (e.g. 'Part One: The Last Thing...', 'Chapter 2: ...', 'Three Years Later')
    - All narrative paragraphs and dialog
    """
    if not text:
        return ""

    lines = text.splitlines()
    cleaned_lines = []

    # Matches only symbol-heavy scraper banners e.g. "━━━━━━━━━━━━━━━━ Part 7 ━━━━━━━━━━━━━━━━", "--- Part 2 ---"
    scraper_part_banner = re.compile(
        r"^[━\-=_\*~#]{3,}\s*(Part\s+\d+|Page\s+\d+)?\s*[━\-=_\*~#]{3,}$",
        re.IGNORECASE,
    )

    # Pure symbol lines (3 or more symbols like ━━━━, ====, ----, ____)
    pure_symbol_line = re.compile(r"^[━\-=_\*~#\s]{3,}$")

    metadata_pattern = re.compile(
        r"^(source:\s*https?://|total\s+parts:\s*\d+|total\s+words:\s*[\d,]+|reading\s+time:\s*\d+)",
        re.IGNORECASE,
    )

    ad_standalone_line = re.compile(
        r"^(advertisement|sponsored|sponsored\s+content|share\s+on\s+facebook|leave\s+a\s+reply|click\s+here\s+to\s+read\s+more)[\s\:\.\-]*$",
        re.IGNORECASE,
    )

    footer_nav_pattern = re.compile(
        r"^[-–—\s]*(END\s+OF\s+PART\s+\d+|PRESS\s+NEX[T]?\s+PART|CONTINUE\s+TO\s+NEXT\s+PAGE|CLICK\s+NEXT\s+PART).*$",
        re.IGNORECASE,
    )

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if cleaned_lines and cleaned_lines[-1] != "":
                cleaned_lines.append("")
            continue

        if scraper_part_banner.match(stripped):
            continue
        if pure_symbol_line.match(stripped):
            continue
        if metadata_pattern.match(stripped):
            continue
        if ad_standalone_line.match(stripped):
            continue
        if footer_nav_pattern.match(stripped):
            continue

        cleaned_lines.append(stripped)

    result = "\n".join(cleaned_lines)
    result = re.sub(r"\n{3,}", "\n\n", result).strip()
    return result


@dataclass
class StoryPart:
    part_num: int
    url: str
    paragraphs: List[str] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "\n\n".join(self.paragraphs)

    @property
    def word_count(self) -> int:
        return sum(len(p.split()) for p in self.paragraphs)


@dataclass
class StoryArticle:
    title: str
    original_url: str
    domain: str
    parts: List[StoryPart] = field(default_factory=list)

    @property
    def total_parts(self) -> int:
        return len(self.parts)

    @property
    def total_words(self) -> int:
        return sum(p.word_count for p in self.parts)

    @property
    def reading_time_minutes(self) -> int:
        return max(1, round(self.total_words / 220))

    def to_pure_body(self) -> str:
        """
        Returns ONLY the clean continuous story body paragraphs.
        Preserves story section titles, chapter headings, and dialog.
        No scraper divider lines (====, ----, ━━━━━), no URL metadata.
        """
        all_paras = []
        for part in self.parts:
            for p in part.paragraphs:
                cleaned_p = p.strip()
                if cleaned_p:
                    all_paras.append(cleaned_p)
        raw_body = "\n\n".join(all_paras)
        return clean_pure_text(raw_body)

    def to_text(self, include_part_headers: bool = False, include_metadata: bool = False) -> str:
        """
        Returns story text. Defaults to clean pure story text.
        """
        if not include_metadata and not include_part_headers:
            return self.to_pure_body()

        lines = []
        if include_metadata and self.title:
            lines.append(f"{self.title.upper()}")
            lines.append("=" * len(self.title))
            lines.append(f"Source: {self.original_url}")
            lines.append(f"Total Parts: {self.total_parts} | Total Words: {self.total_words:,}")
            lines.append("\n" + "-" * 50 + "\n")

        for part in self.parts:
            if include_part_headers and self.total_parts > 1:
                lines.append(f"\n━━━━━━━━━━━━━━━━ Part {part.part_num} ━━━━━━━━━━━━━━━━\n")
            lines.append(part.text)
            lines.append("")

        return "\n".join(lines).strip()

    def to_markdown(self) -> str:
        md = []
        md.append(f"# {self.title}\n")
        md.append(f"> **Source:** [{self.domain}]({self.original_url})  ")
        md.append(f"> **Length:** {self.total_parts} parts · {self.total_words:,} words · ~{self.reading_time_minutes} min read\n")
        md.append("---\n")

        for part in self.parts:
            if self.total_parts > 1:
                md.append(f"## Part {part.part_num}\n")
            for p in part.paragraphs:
                md.append(f"{p}\n")
            md.append("")

        return "\n".join(md)

    def to_html(self, theme: str = "dark") -> str:
        bg_col = "#0f172a" if theme == "dark" else "#f8fafc"
        card_bg = "#1e293b" if theme == "dark" else "#ffffff"
        text_col = "#f1f5f9" if theme == "dark" else "#1e293b"
        accent_col = "#38bdf8" if theme == "dark" else "#0284c7"
        border_col = "#334155" if theme == "dark" else "#e2e8f0"
        muted_col = "#94a3b8" if theme == "dark" else "#64748b"

        parts_html = []
        for part in self.parts:
            header_html = f'<div class="part-banner">Part {part.part_num}</div>' if self.total_parts > 1 else ''
            paras_html = "\n".join(f'<p>{html.escape(p)}</p>' for p in part.paragraphs)
            parts_html.append(f'<section class="story-part">{header_html}\n{paras_html}</section>')

        content_body = "\n<hr class=\"divider\"/>\n".join(parts_html)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(self.title)}</title>
    <style>
        body {{
            background-color: {bg_col};
            color: {text_col};
            font-family: 'Georgia', serif;
            line-height: 1.85;
            font-size: 19px;
            margin: 0;
            padding: 40px 20px;
            display: flex;
            justify-content: center;
        }}
        .container {{
            max-width: 820px;
            width: 100%;
            background: {card_bg};
            padding: 48px 56px;
            border-radius: 16px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.25);
            border: 1px solid {border_col};
        }}
        h1 {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            font-size: 32px;
            line-height: 1.3;
            color: {accent_col};
            margin-top: 0;
            margin-bottom: 16px;
        }}
        .meta {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            font-size: 14px;
            color: {muted_col};
            margin-bottom: 32px;
            padding-bottom: 20px;
            border-bottom: 1px solid {border_col};
        }}
        .part-banner {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            font-size: 16px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 2px;
            color: {accent_col};
            margin: 36px 0 20px 0;
            text-align: center;
            border-top: 1px dashed {border_col};
            border-bottom: 1px dashed {border_col};
            padding: 8px 0;
        }}
        p {{
            margin-bottom: 22px;
            text-align: justify;
        }}
        .divider {{
            border: none;
            border-top: 1px solid {border_col};
            margin: 36px 0;
        }}
        .footer {{
            margin-top: 48px;
            text-align: center;
            font-size: 13px;
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            color: {muted_col};
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{html.escape(self.title)}</h1>
        <div class="meta">
            <span><strong>Source:</strong> {html.escape(self.domain)}</span> &bull;
            <span>{self.total_parts} Parts</span> &bull;
            <span>{self.total_words:,} Words</span> &bull;
            <span>~{self.reading_time_minutes} Min Read</span>
        </div>
        {content_body}
        <div class="footer">
            Saved with <strong>DEA Story Scraper</strong> &bull; <a href="https://www.deainnovations.com" style="color:{accent_col}; text-decoration:none;" target="_blank">www.deainnovations.com</a>
        </div>
    </div>
</body>
</html>"""


class StoryScraper:
    def __init__(self):
        self.session = create_resilient_session()

    @staticmethod
    def clean_text(text: str) -> str:
        if not text:
            return ""
        text = html.unescape(text)
        for old, new in UNICODE_REPLACEMENTS.items():
            text = text.replace(old, new)
        text = re.sub(r"[ \t]+", " ", text)
        return text.strip()

    @staticmethod
    def clean_title(title: str) -> str:
        if not title:
            return "Untitled Story"
        title = StoryScraper.clean_text(title)
        title = re.sub(
            r"\s*[-|–—]\s*(America Focus|Fanstopis|LEVANEWS|Human Heart Tales|DAILY STORIES|Kaylestore|Lead to Happiness|1 Million Stories|Happy Soul Shop|Stories).*$",
            "",
            title,
            flags=re.IGNORECASE,
        )
        title = re.sub(r"^(FULL STORY|Part \d+|Story)\s*[-:–—]\s*", "", title, flags=re.IGNORECASE).strip()
        return title or "Untitled Story"

    def extract_from_soup(self, soup: BeautifulSoup) -> Tuple[str, List[str]]:
        # 1. Extract Title
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

        clean_title = self.clean_title(title)

        # 2. Locate Article Body Container
        content_area = (
            soup.find("div", class_=re.compile(r"(entry-content|post-content|article-content|story-content|elementor-widget-theme-post-content)"))
            or soup.find("article")
            or soup.find("main")
        )
        if not content_area:
            return clean_title, []

        # Make copy for DOM mutation
        container = BeautifulSoup(str(content_area), "html.parser")

        # Decompose non-content tags
        for tag in container.find_all([
            "script", "style", "ins", "nav", "aside", "figure", "iframe", "noscript",
            "form", "button", "svg", "header", "footer", "select", "option"
        ]):
            tag.decompose()

        # Safely decompose widgets without deleting parent wrappers
        for tag in list(container.find_all(class_=re.compile(r"(banner|social-share|share-box|author-box|author-bio|widget-area|comments-area|nav-links|wp-block-buttons|disclaimer)", re.IGNORECASE))):
            if len(tag.find_all(["p", "h2", "h3", "h4"])) < 4:
                tag.decompose()

        for tag in list(container.find_all(id=re.compile(r"(social-share|author-bio|comments|disclaimer)", re.IGNORECASE))):
            if len(tag.find_all(["p", "h2", "h3", "h4"])) < 4:
                tag.decompose()

        # Extract Paragraphs, Quotes, Lists, and Section Headings in exact document order
        paragraphs = []
        target_tags = ["h1", "h2", "h3", "h4", "h5", "h6", "p", "blockquote", "pre", "li"]

        for el in container.find_all(target_tags):
            # Skip parent container if it has child target tags to prevent duplicate text
            if any(el.find_all(target_tags)):
                continue

            txt = self.clean_text(el.get_text(separator=" ", strip=True))
            if not txt:
                continue

            lower = txt.lower()

            # Skip if heading is an exact duplicate of the main title
            if txt.lower() == clean_title.lower():
                continue

            # Discard short pagination/nav fragments
            if len(txt) < 20 and any(k in lower for k in ["next", "continue", "page", "part", "prev", "previous", "share", "read next"]):
                continue

            # Discard obvious advertising or author signatures
            if any(lower.startswith(bad) for bad in DISCARD_STARTS):
                continue

            # Specific author bio patterns
            if "is a contributor who enjoys writing" in lower or "contributor who enjoys writing about" in lower:
                continue
            if ("contributor at america focus" in lower or "andrew collins" in lower) and len(txt) < 180:
                continue
            if "press nex part in bottom of page" in lower or "press next part in bottom of page" in lower:
                continue

            paragraphs.append(txt)

        return clean_title, paragraphs

    def fetch_page(self, url: str) -> Tuple[Optional[BeautifulSoup], str, int]:
        try:
            res = self.session.get(url, timeout=14, allow_redirects=True)
            res.encoding = res.apparent_encoding or "utf-8"
            if res.status_code != 200:
                return None, res.url, res.status_code
            soup = BeautifulSoup(res.text, "html.parser")
            return soup, res.url, 200
        except Exception:
            # Retry with a fresh connection on transient network reset
            try:
                fresh_session = create_resilient_session()
                res = fresh_session.get(url, timeout=14, allow_redirects=True)
                res.encoding = res.apparent_encoding or "utf-8"
                if res.status_code != 200:
                    return None, res.url, res.status_code
                soup = BeautifulSoup(res.text, "html.parser")
                return soup, res.url, 200
            except Exception:
                return None, url, 500

    def scrape(
        self,
        url: str,
        progress_callback: Optional[Callable[[str, int, int, float], None]] = None,
        cancel_event: Optional[threading.Event] = None
    ) -> StoryArticle:
        # Re-initialize fresh session per scrape to avoid state contamination
        self.session = create_resilient_session()

        url = url.strip().strip("'\"<> ")
        if not url:
            raise ValueError("URL cannot be empty.")

        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            if not url.startswith("http://") and not url.startswith("https://"):
                url = "https://" + url
                parsed = urlparse(url)

        domain = parsed.netloc.lower()
        parts: List[StoryPart] = []
        seen_hashes = set()
        seen_urls = set()
        story_title = ""

        def notify(msg: str, part_num: int = 1, total_est: int = 0, pct: float = 0.0):
            if progress_callback:
                progress_callback(msg, part_num, total_est, pct)

        # Detect Strategy
        is_feji = ("feji.io" in domain or "humanhearttales" in domain) and re.search(r"/(full-story-|part-\d+-)", parsed.path, re.IGNORECASE)
        is_query_part = (
            "fanstopis.com" in domain
            or "levanews.com" in domain
            or "1millionstories.net" in domain
            or "part=" in parsed.query
            or "page=" in parsed.query
        )

        if is_feji:
            # Feji Slug Strategy
            path = parsed.path.strip("/")
            slug = path.rsplit("/", 1)[-1]
            if slug.lower().startswith("full-story-"):
                base_suffix = slug[len("full-story-"):]
                start_part = 1
            elif re.match(r"^part-(\d+)-", slug, re.IGNORECASE):
                m = re.match(r"^part-(\d+)-(.+)$", slug, re.IGNORECASE)
                start_part = int(m.group(1))
                base_suffix = m.group(2)
            else:
                base_suffix = slug
                start_part = 1

            current_part = 1
            max_parts = 100

            while current_part <= max_parts:
                if cancel_event and cancel_event.is_set():
                    notify("Scraping cancelled by user.", current_part, 0, 0)
                    break

                if current_part == 1:
                    target_url = f"{parsed.scheme}://{parsed.netloc}/full-story-{base_suffix}/"
                else:
                    target_url = f"{parsed.scheme}://{parsed.netloc}/part-{current_part}-{base_suffix}/"

                if target_url in seen_urls:
                    break
                seen_urls.add(target_url)

                notify(f"Fetching part {current_part}...", current_part, max_parts, 0.0)

                soup, final_url, status = self.fetch_page(target_url)
                if status == 404 and current_part == 1:
                    alt_url = f"{parsed.scheme}://{parsed.netloc}/part-1-{base_suffix}/"
                    soup, final_url, status = self.fetch_page(alt_url)

                if status != 200 or not soup:
                    if status == 404 and current_part == 1:
                        raise RuntimeError(f"Error 404: Page not found at {target_url}. Please check if the URL was cut off when copying.")
                    break

                title, paras = self.extract_from_soup(soup)
                if not story_title and title:
                    story_title = title
                if not paras:
                    break

                joined = "\n\n".join(paras)
                content_hash = hash(joined[:300] + joined[-300:])
                if content_hash in seen_hashes:
                    break
                seen_hashes.add(content_hash)

                parts.append(StoryPart(part_num=current_part, url=target_url, paragraphs=paras))
                current_part += 1

        elif is_query_part:
            # Query Param Strategy (e.g. ?part=2)
            base_clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}/"
            current_part = 1
            max_parts = 50

            while current_part <= max_parts:
                if cancel_event and cancel_event.is_set():
                    notify("Scraping cancelled by user.", current_part, 0, 0)
                    break

                if current_part == 1:
                    target_url = base_clean
                else:
                    target_url = f"{base_clean}?part={current_part}"

                if target_url in seen_urls:
                    break
                seen_urls.add(target_url)

                notify(f"Fetching part {current_part}...", current_part, max_parts, 0.0)

                soup, final_url, status = self.fetch_page(target_url)
                if status != 200 or not soup:
                    if status == 404 and current_part == 1:
                        raise RuntimeError(f"Error 404: Page not found at {target_url}. Please check if the URL was cut off when copying.")
                    break

                title, paras = self.extract_from_soup(soup)
                if not story_title and title:
                    story_title = title
                if not paras:
                    break

                joined = "\n\n".join(paras)
                content_hash = hash(joined[:300] + joined[-300:])
                if content_hash in seen_hashes:
                    break
                seen_hashes.add(content_hash)

                parts.append(StoryPart(part_num=current_part, url=target_url, paragraphs=paras))
                current_part += 1

        else:
            # Path Pagination or Single-Page Strategy
            clean_path = re.sub(r"/\d+/?$", "", parsed.path).rstrip("/")
            base_clean = f"{parsed.scheme}://{parsed.netloc}{clean_path}/"
            current_part = 1
            max_parts = 250
            known_total_pages = 0
            has_query_parts_links = False

            while current_part <= max_parts:
                if cancel_event and cancel_event.is_set():
                    notify("Scraping cancelled by user.", current_part, known_total_pages, 0)
                    break

                if current_part == 1:
                    target_url = url
                else:
                    if has_query_parts_links:
                        target_url = f"{base_clean}?part={current_part}"
                    else:
                        target_url = f"{base_clean}{current_part}/"

                if target_url in seen_urls:
                    break
                seen_urls.add(target_url)

                pct = (current_part / known_total_pages) if known_total_pages > 0 else 0.0
                status_text = f"Fetching part {current_part} of {known_total_pages}..." if known_total_pages else f"Fetching part {current_part}..."
                notify(status_text, current_part, known_total_pages, pct)

                soup, final_url, status = self.fetch_page(target_url)
                if status != 200 or not soup:
                    if status == 404 and current_part == 1:
                        raise RuntimeError(f"Error 404: Page not found at {target_url}. Please check if the URL was cut off when copying.")
                    break

                # Loopback check to base page
                final_clean = final_url.rstrip("/") + "/"
                if current_part > 1 and final_clean == base_clean:
                    break

                # On page 1, inspect pagination links to see if site is multi-page
                if current_part == 1:
                    page_links = soup.select(".post-page-numbers, .page-numbers, .page-links a, .page-links span, .pagination a")
                    found_nums = []
                    for link in page_links:
                        txt = link.get_text(strip=True)
                        if txt.isdigit():
                            found_nums.append(int(txt))
                        href = link.get("href", "")
                        if "part=" in href:
                            has_query_parts_links = True

                    # Also check for ?part= links in body
                    if not has_query_parts_links:
                        for a in soup.find_all("a", href=True):
                            if "part=2" in a["href"]:
                                has_query_parts_links = True
                                break

                    if found_nums:
                        known_total_pages = max(found_nums)

                    is_known_multipage = "america-focus.com" in domain or found_nums or has_query_parts_links

                title, paras = self.extract_from_soup(soup)
                if not story_title and title:
                    story_title = title
                if not paras:
                    break

                joined = "\n\n".join(paras)
                content_hash = hash(joined[:300] + joined[-300:])
                if content_hash in seen_hashes:
                    break
                seen_hashes.add(content_hash)

                parts.append(StoryPart(part_num=current_part, url=target_url, paragraphs=paras))

                if current_part == 1 and not is_known_multipage:
                    break

                current_part += 1

        if not parts:
            raise RuntimeError("Could not extract any story text from the provided URL. Please check that the URL is complete, reachable, and contains an article.")

        return StoryArticle(
            title=story_title or "Untitled Story",
            original_url=url,
            domain=domain,
            parts=parts
        )
