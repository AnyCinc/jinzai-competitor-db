import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import asyncio
import re


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ja,en;q=0.9",
}


async def google_search(query: str, max_results: int = 10) -> List[Dict]:
    """Google検索結果をスクレイピング"""
    encoded_query = query.replace(" ", "+")
    url = f"https://www.google.com/search?q={encoded_query}&num={max_results}&hl=ja"

    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True, timeout=30) as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
        except Exception as e:
            return [{"error": str(e)}]

    soup = BeautifulSoup(resp.text, "lxml")
    results = []

    # Google検索結果の構造を解析
    for g in soup.select("div.g"):
        title_el = g.select_one("h3")
        link_el = g.select_one("a")
        snippet_el = g.select_one("div.VwiC3b, span.aCOpRe, div[data-sncf]")

        if not title_el or not link_el:
            continue

        href = link_el.get("href", "")
        # /url?q= 形式のURLを正規化
        if href.startswith("/url?q="):
            href = href[7:].split("&")[0]

        if not href.startswith("http"):
            continue

        # Google自身のURLをスキップ
        if "google.com" in href:
            continue

        results.append({
            "title": title_el.get_text(strip=True),
            "url": href,
            "snippet": snippet_el.get_text(strip=True) if snippet_el else None,
        })

        if len(results) >= max_results:
            break

    return results


async def fetch_page_text(url: str) -> Optional[str]:
    """指定URLのページテキストを取得"""
    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True, timeout=30) as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
        except Exception:
            return None

    soup = BeautifulSoup(resp.text, "lxml")

    # script, style, navなど不要タグを削除
    for tag in soup(["script", "style", "nav", "footer", "header", "iframe", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)

    # 空行を圧縮して読みやすく
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    text = "\n".join(lines)

    # 長すぎる場合は先頭5000文字に絞る（AIへの入力コスト削減）
    return text[:5000] if len(text) > 5000 else text


async def fetch_page_meta(url: str) -> Dict:
    """ページのメタ情報（タイトル、description）を取得"""
    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True, timeout=15) as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
        except Exception as e:
            return {"url": url, "error": str(e)}

    soup = BeautifulSoup(resp.text, "lxml")

    title = soup.title.string.strip() if soup.title else ""
    desc_el = soup.find("meta", attrs={"name": "description"})
    description = desc_el["content"].strip() if desc_el and desc_el.get("content") else ""

    return {
        "url": url,
        "title": title,
        "description": description,
    }
