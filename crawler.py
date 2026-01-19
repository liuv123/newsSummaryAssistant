# src/crawler.py
import re
from urllib.parse import urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup


def fetch_html(url: str, timeout: int = 10) -> str:
    """下载网页 HTML（必须返回字符串，给 BeautifulSoup 解析用）"""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        )
    }
    r = requests.get(url, headers=headers, timeout=timeout)
    r.raise_for_status()
    r.encoding = r.apparent_encoding
    return r.text


def fetch_news(url: str, timeout: int = 10) -> dict:
    """
    输入：网易新闻URL
    输出：{title, content, url}
    """
    html = fetch_html(url, timeout=timeout)
    soup = BeautifulSoup(html, "lxml")

    # 1) 标题：优先 h1，兜底 title
    h1 = soup.find("h1")
    title = h1.get_text(strip=True) if h1 else ""
    if not title and soup.title:
        title = soup.title.get_text(strip=True)
    if not title:
        title = "（未找到标题）"

    # 2) 正文：先找常见正文容器，找不到就 fallback 全局 <p>
    candidate_selectors = [
        "#content",
        "#endText",
        ".post_body",
        ".article-body",
        "article",
    ]

    container = None
    for css in candidate_selectors:
        container = soup.select_one(css)
        if container:
            break
    if container is None:
        container = soup

    # 去掉脚本/样式
    for tag in container.find_all(["script", "style", "noscript"]):
        tag.decompose()

    # 抽取所有 <p>
    lines = []
    for p in container.find_all("p"):
        text = p.get_text(strip=True)
        if not text:
            continue
        if len(text) < 5:
            continue
        lines.append(text)

    content = "\n".join(lines).strip()
    if not content:
        content = "（未提取到正文：可能页面结构变化/异步加载/反爬限制）"

    return {"url": url, "title": title, "content": content}


def _normalize_url(url: str) -> str:
    """去掉 ? 后面的参数，防止同一篇文章不同参数导致重复"""
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def fetch_home_hot_links(limit: int = 10, timeout: int = 10) -> list[dict]:
    """
    爬取网易主页，提取前 limit 条热点新闻（dy/article/*.html）
    返回格式： [{"url": "...html", "text": "标题文本"}, ...]
    """
    home_url = "https://www.163.com"
    html = fetch_html(home_url, timeout=timeout)
    soup = BeautifulSoup(html, "lxml")

    # 只抓这种格式：https://www.163.com/dy/article/XXXX.html
    pattern = re.compile(r"^https?://(?:www\.)?163\.com/dy/article/.*\.html", re.I)

    results = []
    seen = set()

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href:
            continue

        if not pattern.match(href):
            continue

        url = _normalize_url(href)
        if url in seen:
            continue

        text = a.get_text(strip=True)
        if not text:
            continue

        seen.add(url)
        results.append({"url": url, "text": text})

        if len(results) >= limit:
            break

    return results
