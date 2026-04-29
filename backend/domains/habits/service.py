import logging
from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.domains.habits import crud
from backend.domains.habits.models import Habit, HabitCheck
from backend.domains.habits.schemas import HabitCreate, HabitUpdate

logger = logging.getLogger(__name__)


# ── 모임 습관 메타 해석 헬퍼 ──
# group_id가 있는 모임 습관은 title/category/repeat_type을 GroupSearchPost에서 가져와 표시한다.
# 멤버별 Habit row는 체크 기록(HabitCheck)과 개인화 필드(time, is_hidden_from_group) 보관용으로만 유지.

async def resolve_habit_meta(db: AsyncSession, habit: Habit) -> dict:
    """
    Habit의 표시용 메타(title, category, repeat_type)를 반환.
    group_id가 있고 연결된 GroupSearchPost가 살아있으면 Post 값,
    아니면 Habit row의 직접 값을 사용한다.
    """
    if habit.group_id is not None:
        # 지연 임포트로 도메인 순환 참조 회피
        from backend.domains.support.models import Group
        from backend.domains.neighbor.models import GroupSearchPost, Post

        result = await db.execute(
            select(GroupSearchPost.habit_title, GroupSearchPost.frequency, GroupSearchPost.category)
            .join(Post, Post.id == GroupSearchPost.post_id)
            .join(Group, Group.post_id == Post.id)
            .where(Group.id == habit.group_id, Post.is_active == True)
        )
        row = result.first()
        if row is not None:
            return {
                "title":       row[0],
                "category":    row[2] or habit.category,
                "repeat_type": row[1],
            }

    return {
        "title":       habit.title,
        "category":    habit.category,
        "repeat_type": habit.repeat_type,
    }


async def build_habit_response(db: AsyncSession, habit: Habit) -> dict:
    """`HabitResponse` 호환 dict를 만든다 (title/category/repeat_type은 헬퍼로 해석)."""
    meta = await resolve_habit_meta(db, habit)
    return {
        "id":                  habit.id,
        "user_id":             habit.user_id,
        "group_id":            habit.group_id,
        "title":               meta["title"],
        "category":            meta["category"],
        "time":                habit.time,
        "repeat_type":         meta["repeat_type"],
        "description":         habit.description or "",
        "is_ai_recommended":   habit.is_ai_recommended,
        "is_active":           habit.is_active,
        "is_hidden_from_group": habit.is_hidden_from_group,
        "created_at":          habit.created_at,
        "updated_at":          habit.updated_at,
    }


async def get_habit_or_raise(db: AsyncSession, user_id: int, habit_id: int) -> Habit:
    """습관 조회 + 소유권 검증. 없으면 ValueError."""
    habit = await crud.get_habit(db, habit_id, user_id)
    if not habit:
        raise ValueError("습관을 찾을 수 없습니다")
    return habit


async def get_habits(
    db: AsyncSession, user_id: int, category: str | None = None
) -> list[Habit]:
    return await crud.get_habits(db, user_id, category)


async def create_habit(db: AsyncSession, user_id: int, data: HabitCreate) -> Habit:
    return await crud.create_habit(db, user_id, data)


async def update_habit(
    db: AsyncSession, user_id: int, habit_id: int, data: HabitUpdate
) -> Habit:
    habit = await get_habit_or_raise(db, user_id, habit_id)
    return await crud.update_habit(db, habit, data)


async def deactivate_habit(db: AsyncSession, user_id: int, habit_id: int) -> Habit:
    habit = await get_habit_or_raise(db, user_id, habit_id)
    if habit.group_id is not None:
        raise ValueError("모임 습관은 개별 삭제할 수 없습니다. 모임 탈퇴 시 자동 삭제됩니다.")
    return await crud.deactivate_habit(db, habit)


async def check_habit(
    db: AsyncSession, user_id: int, habit_id: int, checked_date: date
) -> HabitCheck:
    await get_habit_or_raise(db, user_id, habit_id)
    return await crud.check_habit(db, habit_id, checked_date)


async def uncheck_habit(
    db: AsyncSession, user_id: int, habit_id: int, checked_date: date
) -> None:
    await get_habit_or_raise(db, user_id, habit_id)
    if not await crud.uncheck_habit(db, habit_id, checked_date):
        raise ValueError("체크 기록이 없습니다")


async def save_ai_selected_habits(
    db: AsyncSession, user_id: int, selected_habits: list
) -> None:
    """AI 추천 습관 선택 목록을 저장한다."""
    from backend.domains.habits.crud import get_active_habit_titles
    existing = {t.lower() for t in await get_active_habit_titles(db, user_id)}
    selected_habits = [item for item in selected_habits if item.title.lower() not in existing]
    try:
        for item in selected_habits:
            db.add(Habit(
                user_id=user_id,
                title=item.title,
                category=item.category,
                description=item.description,
                repeat_type="매일",
                is_ai_recommended=True,
            ))
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.error(f"습관 저장 중 오류 발생: {e}", exc_info=True)
        raise ValueError("습관 저장 중 오류가 발생했습니다.")
