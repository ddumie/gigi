from datetime import date, datetime, timedelta
from sqlalchemy import func, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from . import models, schemas
from backend.domains.neighbor.models import GroupSearchPost
from backend.domains.auth.models import User
from backend.domains.habits.models import Habit, HabitCheck
from backend.domains.habits.crud import create_group_habit
import secrets, string

# 초대코드 생성
def generate_invitecode(length=4):
    d4code = string.ascii_lowercase + string.digits
    return ''.join(secrets.choice(d4code) for _ in range(length))

async def create_unique_invitecode(db: AsyncSession, prefix="GIGI-", length=4, max_attempts=10):
    for _ in range(max_attempts):
        code_suffix = generate_invitecode(length)
        code = f"{prefix}{code_suffix}"
        result = await db.execute(select(models.InviteCode).where(models.InviteCode.code == code))
        existing = result.scalars().first()
        if not existing:
            return code
    raise ValueError("초대코드 생성 실패")

# 그룹 생성
async def create_group(db: AsyncSession, group: schemas.GroupCreate, user_id: int):
    try:
        db_group = models.Group(
            name=group.name,
            group_type=group.group_type,
            total_support_count=0,
            support_streak=0
        )
        db.add(db_group)

        db_group_profile = models.GroupProfile(
            group_id=db_group.id,
            user_id=user_id,
            name=group.name,
            group_type=group.group_type
        )
        db.add(db_group_profile)

        code = await create_unique_invitecode(db)
        invite = models.InviteCode(
            code=code,
            group_id=db_group.id,
            created_by=user_id,
            is_active=True
        )
        db.add(invite)

        await db.commit()
        await db.refresh(db_group)
        await db.refresh(db_group_profile)
        await db.refresh(invite)

        return db_group
    
    except SQLAlchemyError as e:
        await db.rollback()
        raise e


# 나만 호출하기
async def get_me(db: AsyncSession, group_id: int, user_id: int):
    result = await db.execute(
        select(models.GroupMember).where(models.GroupMember.group_id == group_id,
                                          models.GroupMember.user_id == user_id)
    )
    return result.scalars().first()

# 모임 멤버 호출
async def get_group_members(db: AsyncSession, group_id: int, limit: int, offset: int, exclude_user_id: int):
    result = await db.execute(
        select(models.GroupMember, User.nickname)
        .join(User, User.id == models.GroupMember.user_id)
        .where(models.GroupMember.group_id == group_id,
                models.GroupMember.user_id != exclude_user_id)
        .offset(offset)
        .limit(limit)
    )
    return result.mappings().all()

# 멤버 달성률
async def get_members_achievement(db: AsyncSession, members: list[models.GroupMember]):
    complete_rates = {}

    target_date = date.today()
    user_ids = [m.user_id for m in members]

    habit_count_q = (
        select(Habit.user_id, func.count(Habit.id).label("habit_count"))
        .where(Habit.user_id.in_(user_ids), Habit.is_active == True)
        .group_by(Habit.user_id)
    )
    checked_count_q = (
        select(Habit.user_id, func.count(HabitCheck.id).label("checked_count"))
        .join(Habit, HabitCheck.habit_id == Habit.id)
        .where(
            Habit.user_id.in_(user_ids),
            Habit.is_active == True,
            HabitCheck.checked_date == target_date
        )
        .group_by(Habit.user_id)
    )

    habit_counts = {row.user_id: row.habit_count for row in (await db.execute(habit_count_q)).mappings()}
    checked_counts = {row.user_id: row.checked_count for row in (await db.execute(checked_count_q)).mappings()}

    complete_rates = {
        uid: (checked_counts.get(uid, 0) / habit_counts[uid]) * 100 if habit_counts.get(uid, 0) > 0 else 0
        for uid in user_ids
    }

    return complete_rates

