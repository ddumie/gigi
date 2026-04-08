from pydantic import BaseModel, EmailStr, field_validator, ConfigDict, model_validator
from typing import Optional


# ──────────────────────────────────────────
# 회원가입
# ──────────────────────────────────────────

class RegisterRequest(BaseModel):
    """
    POST /register 요청 바디
    
    프론트에서 2단계로 입력을 받지만
    최종 제출 시 하나의 요청으로 백엔드에 전송됨
    
    1단계: email + password + password_confirm
    2단계: nickname + name + profile_image
    """
    # 1단계 필드
    email: EmailStr                      # Pydantic이 이메일 형식 자동 검증
    password: str                        # 평문 → service.py에서 bcrypt 해싱
    password_confirm: str                # 비밀번호 확인용, DB에 저장 안 함

    # 2단계 필드
    nickname: str                        # unique, 최대 50자
    name: str                            # 실명, 중복 허용
    profile_image: Optional[str] = None # 프로필 이미지 URL, 선택

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        """
        비밀번호 유효성 검사
        기획서 기준: 6자 이상, 종류 제한 없음
        """
        if len(v) < 6:
            raise ValueError("비밀번호는 6자 이상이어야 합니다")
        return v

    @field_validator("nickname")
    @classmethod
    def validate_nickname(cls, v):
        """
        닉네임 유효성 검사
        공백 제거 후 최대 50자
        """
        v = v.strip()
        if not v:
            raise ValueError("닉네임을 입력해주세요")
        if len(v) > 50:
            raise ValueError("닉네임은 50자 이하여야 합니다")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        """
        이름 유효성 검사
        공백 제거 후 비어있으면 에러
        """
        v = v.strip()
        if not v:
            raise ValueError("이름을 입력해주세요")
        if len(v) > 50:
            raise ValueError("이름은 50자 이하여야 합니다")
        return v

    @model_validator(mode='after')
    def check_passwords_match(self):
        if self.password != self.password_confirm:
            raise ValueError("비밀번호가 일치하지 않습니다")
        return self


# ──────────────────────────────────────────
# 중복 확인 (실시간 유효성 안내용)
# 기획서: "이메일·닉네임 실시간 유효성 안내 제공"
# ──────────────────────────────────────────

class EmailCheckRequest(BaseModel):
    """POST /auth/check/email 요청"""
    email: EmailStr

class NicknameCheckRequest(BaseModel):
    nickname: str

    @field_validator("nickname")
    @classmethod
    def validate_nickname(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("닉네임을 입력해주세요")
        return v

class CheckResponse(BaseModel):
    """
    중복 확인 공통 응답
    available=True  → 사용 가능
    available=False → 이미 사용 중
    """
    available: bool
    message: str


# ──────────────────────────────────────────
# 로그인
# ──────────────────────────────────────────

class LoginRequest(BaseModel):
    """POST /login 요청 바디"""
    email: EmailStr
    password: str  # 평문 → service.py에서 bcrypt 검증


# ──────────────────────────────────────────
# 응답 스키마
# ──────────────────────────────────────────

class UserResponse(BaseModel):
    """
    로그인/회원가입 응답 및 GET /me 응답에서 사용
    password_hash 같은 민감 정보는 절대 포함하지 않음
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    nickname: str
    name: str
    profile_image: Optional[str] = None
    is_first_login: bool

class TokenResponse(BaseModel):
    """
    POST /login, POST /register 공통 응답
    프론트에서 access_token을 localStorage 또는 메모리에 저장해서
    이후 요청의 Authorization 헤더에 Bearer {token} 형태로 사용
    """
    access_token: str
    token_type: str = "bearer"
    user: UserResponse               # 로그인 직후 유저 정보 바로 사용할 수 있도록 포함


# ──────────────────────────────────────────
# 비밀번호 변경
# ──────────────────────────────────────────

class PasswordChangeRequest(BaseModel):
    """PUT /auth/password 요청 바디"""
    current_password: str            # 현재 비밀번호 (본인 확인용)
    new_password: str
    new_password_confirm: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v):
        if len(v) < 6:
            raise ValueError("비밀번호는 6자 이상이어야 합니다")
        return v

    @model_validator(mode='after')
    def check_passwords_match(self):
        if self.new_password != self.new_password_confirm:
            raise ValueError("새 비밀번호가 일치하지 않습니다")
        return self