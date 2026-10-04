"""
LLM-based action planner that decides what to do next.
"""
import json
from typing import Optional
from anthropic import Anthropic

from .models import Action, NextAction, TaskPlan, ActionType, TaskState
from .state_manager import StateManager


class ActionPlanner:
    """
    Uses Claude to reason about:
    - What the goal means
    - What to do next based on current state
    - Whether the goal has been achieved
    - When to ask the user for help
    """

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5-20250929-v1:0"):
        self.client = Anthropic(api_key=api_key)
        self.model = model

    def parse_goal(self, user_request: str) -> str:
        """Parse and clarify the user's goal."""
        prompt = f"""You are helping an autonomous AI agent understand what a user wants to accomplish.

User request: "{user_request}"

Parse this request and identify:
1. The ultimate goal (what success looks like)
2. Key information needed
3. Actions required

Respond with ONLY a clear, specific goal statement that captures what needs to be accomplished.

Example:
User: "Find the latest invoice from Company X, extract the amount and due date, enter it into our internal system"
Goal: "Locate the most recent invoice from Company X, extract the invoice amount and due date, and successfully enter these values into the internal invoice tracking system, then verify the entry was saved correctly."

Goal:"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text.strip()

    def create_plan(self, goal: str, state: Optional[TaskState] = None) -> TaskPlan:
        """Create a high-level plan for achieving the goal."""
        context = ""
        if state:
            context = f"\n\nCurrent progress:\n{self._format_state_context(state)}"

        prompt = f"""You are planning how an autonomous AI agent should accomplish a task.

Goal: {goal}{context}

Create a high-level plan with 3-7 steps. Be specific but flexible.
Identify any uncertainties or assumptions.

Respond in JSON format:
{{
    "steps": ["step 1", "step 2", ...],
    "reasoning": "why this approach",
    "uncertainties": ["what might be unclear"],
    "assumptions": ["what we're assuming is true"]
}}"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )

        plan_data = json.loads(response.content[0].text)
        return TaskPlan(**plan_data)

    def decide_next_action(
        self,
        goal: str,
        state: TaskState,
        available_tools: list[str]
    ) -> NextAction:
        """
        Decide what action to take next based on current state.
        This is the core autonomous reasoning loop.
        """
        context = self._format_state_context(state)

        prompt = f"""You are an autonomous AI agent executing a task. Decide what to do next.

Goal: {goal}

Current State:
{context}

Available tools: {', '.join(available_tools)}

Based on what has been done and discovered so far, what should you do next?

Consider:
1. Is there enough information to proceed, or do you need to ask the user?
2. What is the most logical next step toward the goal?
3. Have any previous actions failed that need a different approach?
4. How confident are you in this action?

Respond in JSON format:
{{
    "action": {{
        "type": "ACTION_TYPE",
        "description": "what you're doing",
        "parameters": {{"param": "value"}},
        "reasoning": "why this action",
        "expected_outcome": "what you expect to happen"
    }},
    "confidence": 0.85,
    "should_ask_user": false,
    "user_question": null
}}

Action types available:
- browser_navigate: Navigate to a URL
- browser_click: Click an element (needs selector)
- browser_type: Type into a field (needs selector and text)
- browser_extract: Extract text/data from page (needs selector or description)
- file_read: Read a file (needs path)
- file_search: Search for files (needs pattern/query)
- api_call: Make an API request (needs url, method, data)
- ask_user: Ask the user a question

Guidelines:
- Use file_search before file_read if you don't know the exact path
- Use browser_extract after navigating to get information
- Set should_ask_user=true if you're uncertain or need clarification
- Be specific in parameters (exact selectors, paths, etc.)"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )

        decision_data = json.loads(response.content[0].text)
        action_data = decision_data["action"]
        action_data["type"] = ActionType(action_data["type"].lower())

        return NextAction(
            action=Action(**action_data),
            confidence=decision_data.get("confidence", 0.5),
            should_ask_user=decision_data.get("should_ask_user", False),
            user_question=decision_data.get("user_question")
        )

    def verify_goal_achieved(self, goal: str, state: TaskState) -> dict:
        """
        Verify whether the goal has been achieved.
        This is critical for autonomous systems.
        """
        context = self._format_state_context(state)

        prompt = f"""You are verifying whether an autonomous task has been completed successfully.

Goal: {goal}

Execution History:
{context}

Has the goal been FULLY achieved? Be strict in your assessment.

Respond in JSON format:
{{
    "achieved": true/false,
    "confidence": 0.9,
    "reasoning": "why you believe it is/isn't complete",
    "evidence": {{"key": "value"}},
    "missing": ["what's still needed"]
}}

Guidelines:
- Only return achieved=true if there is clear evidence of success
- Look for verification actions (checking entries, confirming saves, etc.)
- If something was supposed to be saved/entered, was it confirmed?
- List specific evidence that proves completion"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )

        return json.loads(response.content[0].text)

    def suggest_alternative(
        self,
        failed_action: Action,
        error: str,
        state: TaskState
    ) -> Optional[NextAction]:
        """Suggest an alternative approach after a failure."""
        prompt = f"""An autonomous agent tried an action that failed. Suggest an alternative.

Failed action: {failed_action.type.value} - {failed_action.description}
Error: {error}
Reasoning: {failed_action.reasoning}

What else could be tried? Consider:
- Different approach to same goal
- Workaround
- Asking user for help
- Accepting that this path won't work

Respond in JSON with a NextAction or null if no good alternative exists."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )

        result = response.content[0].text.strip()
        if result.lower() == "null" or result == "":
            return None

        data = json.loads(result)
        if not data:
            return None

        data["action"]["type"] = ActionType(data["action"]["type"].lower())
        return NextAction(**data)

    def _format_state_context(self, state: TaskState) -> str:
        """Format state for LLM context."""
        lines = []

        if state.discovered_info:
            lines.append("Discovered:")
            for key, value in state.discovered_info.items():
                value_str = str(value)[:100]  # Truncate long values
                lines.append(f"  - {key}: {value_str}")

        if state.actions_taken:
            lines.append("\nActions taken:")
            for result in state.actions_taken[-10:]:  # Last 10 actions
                status = "✓" if result.status.value == "success" else "✗"
                lines.append(f"  {status} {result.action.type.value}: {result.action.description}")
                if result.output:
                    output_str = str(result.output)[:100]
                    lines.append(f"      → {output_str}")
                if result.error:
                    lines.append(f"      Error: {result.error}")

        return "\n".join(lines) if lines else "No actions taken yet"
