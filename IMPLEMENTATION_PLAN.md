# Phase 5 Implementation Plan: LLM Evaluator Integration

**Created**: 2025-11-25
**Status**: Ready to start
**Estimated Duration**: 2-3 days
**Goal**: Add production-ready LLM-based evaluation with seamless heuristic fallback

---

## Overview

This plan implements Phase 5 of the Agentic Interview System, adding LLM-based evaluation capabilities while maintaining the existing heuristic evaluator as a fallback. The implementation follows a layered approach: infrastructure → client abstraction → evaluator logic → UI integration → testing.

---

## Implementation Strategy

### Approach: Incremental with Safety

1. **Set up infrastructure first** - Ensure secrets management is secure before any API integration
2. **Build abstractions** - Create clean interfaces before implementing providers
3. **Test continuously** - Verify each layer works before moving to the next
4. **Maintain backward compatibility** - All existing functionality must continue working

### Key Principles

- **Security First**: No API keys in code or git, ever
- **Interface Stability**: LLM evaluator must be a drop-in replacement for heuristic
- **Test Without API Keys**: All tests use mocks by default
- **Graceful Degradation**: Fall back to heuristic if LLM unavailable

---

## Phase Breakdown

### Stage 1: Infrastructure & Configuration (Tasks 1-4)

**Goal**: Set up secure configuration management and dependency framework

#### Task 1: Create .gitignore
```bash
# Create or update .gitignore
```

**Contents**:
```gitignore
# Environment and secrets
.env
.env.*
*.key
secrets/

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/

# IDEs
.vscode/
.idea/
*.swp
*.swo

# Testing
.pytest_cache/
.coverage
htmlcov/

# OS
.DS_Store
Thumbs.db
```

**Verification**: Try to `git add .env` - should be ignored

---

#### Task 2: Create .env.example

**Purpose**: Template showing required configuration without exposing secrets

**Contents**:
```bash
# LLM Provider Configuration
# Choose one: "openai" or "anthropic"
LLM_PROVIDER=openai

# API Keys (get from respective provider dashboards)
# OpenAI: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-your-key-here

# Anthropic: https://console.anthropic.com/settings/keys
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Model Selection
# OpenAI models: gpt-4, gpt-4-turbo-preview, gpt-3.5-turbo
# Anthropic models: claude-3-5-sonnet-20241022, claude-3-opus-20240229
LLM_MODEL=gpt-4

# Temperature (0.0-1.0, lower = more deterministic)
# Recommended: 0.2-0.4 for evaluation consistency
LLM_TEMPERATURE=0.3

# Timeout (seconds) for LLM API calls
LLM_TIMEOUT=30

# Max retries for transient failures
LLM_MAX_RETRIES=2
```

**Note for developers**: Copy `.env.example` to `.env` and fill in real values

---

#### Task 3: Update requirements.txt

**Add dependencies**:
```txt
streamlit>=1.28.0
pytest>=7.4.0

# Phase 5: LLM Integration
python-dotenv>=1.0.0
openai>=1.0.0
anthropic>=0.8.0
```

**After updating**, run:
```bash
pip install -r requirements.txt
```

---

#### Task 4: Create settings.py

**Purpose**: Centralized configuration loader with validation

**Key functionality**:
- Load `.env` file using `python-dotenv`
- Read environment variables with type conversion
- Provide sensible defaults where possible
- Validate required variables (error if missing)
- Export as constants for import elsewhere

**Interface design**:
```python
# Other modules import like this:
from settings import (
    LLM_PROVIDER,
    OPENAI_API_KEY,
    ANTHROPIC_API_KEY,
    LLM_MODEL,
    LLM_TEMPERATURE,
    # ...
)

# Optional: validation function
def validate_llm_config() -> tuple[bool, str]:
    """Returns (is_valid, error_message)"""
```

**Error handling**:
- If `.env` doesn't exist → use environment variables only (OK for production)
- If required key missing → return clear error message, don't crash
- If invalid value (e.g., temperature > 1.0) → use default and log warning