# 설정용 모임 읽어오기
async def get_group_4_settings(db: AsyncSession, group_id: int, user_id: int, limit: int = 10, offset: int = 0):
    result = await db.execute(
        select(models.GroupProfile).where(models.GroupProfile.group_id == group_id,
                                           models.GroupProfile.user_id == user_id)
    )
    groupprofile = result.scalars().first()

    result = await db.execute(select(models.InviteCode).where(models.InviteCode.group_id == group_id))
    invite = result.scalars().first()

    member_top_exp = {}
    member_nicknames = {}
    result = await db.execute(
        select(models.GroupMember, User.nickname, models.Group.total_support_count)
        .join(User, User.id == models.GroupMember.user_id)
        .join(models.Group, models.Group.id == models.GroupMember.group_id)
        .where(models.GroupMember.group_id == group_id)
        .offset(offset)
        .limit(limit)
    )
    rows = result.mappings().all()

    members = [row["GroupMember"] for row in rows]
    member_nicknames = {row["GroupMember"].user_id: row["nickname"] for row in rows}
    member_top_exp = {row["GroupMember"].user_id: row["total_support_count"] for row in rows}

    result = await db.execute(select(models.Group).where(models.Group.id == group_id))
    group = result.scalars().first()

    habit_info = None
    if group and group.post_id:
        result = await db.execute(select(GroupSearchPost).where(GroupSearchPost.post_id == group.post_id))
        post_info = result.scalars().first()
        if post_info:
            habit_info = {
                "habit_title": post_info.habit_title,
                "frequency": post_info.frequency
            }

    return group, groupprofile, invite, members, habit_info, member_top_exp, member_nicknames


# 초대코드로 그룹 ID 조회
async def get_group_id_by_code(db: AsyncSession, invite_code: str):
    result = await db.execute(
        select(models.InviteCode).where(models.InviteCode.code == invite_code,
                                         models.InviteCode.is_active == True)
    )
    invite = result.scalars().first()
    return invite.group_id if invite else None


# 모임 구해요의 post_id로 가입하기
async def get_or_create_group_id_by_post(db: AsyncSession, post_id: int, user_id: int):
    result = await db.execute(select(models.Group).where(models.Group.post_id == post_id))
    group = result.scalars().first()

    if not group:
        try:
            result = await db.execute(select(GroupSearchPost).where(GroupSearchPost.post_id == post_id))
            post_info = result.scalars().first()
            if not post_info:
                return None

            group_setting = schemas.GroupCreate(
                name=post_info.title,
                group_type=post_info.group_type,
            )
            group = await create_group(db, group_setting, user_id)
            group.post_id = post_id

            await db.commit()
            await db.refresh(group)
        
        except SQLAlchemyError as e:
            await db.rollback()
            raise e

    return group.id


# 모임 참가
async def add_group_member(db: AsyncSession, group_id: int, user_id: int):
    try:
        new_member = models.GroupMember(group_id=group_id, user_id=user_id)
        db.add(new_member)

        result = await db.execute(select(models.Group).where(models.Group.id == group_id))
        group = result.scalars().first()

        # 그룹에 post 엮여있으면 습관 생성
        if group and group.post_id:
            result = await db.execute(select(GroupSearchPost).where(GroupSearchPost.post_id == group.post_id))
            post_info = result.scalars().first()
            result = await db.execute(select(GroupSearchPost.category).where(GroupSearchPost.post_id == group.post_id))
            post_category = result.scalar()

            if post_info and post_category:
                await create_group_habit(
                    db=db,
                    user_id=user_id,
                    group_id=group_id,
                    title=post_info.habit_title,
                    category=post_category,
                    repeat_type=post_info.frequency
                )
        await db.commit()
        await db.refresh(new_member)
        return new_member
    
    except SQLAlchemyError as e:
        await db.rollback()
        raise e


# 모임 탈퇴
async def remove_group_member(db: AsyncSession, group_id: int, user_id: int):
    try:
        result = await db.execute(select(Habit).where(Habit.group_id == group_id, Habit.user_id == user_id))
        group_habits = result.scalars().all()
        for habit in group_habits:
            await db.delete(habit)

        result = await db.execute(
            select(models.GroupMember).where(models.GroupMember.group_id == group_id,
                                            models.GroupMember.user_id == user_id)
        )
        member = result.scalars().first()
        if not member:
            return None
        
        await db.delete(member)
        await db.commit()
        return True
    
    except SQLAlchemyError as e:
        await db.rollback()
        raise e

