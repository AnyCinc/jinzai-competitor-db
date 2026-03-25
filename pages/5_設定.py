import streamlit as st
import os
import json
from lib.database import init_db
from lib.style import inject_custom_css
from lib.auth import check_auth

st.set_page_config(page_title="設定 | 競合調査DB", page_icon="⚙️", layout="wide")
if not check_auth():
    st.stop()
init_db()
inject_custom_css()

SETTINGS_FILE = os.path.join("data", "settings.json")


def load_settings():
    """設定ファイルを読み込む"""
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_settings(settings):
    """設定ファイルに保存"""
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, ensure_ascii=False)


settings = load_settings()

st.markdown('<p class="section-label">Settings</p>', unsafe_allow_html=True)
st.title("設定")
st.caption("APIキー・パスワードの管理")

st.markdown("---")

# ═══════════════════════════════════════════════════
# ANTHROPIC API KEY
# ═══════════════════════════════════════════════════
st.markdown("### 🔑 Anthropic API Key")
st.caption("AI分析機能に必要です。[Anthropic Console](https://console.anthropic.com/) で取得できます。")

current_key = settings.get("ANTHROPIC_API_KEY", "") or os.getenv("ANTHROPIC_API_KEY", "")
masked_key = f"{current_key[:8]}...{current_key[-4:]}" if len(current_key) > 12 else ""

if masked_key:
    st.success(f"✅ 設定済み: `{masked_key}`")
else:
    st.warning("⚠️ 未設定 — AI分析が使えません")

with st.form("api_key_form"):
    new_key = st.text_input("API Key", type="password", placeholder="sk-ant-api03-...")
    if st.form_submit_button("保存", type="primary"):
        if new_key and new_key.strip():
            settings["ANTHROPIC_API_KEY"] = new_key.strip()
            save_settings(settings)
            # 環境変数にも即座に反映
            os.environ["ANTHROPIC_API_KEY"] = new_key.strip()
            st.success("✅ API Keyを保存しました！")
            st.rerun()
        else:
            st.error("API Keyを入力してください")

st.markdown("---")

# ═══════════════════════════════════════════════════
# APP PASSWORD
# ═══════════════════════════════════════════════════
st.markdown("### 🔒 ログインパスワード")
st.caption("アプリにアクセスする際のパスワードを設定します。")

current_pw = settings.get("APP_PASSWORD", "") or os.getenv("APP_PASSWORD", "")
if current_pw:
    st.success("✅ パスワード設定済み")
else:
    st.info("🔓 パスワード未設定（誰でもアクセス可能）")

with st.form("password_form"):
    new_pw = st.text_input("新しいパスワード", type="password", placeholder="パスワードを入力...")
    new_pw_confirm = st.text_input("パスワード確認", type="password", placeholder="もう一度入力...")
    if st.form_submit_button("パスワード変更", type="primary"):
        if not new_pw:
            st.error("パスワードを入力してください")
        elif new_pw != new_pw_confirm:
            st.error("パスワードが一致しません")
        else:
            settings["APP_PASSWORD"] = new_pw.strip()
            save_settings(settings)
            os.environ["APP_PASSWORD"] = new_pw.strip()
            st.success("✅ パスワードを変更しました！")
            st.rerun()
