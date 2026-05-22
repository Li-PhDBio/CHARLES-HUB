import pytest
from charles_hub.storage import Storage


@pytest.fixture
def storage(tmp_path):
    db = tmp_path / "test.db"
    s = Storage(str(db))
    yield s
    s.close()


def test_save_and_search_message(storage):
    storage.save_message("msg_1", "chat_1", "user_a", "Hello @中书省 check this", ["zhongshu"])
    results = storage.search_messages("check")
    assert len(results) == 1
    assert results[0]["content"] == "Hello @中书省 check this"


def test_message_since(storage):
    storage.save_message("msg_1", "chat_1", "user_a", "first", ["zhongshu"])
    storage.save_message("msg_2", "chat_1", "user_b", "second", ["menxia"])
    results = storage.get_messages_since("2020-01-01T00:00:00", "chat_1")
    assert len(results) == 2


def test_agent_status(storage):
    storage.set_agent_status("zhongshu", "online", {"version": "1.0"})
    storage.set_agent_status("menxia", "online")
    statuses = storage.get_all_agent_statuses()
    assert len(statuses) == 2
    zs = [s for s in statuses if s["agent_name"] == "zhongshu"][0]
    assert zs["status"] == "online"


def test_meeting_lifecycle(storage):
    mid = storage.create_meeting("morning_court", "今日待办")
    storage.close_meeting(mid, "完成三项任务")
    assert mid > 0


def test_pending_messages_for_agent(storage):
    storage.save_message("msg_1", "chat_1", "user_a", "@中书省 draft this", ["zhongshu"])
    storage.save_message("msg_2", "chat_1", "user_b", "@门下省 review", ["menxia"])
    results = storage.get_pending_messages_for_agent("zhongshu", "2020-01-01T00:00:00")
    assert len(results) == 1
    assert results[0]["content"] == "@中书省 draft this"


def test_duplicate_message_ignored(storage):
    storage.save_message("msg_1", "chat_1", "user_a", "test", [])
    storage.save_message("msg_1", "chat_1", "user_a", "test", [])
    assert len(storage.search_messages("test")) == 1
