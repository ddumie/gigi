import pytest
from unittest.mock import AsyncMock, MagicMock
from backend.domains.support import service, schemas

@pytest.mark.asyncio
async def test_create_group_service_success(monkeypatch):
    mock_db = AsyncMock()
    mock_crud = AsyncMock()
    
    # 그룹 생성 성공 시나리오
    mock_group = MagicMock(id=10, name="우리 가족")
    mock_crud.create_group.return_value = mock_group
    # join_group_service가 내부적으로 호출되므로 mock 처리
    monkeypatch.setattr("backend.domains.support.service.join_group_service", AsyncMock())
    monkeypatch.setattr("backend.domains.support.crud", mock_crud)

    group_data = schemas.GroupCreate(name="우리 가족", group_type="가족")
    result = await service.create_group_service(mock_db, group_data, user_id=1)

    assert result["id"] == 10
    mock_crud.create_group.assert_called_once()

@pytest.mark.asyncio
async def test_send_support_self_prevention():
    mock_db = AsyncMock()
    
    # 자기 자신에게 지지 보내기 시도
    with pytest.raises(ValueError) as excinfo:
        await service.send_support_service(
            db=mock_db, 
            group_id=1, 
            from_user_id=100, 
            to_user_id=100
        )
    assert "자기 자신은 지지 할 수 없습니다." in str(excinfo.value)

@pytest.mark.asyncio
async def test_group_summary_already_joined_logic(monkeypatch):
    mock_db = AsyncMock()
    mock_crud = AsyncMock()
    
    # (그룹객체, 닉네임리스트, 멤버ID리스트) 순서로 모킹
    mock_group = MagicMock(id=1, name="가족모임", group_type="가족")
    mock_crud.get_group_summary.return_value = (mock_group, ["아빠", "엄마"], [10, 20])
    monkeypatch.setattr("backend.domains.support.crud", mock_crud)

    # 이미 가입한 유저(10)가 조회할 때
    res1 = await service.group_summary_service(mock_db, "CODE123", user_id=10)
    assert res1["already_joined"] is True

    # 가입하지 않은 유저(30)가 조회할 때
    res2 = await service.group_summary_service(mock_db, "CODE123", user_id=30)
    assert res2["already_joined"] is False

@pytest.mark.asyncio
async def test_groups_info_streak_reset_logic(monkeypatch):
    mock_db = AsyncMock()
    mock_crud = AsyncMock()
    
    # 그룹 데이터: 현재 스트릭이 5지만, 오늘/어제 활동이 전혀 없는 상태 시뮬레이션
    mock_crud.get_group_ids_by_uid.return_value = [{"group_id": 99, "name": "G", "group_type": "T", "total_support_count": 0, "support_streak": 5, "max_streak": 10, "habit_title": "H", "frequency": "F"}]
    mock_crud.get_group_members.return_value = []
    mock_crud.check_my_support.return_value = []
    mock_crud.check_group_support.return_value = []
    mock_crud.check_group_support_yesterday.return_value = []
    
    monkeypatch.setattr("backend.domains.support.crud", mock_crud)
    
    await service.groups_info_service(mock_db, user_id=1)
    
    # 활동이 없어 스트릭 리셋 함수가 호출되었는지 확인
    mock_crud.reset_group_streak.assert_called_once_with(mock_db, 99)
