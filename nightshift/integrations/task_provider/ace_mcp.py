"""Ace task provider via MCP (Model Context Protocol).

Ace exposes tasks through an MCP server (`@dexagroup/mcp-ace`). This adapter
spawns the server as a subprocess and talks to it over stdio using the Python
`mcp` SDK. The tool names exposed by the server are:

- ``ace_list_tasks``  -> list tasks (optionally filtered by status)
- ``ace_get_task``    -> fetch a single task's full detail
- ``ace_move_task``   -> change a task's status (position/kanban move)

The provider is an async context manager: open it with ``async with`` to keep a
single long-lived MCP session, or call ``connect()`` / ``close()`` explicitly.
"""

from __future__ import annotations

import json
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from nightshift.app.config.logging import get_logger
from nightshift.app.config.settings import Settings
from nightshift.integrations.task_provider.base import ExternalTask, TaskProvider

logger = get_logger(__name__)

ACE_LIST_TASKS = "ace_list_tasks"
ACE_GET_TASK = "ace_get_task"
ACE_MOVE_TASK = "ace_move_task"

# ACE exposes string priorities; Night Shift persists an integer.
_PRIORITY_MAP = {
    "LOW": 25,
    "LOWEST": 25,
    "MEDIUM": 50,
    "NORMAL": 50,
    "HIGH": 75,
    "HIGHEST": 100,
    "CRITICAL": 100,
    "URGENT": 100,
}

_PROJECT_CODE_KEYS = ("project_code", "projectCode", "project")


class AceMcpTaskProvider(TaskProvider):
    name = "ace"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._session: ClientSession | None = None
        self._read_stream: Any = None
        self._write_stream: Any = None
        self._client_ctx: Any = None
        # Maps human-readable ref (e.g. "SUPPLI-T-245") -> ACE UUID.
        self._ref_to_id: dict[str, str] = {}

    # -- lifecycle ---------------------------------------------------------

    async def connect(self) -> None:
        """Spawn the MCP server and open a session."""
        if self._session is not None:
            return

        env = {
            "ACE_BASE_URL": self._settings.ace_base_url,
            "ACE_API_KEY": self._settings.ace_api_key,
            "ACE_GATEWAY_API_KEY": self._settings.ace_gateway_api_key,
        }
        env = {k: v for k, v in env.items() if v}

        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@dexagroup/mcp-ace"],
            env=env,
        )

        self._client_ctx = stdio_client(server_params)
        self._read_stream, self._write_stream = await self._client_ctx.__aenter__()
        self._session = ClientSession(self._read_stream, self._write_stream)
        await self._session.__aenter__()
        await self._session.initialize()

        try:
            tools = await self._session.list_tools()
            tool_names = [t.name for t in tools.tools]
        except Exception:  # noqa: BLE001 - list_tools is best-effort
            tool_names = []
        logger.info("ace_mcp_connected", tools=tool_names)

    async def close(self) -> None:
        """Tear down the session and subprocess."""
        if self._session is not None:
            try:
                await self._session.__aexit__(None, None, None)
            except Exception:  # noqa: BLE001
                logger.warning("ace_mcp_session_close_failed")
            self._session = None
        if self._client_ctx is not None:
            try:
                await self._client_ctx.__aexit__(None, None, None)
            except Exception:  # noqa: BLE001
                logger.warning("ace_mcp_client_close_failed")
            self._client_ctx = None
            self._read_stream = None
            self._write_stream = None

    async def __aenter__(self) -> AceMcpTaskProvider:
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()

    # -- internals ---------------------------------------------------------

    async def _call_tool(self, tool_name: str, arguments: dict | None = None) -> Any:
        try:
            return await self._do_call_tool(tool_name, arguments)
        except Exception as exc:  # noqa: BLE001 - attempt a single reconnect
            logger.warning("ace_mcp_call_failed", tool=tool_name, error=str(exc))
            await self.close()
            await self.connect()
            return await self._do_call_tool(tool_name, arguments)

    async def _do_call_tool(self, tool_name: str, arguments: dict | None = None) -> Any:
        if self._session is None:
            raise RuntimeError("Ace MCP session is not connected")
        result = await self._session.call_tool(tool_name, arguments=arguments or {})
        if not result.content:
            return None
        # The Ace server returns a single JSON text blob.
        for content in result.content:
            text = getattr(content, "text", None)
            if text is None:
                continue
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return text
        return None

    def _map_task(self, raw: dict) -> ExternalTask:
        ref = raw.get("ref") or ""
        ace_id = raw.get("id") or ""
        if ref and ace_id:
            self._ref_to_id[ref] = ace_id
        project_code = _extract_project_code(raw)
        description = raw.get("description")
        if not isinstance(description, str):
            description = ""
        return ExternalTask(
            id=ref or ace_id,
            title=raw.get("title", ref or ace_id),
            description=description,
            project_code=project_code,
            acceptance_criteria=raw.get("acceptance_criteria", []),
            priority=_PRIORITY_MAP.get(raw.get("priority", "MEDIUM"), 50),
            status=raw.get("status", ""),
            metadata=raw,
        )

    # -- TaskProvider interface -------------------------------------------

    async def get_candidates(self) -> list[ExternalTask]:
        raw = await self._call_tool(ACE_LIST_TASKS, {"status": "TODO"})
        if raw is None:
            return []
        tasks = raw if isinstance(raw, list) else raw.get("tasks", [])
        return [self._map_task(t) for t in tasks if t.get("status") == "TODO"]

    async def get_task(self, task_id: str) -> ExternalTask:
        # Resolve ref -> UUID if we have it cached; otherwise pass through.
        api_id = self._ref_to_id.get(task_id, task_id)
        raw = await self._call_tool(ACE_GET_TASK, {"taskId": api_id})
        if not isinstance(raw, dict):
            raise ValueError(f"Ace returned unexpected payload for task {task_id}")
        return self._map_task(raw)

    async def update_status(self, task_id: str, status: str) -> None:
        # ACE's move endpoint expects the task UUID, not the ref.
        api_id = self._ref_to_id.get(task_id)
        if api_id is None:
            try:
                await self.get_task(task_id)
            except Exception as exc:  # noqa: BLE001 - fallback to the supplied ID
                logger.warning(
                    "ace_task_id_resolution_failed",
                    task_id=task_id,
                    error=str(exc),
                )
            api_id = self._ref_to_id.get(task_id, task_id)
        await self._call_tool(
            ACE_MOVE_TASK,
            {"taskId": api_id, "status": status, "position": 0},
        )


async def update_ace_status(
    provider: TaskProvider | None,
    task_id: str,
    status: str,
) -> bool:
    """Best-effort status update to Ace; failures are logged, never raised."""
    if provider is None:
        return False
    try:
        await provider.update_status(task_id, status)
        logger.info("ace_status_updated", task_id=task_id, status=status)
        return True
    except Exception as exc:  # noqa: BLE001 - ACE sync must not fail the workflow
        logger.error(
            "ace_status_update_failed",
            task_id=task_id,
            status=status,
            error=str(exc),
        )
        return False


def _extract_project_code(raw: dict) -> str | None:
    """Read ACE project code across the supported task payload shapes."""
    for key in _PROJECT_CODE_KEYS:
        value = raw.get(key)
        if isinstance(value, dict):
            value = value.get("code") or value.get("key") or value.get("name")
        if isinstance(value, str) and value.strip():
            return value.strip().upper()
    return None
