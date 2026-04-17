from datetime import date, datetime, timedelta
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from . import models, schemas
from backend.domains.neighbor.models import GroupSearchPost, FeedPost
from backend.domains.auth.models import User
from backend.domains.habits.models import Habit, HabitCheck
from backend.domains.habits.crud import create_group_habit
import anyio, secrets, string

# 초대코드 생성
def generate_invitecode(length=4):
    d4code = string.ascii_lowercase + string.digits
    return ''.join(secrets.choice(d4code) for _ in range(length))

async def create_unique_invitecode(db: AsyncSession, prefix="GIGI-", length=4, max_attempts=10):
    for _ in range(max_attempts):
        code_suffix = generate_invitecode(length)
        code = f"{prefix}{code_suffix}"
        result = await db.execute(select(models.InviteCode).filter(models.InviteCode.code == code))
        existing = result.scalars().first()
        if not existing:
            return code
    raise ValueError("초대코드 생성 실패")

# 그룹 생성
async def create_group(db: AsyncSession, group: schemas.GroupCreate, user_id: int):
    db_group = models.Group(
        name=group.name,
        group_type=group.group_type,
        total_support_count=0,
        support_streak=0
    )
    db.add(db_group)
    await db.commit()
    await db.refresh(db_group)

    db_group_profile = models.GroupProfile(
        group_id=db_group.id,
        user_id=user_id,
        name=group.name,
        group_type=group.group_type
    )
    db.add(db_group_profile)
    await db.commit()
    await db.refresh(db_group_profile)

    code = await create_unique_invitecode(db)
    invite = models.InviteCode(
        code=code,
        group_id=db_group.id,
        created_by=user_id,
        is_active=True
    )
    db.add(invite)
    await db.commit()
    await db.refresh(invite)

    return db_group

# 모임 읽어오기
async def get_group(db: AsyncSession, group_id: int, user_id: int):
    result = await db.execute(
        select(models.GroupProfile).filter(models.GroupProfile.group_id == group_id,
                                           models.GroupProfile.user_id == user_id)
    )
    groupprofile = result.scalars().first()

    result = await db.execute(select(models.InviteCode).filter(models.InviteCode.group_id == group_id))
    invite = result.scalars().first()

    result = await db.execute(select(models.Group).filter(models.Group.id == group_id))
    group = result.scalars().first()

    habit_info = None
    if group and group.post_id:
        result = await db.execute(select(GroupSearchPost).filter(GroupSearchPost.post_id == group.post_id))
        post_info = result.scalars().first()
        if post_info:
            habit_info = {
                "habit_title": post_info.habit_title,
                "frequency": post_info.frequency
            }

    return group, groupprofile, invite, habit_info

# 나만 호출하기
async def get_me(db: AsyncSession, group_id: int, user_id: int):
    result = await db.execute(
        select(models.GroupMember).filter(models.GroupMember.group_id == group_id,
                                          models.GroupMember.user_id == user_id)
    )
    return result.scalars().first()

# 모임 멤버 호출
async def get_group_members(db: AsyncSession, group_id: int, limit: int, offset: int, user_id: int):
    result = await db.execute(
        select(models.GroupMember)
        .filter(models.GroupMember.group_id == group_id,
                models.GroupMember.user_id != user_id)
        .offset(offset)
        .limit(limit)
    )
    return result.scalars().all()

# 멤버 닉네임
async def get_member_nickname(db: AsyncSession, user_id: int):
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalars().first()
    return user.nickname if user else None

# 멤버 달성률
async def get_member_complete_rate(db: AsyncSession, user_id: int, target_date: date):
    result = await db.execute(select(func.count()).select_from(Habit).filter(Habit.user_id == user_id, Habit.is_active == True))
    habit_count = result.scalar()

    result = await db.execute(
        select(func.count())
        .select_from(HabitCheck)
        .join(Habit, HabitCheck.habit_id == Habit.id)
        .filter(Habit.user_id == user_id, Habit.is_active == True, HabitCheck.checked_date == target_date)
    )
    checked_count = result.scalar()

    return (checked_count / habit_count * 100) if habit_count > 0 else 0

# 여러 멤버 닉네임/달성률
async def get_members_info(db: AsyncSession, members: list[models.GroupMember]):
    member_nicknames = {}
    complete_rates = {}
    target_date = date.today()

    for m in members:
        nickname = await get_member_nickname(db, m.user_id)
        if nickname:
            member_nicknames[m.user_id] = nickname

        complete_rates[m.user_id] = await get_member_complete_rate(db, m.user_id, target_date)

    return member_nicknames, complete_rates

