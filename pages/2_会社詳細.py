import streamlit as st
import json
import os
import uuid
from datetime import datetime
from lib.database import init_db, get_db
from lib.models import Company, CompanyFile, CompanyLink
from lib.style import inject_custom_css, render_strength_tags, render_weakness_tags, render_industry_badge
from lib.ai_analyzer import analyze_company_page
from lib.scraper import fetch_page_text
from lib.auth import check_auth

st.set_page_config(page_title="会社詳細 | 競合調査DB", page_icon="🔍", layout="wide")
if not check_auth():
    st.stop()
init_db()
inject_custom_css()

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./data/uploads")

# ── 会社選択 ─────────────────────────────────────
with get_db() as db:
    companies = db.query(Company).order_by(Company.name).all()

if not companies:
    st.info("まだ会社が登録されていません。「会社一覧」ページから追加してください。")
    st.stop()

# セッションから選択IDを取得
pre_selected_id = st.session_state.get("selected_company_id", None)

company_names = {c.id: c.name for c in companies}
company_ids = list(company_names.keys())

if pre_selected_id and pre_selected_id in company_ids:
    default_index = company_ids.index(pre_selected_id)
else:
    default_index = 0

selected_id = st.selectbox(
    "会社を選択",
    company_ids,
    index=default_index,
    format_func=lambda x: company_names[x],
)

# 選択をセッションに保存
st.session_state["selected_company_id"] = selected_id

st.markdown("---")

# ── 会社データ取得 ───────────────────────────────
with get_db() as db:
    company = db.query(Company).filter(Company.id == selected_id).first()
    if not company:
        st.error("会社が見つかりません")
        st.stop()

    # リレーションデータを事前に読み込み（セッション外で使うため）
    strengths = json.loads(company.strengths) if company.strengths else []
    weaknesses = json.loads(company.weaknesses) if company.weaknesses else []
    links = [(l.id, l.url, l.title, l.link_type, l.description) for l in company.links]
    files = [(f.id, f.original_name, f.file_type, f.size, f.file_path) for f in company.files]

    # 基本情報を保存
    company_data = {
        "id": company.id,
        "name": company.name,
        "hp_url": company.hp_url,
        "industry_detail": company.industry_detail,
        "description": company.description,
        "notes": company.notes,
        "ai_summary": company.ai_summary,
    }

# ── ヘッダー ─────────────────────────────────────
st.markdown('<p class="section-label">Company Detail</p>', unsafe_allow_html=True)

col_title, col_actions = st.columns([4, 2])
with col_title:
    if company_data["industry_detail"]:
        render_industry_badge(company_data["industry_detail"])
    st.title(company_data["name"])
    if company_data["hp_url"]:
        st.markdown(f'<a href="{company_data["hp_url"]}" target="_blank" style="color:#a5a39d;font-size:0.85em;">🔗 {company_data["hp_url"]}</a>', unsafe_allow_html=True)

with col_actions:
    st.markdown("<div style='padding-top:1.5rem'>", unsafe_allow_html=True)

    # AI分析ボタン
    if st.button("🤖 AI分析を実行", type="primary", disabled=not company_data["hp_url"]):
        if not company_data["hp_url"]:
            st.error("HP URLを先に登録してください")
        else:
            with st.spinner("HPを取得中..."):
                page_text = fetch_page_text(company_data["hp_url"])
            if not page_text:
                st.error("ページを取得できませんでした")
            else:
                with st.spinner("AI分析中... (Claude API)"):
                    try:
                        result = analyze_company_page(company_data["hp_url"], page_text)
                        with get_db() as db:
                            c = db.query(Company).filter(Company.id == selected_id).first()
                            c.strengths = json.dumps(result.get("strengths", []), ensure_ascii=False)
                            c.weaknesses = json.dumps(result.get("weaknesses", []), ensure_ascii=False)
                            c.ai_summary = result.get("summary", "")
                            c.updated_at = datetime.utcnow()
                            db.commit()
                        st.success("AI分析が完了しました！")
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))
                    except Exception as e:
                        st.error(f"AI分析エラー: {str(e)}")

    st.markdown("</div>", unsafe_allow_html=True)

