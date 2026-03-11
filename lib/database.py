import os
import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from contextlib import contextmanager


def get_database_url():
    """Streamlit secrets → 環境変数 → デフォルトの順でDB URLを取得"""
    try:
        return st.secrets["DATABASE_URL"]
    except (KeyError, FileNotFoundError):
        return os.getenv("DATABASE_URL", "sqlite:///./data/db.sqlite3")


@st.cache_resource
def get_engine():
    url = get_database_url()
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    connect_args = {"check_same_thread": False} if "sqlite" in url else {}
    return create_engine(url, connect_args=connect_args)


Base = declarative_base()


def get_session():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()


@contextmanager
def get_db():
    session = get_session()
    try:
        yield session
    finally:
        session.close()


def init_db():
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
