"""
Action executor that performs concrete actions.
"""
import os
from pathlib import Path
from typing import Any, Optional
import asyncio
from playwright.async_api import async_playwright, Browser, Page
import httpx
import re

from .models import Action, ActionResult, ActionStatus, ActionType


class ActionExecutor:
    """
    Executes actions decided by the planner.
    Handles browser automation, file operations, and API calls.
    """

    def __init__(self, workspace_dir: Optional[Path] = None):
        self.workspace_dir = workspace_dir or Path.cwd()
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright = None

    async def initialize_browser(self):
        """Initialize browser for automation."""
        if not self.browser:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=False)
            self.page = await self.browser.new_page()

    async def cleanup(self):
        """Cleanup resources."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def execute_action(self, action: Action, max_retries: int = 2) -> ActionResult:
        """
        Execute an action and return the result.
        Includes automatic retry logic for transient failures.
        """
        result = ActionResult(
            action=action,
            status=ActionStatus.IN_PROGRESS
        )

        for attempt in range(max_retries + 1):
            try:
                output = await self._execute_by_type(action)
                result.status = ActionStatus.SUCCESS
                result.output = output
                result.retry_count = attempt
                break
            except Exception as e:
                result.error = str(e)
                result.retry_count = attempt

                if attempt < max_retries:
                    # Wait before retry with exponential backoff
                    await asyncio.sleep(2 ** attempt)
                else:
                    result.status = ActionStatus.FAILED

        return result

    async def _execute_by_type(self, action: Action) -> Any:
        """Route action to appropriate handler."""
        handlers = {
            ActionType.BROWSER_NAVIGATE: self._browser_navigate,
            ActionType.BROWSER_CLICK: self._browser_click,
            ActionType.BROWSER_TYPE: self._browser_type,
            ActionType.BROWSER_EXTRACT: self._browser_extract,
            ActionType.FILE_READ: self._file_read,
            ActionType.FILE_SEARCH: self._file_search,
            ActionType.FILE_WRITE: self._file_write,
            ActionType.API_CALL: self._api_call,
            ActionType.WAIT: self._wait,
        }

        handler = handlers.get(action.type)
        if not handler:
            raise ValueError(f"Unknown action type: {action.type}")

        return await handler(action.parameters)

    # Browser actions
    async def _browser_navigate(self, params: dict) -> str:
        """Navigate to a URL."""
        await self.initialize_browser()
        url = params["url"]
        await self.page.goto(url, wait_until="networkidle")
        return f"Navigated to {url}"

    async def _browser_click(self, params: dict) -> str:
        """Click an element."""
        if not self.page:
            raise RuntimeError("Browser not initialized")

        selector = params["selector"]
        await self.page.click(selector)
        return f"Clicked {selector}"

    async def _browser_type(self, params: dict) -> str:
        """Type into a field."""
        if not self.page:
            raise RuntimeError("Browser not initialized")

        selector = params["selector"]
        text = params["text"]
        await self.page.fill(selector, text)
        return f"Typed '{text}' into {selector}"

    async def _browser_extract(self, params: dict) -> Any:
        """Extract information from the page."""
        if not self.page:
            raise RuntimeError("Browser not initialized")

        # Can extract by selector or get all text
        if "selector" in params:
            selector = params["selector"]
            if "attribute" in params:
                attr = params["attribute"]
                value = await self.page.get_attribute(selector, attr)
            else:
                value = await self.page.text_content(selector)
            return value
        else:
            # Extract all text
            content = await self.page.content()
            # Simple text extraction (could be enhanced with BeautifulSoup)
            text = re.sub(r'<[^>]+>', '', content)
            text = re.sub(r'\s+', ' ', text).strip()
            return text[:5000]  # Limit size

    # File operations
    async def _file_read(self, params: dict) -> str:
        """Read a file."""
        file_path = Path(params["path"])
        if not file_path.is_absolute():
            file_path = self.workspace_dir / file_path

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()

    async def _file_search(self, params: dict) -> list:
        """Search for files matching a pattern."""
        pattern = params.get("pattern", "*")
        directory = params.get("directory", ".")

        search_dir = Path(directory)
        if not search_dir.is_absolute():
            search_dir = self.workspace_dir / search_dir

        # Find files matching pattern
        matches = []
        if search_dir.exists():
            for file_path in search_dir.rglob(pattern):
                if file_path.is_file():
                    matches.append(str(file_path.relative_to(self.workspace_dir)))

        return matches

    async def _file_write(self, params: dict) -> str:
        """Write to a file."""
        file_path = Path(params["path"])
        if not file_path.is_absolute():
            file_path = self.workspace_dir / file_path

        content = params["content"]

        # Create directory if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return f"Wrote {len(content)} bytes to {file_path}"

    # API operations
    async def _api_call(self, params: dict) -> Any:
        """Make an API call."""
        url = params["url"]
        method = params.get("method", "GET").upper()
        data = params.get("data")
        headers = params.get("headers", {})

        async with httpx.AsyncClient() as client:
            response = await client.request(method, url, json=data, headers=headers)
            response.raise_for_status()

            # Try to return JSON, fall back to text
            try:
                return response.json()
            except:
                return response.text

    async def _wait(self, params: dict) -> str:
        """Wait for a specified time."""
        seconds = params.get("seconds", 1)
        await asyncio.sleep(seconds)
        return f"Waited {seconds} seconds"


class ExecutorPool:
    """
    Manages a pool of executors for parallel execution.
    """

    def __init__(self):
        self.executors: dict[str, ActionExecutor] = {}

    async def get_executor(self, workspace: str) -> ActionExecutor:
        """Get or create an executor for a workspace."""
        if workspace not in self.executors:
            self.executors[workspace] = ActionExecutor(Path(workspace))
        return self.executors[workspace]

    async def cleanup_all(self):
        """Cleanup all executors."""
        for executor in self.executors.values():
            await executor.cleanup()