**Testing consideration**: Settings should be mockable in tests

---

### Stage 2: LLM Client Abstraction (Tasks 5-9)

**Goal**: Create provider-agnostic interface for calling LLMs

#### Task 5: Create llm_client.py base structure

**Interface design** (choose one approach):

**Option A: Protocol (Python 3.8+ typing)**
```python
from typing import Protocol

class LLMClient(Protocol):
    def call_llm(self, prompt: str, model: str, temperature: float) -> str:
        """Call LLM and return response text."""
        ...
```

**Option B: Abstract Base Class**
```python
from abc import ABC, abstractmethod

class LLMClient(ABC):
    @abstractmethod
    def call_llm(self, prompt: str, model: str, temperature: float) -> str:
        """Call LLM and return response text."""
        pass
```

**Recommendation**: Use Protocol for lighter weight, ABC if you need shared logic

---

#### Task 6: Implement OpenAIClient

**Responsibilities**:
- Initialize with API key
- Format messages for OpenAI's chat completion API
- Extract response text from JSON response
- Handle OpenAI-specific errors

**Key implementation details**:
```python
import openai

class OpenAIClient:
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)

    def call_llm(self, prompt: str, model: str, temperature: float) -> str:
        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an expert technical interviewer."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=1000  # Adjust based on needs
        )
        return response.choices[0].message.content
```

**Error scenarios to handle**:
- `AuthenticationError` → "Invalid API key"
- `RateLimitError` → Retry with backoff
- `APIConnectionError` → "Network error, please retry"
- `Timeout` → "Request timed out"

---

#### Task 7: Implement AnthropicClient

**Similar to OpenAI but uses Anthropic SDK**:
```python
import anthropic

class AnthropicClient:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)

    def call_llm(self, prompt: str, model: str, temperature: float) -> str:
        message = self.client.messages.create(
            model=model,
            max_tokens=1000,
            temperature=temperature,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return message.content[0].text
```

**Note**: Anthropic uses different message format (no system message in messages array)

---

#### Task 8: Implement MockLLMClient

**Purpose**: Testing without API calls

**Strategy**: Return canned responses based on keywords in prompt

**Example implementation**:
```python
class MockLLMClient:
    def call_llm(self, prompt: str, model: str, temperature: float) -> str:
        # Check for keywords in prompt to determine response
        if "perfect answer" in prompt.lower() or all(kw in prompt.lower() for kw in ["recursion", "base case"]):
            return self._perfect_response()
        elif "partial answer" in prompt.lower():
            return self._partial_response()
        else:
            return self._weak_response()

    def _perfect_response(self) -> str:
        return '''
        {
          "keypoints_coverage": [
            {"keypoint": "...", "covered": true, "evidence": "..."},
            {"keypoint": "...", "covered": true, "evidence": "..."}
          ],
          "score": 95,
          "mastery_label": "strong",
          "feedback": "Excellent answer covering all key concepts.",
          "suggested_followup": ""
        }
        '''
```

**Benefits**:
- Tests run instantly
- No API costs
- Deterministic results
- Can simulate edge cases

---

#### Task 9: Add factory function and error handling

**Factory function**:
```python
def get_llm_client(provider: str, api_key: str) -> LLMClient:
    if provider == "openai":
        return OpenAIClient(api_key)
    elif provider == "anthropic":
        return AnthropicClient(api_key)
    elif provider == "mock":
        return MockLLMClient()
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
```

**Retry logic** (add as decorator or wrapper):
```python
import time
from functools import wraps

def retry_on_failure(max_retries=2, delay=1.0):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except (RateLimitError, APIConnectionError) as e:
                    if attempt == max_retries:
                        raise
                    time.sleep(delay * (attempt + 1))  # Exponential backoff
            return func(*args, **kwargs)
        return wrapper
    return decorator
```

**Timeout handling**: Use timeout parameter in API calls

---

### Stage 3: LLM Evaluator Implementation (Tasks 10-13)

