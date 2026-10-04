"""
Data models for the autonomous task worker.
"""
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class ActionType(str, Enum):
    """Types of actions the system can take."""
    BROWSER_NAVIGATE = "browser_navigate"
    BROWSER_CLICK = "browser_click"
    BROWSER_TYPE = "browser_type"
    BROWSER_EXTRACT = "browser_extract"
    FILE_READ = "file_read"
    FILE_SEARCH = "file_search"
    FILE_WRITE = "file_write"
    API_CALL = "api_call"
    WAIT = "wait"
    ASK_USER = "ask_user"


class ActionStatus(str, Enum):
    """Status of an executed action."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class Action(BaseModel):
    """An action to be executed."""
    type: ActionType
    description: str
    parameters: Dict[str, Any]
    reasoning: str  # Why this action was chosen
    expected_outcome: str


class ActionResult(BaseModel):
    """Result of an executed action."""
    action: Action
    status: ActionStatus
    output: Any = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    retry_count: int = 0


class TaskState(BaseModel):
    """Current state of task execution."""
    task_id: str
    original_request: str
    goal: str  # Parsed/clarified goal
    discovered_info: Dict[str, Any] = Field(default_factory=dict)
    actions_taken: List[ActionResult] = Field(default_factory=list)
    current_step: int = 0
    is_complete: bool = False
    verification_result: Optional[Dict[str, Any]] = None

    def add_discovery(self, key: str, value: Any):
        """Add discovered information to state."""
        self.discovered_info[key] = value

    def add_action_result(self, result: ActionResult):
        """Record an action result."""
        self.actions_taken.append(result)
        self.current_step += 1

    def get_last_action(self) -> Optional[ActionResult]:
        """Get the most recent action result."""
        return self.actions_taken[-1] if self.actions_taken else None

    def get_successful_actions(self) -> List[ActionResult]:
        """Get all successful actions."""
        return [a for a in self.actions_taken if a.status == ActionStatus.SUCCESS]


class TaskPlan(BaseModel):
    """A plan for executing a task."""
    steps: List[str]
    reasoning: str
    uncertainties: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)


class NextAction(BaseModel):
    """Decision about what to do next."""
    action: Action
    confidence: float = Field(ge=0, le=1)  # 0-1 confidence score
    alternatives: List[Action] = Field(default_factory=list)
    should_ask_user: bool = False
    user_question: Optional[str] = None


class TaskResult(BaseModel):
    """Final result of task execution."""
    task_id: str
    original_request: str
    success: bool
    summary: str
    evidence: Dict[str, Any]  # Proof of completion
    state: TaskState
    execution_time_seconds: float

    def to_user_message(self) -> str:
        """Format result for user display."""
        status = "✓ Task completed successfully" if self.success else "✗ Task failed"
        msg = f"{status}\n\n"
        msg += f"Request: {self.original_request}\n\n"
        msg += f"Summary:\n{self.summary}\n\n"

        if self.evidence:
            msg += "Evidence:\n"
            for key, value in self.evidence.items():
                msg += f"  - {key}: {value}\n"

        msg += f"\nExecution time: {self.execution_time_seconds:.2f}s"
        msg += f"\nActions taken: {len(self.state.actions_taken)}"

        return msg
