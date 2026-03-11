import os
import json
from typing import Dict, List, Optional
import anthropic


def get_client() -> anthropic.Anthropic:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY が設定されていません")
    return anthropic.Anthropic(api_key=api_key)


def analyze_company_page(url: str, page_text: str) -> Dict:
    """
    HPのテキストからClaude APIで強み・弱み・概要を分析
    """
    client = get_client()

    prompt = f"""以下は外国人材紹介会社のWebページのテキストです。
URL: {url}

---
{page_text}
---

この会社について、外国人材紹介業の観点から以下を分析してください。
必ずJSON形式で返してください。

{{
  "company_name": "会社名（テキストから推測）",
  "summary": "会社の概要・事業内容（200字以内）",
  "strengths": [
    "強み1",
    "強み2",
    "強み3"
  ],
  "weaknesses": [
    "弱み・課題1（HPから読み取れる懸念点）",
    "弱み・課題2"
  ],
  "service_types": ["技能実習", "特定技能", "高度人材" など該当するもの],
  "target_countries": ["対応国（わかる範囲で）"]
}}

強みは実際にHPに書かれている内容から、弱みはHP情報が不足している点や競合と比べて不利になりそうな点を記載してください。
必ずJSONのみを返してください。"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()

    # JSONブロックを抽出
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {
            "company_name": "",
            "summary": raw,
            "strengths": [],
            "weaknesses": [],
            "service_types": [],
            "target_countries": [],
        }

    return result


def compare_companies(companies_data: List[Dict]) -> str:
    """複数会社の比較レポートを生成"""
    client = get_client()

    companies_json = json.dumps(companies_data, ensure_ascii=False, indent=2)

    prompt = f"""以下は外国人材紹介会社の調査データです。

{companies_json}

これらの会社を比較分析し、以下の観点でレポートを作成してください：
1. 業界全体の傾向
2. 各社の差別化ポイント
3. 競合に勝つための示唆

日本語で500字程度でまとめてください。"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )

    return message.content[0].text.strip()
