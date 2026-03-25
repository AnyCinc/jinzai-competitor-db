import streamlit as st
import json
import os
import uuid
from datetime import datetime
from lib.database import init_db, get_db
from lib.models import Company, CompanyFile, CompanyLink
from lib.style import inject_custom_css, render_strength_tags, render_weakness_tags
from lib.auth import check_auth

st.set_page_config(page_title="会社管理 | 競合調査DB", page_icon="📋", layout="wide")
if not check_auth():
    st.stop()
init_db()
inject_custom_css()

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./data/uploads")

st.markdown('<p class="section-label">Company Management</p>', unsafe_allow_html=True)
st.title("会社管理")
st.caption("会社の追加・編集・AI分析をまとめて管理")

st.markdown("---")

# ═══════════════════════════════════════════════════
# 新規追加フォーム
# ═══════════════════════════════════════════════════
with st.expander("➕ 新しい会社を追加", expanded=False):
    with st.form("add_company", clear_on_submit=True):
        ac1, ac2 = st.columns(2)
        with ac1:
            new_name = st.text_input("会社名 *", placeholder="例: 株式会社ABC")
        with ac2:
            new_url = st.text_input("会社HP URL", placeholder="https://example.com")
        ac3, ac4 = st.columns(2)
        with ac3:
            new_material = st.text_input("営業資料URL", placeholder="https://... (PDF等)")
        with ac4:
            new_video = st.text_input("動画URL", placeholder="https://youtube.com/...")

        if st.form_submit_button("登録", type="primary", use_container_width=True):
            if not new_name or not new_name.strip():
                st.error("会社名は必須です")
            else:
                with get_db() as db:
                    company = Company(
                        name=new_name.strip(),
                        hp_url=new_url.strip() if new_url else None,
                    )
                    db.add(company)
                    db.flush()

                    if new_material and new_material.strip():
                        db.add(CompanyLink(
                            company_id=company.id,
                            url=new_material.strip(),
                            title="営業資料",
                            link_type="material",
                        ))
                    if new_video and new_video.strip():
                        db.add(CompanyLink(
                            company_id=company.id,
                            url=new_video.strip(),
                            title="動画",
                            link_type="youtube",
                        ))
                    db.commit()
                st.success(f"「{new_name.strip()}」を登録しました！")
                st.rerun()

# ═══════════════════════════════════════════════════
# 会社名一括修正
# ═══════════════════════════════════════════════════
with st.expander("🔄 会社名を一括修正（ページタイトル → 正しい会社名）", expanded=False):
    st.caption("ページタイトルがそのまま会社名になっている場合、自動で正しい会社名に変換します。")
    if st.button("プレビュー（変更前 → 変更後を確認）", key="preview_rename"):
        from lib.scraper import extract_company_name
        with get_db() as db:
            all_companies = db.query(Company).order_by(Company.name).all()
            rename_list = []
            for c in all_companies:
                new_name = extract_company_name(c.name, c.hp_url or "", c.description or "")
                if new_name and new_name != c.name and len(new_name) < len(c.name):
                    rename_list.append((c.id, c.name, new_name))

        if rename_list:
            st.session_state["rename_list"] = rename_list
            for cid, old, new in rename_list:
                st.markdown(f"- **{old}**  →  **{new}**")
        else:
            st.info("修正が必要な会社名はありません。")
            st.session_state.pop("rename_list", None)

    if st.session_state.get("rename_list"):
        if st.button("✅ すべて適用する", key="apply_rename", type="primary"):
            with get_db() as db:
                count = 0
                for cid, old, new in st.session_state["rename_list"]:
                    c = db.query(Company).filter(Company.id == cid).first()
                    if c and c.name == old:
                        c.name = new
                        c.updated_at = datetime.utcnow()
                        count += 1
                db.commit()
            st.session_state.pop("rename_list", None)
            st.success(f"{count} 社の会社名を修正しました！")
            st.rerun()

# ═══════════════════════════════════════════════════
# 検索 & 会社一覧
# ═══════════════════════════════════════════════════
search_query = st.text_input("🔍 会社名で検索", placeholder="検索...", label_visibility="collapsed")

with get_db() as db:
    q = db.query(Company).order_by(Company.updated_at.desc())
    if search_query:
        q = q.filter(Company.name.contains(search_query))
    companies = q.all()

    company_list = []
    for c in companies:
        company_list.append({
            "id": c.id,
            "name": c.name,
            "hp_url": c.hp_url,
            "industry_detail": c.industry_detail,
            "description": c.description,
            "notes": c.notes,
            "ai_summary": c.ai_summary,
            "strengths": json.loads(c.strengths) if c.strengths else [],
            "weaknesses": json.loads(c.weaknesses) if c.weaknesses else [],
            "links": [(l.id, l.url, l.title, l.link_type, l.description) for l in c.links],
            "files": [(f.id, f.original_name, f.file_type, f.size, f.file_path) for f in c.files],
        })

