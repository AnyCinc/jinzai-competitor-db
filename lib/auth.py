import streamlit as st
import hashlib
import os


def _get_password_hash(password: str) -> str:
    """パスワードをSHA256でハッシュ化"""
    return hashlib.sha256(password.encode()).hexdigest()


def _get_correct_password() -> str:
    """設定されたパスワードを取得（secrets → 環境変数）"""
    try:
        return st.secrets.get("APP_PASSWORD", "")
    except FileNotFoundError:
        pass
    return os.getenv("APP_PASSWORD", "")


def check_auth() -> bool:
    """認証チェック。未ログインならログイン画面を表示してFalseを返す。"""
    password = _get_correct_password()

    # パスワード未設定の場合は認証スキップ（ローカル開発用）
    if not password:
        return True

    # 既にログイン済みか確認
    if st.session_state.get("authenticated"):
        return True

    # ── ログイン画面 ──
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400&family=Noto+Sans+JP:wght@300;400&display=swap');
    .login-container {
        max-width: 400px;
        margin: 8rem auto;
        text-align: center;
    }
    .login-title {
        font-family: 'Cormorant Garamond', serif;
        font-weight: 300;
        font-size: 2em;
        color: #1c1c1a;
        letter-spacing: 0.05em;
        margin-bottom: 0.2em;
    }
    .login-subtitle {
        font-size: 0.75em;
        letter-spacing: 0.4em;
        color: #a5a39d;
        text-transform: uppercase;
        margin-bottom: 2em;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="manage-app-button"] {display: none;}
    .stDeployButton {display: none;}
    [data-testid="stStatusWidget"] {display: none;}
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<p class="login-title">Competitor Analysis</p>', unsafe_allow_html=True)
    st.markdown('<p class="login-subtitle">競合調査データベース</p>', unsafe_allow_html=True)

    with st.form("login_form"):
        entered = st.text_input("パスワード", type="password", placeholder="パスワードを入力...")
        submitted = st.form_submit_button("ログイン", use_container_width=True)

        if submitted:
            if entered == password:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("パスワードが違います")

    st.markdown('</div>', unsafe_allow_html=True)
    return False
