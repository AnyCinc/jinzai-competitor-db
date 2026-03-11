import json
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
import models
import schemas
from services.scraper import google_search, fetch_page_text
from services.ai_analyzer import analyze_company_page

router = APIRouter(tags=["analysis"])


@router.post("/api/search", response_model=schemas.SearchResponse)
async def search_competitors(
    req: schemas.SearchRequest,
    db: Session = Depends(get_db),
):
    """Googleで同業他社を検索してリストを返す"""
    results = await google_search(req.query, req.max_results)

    # 検索ログを保存
    log = models.SearchLog(
        query=req.query,
        results_json=json.dumps(results, ensure_ascii=False),
    )
    db.add(log)
    db.commit()

    items = [
        schemas.SearchResultItem(
            title=r.get("title", ""),
            url=r.get("url", ""),
            snippet=r.get("snippet"),
        )
        for r in results
        if "error" not in r and r.get("url")
    ]

    return schemas.SearchResponse(query=req.query, results=items)


@router.post("/api/analyze", response_model=schemas.AnalyzeResponse)
async def analyze_url(
    req: schemas.AnalyzeRequest,
    db: Session = Depends(get_db),
):
    """指定URLのHPを取得してAIで分析"""
    page_text = await fetch_page_text(req.url)
    if not page_text:
        raise HTTPException(status_code=422, detail="ページを取得できませんでした")

    try:
        result = analyze_company_page(req.url, page_text)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI分析エラー: {str(e)}")

    # 会社IDが指定されていれば結果を保存
    if req.save_company_id:
        company = db.query(models.Company).filter(
            models.Company.id == req.save_company_id
        ).first()
        if company:
            strengths = result.get("strengths", [])
            weaknesses = result.get("weaknesses", [])
            company.strengths = json.dumps(strengths, ensure_ascii=False)
            company.weaknesses = json.dumps(weaknesses, ensure_ascii=False)
            company.ai_summary = result.get("summary", "")
            company.updated_at = datetime.utcnow()
            db.commit()

    return schemas.AnalyzeResponse(
        url=req.url,
        company_name=result.get("company_name"),
        summary=result.get("summary"),
        strengths=result.get("strengths", []),
        weaknesses=result.get("weaknesses", []),
        raw_text=page_text[:500] if page_text else None,
    )


@router.post("/api/analyze/{company_id}", response_model=schemas.AnalyzeResponse)
async def analyze_company(company_id: int, db: Session = Depends(get_db)):
    """会社IDのHPを取得してAI分析し、DBに保存"""
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="会社が見つかりません")
    if not company.hp_url:
        raise HTTPException(status_code=422, detail="HP URLが登録されていません")

    page_text = await fetch_page_text(company.hp_url)
    if not page_text:
        raise HTTPException(status_code=422, detail="HPを取得できませんでした")

    try:
        result = analyze_company_page(company.hp_url, page_text)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI分析エラー: {str(e)}")

    strengths = result.get("strengths", [])
    weaknesses = result.get("weaknesses", [])
    company.strengths = json.dumps(strengths, ensure_ascii=False)
    company.weaknesses = json.dumps(weaknesses, ensure_ascii=False)
    company.ai_summary = result.get("summary", "")
    company.updated_at = datetime.utcnow()
    db.commit()

    return schemas.AnalyzeResponse(
        url=company.hp_url,
        company_name=result.get("company_name"),
        summary=result.get("summary"),
        strengths=strengths,
        weaknesses=weaknesses,
        raw_text=page_text[:500] if page_text else None,
    )
