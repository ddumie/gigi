from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class GroupCreate(BaseModel):
    name: str
    group_type: str

class GroupParticipate(BaseModel):
    group_id: int
    user_id: int

class GroupResponse(BaseModel):
    id: int
    name: str
    group_type: str
    total_support_count: int
    support_streak: int
    created_at: datetime

class InviteCodeResponse(BaseModel):
    id: int
    code: str
    group_id: int
    created_by: int
    is_activate: bool
    created_at: datetime