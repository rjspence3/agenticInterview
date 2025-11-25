# Agentic Interview System - Project Context

## Project Summary

The **Agentic Interview System** is an MVP for conducting automated technical interviews using multiple cooperating AI agents. The system simulates an interview workflow where questions are served, candidate answers are evaluated against ground truth, and a final assessment is generated.

### Key Personas

1. **Interviewer (Question Author)**
   - Creates and edits interview questions
   - Defines competencies, difficulty levels, and ground-truth keypoints
   - Manages the question bank

2. **Interviewee (Candidate)**
   - Steps through interview questions one at a time
   - Submits text answers
   - Receives per-question scores and feedback
   - Gets a final summary at the end

### Core Agents

The system is composed of three specialized agents:

1. **OrchestratorAgent**
   - Controls the interview flow (which question to serve, when to stop)
   - Manages interview state and progression
   - Coordinates between QuestionsAgent and EvaluatorAgent
   - Generates final summary

2. **QuestionsAgent**
   - Manages the question bank
   - Serves questions in sequence
   - Provides access to question metadata (competency, difficulty, keypoints)

3. **EvaluatorAgent**
   - Compares candidate answers against ground-truth keypoints
   - Produces scores (0-100) and qualitative feedback
   - **MVP: Uses simple heuristic (string matching)**
   - **Design goal: Easy to swap to LLM-based evaluation later**

### Current Scope (MVP)

**In Scope:**
- Single Streamlit app with two views (Interviewer and Interviewee)
- Create/edit questions with keypoints
- Sequential question flow
- Heuristic evaluation (keyword matching against keypoints)
- Per-question scoring and feedback
- Final summary generation
- In-memory storage (session state)

**Explicitly Out of Scope:**
- Database persistence
- User authentication
- Multiple concurrent interviews
- LLM-based evaluation (comes later)
- Question randomization or adaptive difficulty
- Audio/video recording
- Real-time collaboration

## Technical Stack & Constraints

### Core Technologies

- **Python**: 3.10+
- **UI Framework**: Streamlit
- **Storage**: In-memory (Streamlit session state for MVP)
- **Testing**: pytest
- **Dependencies**: Minimal (Streamlit + standard library for MVP)

### Architectural Constraints

1. **Clean Separation of Concerns**
   - `models.py`: Data classes (Question, EvaluationResult, InterviewState)
   - `agents.py`: Business logic (QuestionsAgent, EvaluatorAgent, OrchestratorAgent)
   - `app.py`: UI layer (Streamlit components and state management)

2. **No Database for MVP**
   - Use Streamlit session state for runtime storage
   - Questions and state live only during the session
   - Accept data loss on page refresh (acceptable for MVP)

3. **Evaluator Agent Extensibility**
   - EvaluatorAgent must have a clean interface
   - Implementation must be swappable (heuristic → LLM)
   - Ground truth keypoints are the evaluation contract
   - Current heuristic: case-insensitive substring matching

4. **Pure Python Agent Logic**
   - Agents should be testable without Streamlit
   - No Streamlit imports in `models.py` or `agents.py`
   - UI layer orchestrates agents but doesn't contain business logic

## High-Level Architecture

### Data Models

**Question**
- `id`: Unique identifier
- `text`: Question content
- `competency`: String (e.g., "Python", "System Design")
- `difficulty`: String (e.g., "Easy", "Medium", "Hard")
- `keypoints`: List of strings (ground truth for evaluation)

**EvaluationResult**
- `question_id`: Reference to evaluated question
- `candidate_answer`: The submitted answer text
- `score`: Integer 0-100
- `feedback`: Qualitative text explaining the score
- `matched_keypoints`: List of keypoints found in answer

**InterviewState**
- `questions`: List of Questions to ask
- `current_index`: Which question we're on
- `evaluations`: List of EvaluationResults
- `is_complete`: Boolean flag
- `final_summary`: Generated when complete

### Agent Responsibilities

**QuestionsAgent**
- Holds the question bank (list of Questions)
- Provides questions by index or ID
- Validates question data
- (Future: could generate questions dynamically)

**EvaluatorAgent**
- Takes a Question and candidate answer
- Compares answer against keypoints (heuristic for MVP)
- Returns EvaluationResult with score and feedback
- **Interface design allows future LLM swap**

**OrchestratorAgent**
- Initializes InterviewState with selected questions
- Advances to next question
- Invokes EvaluatorAgent for each answer
- Determines when interview is complete
- Generates final summary from all evaluations

