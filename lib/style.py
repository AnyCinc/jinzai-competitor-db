import streamlit as st


def inject_custom_css():
    """カスタムCSSを注入してエレガントなデザインに"""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300&family=Noto+Sans+JP:wght@300;400;500&family=Montserrat:wght@300;400;500;600&display=swap');

    /* フォント */
    html, body, [class*="css"] {
        font-family: 'Noto Sans JP', 'Montserrat', sans-serif;
        font-weight: 300;
    }

    h1 {
        font-family: 'Cormorant Garamond', serif !important;
        font-weight: 300 !important;
        letter-spacing: 0.05em;
        color: #1c1c1a;
    }
    h2, h3 {
        font-family: 'Noto Sans JP', sans-serif !important;
        font-weight: 400 !important;
        color: #1c1c1a;
    }

    /* セクションラベル */
    .section-label {
        font-size: 0.65em;
        letter-spacing: 0.5em;
        text-transform: uppercase;
        color: #a5a39d;
        margin-bottom: 0;
    }

    /* 強み・弱みタグ */
    .strength-tag {
        display: inline-block;
        padding: 4px 14px;
        margin: 3px 4px 3px 0;
        border: 1px solid #c2d4b8;
        color: #4a6b3a;
        background: #f3f8f0;
        font-size: 0.85em;
    }
    .weakness-tag {
        display: inline-block;
        padding: 4px 14px;
        margin: 3px 4px 3px 0;
        border: 1px solid #e0cdb8;
        color: #8b6f4e;
        background: #faf5ef;
        font-size: 0.85em;
    }

    /* 会社カード */
    .company-card {
        background: #ffffff;
        border: 1px solid #e2e0db;
        padding: 1.2rem 1.5rem;
        margin-bottom: 8px;
        transition: border-color 0.2s;
    }
    .company-card:hover {
        border-color: #bbb;
    }
    .company-card h4 {
        margin: 0 0 4px 0;
        color: #1c1c1a;
        font-weight: 400;
    }
    .company-card .meta {
        font-size: 0.8em;
        color: #a5a39d;
    }
    .company-card .desc {
        font-size: 0.85em;
        color: #6b6a65;
        margin-top: 6px;
    }

    /* 業種バッジ */
    .industry-badge {
        display: inline-block;
        padding: 2px 10px;
        border: 1px solid #e2e0db;
        color: #a5a39d;
        font-size: 0.7em;
        letter-spacing: 0.2em;
        text-transform: uppercase;
    }

    /* AI分析サマリー */
    .ai-summary-box {
        background: #f8f7f4;
        border: 1px solid #e2e0db;
        padding: 1.2rem 1.5rem;
        margin: 1rem 0;
    }
    .ai-summary-box .label {
        font-size: 0.65em;
        letter-spacing: 0.4em;
        text-transform: uppercase;
        color: #a5a39d;
        margin-bottom: 8px;
    }
    .ai-summary-box p {
        color: #6b6a65;
        font-size: 0.9em;
        line-height: 1.7;
    }

    /* 検索結果カード */
    .search-result {
        background: #ffffff;
        border: 1px solid #e2e0db;
        padding: 1.2rem 1.5rem;
        margin-bottom: 6px;
    }
    .search-result:hover {
        background: #fcfbf9;
    }
    .search-result h4 {
        margin: 0 0 4px 0;
        color: #1c1c1a;
        font-weight: 400;
        font-size: 0.95em;
    }
    .search-result .url {
        font-size: 0.75em;
        color: #a5a39d;
        word-break: break-all;
    }
    .search-result .snippet {
        font-size: 0.85em;
        color: #6b6a65;
        margin-top: 6px;
        line-height: 1.6;
    }

    /* Streamlit デフォルトUI調整 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="manage-app-button"] {display: none;}
    .stDeployButton {display: none;}
    [data-testid="stStatusWidget"] {display: none;}

    .stButton > button {
        border-radius: 0 !important;
        letter-spacing: 0.1em;
        font-size: 0.8em;
        font-weight: 400;
    }

    /* サイドバー */
    [data-testid="stSidebar"] {
        background: #f5f4f1;
    }
    [data-testid="stSidebar"] .stMarkdown p {
        font-size: 0.85em;
    }

    /* 区切り線 */
    hr {
        border: none;
        border-top: 1px solid #e2e0db;
        margin: 1.5rem 0;
    }

    /* メトリクス */
    [data-testid="stMetricValue"] {
        font-family: 'Cormorant Garamond', serif;
        font-weight: 300;
    }
    </style>
    """, unsafe_allow_html=True)


def render_strength_tags(items):
    """強みタグをHTMLで表示"""
    if not items:
        st.markdown('<span style="color:#a5a39d;font-size:0.85em;">未登録</span>', unsafe_allow_html=True)
        return
    html = " ".join(f'<span class="strength-tag">{item}</span>' for item in items)
    st.markdown(html, unsafe_allow_html=True)


def render_weakness_tags(items):
    """弱みタグをHTMLで表示"""
    if not items:
        st.markdown('<span style="color:#a5a39d;font-size:0.85em;">未登録</span>', unsafe_allow_html=True)
        return
    html = " ".join(f'<span class="weakness-tag">{item}</span>' for item in items)
    st.markdown(html, unsafe_allow_html=True)


def render_industry_badge(industry):
    """業種バッジをHTMLで表示"""
    if industry:
        st.markdown(f'<span class="industry-badge">{industry}</span>', unsafe_allow_html=True)