# 설정용 모임 읽어오기
async def get_group_4_settings(db: AsyncSession, group_id: int, user_id: int, limit: int = 10, offset: int = 0):
    result = await db.execute(
        select(models.GroupProfile).filter(models.GroupProfile.group_id == group_id,
                                           models.GroupProfile.user_id == user_id)
    )
    groupprofile = result.scalars().first()

    result = await db.execute(select(models.InviteCode).filter(models.InviteCode.group_id == group_id))
    invite = result.scalars().first()

    result = await db.execute(
        select(models.GroupMember)
        .filter(models.GroupMember.group_id == group_id)
        .offset(offset)
        .limit(limit)
    )
    members = result.scalars().all()

    result = await db.execute(select(models.Group).filter(models.Group.id == group_id))
    group = result.scalars().first()

    habit_info = None
    if group and group.post_id:
        result = await db.execute(select(GroupSearchPost).filter(GroupSearchPost.post_id == group.post_id))
        post_info = result.scalars().first()
        if post_info:
            habit_info = {
                "habit_title": post_info.habit_title,
                "frequency": post_info.frequency
            }

    member_top_exp = {}
    member_nicknames = {}
    for m in members:
        result = await db.execute(
            select(models.Group.total_support_count)
            .join(models.GroupMember, models.Group.id == models.GroupMember.group_id)
            .filter(models.GroupMember.user_id == m.user_id)
            .order_by(desc(models.Group.total_support_count))
        )
        top_support_row = result.scalars().first()
        if top_support_row is not None:
            member_top_exp[m.user_id] = top_support_row

        result = await db.execute(select(User).filter(User.id == m.user_id))
        user = result.scalars().first()
        if user:
            member_nicknames[m.user_id] = user.nickname

    return group, groupprofile, invite, members, habit_info, member_top_exp, member_nicknames


# 초대코드로 그룹 ID 조회
async def get_group_id_by_code(db: AsyncSession, invite_code: str):
    result = await db.execute(
        select(models.InviteCode).filter(models.InviteCode.code == invite_code,
                                         models.InviteCode.is_active == True)
    )
    invite = result.scalars().first()
    return invite.group_id if invite else None


# 모임 구해요의 post_id로 가입하기
async def get_or_create_group_id_by_post(db: AsyncSession, post_id: int, user_id: int):
    result = await db.execute(select(models.Group).filter(models.Group.post_id == post_id))
    group = result.scalars().first()
    if not group:
        result = await db.execute(select(GroupSearchPost).filter(GroupSearchPost.post_id == post_id))
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

    return group.id


# 모임 참가
async def add_group_member(db: AsyncSession, group_id: int, user_id: int):
    new_member = models.GroupMember(group_id=group_id, user_id=user_id)
    db.add(new_member)
    await db.commit()
    await db.refresh(new_member)

    result = await db.execute(select(models.Group).filter(models.Group.id == group_id))
    group = result.scalars().first()
    if group and group.post_id:
        result = await db.execute(select(GroupSearchPost).filter(GroupSearchPost.post_id == group.post_id))
        post_info = result.scalars().first()
        result = await db.execute(select(FeedPost.category).filter(FeedPost.post_id == group.post_id))
        post_category = result.scalar()

        if post_info and post_category:
            # 비동기 함수인지 확인 후 처리
            if callable(getattr(create_group_habit, "__await__", None)):
                # 이미 async 함수라면 그냥 await
                await create_group_habit(
                    db=db,
                    user_id=user_id,
                    group_id=group_id,
                    title=post_info.habit_title,
                    category=post_category,
                    repeat_type=post_info.frequency
                )
            else:
                # 동기 함수라면 스레드에서 실행
                await anyio.to_thread.run_sync(
                    create_group_habit,
                    db,
                    user_id,
                    group_id,
                    post_info.habit_title,
                    post_category,
                    post_info.frequency
                )
    return new_member


# 모임 탈퇴
async def remove_group_member(db: AsyncSession, group_id: int, user_id: int):
    result = await db.execute(select(Habit).filter(Habit.group_id == group_id, Habit.user_id == user_id))
    group_habits = result.scalars().all()
    for habit in group_habits:
        await db.delete(habit)

    result = await db.execute(
        select(models.GroupMember).filter(models.GroupMember.group_id == group_id,
                                          models.GroupMember.user_id == user_id)
    )
    member = result.scalars().first()
    if not member:
        return None
    await db.delete(member)
    await db.commit()
    return True