### Interview Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    INTERVIEWER VIEW                          │
│  1. Create questions (text, competency, difficulty, keypoints)│
│  2. View/edit question bank                                  │
│  3. Questions stored in session state                        │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    INTERVIEWEE VIEW                          │
│  1. OrchestratorAgent initializes InterviewState             │
│  2. QuestionsAgent serves current question                   │
│  3. Candidate submits answer                                 │
│  4. EvaluatorAgent scores answer vs keypoints                │
│  5. OrchestratorAgent stores evaluation                      │
│  6. Repeat steps 2-5 until all questions done                │
│  7. OrchestratorAgent generates final summary                │
│  8. Display scores, feedback, and summary                    │
└─────────────────────────────────────────────────────────────┘
```

## LLM Evaluator Design (Phase 5)

### Overview

The system will support **pluggable evaluators** with a stable interface, allowing seamless switching between heuristic and LLM-based evaluation strategies.

**Two Evaluator Implementations:**

1. **EvaluatorAgent (Heuristic)** - Current MVP implementation
   - Simple case-insensitive substring matching against keypoints
   - Deterministic, fast, no external dependencies
   - Used as the default for unit tests (no network calls)
   - Serves as baseline for comparison and offline operation

2. **LLMEvaluatorAgent (Future)** - AI-powered evaluation
   - Uses OpenAI or Anthropic APIs for sophisticated answer assessment
   - Semantic understanding of answers (not just keyword matching)
   - Nuanced feedback generation
   - Context-aware follow-up question suggestions

**Key Design Principle**: Both evaluators expose the **identical public interface**:

```python
def evaluate(self, question: Question, answer: str) -> EvaluationResult
```

This allows the orchestrator and UI to swap evaluators without code changes—only the instantiation differs.

### Evaluator Selection

The Streamlit UI will provide a simple toggle mechanism:

- **Sidebar control**: Radio button or selectbox for "Evaluator Mode"
  - Option 1: "Heuristic (Fast, Offline)"
  - Option 2: "LLM-Powered (Requires API Key)"
- Based on selection, `app.py` instantiates the appropriate evaluator class
- Unit tests **always use heuristic** to avoid network dependencies and non-determinism
- Integration tests can optionally use mocked LLM responses

### Config & Secrets Management

**Critical Security Requirement**: API keys and secrets must NEVER be committed to version control.

**Approach**:

1. **Environment Variables via `.env`**
   - Create a `.env` file (git-ignored) for local development:
     ```
     OPENAI_API_KEY=sk-...
     ANTHROPIC_API_KEY=sk-ant-...
     LLM_MODEL=gpt-4
     LLM_TEMPERATURE=0.3
     ```
   - Use `python-dotenv` to load these into `os.environ`

2. **Settings Module** (`settings.py` or `llm_config.py`)
   - Centralize configuration reading:
     ```python
     import os
     from dotenv import load_dotenv

     load_dotenv()

     OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
     ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
     LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")  # or "anthropic"
     LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4")
     LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))
     ```
   - Validate that required keys are present before allowing LLM mode

3. **Git Safety**
   - `.gitignore` must include:
     ```
     .env
     .env.*
     *.key
     secrets/
     ```
   - Add `.env.example` (committed) showing required variables without actual values:
     ```
     OPENAI_API_KEY=your_key_here
     ANTHROPIC_API_KEY=your_key_here
     LLM_MODEL=gpt-4
     LLM_TEMPERATURE=0.3
     ```

4. **UI Key Validation**
   - When user selects "LLM-Powered" mode:
     - Check if API key is configured
     - If missing, show error: "Please configure API key in .env file"
     - Provide link to documentation on setup

### Prompting Strategy

The LLM evaluator will use a structured prompt that mimics expert human evaluation.

**Prompt Structure**:

```
You are an expert technical interviewer evaluating a candidate's answer.

QUESTION:
{question.text}

COMPETENCY: {question.competency}
DIFFICULTY: {question.difficulty}

GROUND TRUTH KEYPOINTS (the candidate should cover these):
{numbered list of keypoints}

CANDIDATE'S ANSWER:
{answer}

TASK:
1. For each keypoint, determine if it was adequately covered in the answer.
   - Mark as "covered" if the concept is present (even if phrased differently)
   - Provide a brief evidence snippet showing where it was covered (or note if missing)

2. Assign an overall score from 0-100 based on:
   - Keypoint coverage (primary factor)
   - Depth of explanation
   - Accuracy of information
   - Clarity of communication

3. Classify mastery level:
   - "strong": 80-100 points (comprehensive understanding)
   - "mixed": 50-79 points (partial understanding, gaps present)
   - "weak": 0-49 points (significant gaps or misconceptions)

4. Generate short feedback (2-3 sentences) explaining the score and what was strong/weak.

5. If score < 80 and some keypoints were covered, suggest ONE follow-up question to probe the missing concepts.

