"""Subprocess wrapper for @larksuite/cli (Go binary / npm package)."""
import asyncio
import json
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
    def __init__(self, cli_path: str = "lark", env: dict[str, str] | None = None):
        self.cli_path = shutil.which(cli_path) or cli_path
        self._base_env = env or os.environ.copy()

    def _env_for_profile(self, profile: str, app_id: str, app_secret: str) -> dict[str, str]:
        env = self._base_env.copy()
        env["LARK_APP_ID"] = app_id
        env["LARK_APP_SECRET"] = app_secret
        return env

    async def _run(self, *args: str, env: dict[str, str] | None = None,
                   timeout: float = 15.0) -> CLIResult:
        cmd = [self.cli_path, *args]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env or self._base_env,
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

    async def send_message(self, profile: str, app_id: str, app_secret: str,
                           chat_id: str, content: str,
                           reply_to: str | None = None) -> CLIResult:
        args = [
            "messenger", "send-message",
            "--profile", profile,
            "--chat-id", chat_id,
            "--content", content,
        ]
        if reply_to:
            args.extend(["--reply-to", reply_to])
        env = self._env_for_profile(profile, app_id, app_secret)
        return await self._run(*args, env=env)

    async def get_history(self, profile: str, app_id: str, app_secret: str,
                          chat_id: str, limit: int = 50) -> CLIResult:
        env = self._env_for_profile(profile, app_id, app_secret)
        return await self._run(
            "messenger", "list-messages",
            "--profile", profile,
            "--chat-id", chat_id,
            "--limit", str(limit),
            "--format", "json",
            env=env,
        )

    async def listen_events(self, profile: str, app_id: str, app_secret: str
                            ) -> asyncio.subprocess.Process:
        """Start long-running event listener via WebSocket. Returns the process handle."""
        env = self._env_for_profile(profile, app_id, app_secret)
        return await asyncio.create_subprocess_exec(
            self.cli_path, "events", "subscribe",
            "--profile", profile,
            "--format", "json",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
