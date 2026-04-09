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

- 기능 구현이 끝나면 작업 내용을 정리해 `main` 대상으로 Pull Request를 생성합니다.
  
  [PR 전 브랜치 최신화 규칙]  
  모든 작업은 각자 작업 브랜치(feature/...)에서 진행함.  
  PR 생성 전에 아래 명령어로 최신 main을 반영하기  
  
  git checkout `<my-branch-name>`  #본인 작업 브랜치로 이동(필요 시)  
  git fetch origin  
  git merge origin/main  
    
  -> 최신화 후 충돌이 발생하면 해결 후 PR을 생성 (혼자 해결 불가한 경우에는 논의!)  
- 팀장 전연주가 변경사항을 확인한 뒤 `main`에 merge 합니다.
- 공통 구조를 건드리는 변경은 PR 설명에 영향 범위를 함께 적습니다.

## Git 작업 가이드

### 1. 작업 시작 전 `main` 최신화

- 처음 한 번만 저장소를 clone 한 뒤 작업 디렉토리로 이동합니다.
  `git clone <repo-url>`
  `cd gigi`
- 처음 작업할 때 본인 작업 브랜치를 생성합니다.
  `git checkout -b <my-branch-name>`
- 매일 작업 시작 전(아침) 원격 `main` 최신 내용을 본인 브랜치에 먼저 반영합니다.
  `git fetch origin`
  `git merge origin/main`

### 2. `git add .` 대신 본인 파일만 add

- 커밋 전에는 `git status`로 변경 파일을 확인합니다.
- 가능하면 `git add .` 대신 본인이 수정한 파일이나 폴더만 지정해서 add 합니다.
- 커밋 전 `git diff --staged --stat`으로 스테이징 범위를 다시 확인합니다.

### 3. 공통 파일 수정 시 공유

- 아래 파일과 폴더는 여러 작업에 영향을 줄 수 있으니 수정 전 팀에 먼저 공유하는 것을 권장합니다.
- `frontend/shared/`
- `frontend/index.html`
- `backend/config.py`
- `backend/database.py`
- `backend/main.py`
- `backend/api/router.py`

### 4. 전체 작업 흐름

1. `git fetch origin`
2. `git checkout -b <my-branch-name>` 또는 기존 브랜치 체크아웃
3. `git merge origin/main`
4. 코드 작업
5. `git status`
6. `git add <내가 수정한 파일 또는 폴더>`
7. `git diff --staged --stat`
8. `git commit -m "메시지"`
9. `git push origin <my-branch-name>`
10. GitHub에서 `main` 대상 PR 생성

## 로컬 실행

Git clone과 작업 브랜치 준비 후, 로컬 개발 환경을 실행하는 단계입니다.

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
