# 제미나이 연동, 선택한 습관 등록
# Gemini API 호출, 프롬프트 구성, 응답 파싱, 재추천 1회 제한 로직

import asyncio
import json
import logging
from google import genai
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.domains.onboarding.schemas import AIHabitItem
from backend.config import settings
from backend.domains.habits.models import Habit
from backend.domains.auth.models import User
from backend.domains.onboarding import crud


logger = logging.getLogger(__name__)

client = genai.Client(api_key=settings.GEMINI_API_KEY)

# 사용가능한 Gemini 모델 목록 확인용입니다.
# try:
#     for model in client.models.list():
#         print(f"가용한 모델명: {model.name}")
# except Exception as e:
#     print(f"모델 리스트 조회 실패: {e}")


async def get_ai_recommendations(age_group: str | None, health_interests: list[str] | None) -> list[AIHabitItem]:
    """사용자가 설정한 나이대, 관심사 기반 Gemini AI 습관 추천"""
    interests_str = ", ".join(health_interests) if health_interests else "일반 건강 관리"
    interest_count = len(health_interests) if health_interests else 0
    num_habits = 3 if interest_count <= 1 else (4 if interest_count == 2 else 5)
    prompt = f"""
    사용자의 나이대: {age_group if age_group else "미입력"}
    사용자의 관심사: {interests_str}

    위 정보를 바탕으로 사용자에게 추천할 수 있는 건강 습관 {num_habits}가지를 JSON 형식으로 제공해주세요.
    각 습관은 title(습관 제목), category(카테고리), description(짧고 간단한 설명)을 포함해야 합니다.
    카테고리는 다음 중 하나여야 합니다: 운동, 복약, 식단, 수면, 기타
    매번 호출할 때마다 서로 다른 습관을 추천해주세요. 이전에 추천했을 가능성이 있는 습관은 피하고, 다양한 관점에서 새로운 습관을 제안해주세요.
    반드시 다음 조건을 지켜주세요:
    - 별도 비용 없이 지금 당장 실천할 수 있는 습관을 추천하세요.
    - 추천하는 행동은 구체적이고 작은 단위로 제안하세요. (예: "악기 배우기"처럼 막연한 것 대신 "유튜브로 5분 기타 영상 따라하기"처럼 구체적으로)
    description은 구체적인 시간, 횟수, 행동을 포함해서 짧고 명확하게 작성해주세요. 예: "매일 아침 7시, 10분 스트레칭으로 하루를 시작하세요."
    JSON 형식은 다음과 같아야 합니다:
    [
        {{
            "title": "습관 제목",
            "category": "카테고리",
            "description": "설명"
        }},
        ...
    ]
    """

    try:
        response = await asyncio.wait_for(
            client.aio.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=prompt
            ),
            timeout=30.0
        )
        text = response.text.strip()
    except asyncio.TimeoutError:
        logger.error("Gemini API 호출 시간 초과 (30초)")
        raise ValueError("Gemini API 응답 시간이 초과되었습니다.")
    except Exception as e:
        logger.error(f"Gemini API 호출 중 오류 발생: {e}", exc_info=True)
        raise ValueError("Gemini API 호출에 실패했습니다.")

    # Gemini 답변의 불필요 형식 제거(코드블록 제거)
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    try:
        return [AIHabitItem(**h) for h in json.loads(text)]
    except (json.JSONDecodeError, KeyError, TypeError, ValidationError):
        logger.error(f"Gemini JSON 파싱 중 오류 발생: {text}", exc_info=True)
        raise ValueError("Gemini 응답에 실패했습니다.")


async def save_selected_habits(db: AsyncSession, user_id: int, selected: list[AIHabitItem]) -> None:
    """AI 추천 습관 저장과 온보딩 완료처리"""
    if not selected:  # 라우터에서도 확인으로 이중체크 중
        raise ValueError("습관을 하나 이상 선택해주세요.")
    try:
        for item in selected:
            db.add(Habit(
                user_id=user_id,
                title=item.title,
                category=item.category,
                description=item.description,
                repeat_type="매일",
                is_ai_recommended=True
            ))
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalars().first()
        if user:
            user.is_first_login = False  # 첫로그인이면 온보딩안한상태(True), 아니면 이미 사용유저(False)
        else:
            logger.warning(f"온보딩 완료처리 실패: 사용자 {user_id}를 찾을 수 없습니다.")
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.error(f"습관 저장 중 오류 발생: {e}", exc_info=True)
        raise ValueError("습관 저장 중 오류가 발생했습니다.")

#  AI호출 성공해야 카운트증가로 넘어가서 AI성공=둘다성공, AI실패=둘다실패(카운트증가 실패로 에러처리됨)
async def recommend_habits_and_count(db: AsyncSession, user_id: int, age_group: str | None, health_interests: list[str] | None):
    """AI 습관추천 + 추천 횟수(카운트) 증가를 하나로 처리 : AI호출 성공시에만 카운트 증가"""
    habits = await get_ai_recommendations(age_group, health_interests)  # AI 호출
    try:
        updated_pref = await crud.increment_recommend_count(db, user_id)  # 카운트 증가
    except ValueError:  # 카운트 증가 실패하면 ValueError로 라우터에서 502에러
        raise ValueError("추천 횟수 업데이트 중 오류가 발생했습니다.")
    if updated_pref is None:
        raise ValueError("선호도 정보를 찾을 수 없습니다.")
    return habits, updated_pref
