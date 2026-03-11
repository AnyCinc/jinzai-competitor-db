import streamlit as st
import json
from datetime import datetime
from lib.database import init_db, get_db
from lib.models import Company, SearchLog
from lib.style import inject_custom_css, render_strength_tags, render_weakness_tags
from lib.scraper import web_search, fetch_page_text
from lib.ai_analyzer import analyze_company_page
from lib.auth import check_auth

st.set_page_config(page_title="Web検索 | 競合調査DB", page_icon="🌐", layout="wide")
if not check_auth():
    st.stop()
init_db()
inject_custom_css()

st.markdown('<p class="section-label">Discovery</p>', unsafe_allow_html=True)
st.title("Auto Web Search")
st.caption("キーワードで競合他社を自動検索・AI分析してDBに登録")

st.markdown("---")

# ── 検索フォーム ─────────────────────────────────
KEYWORDS = ["外国人材紹介", "技能実習 監理団体", "特定技能 支援機関", "外国人 採用 人材会社"]

# クイックキーワード
st.markdown('<span style="color:#a5a39d;font-size:0.8em;letter-spacing:0.3em;">QUICK KEYWORDS</span>', unsafe_allow_html=True)
kw_cols = st.columns(len(KEYWORDS))
for i, kw in enumerate(KEYWORDS):
    with kw_cols[i]:
        if st.button(kw, key=f"kw_{i}", use_container_width=True):
            st.session_state["search_query"] = kw

col_search, col_num, col_btn = st.columns([4, 1, 1])
with col_search:
    query = st.text_input(
        "検索キーワード",
        value=st.session_state.get("search_query", "外国人材紹介"),
        placeholder="検索キーワードを入力...",
        label_visibility="collapsed",
    )
with col_num:
    max_results = st.selectbox("件数", [5, 10, 20], index=1, label_visibility="collapsed")
with col_btn:
    search_clicked = st.button("🔍 検索", type="primary", use_container_width=True)

st.markdown("---")

# ── 検索実行 ─────────────────────────────────────
if search_clicked and query:
    with st.spinner("検索中..."):
        results = web_search(query, max_results)

    # エラーチェック
    if results and "error" in results[0]:
        st.error(f"検索エラー: {results[0]['error']}")
    else:
        # 検索ログ保存
        with get_db() as db:
            log = SearchLog(
                query=query,
                results_json=json.dumps(results, ensure_ascii=False),
            )
            db.add(log)
            db.commit()

        st.session_state["search_results"] = results
        st.session_state["search_analyses"] = {}
        st.session_state["search_saved"] = set()

# ── 検索結果表示 ─────────────────────────────────
results = st.session_state.get("search_results", [])
analyses = st.session_state.get("search_analyses", {})
saved_set = st.session_state.get("search_saved", set())

if results:
    st.markdown(f'<p class="section-label">{len(results)} RESULTS</p>', unsafe_allow_html=True)
    st.markdown("")

    for i, item in enumerate(results):
        if not item.get("url"):
            continue

        st.markdown(f"""
        <div class="search-result">
            <h4><a href="{item['url']}" target="_blank" style="color:#1c1c1a;text-decoration:none;">{item.get('title', 'No Title')} ↗</a></h4>
            <div class="url">{item['url']}</div>
            {f'<div class="snippet">{item["snippet"]}</div>' if item.get("snippet") else ""}
        </div>
        """, unsafe_allow_html=True)

        col_ai, col_save, col_space = st.columns([1, 1, 3])

        with col_ai:
            if i not in analyses:
                if st.button("🤖 AI分析", key=f"analyze_{i}"):
                    with st.spinner("ページを取得中..."):
                        page_text = fetch_page_text(item["url"])
                    if not page_text:
                        st.error("ページを取得できませんでした")
                    else:
                        with st.spinner("AI分析中..."):
                            try:
                                analysis = analyze_company_page(item["url"], page_text)
                                st.session_state["search_analyses"][i] = analysis
                                st.rerun()
                            except ValueError as e:
                                st.error(str(e))
                            except Exception as e:
                                st.error(f"分析エラー: {str(e)}")

        with col_save:
            if i in saved_set:
                st.markdown("✅ 保存済み")
            else:
                if st.button("💾 DBに保存", key=f"save_{i}"):
                    analysis = analyses.get(i, {})
                    with get_db() as db:
                        new_company = Company(
                            name=analysis.get("company_name") or item.get("title", ""),
                            hp_url=item["url"],
                            description=analysis.get("summary") or item.get("snippet"),
                            strengths=json.dumps(analysis.get("strengths", []), ensure_ascii=False),
                            weaknesses=json.dumps(analysis.get("weaknesses", []), ensure_ascii=False),
                            ai_summary=analysis.get("summary"),
                        )
                        db.add(new_company)
                        db.commit()
                    st.session_state["search_saved"].add(i)
                    st.success("保存しました！")
                    st.rerun()

        # AI分析結果表示
        if i in analyses:
            analysis = analyses[i]
            with st.container():
                st.markdown(f"""
                <div class="ai-summary-box">
                    <div class="label">✨ AI ANALYSIS {f'— {analysis.get("company_name", "")}' if analysis.get("company_name") else ""}</div>
                    <p>{analysis.get('summary', '')}</p>
                </div>
                """, unsafe_allow_html=True)

                col_s, col_w = st.columns(2)
                with col_s:
                    st.markdown('<span style="color:#a5a39d;font-size:0.75em;letter-spacing:0.3em;">STRENGTHS</span>', unsafe_allow_html=True)
                    render_strength_tags(analysis.get("strengths", []))
                with col_w:
                    st.markdown('<span style="color:#a5a39d;font-size:0.75em;letter-spacing:0.3em;">WEAKNESSES</span>', unsafe_allow_html=True)
                    render_weakness_tags(analysis.get("weaknesses", []))

        st.markdown("")

elif not search_clicked:
    st.markdown("""
    <div style="text-align:center; padding:4rem; border:1px dashed #e2e0db;">
        <p style="color:#a5a39d; font-size:1.2em;">🔍</p>
        <p style="color:#a5a39d; font-size:0.85em; letter-spacing:0.2em;">
            キーワードを入力して検索を開始
        </p>
    </div>
    """, unsafe_allow_html=True)
