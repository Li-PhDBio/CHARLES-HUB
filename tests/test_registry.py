from charles_hub.registry import AgentRegistry, AgentInfo


def test_builtin_agents_exist():
    reg = AgentRegistry()
    assert reg.get("zhongshu").owner == "claude_code"
    assert reg.get("menxia").owner == "hermes"
    assert reg.get("shangshu").owner == "hub"


def test_list_all_returns_9_builtin():
    reg = AgentRegistry()
    assert len(reg.list_all()) >= 9


def test_list_by_owner():
    reg = AgentRegistry()
    cc_agents = reg.list_by_owner("claude_code")
    assert all(a.owner == "claude_code" for a in cc_agents)
    assert len(cc_agents) == 3  # zhongshu, bingbu, xingbu


def test_set_status():
    reg = AgentRegistry()
    reg.set_status("zhongshu", "online")
    assert reg.get("zhongshu").status == "online"
    assert reg.get("zhongshu").last_seen is not None


def test_who_owns():
    reg = AgentRegistry()
    assert reg.who_owns("zhongshu") == "claude_code"
    assert reg.who_owns("hubu") == "hermes"
    assert reg.who_owns("unknown_bot") == "unknown"


def test_get_status_summary():
    reg = AgentRegistry()
    reg.set_status("zhongshu", "online")
    reg.set_status("menxia", "online")
    summary = reg.get_status_summary()
    assert "✅" in summary
    assert "中书省" in summary
    assert "门下省" in summary


def test_register_custom_agent():
    reg = AgentRegistry()
    custom = AgentInfo("custom_agent", "自定义", "hub", capabilities=["test"])
    reg.register(custom)
    assert reg.get("custom_agent") is not None
    assert len(reg.list_all()) >= 10
