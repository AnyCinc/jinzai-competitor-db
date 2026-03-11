from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    hp_url = Column(String(500))
    industry_detail = Column(String(255))  # 技能実習、特定技能、高度人材 等
    description = Column(Text)
    strengths = Column(Text)   # JSON配列文字列
    weaknesses = Column(Text)  # JSON配列文字列
    notes = Column(Text)
    ai_summary = Column(Text)
    status = Column(String(50), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    files = relationship("CompanyFile", back_populates="company", cascade="all, delete-orphan")
    links = relationship("CompanyLink", back_populates="company", cascade="all, delete-orphan")


class CompanyFile(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    filename = Column(String(500), nullable=False)   # 保存ファイル名
    original_name = Column(String(500), nullable=False)  # 元のファイル名
    file_type = Column(String(50))  # pdf/video/image
    file_path = Column(String(1000), nullable=False)
    size = Column(Integer)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="files")


class CompanyLink(Base):
    __tablename__ = "links"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    url = Column(String(1000), nullable=False)
    title = Column(String(500))
    link_type = Column(String(50))  # hp/youtube/sns/material/other
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="links")


class SearchLog(Base):
    __tablename__ = "search_logs"

    id = Column(Integer, primary_key=True, index=True)
    query = Column(String(500))
    results_json = Column(Text)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
