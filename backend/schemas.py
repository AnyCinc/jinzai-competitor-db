from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class CompanyBase(BaseModel):
    name: str
    hp_url: Optional[str] = None
    industry_detail: Optional[str] = None
    description: Optional[str] = None
    strengths: Optional[str] = None   # JSON文字列
    weaknesses: Optional[str] = None  # JSON文字列
    notes: Optional[str] = None
    status: Optional[str] = "active"


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(CompanyBase):
    name: Optional[str] = None
    ai_summary: Optional[str] = None


class FileOut(BaseModel):
    id: int
    company_id: int
    filename: str
    original_name: str
    file_type: Optional[str]
    size: Optional[int]
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class LinkBase(BaseModel):
    url: str
    title: Optional[str] = None
    link_type: Optional[str] = "other"
    description: Optional[str] = None


class LinkCreate(LinkBase):
    pass


class LinkOut(LinkBase):
    id: int
    company_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class CompanyOut(CompanyBase):
    id: int
    ai_summary: Optional[str]
    created_at: datetime
    updated_at: datetime
    files: List[FileOut] = []
    links: List[LinkOut] = []

    class Config:
        from_attributes = True


class SearchRequest(BaseModel):
    query: str
    max_results: Optional[int] = 10


class AnalyzeRequest(BaseModel):
    url: str
    save_company_id: Optional[int] = None


class SearchResultItem(BaseModel):
    title: str
    url: str
    snippet: Optional[str] = None


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResultItem]


class AnalyzeResponse(BaseModel):
    url: str
    company_name: Optional[str]
    summary: Optional[str]
    strengths: List[str]
    weaknesses: List[str]
    raw_text: Optional[str]
