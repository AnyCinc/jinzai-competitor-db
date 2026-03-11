from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
import models
import schemas

router = APIRouter(tags=["links"])


@router.post("/api/companies/{company_id}/links", response_model=schemas.LinkOut)
def add_link(
    company_id: int,
    link: schemas.LinkCreate,
    db: Session = Depends(get_db),
):
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="会社が見つかりません")

    db_link = models.CompanyLink(company_id=company_id, **link.model_dump())
    db.add(db_link)
    db.commit()
    db.refresh(db_link)
    return db_link


@router.get("/api/companies/{company_id}/links", response_model=List[schemas.LinkOut])
def list_links(company_id: int, db: Session = Depends(get_db)):
    return (
        db.query(models.CompanyLink)
        .filter(models.CompanyLink.company_id == company_id)
        .order_by(models.CompanyLink.created_at.desc())
        .all()
    )


@router.delete("/api/links/{link_id}")
def delete_link(link_id: int, db: Session = Depends(get_db)):
    db_link = db.query(models.CompanyLink).filter(models.CompanyLink.id == link_id).first()
    if not db_link:
        raise HTTPException(status_code=404, detail="リンクが見つかりません")
    db.delete(db_link)
    db.commit()
    return {"ok": True}
