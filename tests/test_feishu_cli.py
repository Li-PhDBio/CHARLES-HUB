import asyncio
import pytest
from charles_hub.feishu_cli import FeishuCLI, CLIResult


@pytest.fixture
def cli():
    return FeishuCLI(cli_path="echo")


@pytest.mark.asyncio
async def test_send_message_builds_correct_command(cli):
    result = await cli.send_message(
        "zhongshu", "oc_test", "Hello world",
    )
    assert "im" in result.stdout
    assert "+messages-send" in result.stdout
    assert "zhongshu" in result.stdout
    assert "oc_test" in result.stdout
    assert "Hello world" in result.stdout


@pytest.mark.asyncio
async def test_send_message_with_reply(cli):
    result = await cli.send_message(
        "menxia", "oc_test", "驳回", reply_to="om_123",
    )
    assert "+messages-reply" in result.stdout
    assert "om_123" in result.stdout


@pytest.mark.asyncio
async def test_send_markdown(cli):
    result = await cli.send_markdown(
        "zhongshu", "oc_test", "**bold**",
    )
    assert "+messages-send" in result.stdout
    assert "--markdown" in result.stdout
    assert "**bold**" in result.stdout


@pytest.mark.asyncio
async def test_cli_result_dataclass():
    r = CLIResult(success=True, stdout="ok", stderr="", exit_code=0)
    assert r.success
    assert r.stdout == "ok"