if not company_list:
    st.markdown("""
    <div style="text-align:center; padding:3rem; border:1px dashed #e2e0db;">
        <p style="color:#a5a39d; font-size:0.85em;">
            まだ会社が登録されていません。<br>上の「➕ 新しい会社を追加」から登録してください。
        </p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.caption(f"{len(company_list)} 社")

    for co in company_list:
        ai_badge = " 🤖" if co["ai_summary"] else ""

        with st.expander(f'{co["name"]}{ai_badge}', expanded=False):
            # ── 基本情報 ──
            if co["hp_url"]:
                st.markdown(f'🔗 [{co["hp_url"]}]({co["hp_url"]})')
            if co["description"]:
                st.markdown(f'<p style="color:#6b6a65;font-size:0.9em;">{co["description"]}</p>', unsafe_allow_html=True)

            # ── AI分析結果 ──
            if co["ai_summary"]:
                st.markdown(f"""
                <div class="ai-summary-box">
                    <div class="label">✨ AI Analysis</div>
                    <p>{co["ai_summary"]}</p>
                </div>
                """, unsafe_allow_html=True)

                col_s, col_w = st.columns(2)
                with col_s:
                    st.markdown('<span style="color:#a5a39d;font-size:0.7em;letter-spacing:0.3em;">STRENGTHS</span>', unsafe_allow_html=True)
                    render_strength_tags(co["strengths"])
                with col_w:
                    st.markdown('<span style="color:#a5a39d;font-size:0.7em;letter-spacing:0.3em;">WEAKNESSES</span>', unsafe_allow_html=True)
                    render_weakness_tags(co["weaknesses"])

            # ── AI分析ボタン ──
            if co["hp_url"]:
                if st.button("🤖 AI分析を実行", key=f"ai_{co['id']}"):
                    with st.spinner("HPを取得してAI分析中..."):
                        from lib.scraper import fetch_page_text
                        from lib.ai_analyzer import analyze_company_page
                        page_text = fetch_page_text(co["hp_url"])
                        if not page_text:
                            st.error("ページを取得できませんでした")
                        else:
                            try:
                                result = analyze_company_page(co["hp_url"], page_text)
                                with get_db() as db:
                                    c = db.query(Company).filter(Company.id == co["id"]).first()
                                    c.strengths = json.dumps(result.get("strengths", []), ensure_ascii=False)
                                    c.weaknesses = json.dumps(result.get("weaknesses", []), ensure_ascii=False)
                                    c.ai_summary = result.get("summary", "")
                                    c.updated_at = datetime.utcnow()
                                    db.commit()
                                st.success("AI分析が完了しました！")
                                st.rerun()
                            except Exception as e:
                                st.error(f"AI分析エラー: {str(e)}")

            st.markdown("---")

            # ── リンク・資料 ──
            st.markdown("**🔗 リンク・資料**")
            if co["links"]:
                for link_id, link_url, link_title, link_type, link_desc in co["links"]:
                    col_link, col_del = st.columns([5, 1])
                    with col_link:
                        display = link_title or link_url
                        type_emoji = {"youtube": "🎥", "material": "📄", "sns": "💬", "hp": "🌐"}.get(link_type, "🔗")
                        st.markdown(f"{type_emoji} [{display}]({link_url})")
                    with col_del:
                        if st.button("✕", key=f"dl_{co['id']}_{link_id}"):
                            with get_db() as db:
                                t = db.query(CompanyLink).filter(CompanyLink.id == link_id).first()
                                if t:
                                    db.delete(t)
                                    db.commit()
                            st.rerun()
            else:
                st.caption("リンクなし")

            with st.form(f"add_link_{co['id']}", clear_on_submit=True):
                lc1, lc2, lc3 = st.columns([3, 2, 1])
                with lc1:
                    link_url = st.text_input("URL", placeholder="https://...", key=f"lu_{co['id']}")
                with lc2:
                    link_title = st.text_input("タイトル", placeholder="資料名等", key=f"lt_{co['id']}")
                with lc3:
                    link_type = st.selectbox("種別", ["material", "youtube", "hp", "sns", "other"], key=f"ltp_{co['id']}")
                if st.form_submit_button("リンク追加"):
                    if link_url and link_url.strip():
                        with get_db() as db:
                            db.add(CompanyLink(
                                company_id=co["id"],
                                url=link_url.strip(),
                                title=link_title.strip() if link_title else None,
                                link_type=link_type,
                            ))
                            db.commit()
                        st.rerun()

            st.markdown("---")

            # ── ファイル ──
            st.markdown("**📁 ファイル**")
            if co["files"]:
                for file_id, orig_name, file_type, file_size, file_path in co["files"]:
                    col_f, col_fd = st.columns([5, 1])
                    with col_f:
                        size_str = f"{file_size / 1024:.0f} KB" if file_size and file_size < 1024 * 1024 else f"{(file_size or 0) / (1024 * 1024):.1f} MB"
                        emoji = {"pdf": "📄", "video": "🎥", "image": "🖼️"}.get(file_type, "📎")
                        st.markdown(f"{emoji} **{orig_name}** ({size_str})")
                    with col_fd:
                        if st.button("✕", key=f"df_{co['id']}_{file_id}"):
                            with get_db() as db:
                                t = db.query(CompanyFile).filter(CompanyFile.id == file_id).first()
                                if t:
                                    if os.path.exists(t.file_path):
                                        os.remove(t.file_path)
                                    db.delete(t)
                                    db.commit()
                            st.rerun()

            # アップロードキーをセッションで管理（重複防止）
            company_id = co["id"]
            counter_key = f"upload_counter_{company_id}"
            counter = st.session_state.get(counter_key, 0)
            upload_key = f"upload_{company_id}_{counter}"
            uploaded = st.file_uploader(
                "ファイルをアップロード",
                type=["pdf", "mp4", "mov", "avi", "webm", "jpg", "jpeg", "png", "gif", "webp"],
                key=upload_key,
            )
            if uploaded:
                # 同じファイルの重複登録を防ぐ
                last_key = f"last_upload_{company_id}"
                already_uploaded = st.session_state.get(last_key)
                if already_uploaded != uploaded.name:
                    ext = os.path.splitext(uploaded.name)[1]
                    saved_name = f"{uuid.uuid4()}{ext}"
                    company_dir = os.path.join(UPLOAD_DIR, str(company_id))
                    os.makedirs(company_dir, exist_ok=True)
                    file_path = os.path.join(company_dir, saved_name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded.getvalue())

                    content_type = uploaded.type or ""
                    file_type = "other"
                    for prefix, ft in {"application/pdf": "pdf", "video/": "video", "image/": "image"}.items():
                        if content_type.startswith(prefix):
                            file_type = ft
                            break

                    with get_db() as db:
                        db.add(CompanyFile(
                            company_id=company_id,
                            filename=saved_name,
                            original_name=uploaded.name,
                            file_type=file_type,
                            file_path=file_path,
                            size=uploaded.size,
                        ))
                        db.commit()
                    st.session_state[last_key] = uploaded.name
                    st.session_state[counter_key] = counter + 1
                    st.success(f"「{uploaded.name}」をアップロードしました")
                    st.rerun()

            st.markdown("---")

            # ── 編集 ──
            with st.form(f"edit_{co['id']}"):
                st.markdown("**✏️ 編集**")
                ec1, ec2 = st.columns(2)
                with ec1:
                    edit_name = st.text_input("会社名", value=co["name"], key=f"en_{co['id']}")
                with ec2:
                    edit_url = st.text_input("HP URL", value=co["hp_url"] or "", key=f"eu_{co['id']}")
                edit_desc = st.text_area("概要", value=co["description"] or "", height=80, key=f"ed_{co['id']}")
                edit_notes = st.text_area("メモ", value=co["notes"] or "", height=60, key=f"eno_{co['id']}")

                if st.form_submit_button("保存", type="primary"):
                    with get_db() as db:
                        c = db.query(Company).filter(Company.id == co["id"]).first()
                        c.name = edit_name.strip()
                        c.hp_url = edit_url.strip() if edit_url else None
                        c.description = edit_desc.strip() if edit_desc else None
                        c.notes = edit_notes.strip() if edit_notes else None
                        c.updated_at = datetime.utcnow()
                        db.commit()
                    st.success("保存しました！")
                    st.rerun()

            # 削除ボタン
            if st.button("🗑️ この会社を削除", key=f"delete_{co['id']}", type="secondary"):
                st.session_state[f"confirm_delete_{co['id']}"] = True

            if st.session_state.get(f"confirm_delete_{co['id']}"):
                st.warning(f"「{co['name']}」を削除しますか？この操作は元に戻せません。")
                cd1, cd2 = st.columns(2)
                with cd1:
                    if st.button("はい、削除する", key=f"yes_del_{co['id']}", type="primary"):
                        with get_db() as db:
                            c = db.query(Company).filter(Company.id == co["id"]).first()
                            if c:
                                db.delete(c)
                                db.commit()
                        st.session_state.pop(f"confirm_delete_{co['id']}", None)
                        st.rerun()
                with cd2:
                    if st.button("キャンセル", key=f"no_del_{co['id']}"):
                        st.session_state.pop(f"confirm_delete_{co['id']}", None)
                        st.rerun()
