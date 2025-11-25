# Agentic Interview System - Implementation Plan

This plan breaks down the MVP implementation into concrete phases with checkboxes. Complete each phase sequentially, checking off tasks as you go.

---

## Phase 0: Environment & Dependencies

**Goal**: Set up the development environment and verify basic tooling works.

**Tasks**:
- [ ] Create `requirements.txt` with necessary dependencies
  - streamlit
  - pytest
  - Any other standard library needs
- [ ] Create placeholder `app.py` with minimal Streamlit "Hello World"
- [ ] Verify `streamlit run app.py` launches successfully
- [ ] Create `tests/` directory with `__init__.py`
- [ ] Create virtual environment and install dependencies

**Notes**:
- Keep dependencies minimal for MVP
- Use Python 3.10+ features where helpful (dataclasses, type hints)

---

## Phase 1: Data Models

**Goal**: Define the core data structures that agents and UI will use. These should be pure Python dataclasses with no business logic.

**Tasks**:
- [ ] Create `models.py` file
- [ ] Implement `Question` dataclass
  - Fields: `id` (str), `text` (str), `competency` (str), `difficulty` (str), `keypoints` (list[str])
  - Add `__post_init__` validation if needed (e.g., keypoints is a list)
- [ ] Implement `EvaluationResult` dataclass
  - Fields: `question_id` (str), `candidate_answer` (str), `score` (int), `feedback` (str), `matched_keypoints` (list[str])
- [ ] Implement `InterviewState` dataclass
  - Fields: `questions` (list[Question]), `current_index` (int), `evaluations` (list[EvaluationResult]), `is_complete` (bool), `final_summary` (str)
  - Add helper methods: `get_current_question()`, `advance()`, `mark_complete()`
- [ ] Add type hints to all fields
- [ ] Write basic unit tests for model validation in `tests/test_models.py`

**Notes**:
- Use `from dataclasses import dataclass` for clean data classes
- Keep models pure - no Streamlit imports, no agent logic
- `id` fields use simple string IDs (e.g., UUIDs or sequential numbers)

---

## Phase 2: Agents

**Goal**: Implement the three core agents with clean interfaces. Agents contain business logic but no UI code.

### QuestionsAgent

**Tasks**:
- [ ] Create `agents.py` file
- [ ] Implement `QuestionsAgent` class
  - `__init__(self, questions: list[Question])`: Store question bank
  - `get_question(self, index: int) -> Question`: Retrieve question by index
  - `get_all_questions(self) -> list[Question]`: Return full question bank
  - `add_question(self, question: Question)`: Add to question bank
  - `count(self) -> int`: Return number of questions
- [ ] Add input validation (e.g., index bounds checking)

### EvaluatorAgent (Heuristic)

**Tasks**:
- [ ] Implement `EvaluatorAgent` class
  - `__init__(self)`: No external dependencies for MVP
  - `evaluate(self, question: Question, answer: str) -> EvaluationResult`: Core evaluation method
- [ ] Implement heuristic evaluation logic:
  - Case-insensitive substring matching for keypoints
  - Score = (matched_keypoints / total_keypoints) * 100
  - Generate feedback string listing matched and missed keypoints
  - Return EvaluationResult with score, feedback, matched_keypoints
- [ ] Ensure the interface is clean for future LLM swap:
  - `evaluate()` signature should remain stable
  - Only internals change when moving to LLM

### OrchestratorAgent

**Tasks**:
- [ ] Implement `OrchestratorAgent` class
  - `__init__(self, questions_agent: QuestionsAgent, evaluator_agent: EvaluatorAgent)`
  - `start_interview(self, question_ids: list[str] | None) -> InterviewState`: Initialize state
  - `submit_answer(self, state: InterviewState, answer: str) -> InterviewState`: Process answer and advance
  - `is_interview_complete(self, state: InterviewState) -> bool`: Check if done
  - `generate_summary(self, state: InterviewState) -> str`: Create final summary from evaluations
- [ ] Implement orchestration logic:
  - On `submit_answer()`: call evaluator, store result, advance index
  - On last question: mark state as complete
  - `generate_summary()`: compute average score, list competency coverage, provide qualitative summary

**Notes**:
- Agents should work without Streamlit - keep them pure Python
- OrchestratorAgent coordinates but doesn't contain eval logic
- EvaluatorAgent's heuristic is intentionally simple (easy to replace)
- Add docstrings to agent methods for clarity

---

## Phase 3: Streamlit UI

**Goal**: Build the user-facing interface with two distinct views (Interviewer and Interviewee).

### App Structure

**Tasks**:
- [ ] Set up `app.py` with Streamlit page config
- [ ] Create session state initialization:
  - `questions_agent`: QuestionsAgent instance
  - `evaluator_agent`: EvaluatorAgent instance
  - `orchestrator_agent`: OrchestratorAgent instance
  - `interview_state`: InterviewState or None
  - `question_bank`: List of Questions
- [ ] Create two tabs: "Interviewer View" and "Interviewee View"

### Interviewer View

**Tasks**:
- [ ] Create form for adding new questions:
  - Text input for question text
  - Text input for competency (e.g., "Python", "Algorithms")
  - Select box for difficulty ("Easy", "Medium", "Hard")
  - Text area for keypoints (comma-separated)
  - Submit button that adds Question to question bank
- [ ] Display question bank:
  - Show all questions in session state as expandable cards
  - Display: question text, competency, difficulty, keypoints
  - (MVP: no edit/delete functionality yet, but add TODOs for it)
