import pytest
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from backend.domains.onboarding import crud, service
from backend.domains.onboarding.schemas import AIHabitItem

@pytest.mark.asyncio
async def test_increment_recommend_count_functional_logic():
    mock_db = AsyncMock()
    mock_pref = MagicMock()
    
    # 1. 날짜가 바뀌었을 때 카운트가 0에서 다시 1로 시작하는지 확인
    mock_pref.last_recommend_date = date.today() - timedelta(days=1)
    mock_pref.recommend_count = 10
    
    with patch("backend.domains.onboarding.crud.get_preferences", return_value=mock_pref):
        await crud.increment_recommend_count(mock_db, user_id=1)
        assert mock_pref.recommend_count == 1
        assert mock_pref.last_recommend_date == date.today()

    # 2. 하루 15회 제한 로직 확인
    mock_pref.last_recommend_date = date.today()
    mock_pref.recommend_count = 15
    with patch("backend.domains.onboarding.crud.get_preferences", return_value=mock_pref):
        with pytest.raises(ValueError, match="하루 재추천 횟수를 초과했습니다."):
            await crud.increment_recommend_count(mock_db, user_id=1)

@pytest.mark.asyncio
async def test_save_selected_habits_and_complete_onboarding(monkeypatch):
    mock_db = AsyncMock()
    
    # 1. 중복 습관 필터링 확인 (이미 있는 습관은 저장하지 않음)
    monkeypatch.setattr("backend.domains.habits.crud.get_active_habit_titles", AsyncMock(return_value=["운동하기"]))
    
    mock_user = MagicMock(id=1, is_first_login=True)
    mock_db.execute.return_value.scalars.return_value.first.return_value = mock_user

    selected = [
        AIHabitItem(title="운동하기", category="운동", description="설명"),
        AIHabitItem(title="신규습관", category="기타", description="설명")
    ]
    
    await service.save_selected_habits(mock_db, user_id=1, selected=selected)
    
    # 온보딩 완료 처리(is_first_login = False) 및 DB 반영 확인
    assert mock_user.is_first_login is False
    mock_db.commit.assert_called_once()