# 모임 정보 수정
async def update_group_profile(db: AsyncSession, group_id: int, user_id: int, group: schemas.GroupCreate):
    try:
        result = await db.execute(
            select(models.GroupProfile).where(models.GroupProfile.group_id == group_id,
                                            models.GroupProfile.user_id == user_id)
        )
        groupprofile = result.scalars().first()
        if not groupprofile:
            return None

        groupprofile.name = group.name
        groupprofile.group_type = group.group_type

        await db.commit()
        await db.refresh(groupprofile)
        return groupprofile
    
    except SQLAlchemyError as e:
        await db.rollback()
        raise e
    
# 지지하기 생성
async def create_support(db: AsyncSession, group_id: int, from_user_id: int, to_user_id: int):
    try:
        support = models.Support(
            group_id=group_id,
            from_user_id=from_user_id,
            to_user_id=to_user_id
        )
        db.add(support)

        result = await db.execute(select(models.Group).where(models.Group.id == group_id))
        group = result.scalars().first()
        if group:
            today = datetime.now().date()

            result = await db.execute(
                select(models.Support)
                .where(models.Support.group_id == group_id)
                .order_by(models.Support.created_at.desc())
            )
            last_support = result.scalars().first()

            if last_support and last_support.created_at.date() == today - timedelta(days=1):
                group.support_streak += 1
            else:
                group.support_streak = 1

            if group.support_streak > group.max_streak:
                group.max_streak = group.support_streak

            group.total_support_count += 1

        await db.commit()
        await db.refresh(support)
        await db.refresh(group)
        return support
    
    except SQLAlchemyError as e:
        await db.rollback()
        raise e

# 오늘 이미 지지했는지 확인
async def check_support_exists(db: AsyncSession, group_id: int, from_user_id: int, to_user_id: int):
    today = date.today()
    result = await db.execute(
        select(models.Support).where(
            models.Support.group_id == group_id,
            models.Support.from_user_id == from_user_id,
            models.Support.to_user_id == to_user_id,
            func.date(models.Support.created_at) == today
        )
    )
    return result.scalars().first()


# 알림 생성
async def create_notification(db: AsyncSession, user_id: int, type: str, content: str):
    try:
        notification = models.Notification(user_id=user_id, type=type, content=content)
        db.add(notification)

        await db.commit()
        await db.refresh(notification)
        return notification
    
    except SQLAlchemyError as e:
        await db.rollback()
        raise e

# 초대코드로 그룹 정보 가져오기
async def get_group_summary(db: AsyncSession, invite_code: str, limit: int = 10, offset: int = 0):
    result = await db.execute(
        select(models.InviteCode).where(models.InviteCode.code == invite_code,
                                         models.InviteCode.is_active == True)
    )
    invite = result.scalars().first()
    if not invite:
        return None

    result = await db.execute(select(models.Group).where(models.Group.id == invite.group_id))
    group = result.scalars().first()
    if not group:
        return None

    nicknames = []
    member_ids = []

    result = await db.execute(
        select(models.GroupMember, User.nickname)
        .join(User, User.id == models.GroupMember.user_id)
        .where(models.GroupMember.group_id == invite.group_id)
        .offset(offset)
        .limit(limit)
    )
    rows = result.mappings().all()
    members = [row["GroupMember"] for row in rows]
    nicknames = [row["nickname"] for row in rows]
    member_ids = [m.user_id for m in members]

    return group, nicknames, member_ids

# uid로 그룹 id 목록 및 내용물, 습관(post 연결 된 경우) 가져오기
async def get_group_ids_by_uid(db: AsyncSession, user_id: int, limit: int = 3, offset: int = 0):
    result = await db.execute(
        select(
            models.GroupMember.group_id,
            models.Group.name,
            models.Group.group_type,
            models.Group.total_support_count,
            models.Group.support_streak,
            models.Group.max_streak,
            models.Group.post_id,
            GroupSearchPost.habit_title,
            GroupSearchPost.frequency
        )
        .join(models.Group, models.Group.id == models.GroupMember.group_id)
        .outerjoin(GroupSearchPost, GroupSearchPost.post_id == models.Group.post_id)
        .where(models.GroupMember.user_id == user_id)
        .offset(offset)
        .limit(limit)
    )
    return result.mappings().all()

