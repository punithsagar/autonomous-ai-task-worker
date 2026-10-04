"""
Main orchestrator that coordinates autonomous task execution.
"""
import asyncio
from typing import Optional, Callable
from datetime import datetime
import time

from .models import TaskResult, ActionStatus, ActionType
from .state_manager import StateManager
from .planner import ActionPlanner
from .executor import ActionExecutor


class AutonomousTaskWorker:
    """
    The main autonomous execution loop.

    This orchestrates:
    1. Understanding the goal
    2. Planning approach
    3. Deciding next actions
    4. Executing actions
    5. Handling failures
    6. Verifying completion
    """

    def __init__(
        self,
        api_key: str,
        workspace_dir: Optional[str] = None,
        max_steps: int = 50,
        user_interaction_callback: Optional[Callable] = None
    ):
        self.state_manager = StateManager()
        self.planner = ActionPlanner(api_key)
        self.executor = ActionExecutor(workspace_dir)
        self.max_steps = max_steps
        self.user_interaction_callback = user_interaction_callback

    async def execute_task(self, user_request: str) -> TaskResult:
        """
        Main entry point: execute a task autonomously.

        This is the core autonomous loop:
        1. Parse goal
        2. While not complete:
            a. Decide next action
            b. Execute action
            c. Handle result
            d. Check if complete
        3. Verify and return result
        """
        start_time = time.time()

        try:
            # Phase 1: Understand the goal
            print(f"\n{'='*60}")
            print(f"[TASK] TASK: {user_request}")
            print(f"{'='*60}\n")

            goal = self.planner.parse_goal(user_request)
            print(f"[GOAL] Parsed Goal: {goal}\n")

            # Initialize state
            state = self.state_manager.create_task(user_request, goal)

            # Phase 2: Create initial plan
            plan = self.planner.create_plan(goal, state)
            print(f"[PLAN]  Plan:")
            for i, step in enumerate(plan.steps, 1):
                print(f"   {i}. {step}")
            print()

            if plan.uncertainties:
                print(f"[WARNING]  Uncertainties: {', '.join(plan.uncertainties)}\n")

            # Phase 3: Autonomous execution loop
            available_tools = [t.value for t in ActionType]

            while not state.is_complete and state.current_step < self.max_steps:
                print(f"\n--- Step {state.current_step + 1} ---")

                # Decide what to do next
                next_action_decision = self.planner.decide_next_action(
                    goal, state, available_tools
                )

                # Check if we need user input
                if next_action_decision.should_ask_user:
                    response = await self._ask_user(next_action_decision.user_question)
                    self.state_manager.add_discovery("user_response", response)
                    continue

                action = next_action_decision.action
                print(f"[REASONING] Reasoning: {action.reasoning}")
                print(f"[ACTION] Action: {action.type.value} - {action.description}")
                print(f"   Confidence: {next_action_decision.confidence:.0%}")

                # Execute the action
                result = await self.executor.execute_action(action)
                self.state_manager.add_action_result(result)

                # Handle result
                if result.status == ActionStatus.SUCCESS:
                    print(f"[OK] Success: {result.output}")

                    # Store any extracted information
                    if action.type == ActionType.BROWSER_EXTRACT or action.type == ActionType.FILE_READ:
                        key = action.parameters.get("store_as", f"extracted_{state.current_step}")
                        self.state_manager.add_discovery(key, result.output)

                elif result.status == ActionStatus.FAILED:
                    print(f"[X] Failed: {result.error}")

                    # Try to find an alternative approach
                    alternative = self.planner.suggest_alternative(
                        action, result.error, state
                    )

                    if alternative:
                        print(f"[RETRY] Trying alternative: {alternative.action.description}")
                        alt_result = await self.executor.execute_action(alternative.action)
                        self.state_manager.add_action_result(alt_result)

                        if alt_result.status == ActionStatus.FAILED:
                            print("[X] Alternative also failed")
                            # Consider asking user
                            if self.user_interaction_callback:
                                response = await self._ask_user(
                                    f"Action failed: {action.description}. Error: {result.error}. How should I proceed?"
                                )
                                self.state_manager.add_discovery("user_guidance", response)

                # Check if goal is achieved
                verification = self.planner.verify_goal_achieved(goal, state)
                print(f"\n[CHECK] Goal achieved? {verification['achieved']} (confidence: {verification['confidence']:.0%})")

                if verification["achieved"] and verification["confidence"] > 0.7:
                    state.is_complete = True
                    state.verification_result = verification
                    self.state_manager.update_state(
                        is_complete=True,
                        verification_result=verification
                    )
                    break

            # Phase 4: Generate final result
            execution_time = time.time() - start_time

            if state.is_complete:
                verification = state.verification_result
                summary = f"Task completed successfully.\n\n{verification['reasoning']}"
                evidence = verification.get("evidence", {})
                success = True
            else:
                summary = f"Task execution stopped after {state.current_step} steps without completion."
                if state.current_step >= self.max_steps:
                    summary += " Reached maximum step limit."
                evidence = {"final_state": "incomplete"}
                success = False

            result = TaskResult(
                task_id=state.task_id,
                original_request=user_request,
                success=success,
                summary=summary,
                evidence=evidence,
                state=state,
                execution_time_seconds=execution_time
            )

            print(f"\n{'='*60}")
            print(result.to_user_message())
            print(f"{'='*60}\n")

            return result

        finally:
            # Cleanup
            await self.executor.cleanup()

    async def _ask_user(self, question: str) -> str:
        """Ask the user a question and wait for response."""
        print(f"\n[?] Question for user: {question}")

        if self.user_interaction_callback:
            return await self.user_interaction_callback(question)
        else:
            # Fallback to console input
            return input("Your response: ")

    def get_task_status(self, task_id: str) -> dict:
        """Get status of a running or completed task."""
        state = self.state_manager.load_state(task_id)
        return {
            "task_id": task_id,
            "goal": state.goal,
            "current_step": state.current_step,
            "is_complete": state.is_complete,
            "actions_taken": len(state.actions_taken),
            "discovered_info": state.discovered_info
        }
