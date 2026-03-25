FROM python:3.11-slim

WORKDIR /app

# 依存パッケージ
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコード
COPY . .

# データ永続化用ディレクトリ
RUN mkdir -p /data/uploads

ENV PYTHONUNBUFFERED=1

# Railway は $PORT を自動設定
CMD streamlit run streamlit_app.py --server.port=${PORT:-8501} --server.headless=true --server.address=0.0.0.0
