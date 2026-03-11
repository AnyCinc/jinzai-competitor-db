import streamlit as st
import json
import os
import time
from datetime import datetime
from lib.database import init_db, get_db
from lib.models import Company, CompanyLink
from lib.style import inject_custom_css, render_strength_tags, render_weakness_tags
from lib.scraper import web_search, fetch_page_text, fetch_page_meta, find_pdf_links
from lib.auth import check_auth

st.set_page_config(page_title="自動収集 | 競合調査DB", page_icon="🤖", layout="wide")
if not check_auth():
    st.stop()
init_db()
inject_custom_css()

st.markdown('<p class="section-label">Auto Collect</p>', unsafe_allow_html=True)
st.title("自動収集")
st.caption("キーワードで一括検索 → 自動登録 / 既存情報の更新")

# APIキーの有無を確認
has_api_key = False
try:
    key = st.secrets.get("ANTHROPIC_API_KEY", "")
    if key:
        has_api_key = True
except FileNotFoundError:
    pass
if not has_api_key:
    has_api_key = bool(os.getenv("ANTHROPIC_API_KEY"))

if not has_api_key:
    st.info("💡 ANTHROPIC_API_KEY が未設定です。検索・登録は動きますが、AI分析（強み・弱み分析）は使えません。Settings → Secrets で設定できます。")

st.markdown("---")

# ── タブ ─────────────────────────────────────────
tab_search, tab_update, tab_pdf = st.tabs(["🔍 一括検索・自動登録", "🔄 既存情報を更新", "📄 営業資料を収集"])

