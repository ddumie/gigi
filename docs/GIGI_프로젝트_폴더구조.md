# 지지(GIGI) 프로젝트 폴더 구조

> **최종 업데이트**: 2026.04.08  
> **구조 방식**: 도메인 중심 구조 + 바닐라 MPA  
> **기술 스택**: FastAPI + SQLAlchemy + PostgreSQL + 정적 HTML/CSS/JS

---

## 폴더 구조

```text
gigi/
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── router.py
│   │
│   └── domains/
│       ├── auth/
│       ├── onboarding/
│       ├── habits/
│       ├── today/
│       ├── support/
│       ├── neighbor/
│       └── settings/
│
├── frontend/
│   ├── index.html
│   ├── assets/
│   ├── shared/
│   │   ├── styles/
│   │   └── lib/
│   ├── features/
│   │   ├── auth/
│   │   ├── onboarding/
│   │   ├── today/
│   │   ├── habits/
│   │   ├── support/
│   │   ├── neighbor/
│   │   └── settings/
│   └── pages/
│       ├── auth/
│       ├── onboarding/
│       ├── today/
│       ├── habits/
│       ├── support/
│       ├── neighbor/
│       └── settings/
│
├── docs/
│   └── GIGI_프로젝트_폴더구조.md
├── .env.example
├── .gitignore
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
└── README.md
```

---

## 구조 설명

### Backend Core

| 파일 | 역할 |
|---|---|
| `backend/main.py` | FastAPI 앱 생성, API 라우터 등록, frontend 정적 파일 서빙 |
| `backend/config.py` | `.env` 기반 환경 변수 로드 |
| `backend/database.py` | SQLAlchemy 엔진, 세션, Base, 모델 로딩 |
| `backend/api/router.py` | 각 도메인 router를 `/api/v1/*` 아래로 통합 |

### Backend Domains

| 파일 | 역할 |
|---|---|
| `models.py` | DB 테이블 정의 |
| `schemas.py` | 요청/응답 스키마 정의 |
| `crud.py` | DB 입출력 담당 |
| `service.py` | 비즈니스 로직 담당 |
| `router.py` | API 엔드포인트 정의 |

예외:

- `today`는 조합/조회 도메인이라 `models.py`, `crud.py`가 없습니다.
- `settings`는 `User`, `UserPreference`를 수정하는 조합 도메인이라 `models.py`, `crud.py`가 없습니다.

### Frontend

| 폴더/파일 | 역할 |
|---|---|
| `frontend/index.html` | 랜딩 페이지 진입점 |
| `frontend/shared/styles/` | 공통 스타일 시스템 |
| `frontend/shared/lib/` | 공통 JS, API 호출 래퍼 |
| `frontend/features/<domain>/` | 도메인 전용 CSS/JS |
| `frontend/pages/<domain>/` | 실제 페이지 HTML |

---

## 도메인별 책임

| 도메인 | 설명 |
|---|---|
| `auth` | 회원가입, 로그인, JWT, 사용자 계정 |
| `onboarding` | 나이대/관심사 저장, AI 추천 진입 |
| `habits` | 습관 CRUD, 습관 체크 기반 데이터 |
| `today` | 오늘 탭 화면 조합, 받은 지지 알림/미니 달력/요약 조회 |
| `support` | 모임, 초대 코드, 지지하기, 알림, 레벨/스트릭 |
| `neighbor` | 습관 공유 피드, 모임 구해요, 내 글 |
| `settings` | 프로필 수정, 계정 설정 |

---

## 담당자별 작업 폴더

