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

# ── 記事・ニュースサイト除外リスト ──
EXCLUDED_DOMAINS = {
    "news.yahoo.co.jp", "yahoo.co.jp", "news.google.com",
    "youtube.com", "youtu.be", "twitter.com", "x.com",
    "facebook.com", "instagram.com", "tiktok.com", "linkedin.com",
    "note.com", "zenn.dev", "qiita.com", "hatena.ne.jp", "hatenablog.com",
    "ameblo.jp", "livedoor.jp", "fc2.com", "seesaa.net",
    "wikipedia.org", "wikiwand.com",
    "amazon.co.jp", "amazon.com", "rakuten.co.jp",
    "nikkei.com", "asahi.com", "mainichi.jp", "yomiuri.co.jp",
    "sankei.com", "nhk.or.jp", "reuters.com", "bloomberg.co.jp",
    "prtimes.jp", "atpress.ne.jp",
    "recruit.co.jp", "indeed.com", "doda.jp", "mynavi.jp",
    "rikunabi.com", "en-japan.com", "careerjet.jp",
    "townwork.net", "baitoru.com",
    "matome.naver.jp",
    "slideshare.net", "speakerdeck.com",
    "google.com", "google.co.jp",
}

# 記事っぽいURLパターン
ARTICLE_URL_PATTERNS = [
    "/article/", "/articles/", "/news/", "/blog/", "/column/",
    "/post/", "/entry/", "/archive/", "/tag/", "/category/",
    "/topics/", "/magazine/", "/media/", "/story/", "/report/",
    "/press/", "/release/", "/interview/",
]


def _is_company_site(url: str, title: str = "", snippet: str = "") -> bool:
    """URLが企業の公式サイトらしいかどうかを判定"""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    domain = parsed.netloc.lower().replace("www.", "")

    # 除外ドメインチェック
    for exc in EXCLUDED_DOMAINS:
        if domain == exc or domain.endswith("." + exc):
            return False

    # 記事っぽいURLパスを除外
    path = parsed.path.lower()
    for pattern in ARTICLE_URL_PATTERNS:
        if pattern in path:
            return False

    # URLにページ番号パターン（/page/2 など）がある場合は除外
    if "/page/" in path:
        return False

    # タイトルに記事っぽいキーワードが含まれる場合は除外
    article_keywords = [
        "ランキング", "まとめ", "比較サイト", "おすすめ", "選び方",
        "口コミ", "評判", "ニュース", "コラム", "ブログ",
        "【最新", "TOP", "選", "徹底比較",
    ]
    title_lower = title.lower()
    for kw in article_keywords:
        if kw.lower() in title_lower:
            return False

    return True


def _filter_company_results(results: List[Dict]) -> List[Dict]:
    """検索結果から企業サイトだけを抽出"""
    return [
        r for r in results
        if r.get("url") and "error" not in r
        and _is_company_site(r["url"], r.get("title", ""), r.get("snippet", ""))
    ]


