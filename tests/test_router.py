from charles_hub.router import MessageRouter


def test_parse_mention_zhongshu():
    router = MessageRouter()
    rm = router.parse("@中书省 请起草入侵物种适生区建模方案", "chat_1", "msg_1", "emperor")
    assert "中书省" in rm.mentioned_bots


def test_route_cc_agent():
    router = MessageRouter()
    rm = router.parse("@中书省 draft strategy", "chat_1", "msg_1", "user")
    action = router.route_action(rm)
    assert action == "ws_cc"


def test_route_hermes_agent():
    router = MessageRouter()
    rm = router.parse("@门下省 review this", "chat_1", "msg_1", "user")
    action = router.route_action(rm)
    assert action == "http_hermes"


def test_route_hub_agent():
    router = MessageRouter()
    rm = router.parse("@尚书省 dispatch tasks", "chat_1", "msg_1", "user")
    action = router.route_action(rm)
    assert action == "hub_internal"


def test_no_mention_is_broadcast():
    router = MessageRouter()
    rm = router.parse("随便聊聊今天的进展", "chat_1", "msg_1", "user")
    assert len(rm.mentioned_bots) == 0
    assert router.route_action(rm) == "broadcast"


def test_emperor_sender():
    router = MessageRouter()
    rm = router.parse("下旨！", "chat_1", "msg_1", "emperor")
    assert rm.target_owner == "emperor"


def test_multi_mention_targets_first():
    router = MessageRouter()
    rm = router.parse("@中书省 @门下省 都来看看", "chat_1", "msg_1", "user")
    assert rm.target_agent is not None
    action = router.route_action(rm)
    assert action in ("ws_cc", "http_hermes", "hub_internal")


def test_clean_content():
    router = MessageRouter()
    rm = router.parse("@中书省 draft a plan", "chat_1", "msg_1", "user")
    assert "draft a plan" in rm.clean_content
    assert "@中书省" not in rm.clean_content