**Goal**: Create LLMEvaluatorAgent that matches EvaluatorAgent interface

#### Task 10: Create llm_evaluator.py skeleton

**File structure**:
```python
from models import Question, EvaluationResult, KeypointCoverage
from llm_client import LLMClient
import json

class LLMEvaluatorAgent:
    """
    LLM-powered evaluator that semantically analyzes candidate answers.

    Drop-in replacement for EvaluatorAgent with same interface.
    Uses LLM to understand answer quality beyond keyword matching.
    """

    def __init__(self, llm_client: LLMClient, model: str, temperature: float):
        self.llm_client = llm_client
        self.model = model
        self.temperature = temperature

    def evaluate(self, question: Question, answer: str) -> EvaluationResult:
        """
        Evaluate candidate answer using LLM.

        Same interface as EvaluatorAgent.evaluate().
        """
        pass  # Implement in next tasks
```

**Design note**: Takes LLMClient as dependency injection for testability

---

#### Task 11: Design evaluation prompt template

**Template structure** (based on claude.md spec):

```python
EVALUATION_PROMPT = """You are an expert technical interviewer evaluating a candidate's answer.

QUESTION:
{question_text}

COMPETENCY: {competency}
DIFFICULTY: {difficulty}

GROUND TRUTH KEYPOINTS (the candidate should cover these):
{keypoints_numbered}

CANDIDATE'S ANSWER:
{candidate_answer}

TASK:
1. For each keypoint, determine if it was adequately covered in the answer.
   - Mark as "covered" if the concept is present (even if phrased differently)
   - Provide a brief evidence snippet showing where it was covered (or note if missing)

2. Assign an overall score from 0-100 based on:
   - Keypoint coverage (primary factor: each keypoint = {points_per_keypoint} points)
   - Depth of explanation (bonus up to 10 points)
   - Accuracy of information (deduct for errors)
   - Clarity of communication (minor factor)

3. Classify mastery level:
   - "strong": 80-100 points (comprehensive understanding)
   - "mixed": 50-79 points (partial understanding, gaps present)
   - "weak": 0-49 points (significant gaps or misconceptions)

4. Generate short feedback (2-3 sentences) explaining the score and what was strong/weak.

5. If score < 80 and some keypoints were covered, suggest ONE follow-up question to probe the missing concepts.
   If score >= 80, leave suggested_followup empty.

OUTPUT FORMAT (strict JSON, no other text):
{{
  "keypoints_coverage": [
    {{"keypoint": "First keypoint text", "covered": true, "evidence": "Quote showing where addressed"}},
    {{"keypoint": "Second keypoint text", "covered": false, "evidence": "Not mentioned"}}
  ],
  "score": 75,
  "mastery_label": "mixed",
  "feedback": "Answer covers X and Y well but misses Z. Explanation of X was thorough.",
  "suggested_followup": "Can you explain how Z relates to X?"
}}

EXAMPLE 1 - Strong Answer:
Question: "What is recursion?"
Keypoints: ["base case", "recursive case", "stack usage"]
Answer: "Recursion is when a function calls itself. You need a base case to stop, and a recursive case that moves toward it. Each call uses stack memory."

Output:
{{
  "keypoints_coverage": [
    {{"keypoint": "base case", "covered": true, "evidence": "mentioned 'base case to stop'"}},
    {{"keypoint": "recursive case", "covered": true, "evidence": "described 'recursive case that moves toward it'"}},
    {{"keypoint": "stack usage", "covered": true, "evidence": "stated 'uses stack memory'"}}
  ],
  "score": 95,
  "mastery_label": "strong",
  "feedback": "Excellent concise answer covering all key concepts of recursion with correct terminology.",
  "suggested_followup": ""
}}

Now evaluate the candidate's answer above and output ONLY the JSON.
"""
```