# ── 概要・メモ ───────────────────────────────────
if company_data["description"]:
    st.markdown(f'<p style="color:#6b6a65;font-size:0.9em;line-height:1.7;">{company_data["description"]}</p>', unsafe_allow_html=True)

if company_data["notes"]:
    st.markdown(f'<p style="color:#a5a39d;font-size:0.85em;border-top:1px solid #ececea;padding-top:8px;">{company_data["notes"]}</p>', unsafe_allow_html=True)

# ── AI分析サマリー ───────────────────────────────
if company_data["ai_summary"]:
    st.markdown(f"""
    <div class="ai-summary-box">
        <div class="label">✨ AI Analysis Summary</div>
        <p>{company_data["ai_summary"]}</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ── タブ表示 ─────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["💪 強み・弱み", "🔗 リンク", "📁 ファイル", "✏️ 編集"])

# ── 強み・弱み ───────────────────────────────────
with tab1:
    col_s, col_w = st.columns(2)

    with col_s:
        st.markdown("**強み (Strengths)**")
        render_strength_tags(strengths)

        # 強み追加
        new_strength = st.text_input("強みを追加", key="new_strength", placeholder="新しい強み...")
        if st.button("追加", key="add_strength") and new_strength:
            updated = strengths + [new_strength.strip()]
            with get_db() as db:
                c = db.query(Company).filter(Company.id == selected_id).first()
                c.strengths = json.dumps(updated, ensure_ascii=False)
                db.commit()
            st.rerun()

    with col_w:
        st.markdown("**弱み (Weaknesses)**")
        render_weakness_tags(weaknesses)

        # 弱み追加
        new_weakness = st.text_input("弱みを追加", key="new_weakness", placeholder="新しい弱み...")
        if st.button("追加", key="add_weakness") and new_weakness:
            updated = weaknesses + [new_weakness.strip()]
            with get_db() as db:
                c = db.query(Company).filter(Company.id == selected_id).first()
                c.weaknesses = json.dumps(updated, ensure_ascii=False)
                db.commit()
            st.rerun()

# ── リンク ───────────────────────────────────────
with tab2:
    if links:
        for link_id, link_url, link_title, link_type, link_desc in links:
            col_link, col_del = st.columns([5, 1])
            with col_link:
                display_title = link_title or link_url
                type_label = f"[{link_type}] " if link_type else ""
                st.markdown(f"🔗 {type_label}[{display_title}]({link_url})")
                if link_desc:
                    st.caption(link_desc)
            with col_del:
                if st.button("削除", key=f"del_link_{link_id}"):
                    with get_db() as db:
                        target = db.query(CompanyLink).filter(CompanyLink.id == link_id).first()
                        if target:
                            db.delete(target)
                            db.commit()
                    st.rerun()
    else:
        st.caption("リンクはまだ登録されていません")

    st.markdown("---")
    st.markdown("**リンクを追加**")
    with st.form("add_link", clear_on_submit=True):
        lc1, lc2 = st.columns(2)
        with lc1:
            link_url = st.text_input("URL *", placeholder="https://...")
        with lc2:
            link_title = st.text_input("タイトル", placeholder="リンクのタイトル")
        lc3, lc4 = st.columns(2)
        with lc3:
            link_type = st.selectbox("種別", ["hp", "youtube", "sns", "material", "other"])
        with lc4:
            link_desc = st.text_input("説明", placeholder="リンクの説明")
        if st.form_submit_button("リンクを追加"):
            if link_url and link_url.strip():
                with get_db() as db:
                    new_link = CompanyLink(
                        company_id=selected_id,
                        url=link_url.strip(),
                        title=link_title.strip() if link_title else None,
                        link_type=link_type,
                        description=link_desc.strip() if link_desc else None,
                    )
                    db.add(new_link)
                    db.commit()
                st.rerun()
            else:
                st.error("URLは必須です")

# ── ファイル ─────────────────────────────────────
with tab3:
    if files:
        for file_id, orig_name, file_type, file_size, file_path in files:
            col_file, col_fdel = st.columns([5, 1])
            with col_file:
                size_str = f"{file_size / 1024:.0f} KB" if file_size and file_size < 1024 * 1024 else f"{(file_size or 0) / (1024 * 1024):.1f} MB"
                type_emoji = {"pdf": "📄", "video": "🎥", "image": "🖼️"}.get(file_type, "📎")
                st.markdown(f"{type_emoji} **{orig_name}** ({size_str})")
            with col_fdel:
                if st.button("削除", key=f"del_file_{file_id}"):
                    with get_db() as db:
                        target = db.query(CompanyFile).filter(CompanyFile.id == file_id).first()
                        if target:
                            if os.path.exists(target.file_path):
                                os.remove(target.file_path)
                            db.delete(target)
                            db.commit()
                    st.rerun()
    else:
        st.caption("ファイルはまだアップロードされていません")

    st.markdown("---")
    uploaded = st.file_uploader(
        "ファイルをアップロード",
        type=["pdf", "mp4", "mov", "avi", "webm", "jpg", "jpeg", "png", "gif", "webp"],
        help="PDF、動画、画像ファイルに対応しています",
    )
    if uploaded:
        ext = os.path.splitext(uploaded.name)[1]
        saved_name = f"{uuid.uuid4()}{ext}"
        company_dir = os.path.join(UPLOAD_DIR, str(selected_id))
        os.makedirs(company_dir, exist_ok=True)
        file_path = os.path.join(company_dir, saved_name)

        with open(file_path, "wb") as f:
            f.write(uploaded.getvalue())

        content_type = uploaded.type or ""
        type_map = {
            "application/pdf": "pdf",
            "video/": "video",
            "image/": "image",
        }
        file_type = "other"
        for prefix, ft in type_map.items():
            if content_type.startswith(prefix):
                file_type = ft
                break

        with get_db() as db:
            new_file = CompanyFile(
                company_id=selected_id,
                filename=saved_name,
                original_name=uploaded.name,
                file_type=file_type,
                file_path=file_path,
                size=uploaded.size,
            )
            db.add(new_file)
            db.commit()

        st.success(f"「{uploaded.name}」をアップロードしました")
        st.rerun()

# ── 編集 ─────────────────────────────────────────
with tab4:
    with st.form("edit_company"):
        edit_name = st.text_input("会社名", value=company_data["name"])
        ec1, ec2 = st.columns(2)
        with ec1:
            edit_url = st.text_input("HP URL", value=company_data["hp_url"] or "")
        with ec2:
            industry_options = ["", "技能実習", "特定技能", "高度人材", "技能実習・特定技能", "総合人材紹介", "その他"]
            current_industry = company_data["industry_detail"] or ""
            edit_industry = st.selectbox(
                "事業種別",
                industry_options,
                index=industry_options.index(current_industry) if current_industry in industry_options else 0,
                format_func=lambda x: "— 選択 —" if x == "" else x,
            )
        edit_desc = st.text_area("概要", value=company_data["description"] or "", height=100)
        edit_notes = st.text_area("メモ", value=company_data["notes"] or "", height=80)

        if st.form_submit_button("保存", type="primary"):
            with get_db() as db:
                c = db.query(Company).filter(Company.id == selected_id).first()
                c.name = edit_name.strip()
                c.hp_url = edit_url.strip() if edit_url else None
                c.industry_detail = edit_industry if edit_industry else None
                c.description = edit_desc.strip() if edit_desc else None
                c.notes = edit_notes.strip() if edit_notes else None
                c.updated_at = datetime.utcnow()
                db.commit()
            st.success("保存しました！")
            st.rerun()
