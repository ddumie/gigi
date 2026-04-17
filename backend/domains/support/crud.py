from datetime import date, datetime, timedelta
from sqlalchemy import desc, func
from sqlalchemy.orm import Session
from . import models, schemas
from backend.domains.neighbor.models import GroupSearchPost, FeedPost
from backend.domains.auth.models import User
from backend.domains.habits.models import Habit, HabitCheck
from backend.domains.habits.crud import create_group_habit
import secrets, string

# 메모
# 모임 구해요에서 온 모임에는 GroupSearchPost에서 가져온 habit_title과 frequency를 받아다 출력

# 초대코드 생성 (4자리의 숫자 or 알파벳 소문자)
def generate_invitecode(length = 4):
    d4code = string.ascii_lowercase + string.digits
    return ''.join(secrets.choice(d4code) for _ in range(length))

# 초대코드 생성 (중복 방지)
def create_unique_invitecode(db: Session, prefix="GIGI-", length=4, max_attempts=10):
    for _ in range(max_attempts):
        code_suffix = generate_invitecode(length)
        code = f"{prefix}{code_suffix}"
        existing = db.query(models.InviteCode).filter(models.InviteCode.code == code).first()
        if not existing:
            return code
    raise ValueError("초대코드 생성에 실패했습니다. 다시 시도해주세요.")

# 그룹 생성
def create_group(db: Session, group: schemas.GroupCreate, user_id: int):
    # group 생성
    db_group = models.Group(
        name = group.name,
        group_type = group.group_type,
        total_support_count = 0,
        support_streak = 0
    )
    db.add(db_group)
    db.commit()
    db.refresh(db_group)

    # group_profile 생성
    db_group_profile = models.GroupProfile(
        group_id = db_group.id,
        user_id = user_id,
        name = group.name,
        group_type = group.group_type
    )
    db.add(db_group_profile)
    db.commit()
    db.refresh(db_group_profile)

    # 초대코드 생성
    code = create_unique_invitecode(db)
    invite = models.InviteCode(
        code=code,
        group_id=db_group.id,
        created_by=user_id,
        is_active=True
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)

    return db_group

# 모임 읽어오기
def get_group(db: Session, group_id: int, user_id: int):
    groupprofile = db.query(models.GroupProfile).filter(
        models.GroupProfile.group_id == group_id,
        models.GroupProfile.user_id == user_id
    ).first()

    invite = db.query(models.InviteCode).filter(models.InviteCode.group_id == group_id).first()

    group = db.query(models.Group).filter(models.Group.id == group_id).first()

    # 습관 조회 (Group의 post_id가 None이 아닌 경우만.)
    habit_info = None
    if group and group.post_id:
        post_info = db.query(GroupSearchPost).filter(GroupSearchPost.post_id == group.post_id).first()
        if post_info:
            habit_info = {
                "habit_title": post_info.habit_title,
                "frequency": post_info.frequency
            }

    return group, groupprofile, invite, habit_info


# 나만 호출하기
def get_me(db: Session, group_id: int, user_id: int):
    return db.query(models.GroupMember).filter(
        models.GroupMember.group_id == group_id,
        models.GroupMember.user_id == user_id
    ).first()


# 모임 멤버 별도 호출 (내 기록 제외)
def get_group_members(db: Session, group_id: int, limit: int, offset: int, user_id: int):
    return (
        db.query(models.GroupMember)
        .filter(models.GroupMember.group_id == group_id, models.GroupMember.user_id != user_id)
        .offset(offset)
        .limit(limit)
        .all()
    )

# 특정 멤버 닉네임 조회
def get_member_nickname(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).one_or_none()
    return user.nickname if user else None


# 특정 멤버 달성률 계산
def get_member_complete_rate(db: Session, user_id: int, target_date: date):
    habit_count = db.query(Habit).filter(Habit.user_id == user_id).count()
    checked_count = (
        db.query(HabitCheck)
        .join(Habit, HabitCheck.habit_id == Habit.id)
        .filter(Habit.user_id == user_id, HabitCheck.checked_date == target_date)
        .count()
    )
    return (checked_count / habit_count * 100) if habit_count > 0 else 0


# 여러 멤버 닉네임/달성률 dict 생성
def get_members_info(db: Session, members: list[models.GroupMember]):
    member_nicknames = {}
    complete_rates = {}
    target_date = date.today()

    for m in members:
        nickname = get_member_nickname(db, m.user_id)
        if nickname:
            member_nicknames[m.user_id] = nickname

        complete_rates[m.user_id] = get_member_complete_rate(db, m.user_id, target_date)

    return member_nicknames, complete_rates


