import asyncio
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Optional


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ja,en;q=0.9",
}


# ── 非同期版（内部） ──────────────────────────────────

async def _google_search(query: str, max_results: int = 10) -> List[Dict]:
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

    for g in soup.select("div.g"):
        title_el = g.select_one("h3")
        link_el = g.select_one("a")
        snippet_el = g.select_one("div.VwiC3b, span.aCOpRe, div[data-sncf]")

        if not title_el or not link_el:
            continue

        href = link_el.get("href", "")
        if href.startswith("/url?q="):
            href = href[7:].split("&")[0]

        if not href.startswith("http"):
            continue

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


async def _fetch_page_text(url: str) -> Optional[str]:
    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True, timeout=30) as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
        except Exception:
            return None

    soup = BeautifulSoup(resp.text, "lxml")

    for tag in soup(["script", "style", "nav", "footer", "header", "iframe", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    text = "\n".join(lines)

    return text[:5000] if len(text) > 5000 else text


async def _fetch_page_meta(url: str) -> Dict:
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


# ── 同期ラッパー（Streamlit から呼び出し用） ─────────

def _run_async(coro):
    """非同期コルーチンを同期で実行"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


def google_search(query: str, max_results: int = 10) -> List[Dict]:
    """Google検索結果をスクレイピング（同期版）"""
    return _run_async(_google_search(query, max_results))


def fetch_page_text(url: str) -> Optional[str]:
    """指定URLのページテキストを取得（同期版）"""
    return _run_async(_fetch_page_text(url))


def fetch_page_meta(url: str) -> Dict:
    """ページのメタ情報を取得（同期版）"""
    return _run_async(_fetch_page_meta(url))


# ── PDFリンク収集 ──────────────────────────────

async def _find_pdf_links(url: str) -> List[Dict]:
    """ページ内のPDFリンクを収集"""
    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True, timeout=30) as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
        except Exception:
            return []

    soup = BeautifulSoup(resp.text, "lxml")
    pdf_links = []
    seen = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]

        # 相対URLを絶対URLに変換
        if href.startswith("/"):
            from urllib.parse import urljoin
            href = urljoin(url, href)

        if not href.startswith("http"):
            continue

        # PDF判定（URL末尾 or リンクテキストに「資料」「PDF」を含む）
        link_text = a.get_text(strip=True)
        is_pdf = (
            href.lower().endswith(".pdf")
            or "pdf" in href.lower()
            or any(kw in link_text for kw in ["資料", "PDF", "パンフ", "ダウンロード", "会社案内"])
        )

        if is_pdf and href not in seen:
            seen.add(href)
            pdf_links.append({
                "url": href,
                "title": link_text or href.split("/")[-1],
                "type": "material",
            })

    return pdf_links


def find_pdf_links(url: str) -> List[Dict]:
    """ページ内のPDFリンクを収集（同期版）"""
    return _run_async(_find_pdf_links(url))
