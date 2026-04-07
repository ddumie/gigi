# 지지(GIGI)

세대를 잇는 건강한 응원.
나이에 맞는 건강 습관을 기록하고, 가족·친구·이웃과 서로 지지하는 웹 서비스입니다.

## 기술 스택

- Frontend: Vanilla HTML / CSS / JavaScript
- Backend: FastAPI, SQLAlchemy, PostgreSQL
- AI: Gemini API

## 현재 구조

```text
gigi/
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── api/
│   └── domains/
├── frontend/
│   ├── index.html
│   ├── shared/
│   ├── features/
│   └── pages/
├── .env.example
├── requirements.txt
└── README.md
```

자세한 폴더 구조와 수정 규칙은 [docs/GIGI_프로젝트_폴더구조.md](./docs/GIGI_프로젝트_폴더구조.md)를 참고하세요.

## 작업 시작 가이드

- 공통 스타일과 공통 스크립트는 `frontend/shared/`에서 수정합니다.
- 화면별 마크업은 `frontend/pages/`에서 수정합니다.
- 도메인별 전용 CSS/JS는 `frontend/features/<domain>/`에서 수정합니다.
- 백엔드 기능은 `backend/domains/<domain>/` 단위로 작업합니다.
- `today`, `settings`는 모델 없는 조합 도메인입니다.

## 팀 작업 방식

- 작업 시작 전 각자 본인 작업용 개별 브랜치를 생성합니다.
- 하루 작업이 끝나면 작업 내용을 정리해 `main` 대상으로 Pull Request를 생성합니다.
- 팀장 전연주가 변경사항을 확인한 뒤 `main`에 merge 합니다.
- 공통 구조를 건드리는 변경은 PR 설명에 영향 범위를 함께 적습니다.

## 빠른 시작

1. 가상환경을 만들고 활성화합니다.
2. `pip install -r requirements.txt`로 의존성을 설치합니다.
3. `.env.example`을 참고해 `.env`를 작성합니다.
4. `uvicorn backend.main:app --reload`로 서버를 실행합니다.
5. 브라우저에서 `http://127.0.0.1:8000`에 접속합니다.

## 환경 변수

환경 변수는 [.env.example](./.env.example)을 참고해 작성합니다.

## 현재 상태

- 폴더 구조 재편은 완료되었습니다.
- 각 도메인의 실제 API 구현은 아직 placeholder가 포함되어 있습니다.
- `Dockerfile`, `docker-compose.yml`은 배포 단계에서 정리할 예정입니다.
