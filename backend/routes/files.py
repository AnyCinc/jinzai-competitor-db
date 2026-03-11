import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List

from database import get_db
import models
import schemas

router = APIRouter(tags=["files"])

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 524288000))  # 500MB

ALLOWED_TYPES = {
    "application/pdf": "pdf",
    "video/mp4": "video",
    "video/quicktime": "video",
    "video/x-msvideo": "video",
    "video/webm": "video",
    "image/jpeg": "image",
    "image/png": "image",
    "image/gif": "image",
    "image/webp": "image",
}


def get_file_type(content_type: str) -> str:
    return ALLOWED_TYPES.get(content_type, "other")


@router.post("/api/companies/{company_id}/files", response_model=schemas.FileOut)
async def upload_file(
    company_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="会社が見つかりません")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="ファイルサイズが上限（500MB）を超えています")

    ext = os.path.splitext(file.filename)[1] if file.filename else ""
    saved_name = f"{uuid.uuid4()}{ext}"
    company_dir = os.path.join(UPLOAD_DIR, str(company_id))
    os.makedirs(company_dir, exist_ok=True)
    file_path = os.path.join(company_dir, saved_name)

    with open(file_path, "wb") as f:
        f.write(content)

    file_type = get_file_type(file.content_type or "")
    db_file = models.CompanyFile(
        company_id=company_id,
        filename=saved_name,
        original_name=file.filename or saved_name,
        file_type=file_type,
        file_path=file_path,
        size=len(content),
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file


@router.get("/api/companies/{company_id}/files", response_model=List[schemas.FileOut])
def list_files(company_id: int, db: Session = Depends(get_db)):
    return (
        db.query(models.CompanyFile)
        .filter(models.CompanyFile.company_id == company_id)
        .order_by(models.CompanyFile.created_at.desc())
        .all()
    )


@router.delete("/api/files/{file_id}")
def delete_file(file_id: int, db: Session = Depends(get_db)):
    db_file = db.query(models.CompanyFile).filter(models.CompanyFile.id == file_id).first()
    if not db_file:
        raise HTTPException(status_code=404, detail="ファイルが見つかりません")

    if os.path.exists(db_file.file_path):
        os.remove(db_file.file_path)

    db.delete(db_file)
    db.commit()
    return {"ok": True}


@router.get("/api/files/{file_id}/download")
def download_file(file_id: int, db: Session = Depends(get_db)):
    db_file = db.query(models.CompanyFile).filter(models.CompanyFile.id == file_id).first()
    if not db_file:
        raise HTTPException(status_code=404, detail="ファイルが見つかりません")

    if not os.path.exists(db_file.file_path):
        raise HTTPException(status_code=404, detail="ファイルが見つかりません")

    return FileResponse(
        db_file.file_path,
        filename=db_file.original_name,
        media_type="application/octet-stream",
    )


@router.get("/api/files/{file_id}/preview")
def preview_file(file_id: int, db: Session = Depends(get_db)):
    db_file = db.query(models.CompanyFile).filter(models.CompanyFile.id == file_id).first()
    if not db_file:
        raise HTTPException(status_code=404, detail="ファイルが見つかりません")

    if not os.path.exists(db_file.file_path):
        raise HTTPException(status_code=404, detail="ファイルが見つかりません")

    media_types = {
        "pdf": "application/pdf",
        "video": "video/mp4",
        "image": "image/jpeg",
    }
    media_type = media_types.get(db_file.file_type, "application/octet-stream")
    return FileResponse(db_file.file_path, media_type=media_type)
