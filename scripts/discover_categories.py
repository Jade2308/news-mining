import json

# Fix imports for the new project structure
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent
src_path = project_root / 'src'
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import re
import unicodedata
from pathlib import Path
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup


SITES = {
    "vnexpress": "https://vnexpress.net",
    "vietnamnet": "https://vietnamnet.vn",
    "tuoitre": "https://tuoitre.vn",
    "baomoi": "https://www.baomoi.com",
}

SITE_NAV_SELECTORS = {
    "vnexpress": "#wrap-main-nav a[href], nav a[href], .main-nav a[href]",
    "vietnamnet": "#main-nav a[href], nav a[href], .mainmenu a[href], .menu a[href]",
    "tuoitre": "nav a[href], .menu-nav a[href], .header__nav a[href], .menu a[href]",
    "baomoi": (
        "a[href$='.epi'], nav a[href], header a[href], .menu a[href], "
        ".main-menu a[href], .bm-menu a[href], [class*='menu'] a[href], "
        "[class*='drawer'] a[href], [class*='mega'] a[href]"
    ),
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

BLACKLIST_KEYWORDS = [
    "video", "podcast", "photo", "anh", "infographic", "multimedia",
    "tag", "rss", "tim-kiem", "search", "dang-nhap", "login",
    "lien-he", "about", "privacy", "dieu-khoan",
]

BLACKLIST_TEXT_KEYWORDS = {
    "moi", "nong", "video", "chu de", "xem them", "tien ich", "trang chu",
    "dang nhap", "lien he", "xem nhieu", "tin moi", "podcast", "photo",
    "english", "e-magazine",
}


def strip_accents(text: str) -> str:
    text = text.replace("đ", "d").replace("Đ", "D")
    text = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in text if unicodedata.category(ch) != "Mn")


def slugify(text: str) -> str:
    text = strip_accents(text).lower().strip()
    text = re.sub(r"[^\w\s-]", " ", text, flags=re.UNICODE)
    text = re.sub(r"\s+", "-", text).strip("-")
    return text


def normalize_url(base_url: str, href: str) -> str:
    full_url = urljoin(base_url, href)
    p = urlparse(full_url)
    p = p._replace(query="", fragment="")
    return urlunparse(p).rstrip("/")


def is_same_domain(base_url: str, url: str) -> bool:
    d1 = urlparse(base_url).netloc.replace("www.", "")
    d2 = urlparse(url).netloc.replace("www.", "")
    return d1 == d2


def looks_like_article_url(url: str) -> bool:
    low = url.lower()
    return bool(
        re.search(r"-\d{6,}(\.html?|\.htm)?$", low)
        or re.search(r"/\d{6,}(\.html?|\.htm)?$", low)
    )


def _path_segments(url: str) -> list[str]:
    return [s for s in urlparse(url).path.split("/") if s]


def _is_top_level_category(site_name: str, url: str) -> bool:
    low = url.lower()
    segments = _path_segments(low)

    if site_name == "vnexpress":
        return len(segments) == 1 and not segments[0].startswith("topic")

    if site_name == "vietnamnet":
        return len(segments) == 1

    if site_name == "tuoitre":
        return len(segments) == 1 and segments[0].endswith(".htm")

    if site_name == "baomoi":
        if len(segments) != 1 or not segments[0].endswith(".epi"):
            return False
        # loại link bài/tag/chủ đề theo id của Baomoi
        if re.search(r"-c\d+\.epi$", low) or re.search(r"-t\d+\.epi$", low):
            return False
        return True

    return False


def is_valid_category_candidate(site_name: str, base_url: str, text: str, url: str) -> bool:
    if not text or len(text) < 2:
        return False
    if not is_same_domain(base_url, url):
        return False

    text_low = " ".join(text.lower().strip().split())
    text_ascii = strip_accents(text_low)
    if any(k in text_ascii for k in BLACKLIST_TEXT_KEYWORDS):
        return False
    if any(ch.isdigit() for ch in text):
        return False
    if len(text.split()) > 4:
        return False

    low = url.lower()
    if any(k in low for k in BLACKLIST_KEYWORDS):
        return False
    if looks_like_article_url(low):
        return False

    if low.rstrip("/") == base_url.rstrip("/"):
        return False

    # loại bớt link không có path meaningful
    if urlparse(low).path.strip("/") == "":
        return False

    if not _is_top_level_category(site_name, low):
        return False

    if site_name == "baomoi":
        # Chỉ giữ chuyên mục tin, bỏ nhóm tiện ích/phụ
        if not low.endswith(".epi"):
            return False
        if any(x in low for x in ["/tien-ich", "top", "trang"]):
            return False

    return True


def fetch_menu_links(site_name: str, base_url: str) -> dict:
    print(f"[{site_name}] Fetching: {base_url}", flush=True)
    r = requests.get(base_url, headers=HEADERS, timeout=20)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    candidates = []
    selector = SITE_NAV_SELECTORS.get(site_name, "nav a[href]")
    for a in soup.select(selector):
        text = " ".join(a.get_text(" ", strip=True).split())
        href = a.get("href", "").strip()
        if not href:
            continue
        url = normalize_url(base_url, href)
        if is_valid_category_candidate(site_name, base_url, text, url):
            candidates.append((text, url))

    # fallback nếu menu selectors không bắt đủ
    if len(candidates) < 6:
        for a in soup.select("a[href]"):
            text = " ".join(a.get_text(" ", strip=True).split())
            href = a.get("href", "").strip()
            if not href:
                continue
            url = normalize_url(base_url, href)
            if is_valid_category_candidate(site_name, base_url, text, url):
                candidates.append((text, url))

    # dedupe theo URL, giữ text đầu tiên
    by_url = {}
    for text, url in candidates:
        if url not in by_url:
            by_url[url] = text

    mapping = {}
    for url, text in by_url.items():
        key = slugify(text)
        if not key:
            continue
        if key not in mapping:
            mapping[key] = url

    print(f"[{site_name}] Found {len(mapping)} categories", flush=True)
    return mapping


def main():
    print("=== Discover categories from news sites ===", flush=True)
    results = {}

    for site_name, base_url in SITES.items():
        try:
            results[site_name] = fetch_menu_links(site_name, base_url)
        except Exception as e:
            print(f"[{site_name}] ERROR: {e}", flush=True)
            results[site_name] = {}

    out_path = Path.cwd() / "discovered_categories.json"
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nSaved to: {out_path}", flush=True)
    print("\nPreview mapping (copy into crawler if needed):", flush=True)
    for site_name, mapping in results.items():
        print(f"\n# {site_name}")
        print("self.category_urls = {")
        for k, v in mapping.items():
            print(f"    '{k}': '{v}',")
        print("}")


if __name__ == "__main__":
    main()
