import streamlit as st
from lib.database import init_db, get_db
from lib.models import Company
from lib.style import inject_custom_css

# ── ページ設定 ─────────────────────────────────
st.set_page_config(
    page_title="競合調査データベース",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── DB初期化 & CSS注入 ──────────────────────────
init_db()
inject_custom_css()

# ── サイドバー ──────────────────────────────────
with st.sidebar:
    st.markdown('<p class="section-label">Intelligence Tool</p>', unsafe_allow_html=True)
    st.markdown("### 競合調査DB")
    st.markdown("---")
    st.markdown("""
    **使い方**
    1. 📋 **会社一覧** → 会社の追加・管理
    2. 🔍 **会社詳細** → AI分析・編集
    3. 🌐 **Web検索** → 競合を自動検索
    """)

# ── メインコンテンツ ──────────────────────────────
st.markdown('<p class="section-label">Dashboard</p>', unsafe_allow_html=True)
st.title("Competitor Analysis")
st.caption("外国人材紹介会社の競合調査データベースツール")

st.markdown("---")

# 統計情報
with get_db() as db:
    total = db.query(Company).count()
    with_ai = db.query(Company).filter(Company.ai_summary.isnot(None), Company.ai_summary != "").count()
    recent = db.query(Company).order_by(Company.updated_at.desc()).limit(5).all()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("登録企業数", f"{total} 社")
with col2:
    st.metric("AI分析済み", f"{with_ai} 社")
with col3:
    st.metric("未分析", f"{total - with_ai} 社")

st.markdown("---")

# 最近の更新
if recent:
    st.markdown('<p class="section-label">最近更新された会社</p>', unsafe_allow_html=True)
    st.markdown("")
    for company in recent:
        industry = f'<span class="industry-badge">{company.industry_detail}</span> ' if company.industry_detail else ""
        desc = (company.description or "")[:80]
        desc_html = f'<div class="desc">{desc}{"..." if len(company.description or "") > 80 else ""}</div>' if desc else ""

        st.markdown(f"""
        <div class="company-card">
            <h4>{industry}{company.name}</h4>
            {desc_html}
        </div>
        """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div style="text-align:center; padding:3rem; border:1px dashed #e2e0db;">
        <p style="color:#a5a39d; font-size:0.85em;">
            まだ会社が登録されていません。<br>
            左メニューの「会社一覧」から追加してください。
        </p>
    </div>
    """, unsafe_allow_html=True)
