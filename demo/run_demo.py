"""
Demo runner for the Autonomous AI Task Worker.

This demonstrates the system's ability to:
1. Understand a natural language task
2. Break it down autonomously
3. Execute actions
4. Handle errors
5. Verify completion
"""
import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.orchestrator import AutonomousTaskWorker
from dotenv import load_dotenv


async def main():
    """Run the demo."""
    # Load environment variables
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        print("[ERROR] Error: ANTHROPIC_API_KEY not found in environment")
        print("Please create a .env file with your API key")
        print("See .env.example for the format")
        return

    # Initialize the worker
    print("\n" + "="*70)
    print(" "*15 + "AUTONOMOUS AI TASK WORKER DEMO")
    print("="*70)

    workspace_dir = Path(__file__).parent / "sample_data"
    worker = AutonomousTaskWorker(
        api_key=api_key,
        workspace_dir=str(workspace_dir),
        max_steps=20
    )

    # Demo task scenarios
    scenarios = [
        {
            "name": "Invoice Processing",
            "task": (
                "Find the latest invoice from Acme Corp in the sample_data folder, "
                "extract the invoice amount and due date, "
                "then enter it into our internal system at http://localhost:8000, "
                "and confirm it was saved correctly."
            )
        },
        {
            "name": "Multiple Invoice Search",
            "task": (
                "Search through all invoices in sample_data, "
                "find the one from Global Supplies, "
                "extract the total amount and due date, "
                "and report back what you found."
            )
        }
    ]

    print("\nAvailable demo scenarios:")
    for i, scenario in enumerate(scenarios, 1):
        print(f"  {i}. {scenario['name']}")
        print(f"     Task: {scenario['task'][:80]}...")
        print()

    # Run first scenario
    print("Running Scenario 1: Invoice Processing")
    print("-" * 70)

    try:
        result = await worker.execute_task(scenarios[0]["task"])

        # Display results
        print("\n" + "="*70)
        print("FINAL RESULT")
        print("="*70)
        print(result.to_user_message())

        if result.success:
            print("\n[SUCCESS] Task completed successfully!")
        else:
            print("\n⚠️ Task did not complete fully")

        print(f"\nState saved to: task_states/{result.task_id}.json")

    except Exception as e:
        print(f"\n[ERROR] Error during execution: {e}")
        import traceback
        traceback.print_exc()


async def demo_with_custom_task():
    """Run demo with a custom task from command line."""
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        print("[ERROR] Error: ANTHROPIC_API_KEY not found")
        return

    if len(sys.argv) < 2:
        print("Usage: python run_demo.py \"Your task description here\"")
        return

    task = " ".join(sys.argv[1:])

    workspace_dir = Path(__file__).parent / "sample_data"
    worker = AutonomousTaskWorker(
        api_key=api_key,
        workspace_dir=str(workspace_dir),
        max_steps=25
    )

    print(f"\n[TASK] Executing custom task: {task}\n")

    result = await worker.execute_task(task)
    print("\n" + result.to_user_message())


if __name__ == "__main__":
    print("\n[!] Make sure the mock system is running:")
    print("   python demo/mock_system.py")
    print()
    input("Press Enter to continue...")

    if len(sys.argv) > 1:
        asyncio.run(demo_with_custom_task())
    else:
        asyncio.run(main())