def extract_company_name(title: str, url: str = "", description: str = "") -> str:
    """ページタイトルやメタ情報から会社名を抽出する

    例:
      "Home ｜ 外国人材紹介・キャリア支援の株式会社WILSONウイルソン公式サイト"
        → "株式会社WILSON"
      "外国人の人材紹介ならかいじ人材株式会社 | 海外の若者と企業の未来を繋ぐ"
        → "かいじ人材株式会社"
      "グローバルパワー｜外国人紹介・派遣 日本語N1/N2 社会人・中途特化"
        → "グローバルパワー"
      "ORIGINATOR CO., LTD. – グローバル人材紹介のオリジネーター"
        → "ORIGINATOR CO., LTD."
    """
    import re

    if not title:
        return ""

    title = title.replace("\u3000", " ").strip()

    corp_types = ["株式会社", "有限会社", "合同会社", "一般社団法人", "一般財団法人", "協同組合"]

    # ── 0. まず区切り文字で分割（/はURL等を壊すので除外） ──
    separators = ['｜', '|', '–', '—', '：', ':']
    parts = [title]
    for sep in separators:
        new_parts = []
        for p in parts:
            new_parts.extend(p.split(sep))
        parts = new_parts
    parts = [p.strip() for p in parts if p.strip()]

    noise_words = [
        "公式サイト", "公式ホームページ", "公式HP", "公式",
        "ホームページ", "オフィシャルサイト", "OFFICIAL SITE",
        "Official Site", "Corporate Site", "Corp Site", "Home", "TOP",
        "トップページ", "トップ",
    ]

    def _clean(text):
        """ノイズ除去"""
        for n in noise_words:
            text = text.replace(n, "")
        return text.strip(" 　・-–—/|｜：:の")

    def _extract_corp_from_text(text):
        """テキストから「〇〇株式会社」or「株式会社〇〇」を短く正確に抽出"""
        for ct in corp_types:
            idx = text.find(ct)
            if idx == -1:
                continue

            # ── 前株: 株式会社〇〇 ──
            after = text[idx + len(ct):]
            # 株式会社の直後の名前部分を取る（公式/サイト等で止める）
            m = re.match(r'([A-Za-zぁ-んァ-ヶー一-龥Ａ-Ｚａ-ｚ０-９\w]+)', after)
            if m:
                name_part = m.group(1)
                name_part = re.split(r'(?:公式|サイト|ホーム|のご|への|です|ます)', name_part)[0]
                if name_part and len(name_part) >= 1:
                    return ct + name_part

            # ── 後株: 〇〇株式会社 ──
            before = text[:idx]
            if before:
                # 助詞や句読点で分割して、最後の部分を会社名として取る
                # 「外国人の人材紹介ならかいじ人材」→「かいじ人材」
                parts_b = re.split(r'[のはをにでがもとならへ、。\s｜|,・]', before)
                parts_b = [p for p in parts_b if p]
                if parts_b:
                    name_part = parts_b[-1]
                    if len(name_part) >= 2:
                        return name_part + ct
                # 区切りが見つからない（短い文字列）ならそのまま
                if len(before) <= 15:
                    name_part = re.sub(r'^[\s・、,]+', '', before)
                    if name_part:
                        return name_part + ct

        return None

    # ── 1. 各パーツから株式会社パターンを探す ──
    for part in parts:
        result = _extract_corp_from_text(part)
        if result:
            return _clean(result)

    # ── 2. descriptionからも探す ──
    if description:
        result = _extract_corp_from_text(description.replace("\u3000", " "))
        if result:
            return _clean(result)

    # ── 3. CO., LTD. / Inc. / Corp. パターン ──
    for part in parts:
        m = re.search(r'([A-Za-z\s]+(?:CO\.?,?\s*LTD\.?|Inc\.?|Corp\.(?!orat)|LLC))', part, re.IGNORECASE)
        if m:
            name = m.group(1).strip()
            # "Corporate Site" 等を含まないようにする
            name = re.sub(r'\s*Corporate\s*Site\s*$', '', name, flags=re.IGNORECASE).strip()
            if name:
                return name

    # ── 4. パーツをクリーニングして最も会社名らしいものを返す ──
    # さらに「外国人材紹介」等の業種ワードも除去
    biz_noise = [
        "外国人材紹介", "人材紹介", "人材派遣", "技能実習",
        "特定技能", "グローバル人材", "外国人紹介", "派遣",
        "登録支援機関", "監理団体", "キャリア支援",
        "日本語N1/N2", "社会人・中途特化",
        "海外の若者と企業の未来を繋ぐ",
    ]

    cleaned_parts = []
    for part in parts:
        cleaned = _clean(part)
        for bn in biz_noise:
            cleaned = cleaned.replace(bn, "")
        cleaned = re.sub(r'^[\s・、,]+', '', cleaned)
        cleaned = re.sub(r'[\s・、,]+$', '', cleaned)
        if cleaned and 2 <= len(cleaned) <= 30:
            cleaned_parts.append(cleaned)

    if cleaned_parts:
        # 短すぎるもの（3文字未満）や数字だけのものを除外
        good = [p for p in cleaned_parts if len(p) >= 3 and not re.match(r'^[A-Z0-9]{1,3}$', p)]
        if not good:
            good = cleaned_parts
        # 短いものが会社名の可能性が高い（ブランド名）
        good.sort(key=len)
        return good[0]

    # ── 5. URLからドメイン名を抽出 ──
    if url:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc.replace("www.", "")
        domain_name = domain.split(".")[0]
        if domain_name and len(domain_name) >= 2:
            return domain_name.upper()

    # 最終手段
    if parts:
        return _clean(parts[0])[:30] or parts[0][:30]
    return title[:30]


# ── 非同期版（内部） ──────────────────────────────────

async def _duckduckgo_search(query: str, max_results: int = 10) -> List[Dict]:
    """DuckDuckGo HTML検索（クラウドサーバーからでも使える）"""
    from urllib.parse import quote_plus, urljoin
    encoded_query = quote_plus(query)
    url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True, timeout=30) as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
        except Exception as e:
            return [{"error": str(e)}]

    soup = BeautifulSoup(resp.text, "lxml")
    results = []

    for item in soup.select(".result"):
        title_el = item.select_one(".result__title a, .result__a")
        snippet_el = item.select_one(".result__snippet")

        if not title_el:
            continue

        href = title_el.get("href", "")
        # DuckDuckGoのリダイレクトURLを処理
        if "duckduckgo.com" in href and "uddg=" in href:
            from urllib.parse import parse_qs, urlparse
            parsed = urlparse(href)
            params = parse_qs(parsed.query)
            if "uddg" in params:
                href = params["uddg"][0]

        if not href.startswith("http"):
            continue

        if "duckduckgo.com" in href:
            continue

        results.append({
            "title": title_el.get_text(strip=True),
            "url": href,
            "snippet": snippet_el.get_text(strip=True) if snippet_el else None,
        })

        if len(results) >= max_results:
            break

    return results


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


async def _web_search(query: str, max_results: int = 10, filter_companies: bool = True) -> List[Dict]:
    """Google → DuckDuckGo のフォールバック検索（企業サイトフィルタリング付き）"""
    # 多めに取得してフィルター後に必要数を確保
    fetch_count = max_results * 3 if filter_companies else max_results

    results = await _google_search(query, fetch_count)
    valid = [r for r in results if "error" not in r and r.get("url")]
    if not valid:
        # Googleがブロックされた場合、DuckDuckGoにフォールバック
        results = await _duckduckgo_search(query, fetch_count)
        valid = [r for r in results if "error" not in r and r.get("url")]

    if filter_companies:
        valid = _filter_company_results(valid)

    return valid[:max_results]


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


def web_search(query: str, max_results: int = 10, filter_companies: bool = True) -> List[Dict]:
    """Web検索（Google→DuckDuckGoフォールバック、同期版）"""
    return _run_async(_web_search(query, max_results, filter_companies))


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
