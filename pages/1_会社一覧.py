import streamlit as st
import json
from datetime import datetime
from lib.database import init_db, get_db
from lib.models import Company
from lib.style import inject_custom_css
from lib.auth import check_auth

st.set_page_config(page_title="会社一覧 | 競合調査DB", page_icon="📋", layout="wide")
if not check_auth():
    st.stop()
init_db()
inject_custom_css()

st.markdown('<p class="section-label">Company List</p>', unsafe_allow_html=True)
st.title("会社一覧")
st.caption("登録されている競合会社の一覧")

st.markdown("---")

# ── 新規追加フォーム ─────────────────────────────
with st.expander("➕ 新しい会社を追加", expanded=False):
    with st.form("add_company", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("会社名 *", placeholder="株式会社〇〇ジャパン")
        with col2:
            hp_url = st.text_input("HP URL", placeholder="https://example.com")

        col3, col4 = st.columns(2)
        with col3:
            industry = st.selectbox(
                "事業種別",
                ["", "技能実習", "特定技能", "高度人材", "技能実習・特定技能", "総合人材紹介", "その他"],
                format_func=lambda x: "— 選択 —" if x == "" else x,
            )
        with col4:
            notes = st.text_input("メモ", placeholder="メモ（任意）")

        description = st.text_area("概要・メモ", placeholder="会社の概要、特徴など...", height=80)

        submitted = st.form_submit_button("会社を追加", type="primary")

        if submitted:
            if not name or not name.strip():
                st.error("会社名は必須です")
            else:
                with get_db() as db:
                    new_company = Company(
                        name=name.strip(),
                        hp_url=hp_url.strip() if hp_url else None,
                        industry_detail=industry if industry else None,
                        description=description.strip() if description else None,
                        notes=notes.strip() if notes else None,
                    )
                    db.add(new_company)
                    db.commit()
                    st.success(f"「{name.strip()}」を追加しました！")
                    st.rerun()

st.markdown("---")

# ── 検索フィルター ───────────────────────────────
search_query = st.text_input("🔍 会社名で検索", placeholder="検索キーワードを入力...")

# ── 会社一覧 ─────────────────────────────────────
with get_db() as db:
    query = db.query(Company).order_by(Company.updated_at.desc())
    if search_query:
        query = query.filter(Company.name.contains(search_query))
    companies = query.all()

if not companies:
    st.markdown("""
    <div style="text-align:center; padding:3rem; border:1px dashed #e2e0db;">
        <p style="color:#a5a39d; font-size:0.85em;">
            会社が見つかりません
        </p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f'<p class="section-label">{len(companies)} 件</p>', unsafe_allow_html=True)
    st.markdown("")

    for company in companies:
        col_main, col_actions = st.columns([5, 1])

        with col_main:
            industry_html = f'<span class="industry-badge">{company.industry_detail}</span> ' if company.industry_detail else ""
            desc = (company.description or "")[:100]
            desc_html = f'<div class="desc">{desc}{"..." if len(company.description or "") > 100 else ""}</div>' if desc else ""
            url_html = f'<div class="meta">{company.hp_url}</div>' if company.hp_url else ""
            ai_badge = ' <span style="font-size:0.7em;color:#4a6b3a;border:1px solid #c2d4b8;padding:1px 6px;">AI済</span>' if company.ai_summary else ""

            st.markdown(f"""
            <div class="company-card">
                <h4>{industry_html}{company.name}{ai_badge}</h4>
                {url_html}
                {desc_html}
            </div>
            """, unsafe_allow_html=True)

        with col_actions:
            st.markdown("<div style='padding-top:12px'>", unsafe_allow_html=True)

            # 詳細ボタン
            if st.button("詳細", key=f"detail_{company.id}", type="primary"):
                st.session_state["selected_company_id"] = company.id
                st.switch_page("pages/2_会社詳細.py")

            # 削除ボタン
            if st.button("削除", key=f"delete_{company.id}"):
                st.session_state[f"confirm_delete_{company.id}"] = True

            st.markdown("</div>", unsafe_allow_html=True)

        # 削除確認
        if st.session_state.get(f"confirm_delete_{company.id}"):
            st.warning(f"「{company.name}」を本当に削除しますか？")
            col_yes, col_no = st.columns(2)
            with col_yes:
                if st.button("はい、削除する", key=f"yes_delete_{company.id}", type="primary"):
                    with get_db() as db2:
                        target = db2.query(Company).filter(Company.id == company.id).first()
                        if target:
                            db2.delete(target)
                            db2.commit()
                    del st.session_state[f"confirm_delete_{company.id}"]
                    st.rerun()
            with col_no:
                if st.button("キャンセル", key=f"no_delete_{company.id}"):
                    del st.session_state[f"confirm_delete_{company.id}"]
                    st.rerun()
