import pytest
from unittest.mock import MagicMock
from backend.domains.auth import service
from backend.domains.auth.schemas import RegisterRequest, LoginRequest
import jwt

def test_hash_and_verify_password():
    password = "testpassword123"
    hashed = service.hash_password(password)
    assert hashed != password
    assert service.verify_password(password, hashed) is True
    assert service.verify_password("wrongpassword", hashed) is False

def test_register_duplicate_email(monkeypatch):
    # Mocking DB crud
    mock_db = MagicMock()
    mock_crud = MagicMock()
    mock_crud.get_user_by_email.return_value = MagicMock(id=1) # 이미 유저가 존재함
    monkeypatch.setattr("backend.domains.auth.crud", mock_crud)

    data = RegisterRequest(
        email="duplicate@test.com",
        password="password123",
        password_confirm="password123",
        nickname="testnick",
        name="TestUser"
    )
    
    with pytest.raises(ValueError) as excinfo:
        service.register(mock_db, data)
    assert "이미 사용 중인 이메일입니다" in str(excinfo.value)

def test_login_invalid_password(monkeypatch):
    mock_db = MagicMock()
    mock_crud = MagicMock()
    # 유저는 찾았지만 비밀번호가 틀린 상황 가정
    user = MagicMock(password_hash=service.hash_password("correct_password"), is_active=True)
    mock_crud.get_user_by_email.return_value = user
    monkeypatch.setattr("backend.domains.auth.crud", mock_crud)

    data = LoginRequest(email="test@test.com", password="wrong_password")
    with pytest.raises(ValueError) as excinfo:
        service.login(mock_db, data)
    assert "이메일 또는 비밀번호가 올바르지 않습니다" in str(excinfo.value)

def test_update_nickname_duplicate_check(monkeypatch):
    mock_db = MagicMock()
    mock_user = MagicMock(id=1, nickname="old_nick")
    # 다른 사람이 사용 중인 닉네임인 경우
    mock_other_user = MagicMock(id=2, nickname="new_nick")
    
    mock_crud = MagicMock()
    mock_crud.get_user_by_nickname.return_value = mock_other_user
    monkeypatch.setattr("backend.domains.auth.crud", mock_crud)

    with pytest.raises(ValueError, match="이미 사용 중인 닉네임입니다"):
        service.update_nickname(mock_db, mock_user, "new_nick")

    # 본인이 이미 사용 중인 닉네임으로 변경하는 경우 (정상 처리되어야 함)
    mock_crud.get_user_by_nickname.return_value = mock_user
    try:
        service.update_nickname(mock_db, mock_user, "old_nick")
    except ValueError:
        pytest.fail("본인의 기존 닉네임으로 업데이트 시 에러가 발생하면 안 됩니다.")

def test_get_current_user_expired_token(monkeypatch):
    mock_db = MagicMock()
    monkeypatch.setattr("jwt.decode", MagicMock(side_effect=jwt.ExpiredSignatureError))
    
    with pytest.raises(ValueError, match="토큰이 만료되었습니다"):
        service.get_current_user("expired-token", mock_db)
