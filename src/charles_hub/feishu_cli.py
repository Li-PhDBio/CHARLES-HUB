"""Subprocess wrapper for @larksuite/cli (lark-cli)."""
import asyncio
import os
import shutil
from dataclasses import dataclass


@dataclass
class CLIResult:
    success: bool
    stdout: str
    stderr: str
    exit_code: int


class FeishuCLI:
    def __init__(self, cli_path: str = "lark-cli", env: dict[str, str] | None = None):
        self.cli_path = shutil.which(cli_path) or cli_path
        self._base_env = env or os.environ.copy()

    async def _run(self, *args: str, timeout: float = 15.0) -> CLIResult:
        cmd = [self.cli_path, *args]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=self._base_env,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
        except asyncio.TimeoutError:
            proc.kill()
            raise
        return CLIResult(
            success=proc.returncode == 0,
            stdout=stdout.decode("utf-8", errors="replace").strip(),
            stderr=stderr.decode("utf-8", errors="replace").strip(),
            exit_code=proc.returncode or -1,
        )

    async def send_message(self, profile: str, chat_id: str,
                           content: str, reply_to: str | None = None) -> CLIResult:
        if reply_to:
            return await self._run(
                "im", "+messages-reply",
                "--profile", profile,
                "--message-id", reply_to,
                "--text", content,
            )
        return await self._run(
            "im", "+messages-send",
            "--profile", profile,
            "--chat-id", chat_id,
            "--text", content,
        )

    async def send_markdown(self, profile: str, chat_id: str,
                            content: str) -> CLIResult:
        return await self._run(
            "im", "+messages-send",
            "--profile", profile,
            "--chat-id", chat_id,
            "--markdown", content,
        )

    async def get_history(self, profile: str, chat_id: str,
                          limit: int = 50) -> CLIResult:
        return await self._run(
            "im", "+chat-messages-list",
            "--profile", profile,
            "--chat-id", chat_id,
            "--page-size", str(limit),
        )

    async def listen_events(self, profile: str,
                            event_key: str = "im.message.receive_v1"
                            ) -> asyncio.subprocess.Process:
        """Start long-running event consumer. Returns the process handle."""
        return await asyncio.create_subprocess_exec(
            self.cli_path, "event", "consume", event_key,
            "--profile", profile,
            "--quiet",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=self._base_env,
        )
