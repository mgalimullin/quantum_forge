import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from urllib.parse import urljoin, urlparse, unquote, quote
import os

BASE_URL = "https://fallout.fandom.com"

visited = set()
article_count = 0


def extract_article_links(content: BeautifulSoup) -> list[str]:
    links = []

    for a in content.find_all("a", href=True):
        href = a["href"]
        if is_valid_article_link(href):
            links.append(href)

    return links


def filename_to_md_href(filename: str) -> str:
    """
    Fallout TV series.md -> Fallout%20TV%20series.md
    """
    return quote(filename)


def wiki_href_to_filename(href: str) -> str:
    """
    /wiki/Fallout_(TV_series) -> Fallout TV series.md
    """
    title = href.replace("/wiki/", "")
    title = unquote(title)          # %20 и т.п.
    title = title.replace("_", " ")
    title = title.replace("(", "")
    title = title.replace(")", "")

    safe_title = "".join(
        c for c in title if c.isalnum() or c in " _-"
    ).strip()

    return f"{safe_title}.md"


def save_markdown_from_href(href: str, title: str, markdown: str):
    filename = wiki_href_to_filename(href)

    os.makedirs("articles", exist_ok=True)
    path = os.path.join("articles", filename)

    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")
        f.write(markdown)

    print(f"✔ Сохранено: {path}")


def rewrite_internal_links(content: BeautifulSoup):
    for a in content.find_all("a", href=True):
        href = a["href"]

        if not is_valid_article_link(href):
            continue

        filename = wiki_href_to_filename(href)
        a["href"] = filename_to_md_href(filename)


def is_valid_article_link(href: str) -> bool:
    if not href:
        return False

    if not href.startswith("/wiki/"):
        return False

    banned_prefixes = (
        "/wiki/File:",
        "/wiki/Category:",
        "/wiki/Special:",
        "/wiki/Help:",
        "/wiki/Talk:",
        "/wiki/User:",
        "/wiki/Template:",
    )

    if href.startswith(banned_prefixes):
        return False

    if "#" in href:
        return False

    return True


def get_article_title(soup: BeautifulSoup) -> str:
    h1 = soup.find("h1")
    return h1.get_text(strip=True) if h1 else "article"


def clean_article_body(content: BeautifulSoup):
    # Удаляем всё, что не является текстом статьи
    for tag in content.find_all([
        "aside", "figure", "img", "table", "sup", "span",
        "nav", "style", "script"
    ]):
        tag.decompose()

    # Убираем подписи к изображениям (на всякий случай)
    for caption in content.select(".caption, .thumbcaption"):
        caption.decompose()


def save_markdown(title: str, markdown: str):
    safe_title = "".join(c for c in title if c.isalnum() or c in " _-").rstrip()
    filename = f"{safe_title}.md"
    folder_name = "knowledge_base"

    os.makedirs(folder_name, exist_ok=True)
    path = os.path.join(folder_name, filename)

    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")
        f.write(markdown)

    print(f"✔ Сохранено: {path}")


def download_article(url: str, depth: int, max_depth: int, max_articles: int):
    global article_count

    if article_count >= max_articles:
        return

    if depth > max_depth:
        return

    if url in visited:
        return

    print(f"→ [{depth}] {url}")
    visited.add(url)
    article_count += 1

    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    content = soup.find("div", class_="mw-parser-output")
    if not content:
        return

    title = get_article_title(soup)

    clean_article_body(content)

    # 1. СНАЧАЛА собираем ссылки для DFS
    article_links = extract_article_links(content)

    # 2. ПОТОМ переписываем их для Markdown
    rewrite_internal_links(content)

    # 3. Сохраняем Markdown
    markdown = md(str(content), heading_style="ATX")
    save_markdown_from_href(
        href=urlparse(url).path,
        title=title,
        markdown=markdown
    )

    # 4. DFS — в глубину
    for href in article_links:
        if article_count >= max_articles:
            break

        next_url = urljoin(BASE_URL, href)
        download_article(
            next_url,
            depth + 1,
            max_depth,
            max_articles
        )


if __name__ == "__main__":
    START_URL = "https://fallout.fandom.com/wiki/Lucy_MacLean"

    MAX_DEPTH = 1        # глубина рекурсии
    MAX_ARTICLES = 30    # лимит статей

    download_article(
        START_URL,
        depth=0,
        max_depth=MAX_DEPTH,
        max_articles=MAX_ARTICLES
    )

    print("\nГотово.")
