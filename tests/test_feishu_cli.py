import asyncio
import pytest
from charles_hub.feishu_cli import FeishuCLI, CLIResult


@pytest.fixture
def cli():
    return FeishuCLI(cli_path="echo")


@pytest.mark.asyncio
async def test_send_message_builds_correct_command(cli):
    result = await cli.send_message(
        "zhongshu", "app_id_1", "secret_1",
        "oc_test", "Hello world",
    )
    assert "messenger" in result.stdout
    assert "send-message" in result.stdout
    assert "zhongshu" in result.stdout
    assert "oc_test" in result.stdout
    assert "Hello world" in result.stdout


@pytest.mark.asyncio
async def test_send_message_with_reply(cli):
    result = await cli.send_message(
        "menxia", "app_id_2", "secret_2",
        "oc_test", "驳回", reply_to="msg_123",
    )
    assert "--reply-to" in result.stdout
    assert "msg_123" in result.stdout


@pytest.mark.asyncio
async def test_cli_result_dataclass():
    r = CLIResult(success=True, stdout="ok", stderr="", exit_code=0)
    assert r.success
    assert r.stdout == "ok"