# 설정용 모임 읽어오기
def get_group_4_settings(db: Session, group_id: int, user_id: int, limit: int = 10, offset: int = 0):
    groupprofile = db.query(models.GroupProfile).filter(
        models.GroupProfile.group_id == group_id,
        models.GroupProfile.user_id == user_id
    ).first()

    invite = db.query(models.InviteCode).filter(models.InviteCode.group_id == group_id).first()

    members = (
        db.query(models.GroupMember)
        .filter(models.GroupMember.group_id == group_id)
        .offset(offset)
        .limit(limit)
        .all()
    )

    # 습관 조회 (Group의 post_id가 None이 아닌 경우만.)
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    habit_info = None
    if group and group.post_id:
        post_info = db.query(GroupSearchPost).filter(GroupSearchPost.post_id == group.post_id).first()
        if post_info:
            habit_info = {
                "habit_title": post_info.habit_title,
                "frequency": post_info.frequency
            }

    # 각 멤버별 최고 total_support_count 찾기
    member_top_exp = {}
    member_nicknames = {}
    for m in members:
        top_support_row = (
            db.query(models.Group.total_support_count)
            .join(models.GroupMember, models.Group.id == models.GroupMember.group_id)
            .filter(models.GroupMember.user_id == m.user_id)
            .order_by(desc(models.Group.total_support_count))
            .first()
        )
        if top_support_row is not None:
            # 튜플이면 [0], 객체면 속성 접근
            member_top_exp[m.user_id] = getattr(top_support_row, "total_support_count", top_support_row[0])

        user = db.query(User).filter(User.id == m.user_id).one_or_none()
        if user:
            member_nicknames[m.user_id] = user.nickname

    return group, groupprofile, invite, members, habit_info, member_top_exp, member_nicknames


# 초대코드로 그룹 ID 조회
def get_group_id_by_code(db: Session, invite_code: str):
    invite = db.query(models.InviteCode).filter(
        models.InviteCode.code == invite_code,
        models.InviteCode.is_active == True
    ).first()
    if not invite:
        return None
    return invite.group_id

# 모임 구해요의 post_id로 가입하기 (그룹 없으면 그룹도 생성)
def get_or_create_group_id_by_post(db: Session, post_id: int, user_id: int):
    group = db.query(models.Group).filter(models.Group.post_id == post_id).first()
    if not group:
        # GroupSearchPost에서 값 가져와서 넣기
        post_info = db.query(GroupSearchPost).filter(GroupSearchPost.post_id == post_id).first()
        if not post_info:
            return None
        
        group_setting = schemas.GroupCreate(
            name=post_info.title,
            group_type=post_info.group_type,
        )

        group = create_group(db, group_setting, user_id)
        group.post_id = post_id
        db.commit()
        db.refresh(group)

    return group.id

# 모임 참가
def add_group_member(db: Session, group_id: int, user_id: int):
    new_member = models.GroupMember(
        group_id = group_id,
        user_id = user_id
    )
    db.add(new_member)
    db.commit()
    db.refresh(new_member)

    # 습관 추가 (Group의 post_id가 None이 아닌 경우만.)
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    new_habit = None
    if group and group.post_id:
        post_info = db.query(GroupSearchPost).filter(GroupSearchPost.post_id == group.post_id).first()
        post_category = db.query(FeedPost.category).filter(FeedPost.post_id == group.post_id).scalar()

        if post_info and post_category:
            new_habit = create_group_habit(
                db = db,
                user_id = user_id,
                group_id = group_id,
                title = post_info.habit_title,
                category = post_category,
                repeat_type = post_info.frequency
            )

    return new_member

# 모임 탈퇴
def remove_group_member(db: Session, group_id: int, user_id: int):
    # group 습관이 존재 했으면 삭제
    group_habits = db.query(Habit).filter(Habit.group_id == group_id, Habit.user_id == user_id).all()
    for habit in group_habits:
        db.delete(habit)
    
    member = db.query(models.GroupMember).filter(
        models.GroupMember.group_id == group_id,
        models.GroupMember.user_id == user_id
    ).first()
    if not member:
        return None
    db.delete(member)
    db.commit()
    return True

# 모임 정보 수정
def update_group_profile(db: Session, group_id: int, user_id: int, group: schemas.GroupCreate):
    groupprofile = db.query(models.GroupProfile).filter(
        models.GroupProfile.group_id == group_id,
        models.GroupProfile.user_id == user_id
    ).first()
    if not groupprofile:
        return None
    
    groupprofile.name = group.name
    groupprofile.group_type = group.group_type
    db.commit()
    db.refresh(groupprofile)
    return groupprofile

