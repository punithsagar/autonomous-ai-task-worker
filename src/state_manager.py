"""
State management for tracking task execution progress.
"""
from typing import Dict, Any, Optional
import json
from pathlib import Path
from datetime import datetime
import uuid

from .models import TaskState, ActionResult, ActionStatus


class StateManager:
    """
    Manages task execution state, including:
    - Discovered information (extracted data, found files, etc.)
    - Action history
    - Current progress
    """

    def __init__(self, state_dir: Optional[Path] = None):
        self.state_dir = state_dir or Path("task_states")
        self.state_dir.mkdir(exist_ok=True)
        self.current_state: Optional[TaskState] = None

    def create_task(self, request: str, goal: Optional[str] = None) -> TaskState:
        """Create a new task state."""
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        self.current_state = TaskState(
            task_id=task_id,
            original_request=request,
            goal=goal or request,
        )
        self._save_state()
        return self.current_state

    def update_state(self, **updates):
        """Update current state fields."""
        if not self.current_state:
            raise RuntimeError("No active task state")

        for key, value in updates.items():
            if hasattr(self.current_state, key):
                setattr(self.current_state, key, value)

        self._save_state()

    def add_discovery(self, key: str, value: Any):
        """Add discovered information."""
        if not self.current_state:
            raise RuntimeError("No active task state")

        self.current_state.add_discovery(key, value)
        self._save_state()

    def add_action_result(self, result: ActionResult):
        """Record an action result."""
        if not self.current_state:
            raise RuntimeError("No active task state")

        self.current_state.add_action_result(result)
        self._save_state()

    def get_context_summary(self) -> str:
        """
        Generate a summary of current state for LLM context.
        This helps the planner understand what has been done and discovered.
        """
        if not self.current_state:
            return "No active task"

        summary = f"Task: {self.current_state.goal}\n\n"

        # Discovered information
        if self.current_state.discovered_info:
            summary += "Discovered Information:\n"
            for key, value in self.current_state.discovered_info.items():
                summary += f"  - {key}: {value}\n"
            summary += "\n"

        # Recent actions
        recent_actions = self.current_state.actions_taken[-5:]  # Last 5 actions
        if recent_actions:
            summary += "Recent Actions:\n"
            for i, result in enumerate(recent_actions, 1):
                status_symbol = "✓" if result.status == ActionStatus.SUCCESS else "✗"
                summary += f"  {status_symbol} {result.action.type.value}: {result.action.description}\n"
                if result.status == ActionStatus.FAILED and result.error:
                    summary += f"      Error: {result.error}\n"
            summary += "\n"

        summary += f"Progress: Step {self.current_state.current_step}\n"

        return summary

    def get_state(self) -> Optional[TaskState]:
        """Get current task state."""
        return self.current_state

    def _save_state(self):
        """Persist state to disk."""
        if not self.current_state:
            return

        state_file = self.state_dir / f"{self.current_state.task_id}.json"
        with open(state_file, 'w') as f:
            json.dump(self.current_state.model_dump(), f, indent=2, default=str)

    def load_state(self, task_id: str) -> TaskState:
        """Load a previous task state."""
        state_file = self.state_dir / f"{task_id}.json"
        if not state_file.exists():
            raise FileNotFoundError(f"Task state not found: {task_id}")

        with open(state_file, 'r') as f:
            data = json.load(f)
            self.current_state = TaskState(**data)
            return self.current_state

    def get_discovered_value(self, key: str) -> Any:
        """Get a specific discovered value."""
        if not self.current_state:
            return None
        return self.current_state.discovered_info.get(key)

    def has_completed_action_type(self, action_type: str) -> bool:
        """Check if an action type has been successfully completed."""
        if not self.current_state:
            return False

        return any(
            result.status == ActionStatus.SUCCESS and result.action.type == action_type
            for result in self.current_state.actions_taken
        )
