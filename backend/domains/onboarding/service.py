# 제미나이 연동, 선택한 습관 등록
# Gemini API 호출, 프롬프트 구성, 응답 파싱, 재추천 1회 제한 로직

import json
import logging
import google.generativeai as genai
from pydantic import ValidationError
from sqlalchemy.orm import Session
from backend.domains.onboarding.schemas import AIHabitItem
from backend.config import settings
from backend.domains.habits.models import Habit
from backend.domains.auth.models import User

logger = logging.getLogger(__name__)

genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")  # gemini-3.1-flash-lite-preview


def get_ai_recommendations(age_group: str | None, health_interests: list[str] | None) -> list[AIHabitItem]:
    """사용자가 설정한 나이대, 관심사 기반 Gemini AI 습관 추천"""
    interests_str = ", ".join(health_interests) if health_interests else "일반 건강 관리"
    prompt = f"""
    사용자의 나이대: {age_group if age_group else "미입력"}
    사용자의 관심사: {interests_str}
    
    위 정보를 바탕으로 사용자에게 추천할 수 있는 건강 습관 3가지를 JSON 형식으로 제공해주세요.
    각 습관은 title(습관 제목), category(카테고리), description(짧고 간단한 설명)을 포함해야 합니다.
    카테고리는 다음 중 하나여야 합니다: 운동, 복약, 식단, 수면, 기타
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
        response = model.generate_content(prompt, request_options={"timeout": 10})
        text = response.text.strip()
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


def save_selected_habits(db: Session, user_id: int, selected: list[AIHabitItem]) -> None:
    """AI 추천 습관 저장과 온보딩 완료처리"""
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
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.is_first_login = False  # 첫로그인이면 온보딩안한상태(True), 아니면 이미 사용유저(False)
        else:
            logger.warning(f"온보딩 완료처리 실패: 사용자 {user_id}를 찾을 수 없습니다.")
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"습관 저장 중 오류 발생: {e}", exc_info=True)
        raise ValueError("습관 저장 중 오류가 발생했습니다.")
