from charles_hub.meeting import MeetingManager, MeetingType, MeetingPhase


def test_start_morning_court():
    mm = MeetingManager()
    meeting = mm.start_meeting(MeetingType.MORNING_COURT, "shangshu",
                               participants=["zhongshu", "menxia"])
    assert meeting.meeting_type == MeetingType.MORNING_COURT
    assert meeting.host == "shangshu"
    assert "zhongshu" in meeting.participants


def test_meeting_flow():
    mm = MeetingManager()
    meeting = mm.start_meeting(MeetingType.IMPERIAL_COUNCIL, "emperor")
    meeting.open("讨论适生区建模方法")
    assert meeting.phase == MeetingPhase.TOPIC
    meeting.discuss("zhongshu", "建议使用MaxEnt + biomod2")
    assert meeting.phase == MeetingPhase.DISCUSSION
    meeting.decide("采用MaxEnt + biomod2方案")
    assert meeting.phase == MeetingPhase.DECISION
    summary = mm.end_meeting()
    assert summary is not None
    assert "MaxEnt" in summary
    assert "会议纪要" in summary


def test_second_meeting_auto_concludes_first():
    mm = MeetingManager()
    mm.start_meeting(MeetingType.DEPARTMENT_MEETING, "bingbu")
    assert mm.active_meeting.meeting_type == MeetingType.DEPARTMENT_MEETING
    mm.start_meeting(MeetingType.MORNING_COURT, "shangshu")
    assert mm.active_meeting.meeting_type == MeetingType.MORNING_COURT


def test_add_message_to_inactive_meeting():
    mm = MeetingManager()
    mm.add_message("someone", "hello")
    assert mm.active_meeting is None


def test_idle_state():
    mm = MeetingManager()
    assert mm.active_meeting is None
    assert mm.end_meeting() is None
