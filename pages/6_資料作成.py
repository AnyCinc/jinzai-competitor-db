import streamlit as st
import json
from lib.database import init_db, get_db
from lib.models import Company
from lib.style import inject_custom_css
from lib.auth import check_auth

st.set_page_config(page_title="資料作成 | 競合調査DB", page_icon="📝", layout="wide")
if not check_auth():
    st.stop()
init_db()
inject_custom_css()

st.markdown('<p class="section-label">Sales Material Generator</p>', unsafe_allow_html=True)
st.title("営業資料作成")
st.caption("競合分析をもとに、ヒトキワ独自の営業資料を自動生成")

st.markdown("---")

with get_db() as db:
    companies = db.query(Company).filter(
        Company.ai_summary.isnot(None), Company.ai_summary != ""
    ).order_by(Company.name).all()

    company_options = {c.name: {
        "id": c.id,
        "name": c.name,
        "hp_url": c.hp_url,
        "ai_summary": c.ai_summary,
        "strengths": json.loads(c.strengths) if c.strengths else [],
        "weaknesses": json.loads(c.weaknesses) if c.weaknesses else [],
        "hitokiwa_advantages": json.loads(c.hitokiwa_advantages) if c.hitokiwa_advantages else [],
    } for c in companies}

if not company_options:
    st.info("AI分析済みの会社がありません。先に会社管理ページでAI分析を実行してください。")
else:
    selected = st.selectbox("競合を選択", list(company_options.keys()))
    co = company_options[selected]

    st.markdown(f"**{co['name']}** の分析結果をもとに営業資料を作成します。")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**強み**")
        for s in co["strengths"]:
            st.markdown(f"- {s}")
    with col2:
        st.markdown("**弱み**")
        for w in co["weaknesses"]:
            st.markdown(f"- {w}")

    if co["hitokiwa_advantages"]:
        st.markdown("**ヒトキワで勝てるところ**")
        for a in co["hitokiwa_advantages"]:
            st.markdown(f"- {a}")

    st.markdown("---")

    doc_type = st.selectbox("作成する資料タイプ", [
        "営業トークスクリプト（この競合に勝つための）",
        "比較表（ヒトキワ vs この競合）",
        "提案書テンプレート（この競合の顧客を奪うための）",
    ])

    additional = st.text_area("追加の指示（任意）", placeholder="例: 特定技能に特化した内容にして", height=60)

    if st.button("📝 資料を生成", type="primary", use_container_width=True):
        with st.spinner("AIが資料を生成中..."):
            try:
                from lib.ai_analyzer import get_client
                client = get_client()

                prompt = f"""あなたは外国人材紹介会社「ヒトキワ」の営業支援AIです。
以下の競合分析データをもとに、{doc_type}を作成してください。

## 競合情報
- 会社名: {co['name']}
- 概要: {co['ai_summary']}
- 競合の強み: {json.dumps(co['strengths'], ensure_ascii=False)}
- 競合の弱み: {json.dumps(co['weaknesses'], ensure_ascii=False)}
- ヒトキワで勝てるポイント: {json.dumps(co['hitokiwa_advantages'], ensure_ascii=False)}

{f"## 追加指示{chr(10)}{additional}" if additional else ""}

## 要件
- 日本語で作成
- 実際の営業現場で使える具体的な内容にする
- ヒトキワの強みを最大限アピールする
- 競合の弱みを上品に突く表現にする
- マークダウン形式で見やすく整理する"""

                message = client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=3000,
                    messages=[{"role": "user", "content": prompt}],
                )
                result = message.content[0].text.strip()

                st.markdown("---")
                st.markdown("### 📄 生成された資料")
                st.markdown(result)

                st.download_button(
                    "📥 テキストをダウンロード",
                    data=result,
                    file_name=f"hitokiwa_vs_{co['name']}.md",
                    mime="text/markdown",
                )
            except Exception as e:
                st.error(f"生成エラー: {str(e)}")
