"""
Tests for the autonomous task worker.
"""
import pytest
import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models import Action, ActionType, TaskState
from src.state_manager import StateManager
from src.executor import ActionExecutor


class TestStateManager:
    """Test state management functionality."""

    def test_create_task(self):
        """Test task creation."""
        manager = StateManager()
        state = manager.create_task("Test request", "Test goal")

        assert state.original_request == "Test request"
        assert state.goal == "Test goal"
        assert state.current_step == 0
        assert not state.is_complete

    def test_add_discovery(self):
        """Test adding discovered information."""
        manager = StateManager()
        state = manager.create_task("Test", "Test")

        manager.add_discovery("key1", "value1")
        assert manager.get_discovered_value("key1") == "value1"

    def test_context_summary(self):
        """Test context summary generation."""
        manager = StateManager()
        state = manager.create_task("Test task", "Test goal")
        manager.add_discovery("invoice_amount", "1000.00")

        summary = manager.get_context_summary()
        assert "Test goal" in summary
        assert "invoice_amount" in summary


@pytest.mark.asyncio
class TestActionExecutor:
    """Test action execution."""

    async def test_file_search(self):
        """Test file search functionality."""
        executor = ActionExecutor()
        action = Action(
            type=ActionType.FILE_SEARCH,
            description="Search for text files",
            parameters={"pattern": "*.txt", "directory": "."},
            reasoning="Find files",
            expected_outcome="List of files"
        )

        result = await executor.execute_action(action)
        assert result.status in ["success", "failed"]

    async def test_file_read(self, tmp_path):
        """Test file reading."""
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")

        executor = ActionExecutor(tmp_path)
        action = Action(
            type=ActionType.FILE_READ,
            description="Read test file",
            parameters={"path": "test.txt"},
            reasoning="Test reading",
            expected_outcome="File content"
        )

        result = await executor.execute_action(action)
        assert result.status.value == "success"
        assert result.output == "Test content"

    async def test_retry_mechanism(self, tmp_path):
        """Test that executor retries on failure."""
        executor = ActionExecutor(tmp_path)
        action = Action(
            type=ActionType.FILE_READ,
            description="Read non-existent file",
            parameters={"path": "nonexistent.txt"},
            reasoning="Test retry",
            expected_outcome="Should fail"
        )

        result = await executor.execute_action(action, max_retries=2)
        assert result.status.value == "failed"
        assert result.retry_count == 2


class TestModels:
    """Test data models."""

    def test_task_state_creation(self):
        """Test TaskState model."""
        state = TaskState(
            task_id="test123",
            original_request="Do something",
            goal="Accomplish something"
        )

        assert state.task_id == "test123"
        assert state.current_step == 0
        assert not state.is_complete

    def test_add_discovery_to_state(self):
        """Test adding discoveries to state."""
        state = TaskState(
            task_id="test",
            original_request="Test",
            goal="Test"
        )

        state.add_discovery("key", "value")
        assert state.discovered_info["key"] == "value"


def test_action_types():
    """Test that all action types are defined."""
    expected_types = [
        "browser_navigate",
        "browser_click",
        "browser_type",
        "browser_extract",
        "file_read",
        "file_search",
        "file_write",
        "api_call",
        "wait",
        "ask_user"
    ]

    actual_types = [t.value for t in ActionType]
    for expected in expected_types:
        assert expected in actual_types


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