OUTPUT FORMAT (strict JSON):
{
  "keypoints_coverage": [
    {"keypoint": "...", "covered": true, "evidence": "..."},
    ...
  ],
  "score": 75,
  "mastery_label": "mixed",
  "feedback": "...",
  "suggested_followup": "..."
}
```

**Prompt Engineering Considerations**:

- **Few-shot examples**: Add 1-2 example evaluations in the prompt for consistency
- **Temperature**: Use low temperature (0.2-0.4) for deterministic, consistent scoring
- **Output format**: Request JSON for reliable parsing
- **Scoring rubric**: Explicitly define what each score range means
- **Edge cases**: Handle very short answers, off-topic answers, refusals to answer

**Response Parsing**:

- Parse JSON response from LLM
- Map to `EvaluationResult` dataclass fields
- Handle malformed responses gracefully (fallback to heuristic or return error)
- Log prompt and response for debugging (redact sensitive info)

### Evaluation Quality & Governance

**Problem**: LLMs can be inconsistent. We need safeguards to ensure evaluation quality.

**Solution: Evaluation Regression Test Set**

1. **Create Reference Dataset** (`tests/fixtures/eval_reference_set.json`)
   - 10-15 curated Q&A pairs with ground-truth expected bands
   - Cover various scenarios:
     - Perfect answer (all keypoints) → "strong"
     - Good but incomplete (most keypoints) → "mixed"
     - Poor answer (few keypoints) → "weak"
     - Off-topic answer → "weak"
     - Very short answer → depends on content
   - Each entry includes:
     ```json
     {
       "question": {...},
       "answer": "...",
       "expected_band": "strong",  // or "mixed" or "weak"
       "expected_score_min": 80,
       "expected_score_max": 100,
       "notes": "Perfect answer covering all keypoints clearly"
     }
     ```

2. **Regression Tests** (`tests/test_llm_eval_regression.py`)
   - Load reference set
   - Run each Q&A through `LLMEvaluatorAgent` (with mocked responses initially)
   - Assert:
     - Mastery label matches expected band
     - Score falls within expected range
     - All keypoints are correctly identified as covered/not covered
   - Flag if LLM behavior changes unexpectedly (e.g., after prompt modifications)

3. **A/B Comparison**
   - Run same reference set through both heuristic and LLM evaluators
   - Compare scores and identify discrepancies
   - Helps validate that LLM is genuinely more accurate (not just more verbose)

4. **Monitoring & Logging**
   - Log all LLM evaluations (prompt, response, latency, cost)
   - Track aggregate stats: average score, distribution of mastery labels
   - Alert if sudden changes in behavior (e.g., all answers scoring <50)

5. **Human Review Loop** (Post-MVP)
   - Allow interviewers to review and override LLM scores
   - Collect human feedback to refine prompts
   - Build a dataset of human-labeled evaluations for fine-tuning

**Validation Before Production Use**:

Before using `LLMEvaluatorAgent` with real candidates:

✅ Reference set passes with >90% agreement on mastery band
✅ Prompt is tested with diverse answer styles (verbose, terse, technical, casual)
✅ Edge cases handled gracefully (empty answers, non-English, gibberish)
✅ Costs are acceptable (<$0.10 per interview)
✅ Latency is acceptable (<5 seconds per question)

### LLM Client Architecture

To keep code maintainable and provider-agnostic:

1. **Thin Abstraction Layer** (`llm_client.py`)
   - Wraps provider-specific SDKs (OpenAI, Anthropic, etc.)
   - Provides unified interface:
     ```python
     def call_llm(prompt: str, model: str, temperature: float) -> str:
         """Returns LLM response text."""
     ```
   - Handles retries, rate limiting, error handling
   - Abstracts away provider differences (message formats, auth)

2. **Provider Implementations**
   - `OpenAIClient`: Uses `openai` library
   - `AnthropicClient`: Uses `anthropic` library
   - Factory pattern to select provider based on config

3. **Mocking for Tests**
   - Create `MockLLMClient` that returns canned responses
   - Tests use mock by default (no real API calls)
   - Integration tests can opt into real LLM calls with env var flag

**Dependencies to Add** (when implementing Phase 5):
- `openai>=1.0.0` (if using OpenAI)
- `anthropic>=0.8.0` (if using Anthropic)
- `python-dotenv>=1.0.0` (for .env loading)
- `pydantic>=2.0.0` (optional, for robust config validation)

### Migration Path

**Step 1: Add Infrastructure**
- Create `settings.py`, `llm_client.py`, `.env.example`
- Add new dependencies to `requirements.txt`
- Update `.gitignore`

**Step 2: Implement `LLMEvaluatorAgent`**
- Same interface as `EvaluatorAgent`
- Construct prompt from question + keypoints + answer
- Call LLM via client
- Parse response and return `EvaluationResult`

**Step 3: Add UI Toggle**
- Sidebar evaluator selection
- Instantiate appropriate evaluator based on selection
- Show API key status and configuration help

**Step 4: Create Test Fixtures**
- Build reference evaluation set
- Add regression tests with mocked LLM responses
- Validate prompt correctness

**Step 5: Manual Testing**
- Test with real API keys on known questions
- Compare LLM vs heuristic results
- Refine prompt based on quality

**Step 6: Documentation**
- Update README with LLM setup instructions
- Document prompt design decisions
- Add troubleshooting guide for API errors

## File Map

### Current Structure (MVP Complete)

```
agenticInterview/
├── claude.md                    # This file: project context
├── plan.md                      # Implementation plan with phases
├── requirements.txt             # Python dependencies
├── app.py                       # Streamlit entrypoint
├── models.py                    # Data classes (Question, EvaluationResult, InterviewState)
├── agents.py                    # Agent classes (QuestionsAgent, EvaluatorAgent, OrchestratorAgent)
└── tests/
    ├── __init__.py
    └── test_basic_flow.py       # Unit tests for agents and flow