# ═══════════════════════════════════════════════════
# 一括検索・自動登録
# ═══════════════════════════════════════════════════
with tab_search:
    st.markdown("### 一括検索 → 自動登録")
    st.markdown("キーワードで検索して見つかった会社をDBに自動登録します。")

    # キーワード設定
    PRESET_KEYWORDS = [
        "外国人材紹介 会社",
        "技能実習 監理団体 一覧",
        "特定技能 登録支援機関",
        "外国人 人材派遣 会社",
        "外国人採用 支援 企業",
    ]

    st.markdown('<span style="color:#a5a39d;font-size:0.75em;letter-spacing:0.3em;">プリセットキーワード</span>', unsafe_allow_html=True)

    # プリセットキーワード選択
    selected_keywords = []
    kw_cols = st.columns(3)
    for i, kw in enumerate(PRESET_KEYWORDS):
        with kw_cols[i % 3]:
            if st.checkbox(kw, key=f"preset_{i}"):
                selected_keywords.append(kw)

    # カスタムキーワード
    custom_kw = st.text_input("追加キーワード（カンマ区切り）", placeholder="例: ベトナム人材, フィリピン人材紹介")
    if custom_kw:
        selected_keywords.extend([k.strip() for k in custom_kw.split(",") if k.strip()])

    col_num, col_ai, col_btn = st.columns([1, 1, 2])
    with col_num:
        per_keyword = st.selectbox("各キーワードの検索件数", [3, 5, 10], index=1)
    with col_ai:
        use_ai = st.checkbox("AI分析も実行", value=has_api_key, disabled=not has_api_key)
    with col_btn:
        st.markdown("<div style='padding-top:1.6rem'>", unsafe_allow_html=True)
        start_batch = st.button("🚀 一括検索・登録を開始", type="primary", disabled=not selected_keywords)
        st.markdown("</div>", unsafe_allow_html=True)

    if start_batch and selected_keywords:
        # AI分析の準備
        if use_ai and has_api_key:
            from lib.ai_analyzer import analyze_company_page

        # 既存URLリスト取得（重複防止用）
        with get_db() as db:
            existing_urls = set(
                url for (url,) in db.query(Company.hp_url).filter(Company.hp_url.isnot(None)).all()
            )

        total_added = 0
        total_skipped = 0
        total_searched = 0
        progress_bar = st.progress(0)
        status_text = st.empty()
        results_container = st.container()

        total_keywords = len(selected_keywords)
        for ki, keyword in enumerate(selected_keywords):
            status_text.markdown(f"🔍 **検索中**: {keyword} ({ki+1}/{total_keywords})")

            search_results = web_search(keyword, per_keyword)
            valid_results = [r for r in search_results if r.get("url") and "error" not in r]
            total_searched += len(valid_results)

            if not valid_results:
                with results_container:
                    st.warning(f"「{keyword}」: 検索結果が0件でした")

            for ri, item in enumerate(valid_results):
                progress = (ki * per_keyword + ri + 1) / (total_keywords * per_keyword)
                progress_bar.progress(min(progress, 1.0))

                # 重複チェック
                if item["url"] in existing_urls:
                    total_skipped += 1
                    continue

                company_name = item.get("title", "")
                description = item.get("snippet", "")
                industry = None
                strengths_json = "[]"
                weaknesses_json = "[]"
                ai_summary = None

                # AI分析（オプション）
                if use_ai and has_api_key:
                    status_text.markdown(f"🤖 **AI分析中**: {company_name[:40]}")
                    page_text = fetch_page_text(item["url"])
                    if page_text:
                        try:
                            analysis = analyze_company_page(item["url"], page_text)
                            company_name = analysis.get("company_name") or company_name
                            description = analysis.get("summary") or description
                            industry = ", ".join(analysis.get("service_types", [])) or None
                            strengths_json = json.dumps(analysis.get("strengths", []), ensure_ascii=False)
                            weaknesses_json = json.dumps(analysis.get("weaknesses", []), ensure_ascii=False)
                            ai_summary = analysis.get("summary")
                        except Exception as e:
                            pass  # AI分析失敗でも登録は続行
                else:
                    # AI分析なしの場合、ページメタ情報を取得
                    status_text.markdown(f"📝 **情報取得中**: {company_name[:40]}")
                    meta = fetch_page_meta(item["url"])
                    if meta and not meta.get("error"):
                        if meta.get("title"):
                            company_name = meta["title"]
                        if meta.get("description"):
                            description = meta["description"]

                # DB登録
                with get_db() as db:
                    new_company = Company(
                        name=company_name,
                        hp_url=item["url"],
                        description=description,
                        industry_detail=industry,
                        strengths=strengths_json,
                        weaknesses=weaknesses_json,
                        ai_summary=ai_summary,
                    )
                    db.add(new_company)
                    db.commit()

                existing_urls.add(item["url"])
                total_added += 1

                with results_container:
                    ai_badge = " 🤖" if ai_summary else ""
                    st.markdown(f"""
                    <div class="company-card">
                        <h4>✅ {company_name}{ai_badge}</h4>
                        <div class="meta">{item['url']}</div>
                        <div class="desc">{(description or '')[:100]}</div>
                    </div>
                    """, unsafe_allow_html=True)

                time.sleep(0.5)

        progress_bar.progress(1.0)
        status_text.empty()
        st.success(f"完了！ 検索{total_searched}件中 → {total_added}社を新規登録、{total_skipped}件をスキップ（重複）しました。")