# 모임 정보 수정
async def update_group_profile(db: AsyncSession, group_id: int, user_id: int, group: schemas.GroupCreate):
    result = await db.execute(
        select(models.GroupProfile).filter(models.GroupProfile.group_id == group_id,
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

# 지지하기 생성
async def create_support(db: AsyncSession, group_id: int, from_user_id: int, to_user_id: int):
    support = models.Support(
        group_id=group_id,
        from_user_id=from_user_id,
        to_user_id=to_user_id
    )
    db.add(support)

    result = await db.execute(select(models.Group).filter(models.Group.id == group_id))
    group = result.scalars().first()
    if group:
        today = datetime.now().date()

        result = await db.execute(
            select(models.Support)
            .filter(models.Support.group_id == group_id)
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


# 오늘 이미 지지했는지 확인
async def check_support_exists(db: AsyncSession, group_id: int, from_user_id: int, to_user_id: int):
    today = date.today()
    result = await db.execute(
        select(models.Support).filter(
            models.Support.group_id == group_id,
            models.Support.from_user_id == from_user_id,
            models.Support.to_user_id == to_user_id,
            func.date(models.Support.created_at) == today
        )
    )
    return result.scalars().first()


# 알림 생성
async def create_notification(db: AsyncSession, user_id: int, type: str, content: str):
    notification = models.Notification(user_id=user_id, type=type, content=content)
    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    return notification


# 초대코드로 그룹 정보 가져오기
async def get_group_summary(db: AsyncSession, invite_code: str, limit: int = 10, offset: int = 0):
    result = await db.execute(
        select(models.InviteCode).filter(models.InviteCode.code == invite_code,
                                         models.InviteCode.is_active == True)
    )
    invite = result.scalars().first()
    if not invite:
        return None

    result = await db.execute(select(models.Group).filter(models.Group.id == invite.group_id))
    group = result.scalars().first()
    if not group:
        return None

    result = await db.execute(
        select(models.GroupMember)
        .filter(models.GroupMember.group_id == invite.group_id)
        .offset(offset)
        .limit(limit)
    )
    members = result.scalars().all()

    nicknames = []
    member_ids = []
    for m in members:
        result = await db.execute(select(User).filter(User.id == m.user_id))
        user = result.scalars().first()
        if user:
            nicknames.append(user.nickname)
            member_ids.append(m.user_id)

    return group, nicknames, member_ids

# uid로 그룹 id 목록 가져오기
async def get_group_ids_by_uid(db: AsyncSession, user_id: int, limit: int = 3, offset: int = 0):
    result = await db.execute(
        select(models.GroupMember.group_id)
        .filter(models.GroupMember.user_id == user_id)
        .offset(offset)
        .limit(limit)
    )
    return result.all()

# 모임 존재 여부 확인
async def get_group_by_id(db: AsyncSession, group_id: int):
    result = await db.execute(select(models.Group).filter(models.Group.id == group_id))
    return result.scalars().first()


# 특정 모임의 특정 맴버 조회
async def get_group_member(db: AsyncSession, group_id: int, user_id: int):
    result = await db.execute(
        select(models.GroupMember).filter(models.GroupMember.group_id == group_id,
                                          models.GroupMember.user_id == user_id)
    )
    return result.scalars().first()


# 당일 그룹 지지 리스트 반환
async def check_group_support(db: AsyncSession, group_id: int, from_user_id: int):
    today = date.today()
    result = await db.execute(
        select(models.Support).filter(
            models.Support.group_id == group_id,
            models.Support.from_user_id == from_user_id,
            models.Support.created_at >= today
        )
    )
    return result.scalars().all()


# 전일 그룹 지지 리스트 반환
async def check_group_support_yesterday(db: AsyncSession, group_id: int, from_user_id: int):
    today = date.today()
    yesterday = today - timedelta(days=1)
    result = await db.execute(
        select(models.Support).filter(
            models.Support.group_id == group_id,
            models.Support.from_user_id == from_user_id,
            models.Support.created_at >= yesterday,
            models.Support.created_at < today
        )
    )
    return result.scalars().all()


# 스트릭 초기화
async def reset_group_streak(db: AsyncSession, group_id: int):
    result = await db.execute(select(models.Group).filter(models.Group.id == group_id))
    group = result.scalars().first()
    if group:
        group.support_streak = 0
        await db.commit()
        await db.refresh(group)
    return group


# 특정 유저 조회
async def get_user_by_id(db: AsyncSession, user_id: int):
    result = await db.execute(select(User).filter(User.id == user_id))
    return result.scalars().first()


# 안 읽은 알림 가져오기
async def get_unread_notification_count(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(func.count()).select_from(models.Notification).filter(
            models.Notification.user_id == user_id,
            models.Notification.is_read == False
        )
    )
    return result.scalar()