**Implementation**:
```python
def _build_prompt(self, question: Question, answer: str) -> str:
    keypoints_numbered = "\n".join(
        f"{i+1}. {kp}" for i, kp in enumerate(question.keypoints)
    )
    points_per_keypoint = 100 // len(question.keypoints) if question.keypoints else 100

    return EVALUATION_PROMPT.format(
        question_text=question.text,
        competency=question.competency,
        difficulty=question.difficulty,
        keypoints_numbered=keypoints_numbered,
        points_per_keypoint=points_per_keypoint,
        candidate_answer=answer if answer.strip() else "[Empty answer]"
    )
```

---

#### Task 12: Implement evaluate() method

**Full implementation**:
```python
def evaluate(self, question: Question, answer: str) -> EvaluationResult:
    # Step 1: Build prompt
    prompt = self._build_prompt(question, answer)

    # Step 2: Call LLM
    try:
        response = self.llm_client.call_llm(prompt, self.model, self.temperature)
    except Exception as e:
        # Log error and return fallback
        return self._error_fallback(question, answer, str(e))

    # Step 3: Parse JSON response
    try:
        result = self._parse_response(response, question, answer)
        return result
    except Exception as e:
        # Parsing failed, return fallback
        return self._error_fallback(question, answer, f"Parse error: {e}")
```

---

#### Task 13: Add response parsing and error handling

**Parsing logic**:
```python
def _parse_response(self, response: str, question: Question, answer: str) -> EvaluationResult:
    # Extract JSON from response (may have extra text)
    json_start = response.find('{')
    json_end = response.rfind('}') + 1
    if json_start == -1 or json_end == 0:
        raise ValueError("No JSON found in response")

    json_str = response[json_start:json_end]
    data = json.loads(json_str)

    # Build KeypointCoverage list
    coverage = [
        KeypointCoverage(
            keypoint=item["keypoint"],
            covered=item["covered"],
            evidence=item["evidence"]
        )
        for item in data["keypoints_coverage"]
    ]

    # Build EvaluationResult
    return EvaluationResult(
        question_id=question.id,
        raw_answer=answer,
        score_0_100=data["score"],
        mastery_label=data["mastery_label"],
        keypoints_coverage=coverage,
        short_feedback=data["feedback"],
        suggested_followup=data.get("suggested_followup", "")
    )

def _error_fallback(self, question: Question, answer: str, error: str) -> EvaluationResult:
    """Return a safe error result if LLM fails"""
    return EvaluationResult(
        question_id=question.id,
        raw_answer=answer,
        score_0_100=0,
        mastery_label="weak",
        keypoints_coverage=[
            KeypointCoverage(keypoint=kp, covered=False, evidence="Evaluation error")
            for kp in question.keypoints
        ],
        short_feedback=f"Unable to evaluate: {error}",
        suggested_followup=""
    )
```

---

### Stage 4: UI Integration (Tasks 14-16)

**Goal**: Add evaluator selection to Streamlit UI

#### Task 14: Add sidebar evaluator mode toggle

**Location**: Top of `app.py`, before view selection

**Code**:
```python
st.sidebar.header("⚙️ Configuration")

# Evaluator mode selection
evaluator_mode = st.sidebar.radio(
    "Evaluation Method",
    ["Heuristic (Fast, Offline)", "LLM-Powered (AI)"],
    help="""
    Heuristic: Simple keyword matching, instant results, no API costs
    LLM-Powered: AI semantic analysis, richer feedback, requires API key
    """
)

# Store in session state
st.session_state.evaluator_mode = evaluator_mode
```

---

#### Task 15: Implement evaluator selection logic