# 모임 존재 여부 확인
async def get_group_by_id(db: AsyncSession, group_id: int):
    result = await db.execute(select(models.Group).where(models.Group.id == group_id))
    return result.scalars().first()


# 특정 모임의 특정 맴버 조회
async def get_group_member(db: AsyncSession, group_id: int, user_id: int):
    result = await db.execute(
        select(models.GroupMember).where(models.GroupMember.group_id == group_id,
                                          models.GroupMember.user_id == user_id)
    )
    return result.scalars().first()


# 당일 내가 그룹에 지지한 리스트 반환
async def check_my_support(db: AsyncSession, group_id: int, from_user_id: int):
    today = date.today()
    result = await db.execute(
        select(models.Support).where(
            models.Support.group_id == group_id,
            models.Support.from_user_id == from_user_id,
            models.Support.created_at >= today
        )
    )
    return result.scalars().all()

# 당일 그룹 내 지지 리스트 반환
async def check_group_support(db: AsyncSession, group_id: int):
    today = date.today()
    result = await db.execute(
        select(models.Support).where(
            models.Support.group_id == group_id,
            models.Support.created_at >= today
        )
    )
    return result.scalars().all()

# 전일 그룹 지지 리스트 반환
async def check_group_support_yesterday(db: AsyncSession, group_id: int):
    today = date.today()
    yesterday = today - timedelta(days=1)
    result = await db.execute(
        select(models.Support).where(
            models.Support.group_id == group_id,
            models.Support.created_at >= yesterday,
            models.Support.created_at < today
        )
    )
    return result.scalars().all()


# 스트릭 초기화
async def reset_group_streak(db: AsyncSession, group_id: int):
    try:
        result = await db.execute(select(models.Group).where(models.Group.id == group_id))
        group = result.scalars().first()
        if group:
            group.support_streak = 0
            await db.commit()
            await db.refresh(group)
        return group

    except SQLAlchemyError as e:
        await db.rollback()
        raise e

# 특정 유저 조회
async def get_user_by_id(db: AsyncSession, user_id: int):
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalars().first()


# 안 읽은 알림 가져오기
async def get_unread_notification_count(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(func.count()).select_from(models.Notification).where(
            models.Notification.user_id == user_id,
            models.Notification.is_read == False
        )
    )
    return result.scalar()


# 최근 알림 리스트 가져오기
async def get_recent_notifications(db: AsyncSession, user_id: int, limit: int = 3):
    result = await db.execute(
        select(models.Notification)
        .where(models.Notification.user_id == user_id)
        .order_by(models.Notification.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


# 사용자의 안 읽은 알림 전부 읽음 처리
async def mark_all_notifications_read(db: AsyncSession, user_id: int):
    try:
        result = await db.execute(
            update(models.Notification)
            .where(
                models.Notification.user_id == user_id,
                models.Notification.is_read == False
            )
            .values(is_read=True)
        )

        await db.commit()
        return result.rowcount or 0
    
    except SQLAlchemyError as e:
        await db.rollback()
        raise e

# 지지탭용 개인별 습관 리스트 가져오기
async def get_personal_habits(db: AsyncSession, user_id: int):
    today = date.today()
    result = await db.execute(
        select(
            Habit.id,
            Habit.title,
            Habit.category,
            (HabitCheck.id.isnot(None).label("is_checked"))
        )
        .outerjoin(HabitCheck, (Habit.id == HabitCheck.habit_id) & (HabitCheck.checked_date == today))
        .where(Habit.user_id == user_id , Habit.is_active == True, Habit.is_hidden_from_group == False)
    )
    return result.mappings().all()

# 맴버별 마지막 활동 기록
async def get_members_last_activity(db: AsyncSession, members: list[models.GroupMember]):
    user_ids = [m.user_id for m in members]

    result = await db.execute(
        select(Habit.user_id, func.max(HabitCheck.created_at).label("last_checked"))
        .join(Habit, Habit.id == HabitCheck.habit_id)
        .where(Habit.user_id.in_(user_ids))
        .group_by(Habit.user_id)
    )

    rows = result.mappings().all()
    return {row["user_id"]: row["last_checked"] for row in rows}