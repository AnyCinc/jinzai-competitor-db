# ============================================================
# Stage 1: フロントエンド ビルド (Node.js)
# ============================================================
FROM node:20-alpine AS frontend-build

WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ============================================================
# Stage 2: バックエンド + 配信 (Python)
# ============================================================
FROM python:3.11-slim

WORKDIR /app

# Python 依存パッケージ
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# バックエンドコード
COPY backend/ ./backend/

# フロントエンドビルド成果物をコピー
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# アップロード用ディレクトリ
RUN mkdir -p /data/uploads

# 環境変数デフォルト
ENV UPLOAD_DIR=/data/uploads
ENV PYTHONUNBUFFERED=1

WORKDIR /app/backend

# Railway は $PORT を自動設定
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