```

### Planned Structure (After Phase 5)

```
agenticInterview/
├── claude.md                    # Project context
├── plan.md                      # Implementation plan
├── requirements.txt             # Python dependencies
├── .env.example                 # Example environment variables (committed)
├── .env                         # Actual API keys (git-ignored)
├── .gitignore                   # Ignore secrets and cache files
├── app.py                       # Streamlit entrypoint
├── models.py                    # Data classes
├── agents.py                    # Heuristic evaluator + base agents
├── llm_evaluator.py             # LLM-based evaluator
├── llm_client.py                # LLM API client abstraction
├── settings.py                  # Configuration and environment variables
└── tests/
    ├── __init__.py
    ├── test_basic_flow.py       # Unit tests (heuristic evaluator)
    ├── test_llm_evaluator.py    # LLM evaluator tests (mocked)
    ├── test_llm_eval_regression.py  # Regression tests with reference set
    └── fixtures/
        └── eval_reference_set.json  # Ground truth Q&A pairs
```

### File Descriptions

**Current Files:**
- **`app.py`**: Streamlit UI with two views (Interviewer, Interviewee). Manages session state and renders forms/results.
- **`models.py`**: Dataclasses for Question, EvaluationResult, InterviewState, KeypointCoverage. Pure data, no logic.
- **`agents.py`**: QuestionsAgent, EvaluatorAgent (heuristic), OrchestratorAgent. No Streamlit dependencies.
- **`requirements.txt`**: Minimal deps (streamlit, pytest).
- **`tests/test_basic_flow.py`**: Pure Python test simulating an interview without UI.

**Phase 5 Additions:**
- **`llm_evaluator.py`**: LLMEvaluatorAgent class with same interface as EvaluatorAgent. Calls LLM API for evaluation.
- **`llm_client.py`**: Thin wrapper around OpenAI/Anthropic SDKs. Handles API calls, retries, errors.
- **`settings.py`**: Loads configuration from environment variables. Validates API keys.
- **`.env.example`**: Template showing required environment variables (safe to commit).
- **`.env`**: Actual API keys and secrets (never committed).
- **`tests/test_llm_evaluator.py`**: Tests for LLM evaluator using mocked responses.
- **`tests/test_llm_eval_regression.py`**: Regression tests using reference evaluation set.
- **`tests/fixtures/eval_reference_set.json`**: Curated Q&A pairs with expected evaluation bands.

## Dev Workflow

### Initial Setup

1. Review `claude.md` (this file) for project context
2. Review `plan.md` for implementation phases
3. Create virtual environment: `python -m venv venv && source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`

### Development Cycle

1. **Check `plan.md`** for next phase/task
2. **Implement** the code for that task
3. **Test** using pytest: `pytest tests/`
4. **Run app** locally: `streamlit run app.py`
5. **Verify** functionality in both views
6. **Update checkboxes** in `plan.md` as tasks complete

### Running the App

```bash
streamlit run app.py
```

The app will open in your browser with two views:
- **Interviewer View**: Create and manage questions
- **Interviewee View**: Take the interview

### Testing

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest -v tests/

# Run specific test file
pytest tests/test_basic_flow.py
```

### Evolving the Architecture

As the project grows beyond MVP:

1. **Update `claude.md`** first with architectural changes
2. **Update `plan.md`** with new implementation phases
3. **Implement** the changes
4. **Keep docs in sync** - these files are the source of truth

### Future Enhancements (Post-MVP)

- Swap EvaluatorAgent to LLM-based (OpenAI, Anthropic, local model)
- Add database persistence (SQLite, PostgreSQL)
- Question generation using LLM
- Adaptive difficulty (orchestrator adjusts based on performance)
- Export interview transcripts and reports
- Multiple evaluation rubrics
- Interviewer analytics dashboard