**Initialization code**:
```python
def initialize_evaluator():
    """Initialize evaluator based on selected mode"""
    from settings import LLM_PROVIDER, OPENAI_API_KEY, ANTHROPIC_API_KEY, LLM_MODEL, LLM_TEMPERATURE
    from llm_client import get_llm_client
    from llm_evaluator import LLMEvaluatorAgent
    from agents import EvaluatorAgent

    mode = st.session_state.get('evaluator_mode', 'Heuristic (Fast, Offline)')

    if mode == "Heuristic (Fast, Offline)":
        return EvaluatorAgent()
    else:
        # Check if API key configured
        api_key = OPENAI_API_KEY if LLM_PROVIDER == "openai" else ANTHROPIC_API_KEY

        if not api_key or api_key == "your-key-here":
            st.sidebar.error("❌ LLM API key not configured. Using heuristic fallback.")
            st.sidebar.info("To use LLM evaluation: Create `.env` file from `.env.example` and add your API key")
            return EvaluatorAgent()

        try:
            client = get_llm_client(LLM_PROVIDER, api_key)
            return LLMEvaluatorAgent(client, LLM_MODEL, LLM_TEMPERATURE)
        except Exception as e:
            st.sidebar.error(f"❌ LLM initialization failed: {e}")
            st.sidebar.info("Falling back to heuristic evaluator")
            return EvaluatorAgent()

# Use in main code
if 'evaluator_agent' not in st.session_state:
    st.session_state.evaluator_agent = initialize_evaluator()
```

---

#### Task 16: Add evaluator status display

**Status indicator**:
```python
# Show current evaluator status
evaluator = st.session_state.evaluator_agent
if isinstance(evaluator, LLMEvaluatorAgent):
    st.sidebar.success(f"✓ Using: LLM ({LLM_MODEL})")
    st.sidebar.caption(f"Provider: {LLM_PROVIDER}")
else:
    st.sidebar.info("Using: Heuristic (keyword matching)")

# Add button to reinitialize if switching modes
if st.sidebar.button("Apply Evaluator Change"):
    st.session_state.evaluator_agent = initialize_evaluator()
    st.rerun()
```

---

### Stage 5: Testing (Tasks 17-20)

**Goal**: Verify implementation works and maintain backward compatibility

#### Task 17: Create tests/test_llm_evaluator.py

**Test cases**:
```python
def test_prompt_construction():
    """Verify prompt includes all question fields"""

def test_response_parsing_valid_json():
    """Test parsing of well-formed LLM response"""

def test_response_parsing_malformed_json():
    """Test graceful handling of bad JSON"""

def test_error_fallback():
    """Test fallback when LLM call fails"""

def test_empty_answer():
    """Test evaluation of empty answer"""

def test_mock_client():
    """Test MockLLMClient returns expected format"""
```

**All tests use MockLLMClient** - no real API calls

---

#### Task 18: Add integration test

**Add to `tests/test_basic_flow.py`**:
```python
def test_llm_evaluator_integration():
    """Test that LLM evaluator works in full interview flow"""
    from llm_client import MockLLMClient
    from llm_evaluator import LLMEvaluatorAgent

    # Create agents with LLM evaluator
    questions_agent = QuestionsAgent(sample_questions)
    llm_evaluator = LLMEvaluatorAgent(MockLLMClient(), "gpt-4", 0.3)
    orchestrator = OrchestratorAgent(questions_agent, llm_evaluator)

    # Run interview
    state = InterviewState(current_index=0, finished=False, evaluations=[])
    state = orchestrator.step(state, "base case recursive case stack")

    # Verify same behavior as heuristic
    assert len(state.evaluations) == 1
    assert state.evaluations[0].score_0_100 > 0
    assert state.evaluations[0].mastery_label in ["strong", "mixed", "weak"]
```

---

#### Task 19: Run all existing tests

**Command**:
```bash
pytest tests/ -v
```

**Verify**:
- All existing tests still pass
- New LLM tests pass with MockLLMClient
- No API keys required to run tests
- Test execution time remains fast

---

#### Task 20: Manual testing with diverse answers

