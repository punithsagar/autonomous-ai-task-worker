# Autonomous AI Task Worker

An autonomous AI task worker prototype built for the CentrAlign AI challenge.

The system accepts a natural-language goal and attempts to complete it by deciding what actions are required, executing those actions through available tools, tracking state, responding to failures, and verifying whether the requested outcome was actually achieved.

The prototype focuses on a controlled company environment containing invoice files and a simulated internal company system.

---

## What It Does

A user can provide a goal such as:

> Find the latest invoice from Acme Corp, extract the amount and due date, enter it into the internal company system, and confirm that it was saved.

Instead of requiring every individual step to be specified, the worker is designed around the following loop:

```text
User Goal
    |
    v
Orchestrator
    |
    v
Planner
    |
    v
Choose Next Action
    |
    v
Executor
    |
    v
Observe Result
    |
    v
Update State
    |
    +------> Retry / Alternative action
    |
    v
Verify Goal
    |
    v
Return Result + Evidence
```

The core architecture separates planning, execution, and state management so that the system can adapt its next action based on what happened previously.

---

## Key Features

### Autonomous planning

The planner uses Claude to interpret the user's goal and determine the actions required to make progress.

### Real execution

The worker is designed to perform actual operations rather than only describe what should be done.

The prototype includes operations involving:

* Local invoice files
* File discovery and reading
* Data extraction
* Browser interaction
* HTTP/API interaction
* The simulated company system

### State tracking

The state manager keeps track of progress and information discovered during execution so that later actions can use previous observations.

### Failure handling

The execution architecture supports handling failed actions through retries, alternatives, and escalation when the worker cannot safely continue.

### Verification

An action succeeding is not treated as proof that the overall goal succeeded.

The worker performs a separate verification step to check the resulting state and determine whether the requested outcome was actually achieved.

### Generalization

The same core worker can be used for different task descriptions. The prototype includes multiple invoice-processing scenarios to demonstrate this concept.

---

## Project Structure

```text
autonomous-ai-task-worker/
|
├── README.md
├── .env.example
├── .gitignore
├── setup.py
├── install.bat
├── install.sh
├── check_setup.py
|
├── src/
│   ├── __init__.py
│   ├── models.py
│   ├── orchestrator.py
│   ├── planner.py
│   ├── executor.py
│   └── state_manager.py
|
├── demo/
│   ├── mock_system.py
│   ├── run_demo.py
│   ├── run_demo_free.py
│   └── sample_data/
│       ├── invoice_acme_corp_2024_001.txt
│       ├── invoice_global_supplies_latest.txt
│       └── invoice_techsolutions_2024_055.txt
|
├── tests/
│   ├── test_autonomous_worker.py
│   └── test_integration.py
|
└── task_states/
    └── README.md
```

---

## Core Components

### `src/orchestrator.py`

Coordinates the autonomous execution loop.

It connects the goal, planner, executor, state, and verification stages.

### `src/planner.py`

The LLM-based planning component.

It uses Claude to interpret the user's request and determine the next action.

### `src/executor.py`

Executes the selected actions.

The prototype supports operations involving files, browser interaction, and APIs.

### `src/state_manager.py`

Maintains execution state and discovered information.

### `src/models.py`

Contains the data structures used by the worker.

---

## Demo Environment

The project includes a controlled simulated company environment.

### Mock company system

```text
demo/mock_system.py
```

This provides the local internal company application used by the worker.

### Sample invoices

```text
demo/sample_data/
```

contains example invoice files from different companies.

The current demo includes:

* Acme Corporation
* Global Supplies
* TechSolutions

This allows the worker to operate on more than one input scenario.

---

# Running the Project

## Requirements

* Python 3.9+
* Anthropic API key for the real AI-powered version
* Chromium for Playwright/browser automation

Python 3.13 was used during development/testing of the current environment.

---

## 1. Create/activate the virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

---

## 2. Install dependencies

If `requirements.txt` is present:

```powershell
python -m pip install -r requirements.txt
```

Install the additional FastAPI form dependency if required:

```powershell
python -m pip install python-multipart
```

Install Chromium:

```powershell
python -m playwright install chromium
```

---

## 3. Configure the Anthropic API

Copy the example environment file:

```powershell
copy .env.example .env
```

Then add your Anthropic API key to `.env`.

Example:

```text
ANTHROPIC_API_KEY=your_api_key_here
```

Do not commit `.env` to GitHub.

The repository's `.gitignore` excludes `.env`.

---

# Real AI-Powered Demo

The real version uses the Anthropic API for planning.

### Terminal 1

Start the simulated company system:

```powershell
python demo/mock_system.py
```

Leave this terminal running.

### Terminal 2

Activate the environment if necessary:

```powershell
.\.venv\Scripts\Activate.ps1
```

Then run:

```powershell
python demo/run_demo.py
```

The demo provides two scenarios:

1. Invoice processing for Acme Corporation
2. Searching multiple invoices for Global Supplies

The intended flow is:

```text
Find invoice
    ↓
Read invoice
    ↓
Extract information
    ↓
Navigate to company system
    ↓
Enter information
    ↓
Submit
    ↓
Verify saved result
```

---

# Free Demo — No API Credits Required

The repository also includes:

```text
demo/run_demo_free.py
```

This version does **not** call the Anthropic API.

It is provided as a fallback demonstration when API credits are unavailable.

It shows the intended autonomous workflow and execution sequence without requiring an API account or API credits.

Run:

```powershell
python demo/run_demo_free.py
```

The free demo explicitly identifies itself as simulated behavior so that it is not confused with the real Claude-powered execution.

### Important distinction

```text
Real demo
Claude API
     ↓
LLM-based planning
     ↓
Worker execution
     ↓
Verification
```

versus:

```text
Free demo
No API call
     ↓
Demonstration of the same intended workflow
```

The free demo is therefore useful for demonstrating the prototype's flow, but it should not be presented as evidence that Claude performed the planning.

---

# Example Task

The primary task is:

```text
Find the latest invoice from Acme Corp in the sample_data folder,
extract the invoice amount and due date, then enter it into our
internal system and confirm it was saved correctly.
```

The free demonstration shows the following sequence:

```text
1. Search for invoice files
2. Identify the relevant invoice
3. Read the invoice
4. Extract amount and due date
5. Navigate to the internal company system
6. Fill the invoice form
7. Submit the invoice
8. Verify that the invoice was saved
9. Return completion evidence
```

The example execution extracts:

```text
Company: Acme Corporation
Amount: $29160.00
Due Date: November 1, 2024
```

and demonstrates verification of the resulting company record.

---

# Why This Is Autonomous

Traditional automation might hardcode:

```text
search_files("invoice_acme.txt")
read_file("invoice_acme.txt")
extract_amount()
submit_form()
```

The intended worker architecture instead follows:

```text
while the goal is not verified:

    assess current state

    decide the next useful action

    execute the action

    observe the result

    update state

    determine whether the goal has been achieved
```

The important distinction is that planning and execution are separate components.

The worker receives a goal rather than a complete sequence of instructions.

---

# Evaluation Criteria Alignment

The prototype was designed around the main challenge requirements.

| Criterion               | Prototype approach                                               |
| ----------------------- | ---------------------------------------------------------------- |
| Autonomy                | Planner determines actions from the user's goal                  |
| Execution               | Executor performs file, browser, and API operations              |
| Reliability             | Execution architecture supports retries and alternatives         |
| Verification            | Final state is checked separately                                |
| Generalization          | Multiple task scenarios use the same core architecture           |
| Engineering Quality     | Separated planner, executor, state, and orchestration components |
| Product Thinking        | Focuses on completing the user's requested outcome               |
| Technical Understanding | Architecture and design decisions are documented                 |

---

# Known Limitations

This is a prototype rather than a production autonomous worker.

### 1. Controlled environment

The current demonstration operates against a simulated company system and local sample data.

It does not attempt to support arbitrary production websites or enterprise applications.

### 2. Limited tool set

Only the capabilities implemented in the current executor are available.

The system does not yet provide a large general-purpose tool ecosystem.

### 3. LLM dependency

