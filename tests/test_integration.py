"""
Integration tests demonstrating key autonomous features.
"""
import pytest
import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.orchestrator import AutonomousTaskWorker
from src.models import ActionType, ActionStatus
from src.state_manager import StateManager


class TestAutonomousFeatures:
    """Test that autonomous features work correctly."""

    def test_state_persistence(self):
        """Test that state is persisted across actions."""
        manager = StateManager()
        state = manager.create_task(
            "Test task",
            "Accomplish something"
        )

        # Add discoveries
        manager.add_discovery("key1", "value1")
        manager.add_discovery("key2", {"nested": "data"})

        # Load state back
        loaded = manager.load_state(state.task_id)

        assert loaded.discovered_info["key1"] == "value1"
        assert loaded.discovered_info["key2"]["nested"] == "data"

    def test_context_summary_generation(self):
        """Test that context summaries are informative."""
        manager = StateManager()
        state = manager.create_task("Test", "Test goal")

        manager.add_discovery("invoice_amount", "1000.00")
        manager.add_discovery("company_name", "Acme Corp")

        summary = manager.get_context_summary()

        assert "Test goal" in summary
        assert "invoice_amount" in summary
        assert "1000.00" in summary

    @pytest.mark.asyncio
    async def test_file_operations_work(self, tmp_path):
        """Test that file operations execute correctly."""
        from src.executor import ActionExecutor
        from src.models import Action

        # Create test file
        test_file = tmp_path / "test_invoice.txt"
        test_file.write_text("Invoice: $500.00\nDue: 2024-11-01")

        executor = ActionExecutor(tmp_path)

        # Test file search
        search_action = Action(
            type=ActionType.FILE_SEARCH,
            description="Find invoice files",
            parameters={"pattern": "*.txt", "directory": "."},
            reasoning="Need to find files",
            expected_outcome="List of files"
        )

        result = await executor.execute_action(search_action)
        assert result.status == ActionStatus.SUCCESS
        assert "test_invoice.txt" in str(result.output)

        # Test file read
        read_action = Action(
            type=ActionType.FILE_READ,
            description="Read invoice",
            parameters={"path": "test_invoice.txt"},
            reasoning="Need content",
            expected_outcome="File content"
        )

        result = await executor.execute_action(read_action)
        assert result.status == ActionStatus.SUCCESS
        assert "$500.00" in result.output

    @pytest.mark.asyncio
    async def test_retry_mechanism_works(self, tmp_path):
        """Test that failed actions are retried."""
        from src.executor import ActionExecutor
        from src.models import Action

        executor = ActionExecutor(tmp_path)

        # Try to read non-existent file
        action = Action(
            type=ActionType.FILE_READ,
            description="Read missing file",
            parameters={"path": "nonexistent.txt"},
            reasoning="Test",
            expected_outcome="Should fail"
        )

        result = await executor.execute_action(action, max_retries=2)

        # Should fail after retries
        assert result.status == ActionStatus.FAILED
        assert result.retry_count == 2

    def test_discovered_info_tracking(self):
        """Test that discovered information is tracked correctly."""
        manager = StateManager()
        state = manager.create_task("Task", "Goal")

        # Simulate discovering information through task execution
        manager.add_discovery("step1_output", "Found 3 files")
        manager.add_discovery("step2_output", "Selected file A")
        manager.add_discovery("extracted_amount", "1234.56")

        # Verify we can retrieve it
        assert manager.get_discovered_value("extracted_amount") == "1234.56"
        assert "step1_output" in manager.get_state().discovered_info

    @pytest.mark.asyncio
    async def test_action_result_includes_context(self, tmp_path):
        """Test that action results include full context."""
        from src.executor import ActionExecutor
        from src.models import Action

        executor = ActionExecutor(tmp_path)

        action = Action(
            type=ActionType.WAIT,
            description="Wait briefly",
            parameters={"seconds": 0.1},
            reasoning="Testing action context",
            expected_outcome="Should wait"
        )

        result = await executor.execute_action(action)

        # Result should include all action details
        assert result.action.description == "Wait briefly"
        assert result.action.reasoning == "Testing action context"
        assert result.status == ActionStatus.SUCCESS

    def test_action_history_is_maintained(self):
        """Test that full action history is preserved."""
        from src.models import Action, ActionResult, ActionType, ActionStatus

        manager = StateManager()
        state = manager.create_task("Task", "Goal")

        # Simulate multiple actions
        for i in range(5):
            action = Action(
                type=ActionType.FILE_SEARCH,
                description=f"Action {i}",
                parameters={},
                reasoning=f"Reason {i}",
                expected_outcome="Output"
            )

            result = ActionResult(
                action=action,
                status=ActionStatus.SUCCESS,
                output=f"Result {i}"
            )

            manager.add_action_result(result)

        # All actions should be in history
        assert len(state.actions_taken) == 5
        assert state.current_step == 5

    def test_successful_actions_can_be_filtered(self):
        """Test that we can identify successful actions."""
        from src.models import Action, ActionResult, ActionType, ActionStatus

        manager = StateManager()
        state = manager.create_task("Task", "Goal")

        # Add mix of successful and failed actions
        for i, status in enumerate([
            ActionStatus.SUCCESS,
            ActionStatus.FAILED,
            ActionStatus.SUCCESS,
            ActionStatus.FAILED,
            ActionStatus.SUCCESS
        ]):
            action = Action(
                type=ActionType.FILE_SEARCH,
                description=f"Action {i}",
                parameters={},
                reasoning="Test",
                expected_outcome="Output"
            )

            result = ActionResult(
                action=action,
                status=status,
                output=f"Result {i}" if status == ActionStatus.SUCCESS else None,
                error="Error" if status == ActionStatus.FAILED else None
            )

            manager.add_action_result(result)

        # Should be able to get only successful actions
        successful = state.get_successful_actions()
        assert len(successful) == 3
        assert all(r.status == ActionStatus.SUCCESS for r in successful)


class TestEndToEnd:
    """End-to-end integration tests."""

    @pytest.mark.asyncio
    async def test_file_processing_workflow(self, tmp_path):
        """Test a complete file processing workflow."""
        from src.executor import ActionExecutor
        from src.models import Action, ActionType

        # Setup: Create test files
        (tmp_path / "invoice1.txt").write_text("Company: Acme\nAmount: $1000")
        (tmp_path / "invoice2.txt").write_text("Company: TechCo\nAmount: $2000")
        (tmp_path / "invoice3.txt").write_text("Company: Acme\nAmount: $1500")

        executor = ActionExecutor(tmp_path)

        # Step 1: Search for files
        search = Action(
            type=ActionType.FILE_SEARCH,
            description="Find invoices",
            parameters={"pattern": "invoice*.txt", "directory": "."},
            reasoning="Need to find files",
            expected_outcome="File list"
        )

        result1 = await executor.execute_action(search)
        assert result1.status == ActionStatus.SUCCESS
        files = result1.output
        assert len(files) == 3

        # Step 2: Read each file
        contents = []
        for file in files:
            read = Action(
                type=ActionType.FILE_READ,
                description=f"Read {file}",
                parameters={"path": file},
                reasoning="Extract data",
                expected_outcome="File content"
            )
            result = await executor.execute_action(read)
            if result.status == ActionStatus.SUCCESS:
                contents.append(result.output)

        # Step 3: Verify we read all files
        assert len(contents) == 3
        assert any("Acme" in c and "$1000" in c for c in contents)
        assert any("TechCo" in c for c in contents)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
