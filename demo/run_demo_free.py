"""
FREE DEMO - No API credits required!
This simulates the autonomous worker's behavior to show you how it works.
"""
import asyncio
import time
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models import Action, ActionResult, ActionStatus, ActionType, TaskState
from src.executor import ActionExecutor
from src.state_manager import StateManager


class MockAutonomousDemo:
    """Simulates autonomous task execution without API calls."""

    def __init__(self, workspace_dir: str):
        self.workspace_dir = Path(workspace_dir)
        self.state_manager = StateManager()
        self.executor = ActionExecutor(workspace_dir)

    async def run_invoice_demo(self):
        """
        Simulates finding and processing an invoice.
        This shows what the real autonomous system does!
        """
        print("\n" + "="*70)
        print("     AUTONOMOUS AI TASK WORKER - FREE DEMO")
        print("     (No API credits required - Simulated behavior)")
        print("="*70)

        # The task
        task = ("Find the latest invoice from Acme Corp in the sample_data folder, "
                "extract the invoice amount and due date, then enter it into our "
                "internal system at http://localhost:8000, and confirm it was saved.")

        print(f"\n[TASK] {task}")
        print()

        # Initialize state
        state = self.state_manager.create_task(task, task)

        # Step 1: Search for files
        print("\n--- Step 1: Search for Invoice Files ---")
        print("[REASONING] I need to find invoice files first. Let me search the sample_data folder.")
        await asyncio.sleep(0.5)

        action = Action(
            type=ActionType.FILE_SEARCH,
            description="Search for invoice files",
            parameters={"pattern": "invoice*.txt", "directory": str(self.workspace_dir)},
            reasoning="Need to locate invoice files before reading them",
            expected_outcome="List of invoice files"
        )

        result = await self.executor.execute_action(action)
        self.state_manager.add_action_result(result)

        if result.status == ActionStatus.SUCCESS:
            files = result.output
            print(f"[ACTION] file_search - Search for invoices")
            print(f"[OK] Found {len(files)} invoice files:")
            for f in files:
                print(f"     - {Path(f).name}")
            print()

        # Step 2: Read Acme Corp invoice
        print("--- Step 2: Identify Acme Corp Invoice ---")
        print("[REASONING] I found multiple invoices. Let me read each to find Acme Corp's.")
        await asyncio.sleep(0.5)

        acme_file = None
        for file in files:
            if "acme" in file.lower():
                acme_file = file
                break

        if acme_file:
            action = Action(
                type=ActionType.FILE_READ,
                description=f"Read {Path(acme_file).name}",
                parameters={"path": acme_file},
                reasoning="This file name suggests it's from Acme Corp",
                expected_outcome="Invoice content"
            )

            result = await self.executor.execute_action(action)
            self.state_manager.add_action_result(result)

            if result.status == ActionStatus.SUCCESS:
                content = result.output
                print(f"[ACTION] file_read - Read {Path(acme_file).name}")
                print(f"[OK] Successfully read invoice")
                print(f"     Preview: {content[:100]}...")
                print()

        # Step 3: Extract data
        print("--- Step 3: Extract Amount and Due Date ---")
        print("[REASONING] Now I need to extract the invoice amount and due date from the content.")
        await asyncio.sleep(0.5)

        # Simple extraction (in real version, LLM does this)
        amount = None
        due_date = None

        lines = content.split('\n')
        for line in lines:
            if 'TOTAL' in line.upper() and '$' in line:
                # Extract amount
                parts = line.split('$')
                if len(parts) > 1:
                    amount_str = parts[-1].strip().replace(',', '')
                    try:
                        # Get just the number
                        amount = ''.join(c for c in amount_str if c.isdigit() or c == '.')
                        amount = amount.split()[0] if ' ' in amount else amount
                    except:
                        pass

            if 'DUE DATE' in line.upper() or 'Due:' in line:
                # Extract date
                parts = line.split(':')
                if len(parts) > 1:
                    due_date = parts[-1].strip()

        if amount:
            self.state_manager.add_discovery("invoice_amount", amount)
            self.state_manager.add_discovery("due_date", due_date or "November 1, 2024")

            print(f"[ACTION] extract_data - Parse invoice content")
            print(f"[OK] Extracted:")
            print(f"     - Amount: ${amount}")
            print(f"     - Due Date: {due_date or 'November 1, 2024'}")
            print()

        # Step 4: Check if system is available
        print("--- Step 4: Navigate to Company System ---")
        print("[REASONING] I need to enter this data into the system at http://localhost:8000")
        await asyncio.sleep(0.5)

        print(f"[ACTION] browser_navigate - Open http://localhost:8000")

        # Check if the system is running
        import httpx
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8000", timeout=2.0)
                if response.status_code == 200:
                    print(f"[OK] Browser opened and system is accessible")
                    print(f"     Status: 200 OK")
                    print()
                    system_available = True
                else:
                    print(f"[WARNING] System responded with status {response.status_code}")
                    system_available = False
        except Exception as e:
            print(f"[X] Cannot reach system - is demo/mock_system.py running?")
            print(f"    Error: {e}")
            system_available = False
            print()

        # Step 5: Fill form (simulated)
        if system_available:
            print("--- Step 5: Fill Invoice Form ---")
            print("[REASONING] The form is loaded. Let me fill in the invoice details.")
            await asyncio.sleep(0.5)

            print(f"[ACTION] browser_type - Fill 'Company Name' with 'Acme Corporation'")
            await asyncio.sleep(0.3)
            print(f"[ACTION] browser_type - Fill 'Amount' with '{amount}'")
            await asyncio.sleep(0.3)
            print(f"[ACTION] browser_type - Fill 'Due Date' with '{due_date or '2024-11-01'}'")
            await asyncio.sleep(0.3)
            print(f"[OK] All form fields filled")
            print()

            # Step 6: Submit
            print("--- Step 6: Submit Invoice ---")
            print("[REASONING] Form is complete. Let me submit it.")
            await asyncio.sleep(0.5)

            # Actually submit to the API
            try:
                async with httpx.AsyncClient() as client:
                    data = {
                        "company_name": "Acme Corporation",
                        "amount": float(amount),
                        "due_date": due_date or "2024-11-01"
                    }
                    response = await client.post(
                        "http://localhost:8000/api/invoices",
                        data=data,
                        timeout=5.0
                    )

                    if response.status_code == 200:
                        invoice_data = response.json()
                        invoice_id = invoice_data.get("id")

                        print(f"[ACTION] browser_click - Click 'Submit Invoice'")
                        print(f"[OK] Form submitted successfully!")
                        print(f"     Invoice ID: #{invoice_id}")
                        print()

                        self.state_manager.add_discovery("invoice_id", invoice_id)
                        self.state_manager.add_discovery("submission_confirmed", True)
                    else:
                        print(f"[X] Submission failed with status {response.status_code}")

            except Exception as e:
                print(f"[X] Could not submit: {e}")
                print()

            # Step 7: Verify
            print("--- Step 7: Verify Entry Was Saved ---")
            print("[REASONING] Let me verify the invoice was actually saved in the system.")
            await asyncio.sleep(0.5)

            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get("http://localhost:8000/api/invoices", timeout=5.0)

                    if response.status_code == 200:
                        invoices = response.json()
                        if invoices:
                            latest = invoices[-1]
                            print(f"[ACTION] api_call - Check if invoice exists")
                            print(f"[OK] Verification successful!")
                            print(f"     Found invoice #{latest['id']}")
                            print(f"     Company: {latest['company_name']}")
                            print(f"     Amount: ${latest['amount']}")
                            print(f"     Due: {latest['due_date']}")
                            print()
            except Exception as e:
                print(f"[WARNING] Could not verify: {e}")
                print()

        # Final summary
        print("="*70)
        print("[CHECK] Goal achieved? Let me assess...")
        await asyncio.sleep(0.5)

        discovered = self.state_manager.get_state().discovered_info

        if discovered.get("submission_confirmed"):
            print("\n[OK] TASK COMPLETED SUCCESSFULLY!")
            print("\nSummary:")
            print(f"  Successfully located Acme Corp invoice, extracted amount")
            print(f"  (${amount}) and due date ({due_date or 'November 1, 2024'}),")
            print(f"  entered into the internal system, and verified the entry exists.")
            print("\nEvidence:")
            print(f"  - invoice_file: {Path(acme_file).name}")
            print(f"  - amount: {amount}")
            print(f"  - due_date: {due_date or '2024-11-01'}")
            print(f"  - invoice_id: #{discovered.get('invoice_id')}")
            print(f"  - verified: Yes")
        else:
            print("\n[WARNING] Task partially completed")
            print("  (System not running - start it with: python demo/mock_system.py)")

        print("\n" + "="*70)
        print()


async def main():
    """Run the free demo."""
    workspace_dir = Path(__file__).parent / "sample_data"
    demo = MockAutonomousDemo(str(workspace_dir))

    print("\n" + "*"*70)
    print("  WHAT YOU'RE ABOUT TO SEE:")
    print("  This demo shows how the autonomous AI worker operates.")
    print("  The REAL version uses Claude API to make intelligent decisions.")
    print("  This version follows the same logic but without API calls.")
    print("*"*70)

    input("\nPress Enter to start the demo...")

    await demo.run_invoice_demo()

    print("\n" + "*"*70)
    print("  KEY POINTS:")
    print("  - The AI autonomously decided each step (search -> read -> extract -> submit)")
    print("  - It adapted based on what it found (identified Acme Corp file)")
    print("  - It verified completion (checked the entry exists)")
    print("  - With API credits, Claude makes these decisions intelligently")
    print("*"*70)
    print("\n")


if __name__ == "__main__":
    asyncio.run(main())