- [ ] Add simple validation:
  - Don't allow empty questions or keypoints

### Interviewee View

**Tasks**:
- [ ] Add "Start Interview" button:
  - Only show if interview_state is None
  - On click: call `orchestrator.start_interview()` with all questions
  - Initialize interview_state in session state
- [ ] Display current question:
  - Show question text, competency, difficulty
  - Do NOT show keypoints (they're ground truth)
  - Show progress: "Question X of Y"
- [ ] Create answer submission:
  - Text area for candidate answer
  - Submit button that calls `orchestrator.submit_answer()`
  - Update session state with new interview_state
- [ ] Display evaluation results after each answer:
  - Show score for that question
  - Show feedback (matched/missed keypoints)
  - Add "Next Question" button or auto-advance
- [ ] Display final summary when complete:
  - Show overall score (average of all questions)
  - Show per-question breakdown
  - Show orchestrator's generated summary
  - Add "Start New Interview" button to reset

**Notes**:
- Use `st.session_state` to persist data during the session
- Keep UI code in `app.py`, agent calls should be simple method invocations
- Use Streamlit's built-in widgets (st.form, st.tabs, st.expander, etc.)
- Handle edge case: no questions in bank (show message in Interviewee view)

---

## Phase 4: Basic Tests

**Goal**: Add unit tests that verify agent behavior without requiring UI interaction.

**Tasks**:
- [ ] Create `tests/test_basic_flow.py`
- [ ] Write test for QuestionsAgent:
  - Test adding questions
  - Test retrieving questions by index
  - Test count() method
- [ ] Write test for EvaluatorAgent heuristic:
  - Create sample Question with known keypoints
  - Test answer with all keypoints → score = 100
  - Test answer with partial keypoints → score = 50
  - Test answer with no keypoints → score = 0
  - Verify matched_keypoints list is correct
  - Verify feedback string mentions missed keypoints
- [ ] Write test for OrchestratorAgent flow:
  - Create QuestionsAgent with 2-3 questions
  - Start interview
  - Submit answers for each question
  - Verify state advances correctly
  - Verify is_complete flag set after last question
  - Verify summary generated
- [ ] Write integration test:
  - Simulate full interview: create agents → start → answer all → check summary
  - Assert expected score range
  - Assert evaluation count matches question count
- [ ] Run `pytest tests/` and ensure all pass

**Notes**:
- Tests should be pure Python (no Streamlit imports)
- Use pytest fixtures for creating test questions and agents
- Aim for >80% code coverage of agent logic
- Tests prove agents work independently of UI

---

## Phase 5: LLM Evaluator Integration

**Goal**: Implement a production-ready LLM-based evaluator that can replace the heuristic evaluator with minimal code changes. The evaluator must be safe, tested, and easy to configure.

### Infrastructure & Configuration

**Tasks**:
- [ ] Create `.gitignore` file (if not exists) with security-critical entries:
  - `.env` and `.env.*`
  - `*.key`
  - `secrets/`
  - `__pycache__/`
  - `*.pyc`
- [ ] Create `.env.example` as a template for configuration:
  - Document all required environment variables
  - Include example values (not real keys)
  - Add comments explaining each variable's purpose
- [ ] Create `settings.py` module:
  - Use `python-dotenv` to load `.env` file
  - Read configuration from environment variables:
    - `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`
    - `LLM_PROVIDER` ("openai" or "anthropic")
    - `LLM_MODEL` (e.g., "gpt-4", "claude-3-sonnet-20240229")
    - `LLM_TEMPERATURE` (0.2-0.4 recommended)
  - Provide sensible defaults where possible
  - Add validation: error if required keys missing
  - Export configuration as constants
- [ ] Update `requirements.txt` with new dependencies:
  - `python-dotenv>=1.0.0`
  - `openai>=1.0.0` (if using OpenAI)
  - `anthropic>=0.8.0` (if using Anthropic)
  - Consider: `pydantic>=2.0.0` for config validation

### LLM Client Abstraction

**Tasks**:
- [ ] Create `llm_client.py` with provider-agnostic interface:
  - Define `LLMClient` base class or protocol with `call_llm(prompt, model, temperature) -> str`
  - Implement `OpenAIClient` class:
    - Initialize with API key from settings
    - Use `openai.ChatCompletion.create()` or equivalent
    - Handle message formatting (system/user messages)
    - Extract text from response
  - Implement `AnthropicClient` class:
    - Initialize with API key from settings
    - Use Anthropic SDK's message API
    - Handle message formatting
    - Extract text from response
  - Implement factory function `get_llm_client(provider: str) -> LLMClient`:
    - Select client based on provider string
    - Raise error if provider unknown
  - Add error handling:
    - Retry logic for transient failures (rate limits, timeouts)
    - Clear error messages for auth failures
    - Timeout configuration (10-30 seconds)
- [ ] Create `MockLLMClient` for testing:
  - Implement same interface as real clients
  - Return canned responses based on input keywords
  - No external API calls
  - Useful for unit tests and development without API keys

### LLM Evaluator Implementation

**Tasks**:
- [ ] Create `llm_evaluator.py` file:
  - Import: `Question`, `EvaluationResult`, `KeypointCoverage`, `LLMClient`
  - Define `LLMEvaluatorAgent` class with same interface as `EvaluatorAgent`
  - Implement `__init__(self, llm_client: LLMClient)`:
    - Store client for later use
    - Optionally load prompt template from file
  - Implement `evaluate(self, question: Question, answer: str) -> EvaluationResult`:
    - Construct prompt from template with question, keypoints, answer
    - Call `llm_client.call_llm(prompt, model, temperature)`
    - Parse JSON response from LLM
    - Map to `EvaluationResult` object:
      - Extract score, mastery_label, feedback, suggested_followup
      - Build `KeypointCoverage` list from keypoints_coverage
    - Handle malformed responses:
      - Try to extract partial data
      - Log warning
      - Fallback to heuristic or return error EvaluationResult
  - Add prompt template as string or file:
    - Use the structure defined in `claude.md` "Prompting Strategy"
    - Include few-shot examples for consistency
    - Request strict JSON output
  - Add docstrings explaining:
    - Purpose and design
    - Prompt engineering approach
    - Expected LLM behavior

**Prompt Design**:
- [ ] Create prompt template with:
  - Clear role definition ("You are an expert technical interviewer")
  - Structured input sections (QUESTION, KEYPOINTS, ANSWER)
  - Explicit task breakdown (1. evaluate keypoints, 2. score, 3. classify, 4. feedback, 5. follow-up)
  - JSON schema for output
  - 1-2 few-shot examples showing ideal evaluations
- [ ] Test prompt with various answer types:
  - Perfect answer (all keypoints)
  - Partial answer (some keypoints)
  - Poor answer (no keypoints)
  - Off-topic answer
  - Very short answer

### UI Integration

**Tasks**:
- [ ] Update `app.py` to support evaluator selection:
  - Add sidebar control before main view selector:
    - Radio buttons: "Evaluator Mode"
    - Options: "Heuristic (Fast, Offline)" vs "LLM-Powered (Requires API Key)"
  - Store selection in `st.session_state.evaluator_mode`
  - When initializing evaluator:
    - Check `evaluator_mode` value
    - If "Heuristic": instantiate `EvaluatorAgent()`
    - If "LLM-Powered":
      - Check if API key is configured in settings
      - If not configured: show error message with setup instructions, fall back to heuristic
      - If configured: instantiate `LLMEvaluatorAgent(get_llm_client(...))`
  - Display current evaluator status in sidebar:
    - Show "Using: Heuristic" or "Using: LLM (gpt-4)"
    - If LLM: show API key status (configured vs missing)
  - Add help text explaining difference:
    - Heuristic: keyword matching, fast, no API costs
    - LLM: semantic understanding, richer feedback, requires API key and costs money

### Testing

**Tasks**:
- [ ] Create `tests/test_llm_evaluator.py`:
  - Test prompt construction:
    - Verify all question fields are included
    - Verify all keypoints are listed
    - Verify answer is included
  - Test response parsing:
    - Mock LLM response with valid JSON
    - Verify `EvaluationResult` is correctly constructed
    - Check all fields are populated
  - Test error handling:
    - Mock malformed JSON response
    - Verify graceful degradation
    - Ensure no crashes
  - Test empty/edge cases:
    - Empty answer
    - No keypoints
    - Very long answer
  - All tests use `MockLLMClient` (no real API calls)
- [ ] Add integration test in `test_basic_flow.py`:
  - Test that `LLMEvaluatorAgent` can replace `EvaluatorAgent` seamlessly
  - Same questions, mock LLM responses
  - Verify interview flow completes normally
- [ ] Run existing tests to ensure backward compatibility:
  - All tests still pass with heuristic evaluator
  - No changes to existing test behavior

**Notes**:
- Keep heuristic evaluator as default for tests (fast, deterministic)
- LLM evaluator is an opt-in enhancement
- Tests must not require API keys to run
- Mock client should provide realistic-looking responses

---

## Phase 6: Evaluation Quality Assurance

**Goal**: Build a reference evaluation set and regression tests to ensure LLM evaluator behavior is consistent and high-quality. This phase validates that the LLM produces reliable scores before using it with real candidates.

### Reference Evaluation Set

**Tasks**:
- [ ] Create `tests/fixtures/` directory
- [ ] Design evaluation reference set schema:
  - Each entry should include:
    - `id`: Unique identifier
    - `question`: Full Question object (text, competency, difficulty, keypoints)
    - `answer`: Candidate's answer text
    - `expected_band`: "strong", "mixed", or "weak"
    - `expected_score_min`: Minimum acceptable score (e.g., 80)
    - `expected_score_max`: Maximum acceptable score (e.g., 100)
    - `expected_covered_keypoints`: List of keypoints that should be marked as covered
    - `notes`: Explanation of why this is the expected evaluation
- [ ] Create `tests/fixtures/eval_reference_set.json`:
  - Add 10-15 diverse test cases covering:
    - **Perfect answer** (all keypoints, clear explanation) → "strong", 90-100
    - **Good answer** (most keypoints, decent explanation) → "strong", 80-89
    - **Partial answer** (some keypoints, missing others) → "mixed", 60-79
    - **Weak answer** (few keypoints, shallow) → "mixed", 50-59
    - **Poor answer** (no keypoints or wrong concepts) → "weak", 0-49
    - **Off-topic answer** (doesn't address question) → "weak", 0-10
    - **Empty answer** → "weak", 0
    - **Verbose but incomplete** (lots of words, missing key concepts) → "mixed"
    - **Terse but accurate** (short but covers keypoints) → "strong"
  - Include variety of competencies (Python, Algorithms, System Design, etc.)
  - Include variety of difficulties (Easy, Medium, Hard)
- [ ] Document reference set creation process:
  - Explain how expected bands were determined
  - Note any edge cases or debatable evaluations
  - Provide guidelines for adding new cases

### Regression Testing

**Tasks**:
- [ ] Create `tests/test_llm_eval_regression.py`:
  - Load reference set from JSON file
  - For each test case:
    - Create `Question` from test data
    - Initialize `LLMEvaluatorAgent` with `MockLLMClient`
    - Configure mock to return pre-crafted evaluation matching expected behavior
    - Call `evaluate(question, answer)`
    - Assert:
      - `mastery_label` matches `expected_band`
      - `score_0_100` is within `[expected_score_min, expected_score_max]`
      - Keypoints in `expected_covered_keypoints` are marked as covered
      - Response is well-formed (no missing fields)
  - Add summary report at end:
    - Count: passed / total
    - List any failures with details
- [ ] Create comparison test (`test_heuristic_vs_llm.py`):
  - Run same reference set through both evaluators
  - Compare results:
    - Where do they agree?
    - Where do they disagree significantly?
    - Is LLM more generous or stricter?
  - Generate comparison report
  - Use this to validate that LLM is actually better (not just different)
- [ ] Add prompt validation test:
  - Test that prompt template includes all required fields
  - Test that few-shot examples are well-formed
  - Test that JSON schema is clear and unambiguous

### Manual Validation

**Tasks**:
- [ ] Create manual test script (`scripts/test_llm_live.py`):
  - Takes API key as argument or from .env
  - Runs subset of reference set through real LLM (not mock)
  - Displays results side-by-side with expected values
  - Allows human review of LLM evaluation quality
- [ ] Conduct manual testing session:
  - Run live tests with OpenAI/Anthropic
  - Review 5-10 evaluations manually
  - Check for:
    - Reasonable scores
    - Helpful feedback
    - Appropriate mastery labels
    - Useful follow-up questions
  - Document any issues or surprises
- [ ] Iterate on prompt if needed:
  - Adjust prompt wording based on manual review
  - Re-run tests after changes
  - Update `claude.md` with prompt design decisions

### Performance & Cost Monitoring

**Tasks**:
- [ ] Add logging to `LLMEvaluatorAgent`:
  - Log each evaluation: question_id, latency, tokens used
  - Log prompt and response (redact sensitive info if needed)
  - Aggregate stats: average latency, total cost estimate
- [ ] Create performance benchmark script:
  - Evaluate reference set with both evaluators
  - Measure: latency, cost (estimated), score distribution
  - Compare heuristic vs LLM on objective metrics
- [ ] Document cost estimates in `claude.md`:
  - Cost per question evaluation (e.g., $0.01-0.05)
  - Cost per full interview (e.g., 5 questions = $0.05-0.25)
  - Recommend budgets and guardrails

**Completion Criteria**:

Phase 6 is complete when:

✅ Reference set has 10+ diverse test cases with documented expectations
✅ Regression tests pass with mocked LLM responses (>90% agreement on mastery band)
✅ Manual validation confirms LLM evaluations are reasonable and helpful
✅ Prompt is stable and documented
✅ Cost and performance metrics are acceptable
✅ Tests catch regressions if prompt or LLM behavior changes

**Notes**:
- This phase is critical before using LLM evaluator in production
- Reference set is a living document—add new cases as edge cases are discovered
- Regression tests prevent silent degradation of evaluation quality
- Manual validation ensures LLM evaluations are genuinely useful, not just plausible

---

## Phase 7: Polish & Documentation

**Goal**: Finalize MVP with documentation and minor UX improvements.

**Tasks**:
- [ ] Create `README.md`:
  - Project description
  - Installation instructions
  - How to run the app
  - How to run tests
  - Screenshot or GIF of UI (optional)
- [ ] Add docstrings to all classes and public methods
- [ ] Add error handling:
  - Handle empty question bank gracefully
  - Handle invalid session state
  - Show friendly error messages in UI
- [ ] Add basic styling:
  - Use Streamlit's `st.success()`, `st.warning()`, `st.error()` for feedback
  - Add emojis to section headers (optional)
  - Ensure consistent spacing and layout
- [ ] Final testing:
  - Manual test full interviewer → interviewee flow
  - Test edge cases (0 questions, 1 question, many questions)
  - Verify all checkboxes in this plan are complete

**Notes**:
- MVP is done when a user can create questions, take interview, and see results
- Documentation should enable a new developer to run the project in <5 minutes
- Keep it simple - don't over-engineer

---

## Completion Criteria

The MVP is complete when:

✅ User can create questions with keypoints in Interviewer view
✅ User can take interview with those questions in Interviewee view
✅ Each answer is evaluated against keypoints with a score
✅ Final summary is generated with overall score
✅ All agents work independently (tested without UI)
✅ Code is clean, documented, and follows the architecture in `claude.md`
✅ Tests pass and cover core agent logic

---

## Phase 5 & 6 Completion Criteria

Phase 5 (LLM Evaluator Integration) is complete when:

✅ `.gitignore` protects secrets from being committed
✅ `.env.example` documents all configuration variables
✅ `settings.py` loads and validates configuration
✅ `llm_client.py` provides provider-agnostic LLM interface
✅ `llm_evaluator.py` implements LLMEvaluatorAgent with same interface as EvaluatorAgent
✅ Streamlit UI has evaluator mode toggle
✅ All tests pass with mocked LLM (no API keys required)
✅ LLM evaluator can be used interchangeably with heuristic evaluator

Phase 6 (Evaluation Quality Assurance) is complete when:

✅ Reference evaluation set has 10-15 diverse, documented test cases
✅ Regression tests validate LLM behavior against reference set
✅ Manual validation with real LLM shows acceptable quality
✅ Prompt is stable and produces consistent results
✅ Cost and latency metrics are documented and acceptable

---

## Phase 6: Persistence, Templates & Sessions

**Goal**: Transform the prototype into a durable system that manages multiple people, templates, and interview sessions with persistent data storage. This phase introduces proper data modeling while keeping the AI evaluator layer unchanged.

**Why This Phase Exists**: The current system uses in-memory session state and ad-hoc question creation. To build a production interview platform, we need to manage people (interviewees), reusable interview templates, and persistent session records with full transcripts and evaluations. This phase lays the foundation for multi-tenant capability (even if we run single-tenant initially) and enables historical analysis and reporting in Phase 7.

### Data Model: People & Templates

**Tasks**:
- [ ] **Design schema for people and organizations**
  - [ ] Define `Person` model:
    - Fields: id, name, email, role, department, tags (JSON or separate table), status (active/inactive), organization_id
    - Represents interviewees, candidates, or employees being assessed
  - [ ] Define `Organization` model:
    - Fields: id, name, settings (JSON)
    - Even if single-tenant for MVP, include organization_id in other tables for future multi-tenancy
  - [ ] Document relationships: Person → Organization (many-to-one)

- [ ] **Design schema for interview templates**
  - [ ] Define `InterviewTemplate` model:
    - Fields: id, name, description, organization_id, version, active (boolean), created_at, updated_at
    - Represents reusable interview blueprints (e.g., "Python Developer L2", "Product Manager Screening")
  - [ ] Define `TemplateQuestion` model:
    - Fields: id, template_id, order_index, question_text, competency, difficulty, keypoints (JSON array)
    - Links to InterviewTemplate (many-to-one)
    - order_index determines question sequence during interview
  - [ ] Document relationships: TemplateQuestion → InterviewTemplate (many-to-one)
  - [ ] Note: keypoints stored as JSON array for now (normalize to separate table later if needed)

### Data Model: Sessions & Transcripts

**Tasks**:
- [ ] **Design schema for interview sessions**
  - [ ] Define `InterviewSession` model:
    - Fields: id, template_id, person_id, status (enum: scheduled/in_progress/completed/cancelled), started_at, completed_at, evaluator_type (heuristic/llm), organization_id
    - Represents a single interview instance with a specific person using a specific template
  - [ ] Document relationships: InterviewSession → Person (many-to-one), InterviewSession → InterviewTemplate (many-to-one)

- [ ] **Design schema for transcripts**
  - [ ] Define `TranscriptEntry` model:
    - Fields: id, session_id, speaker (enum: system/participant), text, created_at, sequence_index
    - Captures the full conversation flow: questions asked, answers given, system messages
  - [ ] Document relationships: TranscriptEntry → InterviewSession (many-to-one)
  - [ ] Ensure sequence_index allows proper ordering of conversation flow

- [ ] **Design schema for evaluations**
  - [ ] Define `QuestionEvaluation` model:
    - Fields: id, session_id, template_question_id, evaluator_type (heuristic/llm), score_0_100, mastery_label (strong/mixed/weak), raw_answer (text), short_feedback (text), keypoints_coverage (JSON), suggested_followup (text), created_at
    - Aligns with existing `EvaluationResult` dataclass structure
    - Captures which evaluator was used for traceability
  - [ ] Document relationships: QuestionEvaluation → InterviewSession (many-to-one), QuestionEvaluation → TemplateQuestion (many-to-one)
  - [ ] keypoints_coverage stored as JSON array of objects: `[{"keypoint": "...", "covered": true/false, "evidence": "..."}]`

### Implementation: Storage Layer

**Tasks**:
- [ ] **Choose and configure ORM**
  - [ ] Decision: SQLAlchemy (recommended) or alternative ORM
  - [ ] For MVP: Use SQLite for simple local deployment
  - [ ] Design for easy migration to PostgreSQL for production
  - [ ] Create base model classes and database connection management

- [ ] **Implement models as SQLAlchemy/ORM classes**
  - [ ] Create `models/` directory or expand `models.py`
  - [ ] Implement Person, Organization models
  - [ ] Implement InterviewTemplate, TemplateQuestion models
  - [ ] Implement InterviewSession, TranscriptEntry, QuestionEvaluation models
  - [ ] Add proper foreign key constraints and indexes

- [ ] **Database migrations**
  - [ ] Set up Alembic (or similar) for schema migrations
  - [ ] Create initial migration with all tables
  - [ ] Document migration workflow for future schema changes
  - [ ] Ensure migrations work with both SQLite (dev) and PostgreSQL (prod)

- [ ] **Testing infrastructure**
  - [ ] Configure tests to use in-memory SQLite or temporary database
  - [ ] Add fixtures for creating test data (people, templates, sessions)
  - [ ] Update existing tests to work with persistent storage
  - [ ] Add new tests for CRUD operations on all models

### UI: People & Template Management

**Tasks**:
- [ ] **Create admin/management view**
  - [ ] Add new Streamlit tab or page for "Admin" functions
  - [ ] Keep existing Interviewer/Interviewee views functional during transition

- [ ] **People management interface**
  - [ ] Build form to create new Person records:
    - Input fields: name, email, role, department, tags (comma-separated)
    - Validation: required fields, email format
  - [ ] Display list of all people with filters (by department, role, status)
  - [ ] Add ability to view/edit existing person records
  - [ ] Add status toggle (active/inactive)
  - [ ] Simple UI: forms and tables, no drag-and-drop needed for MVP

- [ ] **Template management interface**
  - [ ] Build form to create new InterviewTemplate:
    - Input fields: name, description
    - Initially empty (add questions in next step)
  - [ ] Display list of all templates with metadata (name, question count, created date)
  - [ ] For each template, provide interface to manage TemplateQuestions:
    - Add new questions to template (text, competency, difficulty, keypoints)
    - Reorder questions (simple up/down buttons or number input)
    - Edit existing questions
    - Remove questions from template
  - [ ] Add template activation toggle (active/inactive)
  - [ ] Show template version information

### Runtime: Wire Templates to Sessions

**Tasks**:
- [ ] **Update interview start flow**
  - [ ] Modify Interviewee view to show two-step setup:
    - Step 1: Select a Person (dropdown of active people)
    - Step 2: Select an InterviewTemplate (dropdown of active templates)
  - [ ] On "Start Interview" button:
    - Create new InterviewSession record (status=in_progress, started_at=now)
    - Link to selected person_id and template_id
    - Store evaluator_type based on current UI toggle (heuristic/llm)
  - [ ] Load TemplateQuestions for the selected template in order

- [ ] **Update interview runtime**
  - [ ] For each question asked:
    - Create TranscriptEntry (speaker=system, text=question)
  - [ ] For each answer submitted:
    - Create TranscriptEntry (speaker=participant, text=answer)
    - Call selected evaluator (heuristic or LLM)
    - Store QuestionEvaluation record with all results
    - Link to session_id and template_question_id
  - [ ] Maintain proper sequence_index for transcript ordering

- [ ] **Update interview completion**
  - [ ] When all template questions answered:
    - Update InterviewSession: status=completed, completed_at=now
    - Generate final summary (existing logic)
    - Store summary in session metadata or new field
  - [ ] Display completion confirmation with session ID

- [ ] **Maintain backward compatibility**
  - [ ] Ensure existing OrchestratorAgent can work with new data model
  - [ ] Consider creating adapter layer if needed to bridge old interfaces and new persistence

### Migration & Data Management

**Tasks**:
- [ ] **Seed data for development**
  - [ ] Create script to populate database with sample data:
    - 5-10 sample people
    - 2-3 interview templates with questions
    - Example completed sessions
  - [ ] Document how to run seed script

- [ ] **Data import/export**
  - [ ] Add utility to export templates as JSON (for backup/sharing)
  - [ ] Add utility to import templates from JSON
  - [ ] Consider CSV import for bulk person creation

- [ ] **Data cleanup utilities**
  - [ ] Script to archive old sessions (if status=completed and older than X days)
  - [ ] Script to anonymize person data for testing/demos

**Notes**:
- Keep the AI evaluator layer (Phase 5 work) completely unchanged
- All existing evaluation logic continues to work, just with persistent storage
- Multi-tenant capability is designed in but not enforced for MVP (single organization)
- Focus on solid data model and simple CRUD UIs; polish comes later

---

## Phase 7: Lenses & Reporting

**Goal**: Build on stored transcripts and evaluations to add post-interview "lens" analysis (AI-powered structured insights) and basic reporting dashboards. This phase transforms raw interview data into actionable intelligence.

**Why This Phase Exists**: Interview transcripts contain rich information beyond just question-answer scoring. Lenses allow us to apply different analytical frameworks (e.g., "Debugging Process Quality", "Communication Skills", "Problem-Solving Approach") to extract structured insights, identify patterns, and generate comparative reports across multiple interviews.

### Data Model: Lenses

**Tasks**:
- [ ] **Design lens schema**
  - [ ] Define `Lens` model:
    - Fields: id, name, description, config (JSON), active (boolean), version, created_at, updated_at, organization_id
    - config contains: criteria definitions, output schema, scoring scales, prompt templates
    - Example lens: "Debugging Process Assessment" with criteria like "systematic approach", "hypothesis formation", "tool usage"
  - [ ] Define `LensResult` model:
    - Fields: id, session_id, lens_id, status (pending/completed/failed), created_at, completed_at, llm_provider, llm_model, error_message
    - Represents one application of a lens to a completed interview session
  - [ ] Define `LensCriterionResult` model:
    - Fields: id, lens_result_id, criterion_name, score (numeric, scale defined in lens config), flags (JSON array), extracted_items (JSON array), supporting_quotes (JSON array), notes (text)
    - Captures results for each individual criterion within a lens
    - score: e.g., 0-5 or 0-10 depending on lens configuration
    - flags: boolean indicators (e.g., ["unclear_explanation", "contradictory_statements"])
    - extracted_items: structured data (e.g., ["process: requirements gathering", "process: architecture design"])
    - supporting_quotes: transcript snippets that support the assessment

- [ ] **Document lens output schema**
  - [ ] Define standard JSON structure for lens results:
    ```json
    {
      "criterion": "systematic_debugging",
      "score": 4,
      "scale": "0-5",
      "flags": ["uses_hypothesis_testing", "missing_log_analysis"],
      "extracted_items": ["reproduced issue", "checked logs", "tested fix"],
      "supporting_quotes": [
        {"speaker": "participant", "text": "First I would reproduce...", "timestamp": "..."}
      ],
      "notes": "Candidate showed strong systematic approach but didn't mention log analysis"
    }
    ```
  - [ ] Ensure schema supports:
    - Numeric scores (with defined scale)
    - Boolean flags (yes/no/unknown)
    - Lists of extracted concepts/items
    - Supporting evidence with transcript references
    - Free-form notes

- [ ] **Define relationships**
  - [ ] LensResult → InterviewSession (many-to-one)
  - [ ] LensResult → Lens (many-to-one)
  - [ ] LensCriterionResult → LensResult (many-to-one)

### Implementation: Lens Analysis Pipeline

**Tasks**:
- [ ] **Design lens execution architecture**
  - [ ] Decision: Synchronous vs background job processing
    - Recommendation: Start with synchronous for MVP, design for async later
    - Consider: Celery, RQ, or similar for background processing in production
  - [ ] Define pipeline steps:
    1. Fetch completed InterviewSession with full transcript
    2. For each active Lens applicable to this session:
       - Build lens-specific prompt using transcript
       - Call LLM via existing `llm_client`
       - Parse and validate JSON response
       - Store results in LensResult + LensCriterionResult tables
    3. Handle errors gracefully (retry, fallback, error logging)

- [ ] **Implement lens prompt builder**
  - [ ] Create `lens_prompt_builder.py` or similar module
  - [ ] Function: `build_lens_prompt(lens: Lens, session: InterviewSession, transcript: List[TranscriptEntry]) -> str`
  - [ ] Prompt structure:
    ```
    You are analyzing a technical interview transcript to assess: {lens.name}

    TRANSCRIPT:
    [formatted conversation with speaker labels and timestamps]

    ASSESSMENT CRITERIA:
    [from lens.config, list each criterion with its definition]

    TASK:
    For each criterion, analyze the transcript and output:
    - score (0-{scale})
    - flags (list of observations)
    - extracted_items (list of specific behaviors/concepts identified)
    - supporting_quotes (specific text from transcript)
    - notes (brief explanation)

    OUTPUT FORMAT (strict JSON):
    {
      "criteria_results": [
        {
          "criterion": "...",
          "score": X,
          "flags": [...],
          "extracted_items": [...],
          "supporting_quotes": [...],
          "notes": "..."
        }
      ]
    }

    EXAMPLE: [include 1-2 examples in prompt for consistency]
    ```
  - [ ] Ensure prompt includes:
    - Full transcript with context
    - Clear criterion definitions
    - Output format specification
    - Few-shot examples for consistency

- [ ] **Implement lens executor**
  - [ ] Create `lens_executor.py` or expand existing evaluator modules
  - [ ] Class: `LensExecutor(llm_client: LLMClient)`
  - [ ] Method: `execute_lens(session_id: int, lens_id: int) -> LensResult`
  - [ ] Implementation:
    - Fetch session, transcript, and lens configuration from database
    - Build prompt using prompt builder
    - Call LLM with appropriate model and temperature
    - Parse JSON response (use Pydantic for validation)
    - Create LensResult record (status=completed)
    - Create LensCriterionResult records for each criterion
    - Handle errors: store status=failed, log error_message, don't crash
  - [ ] Reuse existing patterns from Phase 5:
    - Provider-agnostic via `llm_client.py`
    - Retry logic with exponential backoff
    - Timeout handling
    - MockLLMClient support for testing

- [ ] **Add lens response validation**
  - [ ] Use Pydantic models to define expected response structure
  - [ ] Validate: correct criterion names, scores within range, required fields present
  - [ ] Handle malformed responses:
    - Log error with raw response for debugging
    - Mark LensResult as failed
    - Don't crash; allow other lenses to continue

### Lens Configuration & Management

**Tasks**:
- [ ] **Create lens management interface**
  - [ ] Add "Lenses" section to Admin view
  - [ ] Form to create new Lens:
    - Name, description
    - Define criteria (for MVP: JSON config input, not full no-code builder)
    - Set scoring scale (e.g., 0-5, 0-10)
    - Mark as active/inactive
  - [ ] Display list of all lenses with metadata
  - [ ] Allow editing lens configuration (versioning noted but not enforced in MVP)

- [ ] **Document lens versioning strategy**
  - [ ] Note in plan: lenses should be versioned when criteria change
  - [ ] For MVP: simple version number field
  - [ ] Future: copy-on-edit pattern to preserve historical lens definitions
  - [ ] Rationale: ensures old LensResults can be interpreted correctly even if lens evolves

- [ ] **Provide example lens configurations**
  - [ ] Document 2-3 example lenses with full config:
    - "Debugging Process Assessment"
    - "Communication Clarity"
    - "System Design Thinking"
  - [ ] Include sample criterion definitions and expected outputs
  - [ ] Provide as seed data or importable JSON

### Reporting UI

**Tasks**:
- [ ] **Create reporting dashboard**
  - [ ] Add "Reports" view to Streamlit app (new tab/page)
  - [ ] Show overview metrics:
    - Total interviews completed (by date range)
    - Average scores by lens
    - Score distributions (histograms)
    - Breakdown by department, role, template

- [ ] **Implement filters**
  - [ ] Date range picker (start date, end date)
  - [ ] Person filter (multi-select or search)
  - [ ] Department filter (dropdown)
  - [ ] Role filter (dropdown)
  - [ ] Lens filter (multi-select)
  - [ ] Template filter (multi-select)
  - [ ] Apply filters to all charts and tables

- [ ] **Add summary charts**
  - [ ] Score distribution by lens (bar chart or box plot)
  - [ ] Average score by department (bar chart)
  - [ ] Average score by role (bar chart)
  - [ ] Trend over time (line chart: avg score per week/month)
  - [ ] Use Streamlit's built-in charting or Plotly for interactivity

- [ ] **Implement session list view**
  - [ ] Table showing all sessions matching filters
  - [ ] Columns: Person name, Template name, Date, Status, Overall score, Key lens scores
  - [ ] Sortable by date, score, etc.
  - [ ] Clickable rows to drill down

- [ ] **Build session detail view**
  - [ ] Drilldown page for a specific InterviewSession
  - [ ] Show:
    - Person details (name, role, department)
    - Template used
    - Session metadata (date, duration, evaluator type)
    - Full transcript (formatted conversation view)
    - Question-level evaluations (score, feedback, keypoints covered)
    - Lens results:
      - For each lens: overall assessment, per-criterion scores
      - Display supporting quotes with links to transcript
      - Show flags and extracted items
  - [ ] Make transcript searchable/filterable
  - [ ] Highlight quoted sections when viewing lens results

- [ ] **Add export functionality**
  - [ ] Export session detail as PDF or JSON
  - [ ] Export filtered report data as CSV
  - [ ] Include all lens results and supporting quotes in export

### Observability & Traceability

**Tasks**:
- [ ] **Add lens pipeline logging**
  - [ ] Log key events:
    - Lens execution start (session_id, lens_id, timestamp)
    - LLM call (provider, model, prompt length, timestamp)
    - LLM response (success/failure, response length, parse status)
    - Lens execution end (duration, result count, timestamp)
  - [ ] Log errors with full context for debugging
  - [ ] Use structured logging (JSON logs) for easy parsing

- [ ] **Implement traceability**
  - [ ] Ensure every displayed score/flag links back to:
    - Source LensResult record (which session, which lens, when)
    - Supporting quotes from transcript (with speaker and sequence)
    - LLM call metadata (provider, model, temperature)
  - [ ] In UI: show "why this score?" tooltip or expandable section

- [ ] **Add performance monitoring (design)**
  - [ ] Document what to track (for Phase 8 or production):
    - Latency: lens execution time per session
    - Token usage: total tokens per lens call
    - Cost: estimated $ per lens execution
    - Error rate: % of lens executions that fail
  - [ ] For MVP: log these metrics, build dashboards later
  - [ ] Design for integration with monitoring tools (Prometheus, Datadog, etc.)

- [ ] **Implement retry and failure handling**
  - [ ] If lens execution fails:
    - Mark LensResult as failed
    - Log error details
    - Allow manual retry from UI (optional for MVP)
  - [ ] If specific criterion parsing fails:
    - Mark that criterion as null/missing
    - Continue processing other criteria
    - Log warning but don't fail entire lens

### Testing

**Tasks**:
- [ ] **Unit tests for lens logic**
  - [ ] Test prompt building with various transcript formats
  - [ ] Test response parsing with valid/invalid JSON
  - [ ] Test error handling (malformed responses, missing fields)
  - [ ] Use MockLLMClient for fast, deterministic tests

- [ ] **Integration tests**
  - [ ] Test full lens pipeline: session → lens execution → results stored
  - [ ] Test multiple lenses on same session
  - [ ] Test filtering and reporting queries

- [ ] **Regression tests (optional for MVP, document for later)**
  - [ ] Create reference set of transcripts with expected lens results
  - [ ] Similar to Phase 5 evaluation testing
  - [ ] Ensures prompt changes don't degrade lens quality

**Notes**:
- Lens system is modular: each lens is independent, easy to add new ones
- Reuses all LLM infrastructure from Phase 5 (no new API integration needed)
- Focus on structured extraction and traceability, not just free-form analysis
- Supporting quotes are key: every score should have evidence

---

## Next Steps (Beyond Phase 7)

After completing all phases, consider these enhancements:

**Data & Persistence**:
- Add database persistence (SQLite for local, PostgreSQL for production)
- Store interview history and results
- Track candidate performance over time

**Question Management**:
- Add edit/delete for questions in Interviewer view
- Question filtering by competency or difficulty
- Question versioning and change tracking
- Import/export question banks

**Advanced Features**:
- LLM-powered question generation based on job description
- Adaptive difficulty (orchestrator adjusts based on performance)
- Multi-round interviews with follow-up questions
- Code execution for programming questions
- Whiteboard/diagram support

**Collaboration & Sharing**:
- Authentication and user management
- Multi-interviewer reviews
- Real-time collaboration
- Share interview results with team

**Analytics & Reporting**:
- Export interview results as PDF or JSON
- Build analytics dashboard for interviewers
- Aggregate statistics across candidates
- Competency gap analysis

**Evaluation Enhancements**:
- Human-in-the-loop review and score adjustment
- Fine-tune LLM on human-labeled evaluations
- Multiple evaluation rubrics (technical depth, communication, problem-solving)
- Calibration across multiple interviewers
