from pydantic import BaseModel
from typing import Optional, List

# 그룹 정보 요청 (초대코드)
class GroupSummary(BaseModel):
    id: int
    name: str
    group_type: str
    members: List[str]   # 닉네임 리스트

# 그룹 생성 요청
class GroupCreate(BaseModel):
    name: str
    group_type: str

class InviteResponse(BaseModel):
    message: str
    group_id: int
    user_id: int

class GroupCreateResponse(BaseModel):
    id: int   # create_group_service 반환값과 일치

class MemberInfo(BaseModel):
    nickname: Optional[str]
    complete_rate: Optional[float]
    supported_today: bool

class GroupInfo(BaseModel):
    id: int
    name: str
    group_type: str
    exp: int
    streak: int
    max_streak: int
    habit: Optional[str]
    frequency: Optional[str]

class GroupListItem(BaseModel):
    group: GroupInfo
    invite: dict   # {"code": str}
    members: List[MemberInfo]

class GroupsResponse(BaseModel):
    groups: List[GroupListItem]

class GroupSettingsMember(BaseModel):
    id: int
    nickname: Optional[str]
    top_exp: Optional[int]

class GroupSettingsInfo(BaseModel):
    id: int
    name: str
    group_type: str
    habit: Optional[str]
    frequency: Optional[str]

class GroupSettingsResponse(BaseModel):
    group: GroupSettingsInfo
    invite: dict   # {"code": str}
    members: List[GroupSettingsMember]

class LeaveResponse(BaseModel):
    message: str
    group_id: int
    user_id: int

class UpdateGroupResponse(BaseModel):
    id: int
    name: str
    group_type: str

class SupportResponse(BaseModel):
    message: str
    support_id: int
    notification_id: int

class JoinByPostResponse(BaseModel):
    message: str
    group_id: int
    user_id: int