**Test script** (optional but recommended):
```python
# scripts/test_prompt_manually.py
from models import Question
from llm_client import MockLLMClient
from llm_evaluator import LLMEvaluatorAgent

def test_answer_types():
    q = Question(
        id="1",
        text="What is recursion?",
        competency="Python",
        difficulty="Medium",
        keypoints=["base case", "recursive case", "stack usage"]
    )

    evaluator = LLMEvaluatorAgent(MockLLMClient(), "gpt-4", 0.3)

    test_cases = [
        ("Perfect answer", "Recursion is when a function calls itself. Need a base case to stop and recursive case to continue. Uses call stack."),
        ("Partial answer", "A function that calls itself."),
        ("Poor answer", "Looping through data."),
        ("Off-topic", "Python is a programming language."),
        ("Empty", ""),
    ]

    for name, answer in test_cases:
        result = evaluator.evaluate(q, answer)
        print(f"\n{name}:")
        print(f"  Score: {result.score_0_100}")
        print(f"  Mastery: {result.mastery_label}")
        print(f"  Feedback: {result.short_feedback}")
```

---

## Decision Points

### Before Starting

**1. Which LLM provider to implement first?**
- ✅ **Recommended**: Implement both OpenAI and Anthropic
- ⚠️ **Alternative**: Start with OpenAI only (simpler, widely used)
- **Rationale**: Having both provides flexibility and fallback options

**2. Which model to use by default?**
- OpenAI options: `gpt-4`, `gpt-4-turbo`, `gpt-3.5-turbo`
- Anthropic options: `claude-3-5-sonnet-20241022`, `claude-3-opus-20240229`
- ✅ **Recommended**: `gpt-4` or `claude-3-5-sonnet-20241022` (best quality)
- 💰 **Budget option**: `gpt-3.5-turbo` (faster, cheaper, decent quality)

**3. Temperature setting?**
- Range: 0.0 (deterministic) to 1.0 (creative)
- ✅ **Recommended**: 0.3 (good balance for evaluation)
- **Rationale**: Low enough for consistency, high enough to handle variety

---

## Risk Mitigation

### Potential Issues & Solutions

**Issue**: API keys accidentally committed to git
- ✅ **Prevention**: Create `.gitignore` FIRST before any sensitive files

**Issue**: Tests fail without API keys
- ✅ **Prevention**: Use `MockLLMClient` by default in all tests

**Issue**: LLM responses are inconsistent
- ✅ **Mitigation**: Low temperature, clear prompt, Phase 6 regression tests

**Issue**: API costs accumulate unexpectedly
- ✅ **Mitigation**: Add logging, document costs, use cheaper models for testing

**Issue**: LLM parsing fails on malformed JSON
- ✅ **Mitigation**: Robust parsing, fallback to heuristic evaluator

---

## Success Criteria

Phase 5 is complete when:

✅ `.gitignore` prevents secrets from being committed
✅ `.env.example` documents all configuration
✅ `settings.py` loads configuration securely
✅ Both OpenAI and Anthropic clients work
✅ `MockLLMClient` provides realistic test responses
✅ `LLMEvaluatorAgent` can evaluate answers
✅ UI toggle switches between heuristic and LLM
✅ All tests pass without API keys
✅ Backward compatibility maintained
✅ Error handling gracefully falls back to heuristic

---

## Next Steps After Phase 5

**Immediate** (same session):
1. Update `STATUS.md` with completion
2. Document any issues or deviations from plan
3. Create sample `.env` file for your own testing

**Phase 6** (next session):
1. Create reference evaluation set
2. Build regression tests
3. Validate LLM quality manually
4. Document cost and performance metrics

---

## Estimated Timeline

**Conservative estimate** (includes breaks, debugging):
- Stage 1 (Infrastructure): 1-2 hours
- Stage 2 (LLM Client): 2-3 hours
- Stage 3 (LLM Evaluator): 3-4 hours
- Stage 4 (UI Integration): 1-2 hours
- Stage 5 (Testing): 2-3 hours
- **Total**: 9-14 hours (~2 days with breaks)

**Aggressive estimate** (experienced dev, no blockers):
- Full implementation: 6-8 hours (~1 day)

---

## Notes & Reminders

- Keep the heuristic evaluator working - it's the fallback
- Test each component in isolation before integration
- Don't test with real API keys until MockLLMClient works
- Document any prompt changes for Phase 6 regression tests
- If stuck, refer to `claude.md` for architectural guidance

---

*Ready to begin? Start with Task 1: Create .gitignore*