| 담당자 | 담당 영역 | 주 작업 폴더 |
|---|---|---|
| 전연주(PM) | `today`, `habits`, 첫 로그인 모달, 오늘 탭 조합 조회 | `backend/domains/today/`, `backend/domains/habits/`, `frontend/pages/today/`, `frontend/pages/habits/`, `frontend/features/today/`, `frontend/features/habits/` |
| 김평일 | `auth`, `settings`, 랜딩 | `backend/domains/auth/`, `backend/domains/settings/`, `frontend/index.html`, `frontend/pages/auth/`, `frontend/pages/settings/`, `frontend/features/auth/`, `frontend/features/settings/` |
| 김유선 | `onboarding`, AI 추천 흐름 | `backend/domains/onboarding/`, `frontend/pages/onboarding/`, `frontend/features/onboarding/` |
| 이영진 | `neighbor` | `backend/domains/neighbor/`, `frontend/pages/neighbor/`, `frontend/features/neighbor/` |
| 박기상 | `support`, 모임 생성/관리, 추후 배포 관련 파일 | `backend/domains/support/`, `frontend/pages/support/`, `frontend/features/support/`, `Dockerfile`, `docker-compose.yml` |

### 공통 파일 담당

| 구분 | 폴더/파일 | 메모 |
|---|---|---|
| 프론트 공통 | `frontend/shared/styles/`, `frontend/shared/lib/`, `frontend/index.html` | 공통 자산이므로 수정 시 팀 내 공유 후 진행 권장 |
| 백엔드 공통 | `backend/config.py`, `backend/database.py`, `backend/main.py`, `backend/api/router.py` | 여러 도메인에 영향이 있으므로 변경 시 PR 설명에 영향 범위 명시 |
| 문서 | `README.md`, `docs/GIGI_프로젝트_폴더구조.md` | 구조나 작업 방식이 바뀌면 함께 업데이트 |

### 경계 메모

- `today`는 자체 모델 없이 `habits`, `support` 데이터를 조합하는 도메인입니다.
- `settings`는 자체 모델 없이 `auth.User`, `onboarding.UserPreference`를 수정하는 도메인입니다.
- `neighbor`의 `group-search-join` 화면은 이웃 도메인에 속하지만, 실제 모임 생성과 습관 자동 추가는 백엔드 `today`/`habits` 및 `support` 연동이 필요할 수 있습니다.

---

## 프론트 작업 규칙

- 공통 CSS는 `frontend/shared/styles/`에서만 수정합니다.
- 공통 JS는 `frontend/shared/lib/`에서만 수정합니다.
- 페이지별 마크업은 `frontend/pages/`에서 수정합니다.
- 페이지 전용 스타일과 동작은 `frontend/features/<domain>/`에 작성합니다.
- 한 페이지는 기본적으로 공통 CSS 3개 + 공통 JS 2개 + 도메인 CSS/JS를 로드합니다.

---

## 백엔드 작업 규칙

- 기능 추가는 `backend/domains/<domain>/` 안에서 처리합니다.
- `router -> service -> crud` 흐름을 기본으로 사용합니다.
- DB 테이블 수정이 필요한 경우 `models.py`를 먼저 확인합니다.
- `today`, `settings`는 다른 도메인의 데이터를 조합하는 구조이므로 별도 모델을 만들지 않습니다.
- 공통 설정 변경은 `config.py`, DB 연결 관련 변경은 `database.py`, 전체 라우팅 변경은 `api/router.py`에서 처리합니다.

---

## 모델 기준 메모

- `auth.models.User`
  - `account_type` 제거
  - `nickname` unique
  - `is_first_login` 유지
- `onboarding.models.UserPreference`
  - `exercise_time` 제거
- `habits.models`
  - `Routine`, `RoutineCheck` 유지
- `support.models`
  - `Group`, `GroupMember`, `InviteCode`, `Support`, `Notification`
  - `Message` 제거
- `neighbor.models`
  - `Post.post_type`은 `feed` / `group_search`
  - `Comment` 제거

---

## 팀 작업 방식

- 하루 작업 완료 후 작업 브랜치에서 `main` 대상 PR을 생성합니다.
- 팀장 전연주가 확인 후 `main`에 merge 합니다.
- 공통 구조를 건드리는 경우 PR 설명에 변경 이유와 영향 범위를 함께 적습니다.
- 구조 관련 변경이 생기면 이 문서와 `README.md`를 함께 업데이트합니다.
