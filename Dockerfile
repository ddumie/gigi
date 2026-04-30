# Python 기반 이미지 선택 (경량화된 slim 버전)
FROM python:3.14-slim

# 작업 디렉토리 설정
WORKDIR /app

# 필요한 시스템 패키지 설치 (PostgreSQL 클라이언트 라이브러리 등)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 프로젝트 전체 코드 복사 (backend, frontend 포함)
COPY . .

# 포트 설정 (FastAPI 기본 포트 8000)
EXPOSE 8000

# 서버 실행 (uvicorn)
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]