# 지지하기 생성
def create_support(db: Session, group_id: int, from_user_id: int, to_user_id: int):
    support = models.Support(
        group_id=group_id,
        from_user_id=from_user_id,
        to_user_id=to_user_id
    )
    db.add(support)

    # 그룹 streak 갱신
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if group:
        today = datetime.now().date()

        last_supoprt = (
            db.query(models.Support)
            .filter(models.Support.group_id == group_id)
            .order_by(models.Support.created_at.desc())
            .first()
        )
    
        if last_supoprt and last_supoprt.created_at.date() == today - timedelta(days=1):
            group.support_streak += 1
        else:
            group.support_streak = 1

        if group.support_streak > group.max_streak:
            group.max_streak = group.support_streak
        
        group.total_support_count += 1
        
    
    db.commit()
    db.refresh(support)
    db.refresh(group)
    return support

# 오늘 이미 지지했는지 확인
def check_support_exists(db: Session, group_id: int, from_user_id: int, to_user_id: int):
    today = date.today()
    return db.query(models.Support).filter(
        models.Support.group_id == group_id,
        models.Support.from_user_id == from_user_id,
        models.Support.to_user_id == to_user_id,
        func.date(models.Support.created_at) == today
    ).first()

# 알림 생성
def create_notification(db: Session, user_id: int, type: str, content: str):
    notification = models.Notification(
        user_id=user_id,
        type=type,
        content=content
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification

# 초대코드로 그룹 정보 가져오기
def get_group_summary(db: Session, invite_code: str, limit: int = 10, offset: int = 0):
    # 초대코드 확인
    invite = db.query(models.InviteCode).filter(
        models.InviteCode.code == invite_code,
        models.InviteCode.is_active == True
    ).first()
    if not invite:
        return None
    
    # 그룹 조회
    group = db.query(models.Group).filter(models.Group.id == invite.group_id).first()
    if not group:
        return None
    
    # 그룹 맴버 조회 및 닉네임 반환
    members = (
        db.query(models.GroupMember)
        .filter(models.GroupMember.group_id == invite.group_id)
        .offset(offset)
        .limit(limit)
        .all())
    nicknames = []
    member_ids = []
    for m in members:
        user = db.query(User).filter(User.id == m.user_id).first()
        if user:
            nicknames.append(user.nickname)
            member_ids.append(m.user_id)

    return group, nicknames, member_ids
    
# uid로 그룹 id 목록 가져오기
def get_group_ids_by_uid(db: Session, user_id: int, limit: int = 3, offset: int = 0):
    return (
        db.query(models.GroupMember.group_id)
        .filter(models.GroupMember.user_id == user_id)
        .offset(offset)
        .limit(limit)
        .all()
    )

# 모임 존재 여부 확인
def get_group_by_id(db: Session, group_id: int):
    return db.query(models.Group).filter(models.Group.id == group_id).first()

# 특정 모임의 특정 맴버 조회
def get_group_member(db: Session, group_id: int, user_id: int):
    return db.query(models.GroupMember).filter(
        models.GroupMember.group_id == group_id,
        models.GroupMember.user_id == user_id
    ).first()

# 당일 그룹 지지 리스트 반환
def check_group_support(db: Session, group_id: int, from_user_id: int):
    today = date.today()
    return db.query(models.Support).filter(
        models.Support.group_id == group_id,
        models.Support.from_user_id == from_user_id,
        models.Support.created_at >= today
    ).all()

# 전일 그룹 지지 리스트 반환
def check_group_support_yesterday(db: Session, group_id: int, from_user_id: int):
    today = date.today()
    yesterday = today - timedelta(days=1)
    return db.query(models.Support).filter(
        models.Support.group_id == group_id,
        models.Support.from_user_id == from_user_id,
        models.Support.created_at >= yesterday,
        models.Support.created_at < today
    ).all()

# 스트릭 초기화
def reset_group_streak(db: Session, group_id: int):
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if group:
        group.support_streak = 0
        db.commit()
        db.refresh(group)
    return group

# 특정 유저 조회
def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

# 안 읽은 알림 가져오기
def get_unread_notification_count(db: Session, user_id: int):
    return db.query(models.Notification).filter(
        models.Notification.user_id == user_id,
        models.Notification.is_read == False
    ).count()