# ═══════════════════════════════════════════════════
# 既存情報を更新
# ═══════════════════════════════════════════════════
with tab_update:
    st.markdown("### 既存会社のHP情報を再スキャン")
    st.markdown("登録済み会社のHPを再度チェックして情報を更新します。")

    if not has_api_key:
        st.warning("AI分析にはAPIキーが必要です。APIキーなしでもページ情報の基本更新は可能です。")

    with get_db() as db:
        companies = db.query(Company).filter(Company.hp_url.isnot(None)).order_by(Company.name).all()
        company_list = [(c.id, c.name, c.hp_url, c.ai_summary, c.updated_at) for c in companies]

    if not company_list:
        st.info("HP URLが登録されている会社がありません。先に「一括検索」で会社を登録してください。")
    else:
        st.markdown(f"対象: **{len(company_list)}社** (HP URL登録済み)")

        col_mode, col_go = st.columns([2, 1])
        with col_mode:
            if has_api_key:
                update_mode = st.radio(
                    "更新対象",
                    ["全社更新", "AI未分析の会社だけ"],
                    horizontal=True,
                )
            else:
                update_mode = "全社更新"
                st.caption("APIキー未設定のため、ページ基本情報の更新のみ")
        with col_go:
            st.markdown("<div style='padding-top:1.6rem'>", unsafe_allow_html=True)
            start_update = st.button("🔄 更新を開始", type="primary")
            st.markdown("</div>", unsafe_allow_html=True)

        if start_update:
            if has_api_key:
                from lib.ai_analyzer import analyze_company_page

            if update_mode == "AI未分析の会社だけ":
                targets = [(cid, name, url) for cid, name, url, summary, _ in company_list if not summary]
            else:
                targets = [(cid, name, url) for cid, name, url, _, _ in company_list]

            if not targets:
                st.info("更新対象の会社がありません。")
            else:
                progress_bar = st.progress(0)
                status_text = st.empty()
                updated = 0
                failed = 0

                for i, (cid, name, url) in enumerate(targets):
                    progress_bar.progress((i + 1) / len(targets))
                    status_text.markdown(f"🔄 **更新中**: {name} ({i+1}/{len(targets)})")

                    page_text = fetch_page_text(url)
                    if not page_text:
                        failed += 1
                        continue

                    with get_db() as db:
                        c = db.query(Company).filter(Company.id == cid).first()
                        if not c:
                            continue

                        if has_api_key:
                            try:
                                result = analyze_company_page(url, page_text)
                                c.strengths = json.dumps(result.get("strengths", []), ensure_ascii=False)
                                c.weaknesses = json.dumps(result.get("weaknesses", []), ensure_ascii=False)
                                c.ai_summary = result.get("summary", "")
                                if result.get("service_types"):
                                    c.industry_detail = ", ".join(result["service_types"])
                            except Exception:
                                failed += 1
                                continue
                        else:
                            # APIキーなし: ページテキストから基本情報だけ更新
                            if not c.description:
                                c.description = page_text[:300]

                        c.updated_at = datetime.utcnow()
                        db.commit()

                    updated += 1
                    time.sleep(0.5)

                progress_bar.progress(1.0)
                status_text.empty()
                st.success(f"完了！ {updated}社を更新、{failed}社が失敗しました。")

# ═══════════════════════════════════════════════════
# 営業資料PDF収集
# ═══════════════════════════════════════════════════
with tab_pdf:
    st.markdown("### 営業資料・PDFリンクを自動収集")
    st.markdown("登録済み会社のHPからPDFリンクや資料ページを探して、リンクとしてDBに保存します。")

    with get_db() as db:
        companies = db.query(Company).filter(Company.hp_url.isnot(None)).order_by(Company.name).all()
        company_list_pdf = [(c.id, c.name, c.hp_url) for c in companies]

    if not company_list_pdf:
        st.info("HP URLが登録されている会社がありません。先に「一括検索」で会社を登録してください。")
    else:
        st.markdown(f"対象: **{len(company_list_pdf)}社**")

        start_pdf = st.button("📄 PDF・資料リンクを収集", type="primary")

        if start_pdf:
            progress_bar = st.progress(0)
            status_text = st.empty()
            total_found = 0

            for i, (cid, name, url) in enumerate(company_list_pdf):
                progress_bar.progress((i + 1) / len(company_list_pdf))
                status_text.markdown(f"📄 **スキャン中**: {name} ({i+1}/{len(company_list_pdf)})")

                pdf_links = find_pdf_links(url)

                if pdf_links:
                    with get_db() as db:
                        existing_link_urls = set(
                            u for (u,) in db.query(CompanyLink.url).filter(CompanyLink.company_id == cid).all()
                        )

                        for pl in pdf_links:
                            if pl["url"] not in existing_link_urls:
                                new_link = CompanyLink(
                                    company_id=cid,
                                    url=pl["url"],
                                    title=pl["title"],
                                    link_type="material",
                                    description="自動収集されたPDF/資料リンク",
                                )
                                db.add(new_link)
                                total_found += 1
                        db.commit()

                    st.markdown(f"""
                    <div class="company-card">
                        <h4>📄 {name}: {len(pdf_links)}件の資料リンクを発見</h4>
                        <div class="meta">{', '.join(pl['title'][:30] for pl in pdf_links[:3])}{'...' if len(pdf_links) > 3 else ''}</div>
                    </div>
                    """, unsafe_allow_html=True)

                time.sleep(0.5)

            progress_bar.progress(1.0)
            status_text.empty()
            st.success(f"完了！ 合計 {total_found}件の資料リンクを新規登録しました。")