The real autonomous planner depends on access to the Anthropic API.

If the API is unavailable or the account has insufficient credits, the real planning flow cannot execute.

A separate free demonstration is included for this situation.

### 4. Limited business workflows

The prototype focuses primarily on invoice-oriented tasks.

More company processes would require additional tools and execution capabilities.

### 5. Browser/environment assumptions

Browser automation depends on the local Playwright/Chromium environment and the structure of the simulated application.

Changes to the application interface may require executor/tool updates.

### 6. Prototype-level failure handling

The system includes retry/alternative handling, but production deployment would require stronger safeguards, permissions, observability, and recovery mechanisms.

---

# What I Would Build Next

With additional development time, I would extend the worker in the following areas.

### 1. Larger tool ecosystem

Add reusable tools for:

* Customer records
* Orders
* Documents
* Email
* Databases
* Internal APIs
* CRM operations

The goal would be to let the planner compose capabilities rather than creating task-specific workflows.

### 2. Stronger verification

Introduce more robust post-action verification using independent checks against the resulting system state.

### 3. Better failure recovery

Add richer recovery strategies including:

* Retry with modified parameters
* Alternative tools
* Alternative execution paths
* Explicit human approval for risky actions

### 4. Human approval

Add approval checkpoints before irreversible or sensitive operations.

### 5. Persistent memory

Move beyond per-task state and support useful long-term information while keeping task context isolated and controllable.

### 6. Evaluation suite

Create a larger benchmark containing different goals, unexpected failures, ambiguous inputs, and verification cases.

This would make it possible to measure:

* Task completion rate
* Recovery rate
* Verification accuracy
* Number of actions
* Failure frequency
* Cost and latency

### 7. Production deployment

A future version could expose the worker through an API and connect it to real business systems with authentication, permissions, logging, and audit trails.

---

# Assumptions

The prototype makes several deliberate assumptions.

1. The company environment is controlled and safe for autonomous experimentation.

2. Invoice files contain enough structured information for the worker to identify the required fields.

3. The simulated internal company application exposes the functionality required by the demo.

4. Browser automation is an acceptable mechanism for interacting with the simulated company system.

5. The LLM is used for planning and decision-making, while deterministic code handles actual tool execution.

6. Verification should be based on the resulting system state rather than simply trusting that an action returned successfully.

7. The prototype does not need to support every possible business workflow.

8. Human approval is preferable to unsafe autonomous execution when the worker cannot confidently proceed.

---

# Models, APIs, Frameworks and Components

## Model

The real planner uses an Anthropic Claude model through the Anthropic API.

The model is used primarily for interpreting the natural-language task and generating planning decisions.

---

## API

### Anthropic API

Used by:

```text
src/planner.py
```

The API is accessed through the official Python Anthropic SDK.

---

## Python Frameworks / Libraries

### Python

Primary implementation language.

### Pydantic

Used for structured/type-safe data models.

### FastAPI

Used to implement the simulated internal company system.

### Uvicorn

Used to run the local FastAPI application.

### Playwright

Used for browser automation.

### HTTPX

Used for HTTP/API operations.

### python-dotenv

Used to load environment variables such as the Anthropic API key.

---

## Pre-built Components

The project uses established open-source Python libraries rather than implementing browser automation, HTTP handling, API clients, or data validation from scratch.

The simulated company system and task-worker logic are project-specific components created for this prototype.

---

# Testing

The repository contains:

```text
tests/test_autonomous_worker.py
tests/test_integration.py
```

Run the tests with:

```powershell
python -m pytest
```

---

# Security

Never commit your real API key.

The `.env` file is intentionally excluded through `.gitignore`.

Use:

```text
.env.example
```

as the template for configuration.

---

# Project Status

This project is a focused prototype for demonstrating autonomous task execution.

The primary objective is to demonstrate:

```text
Goal
  ↓
Planning
  ↓
Execution
  ↓
Observation
  ↓
Adaptation
  ↓
Verification
  ↓
Evidence
```

rather than attempting to build a production-ready autonomous enterprise platform.

---

## Author

**Punith Sagar**

GitHub:

https://github.com/punithsagar
