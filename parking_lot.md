# Feature Parking Lot

This document tracks potential future enhancements that are out of scope for the current implementation but worth considering for future development.

---

## Agent Architecture Enhancements

### Adaptive Interviewing
**Priority**: Medium
**Complexity**: High
**Description**: An "Interviewer Agent" that dynamically generates follow-up questions based on previous answers, creating a more conversational and probing interview experience.

**Implementation ideas**:
- Track session context across questions
- Generate follow-up prompts when answers are incomplete
- Allow configurable depth (0-3 follow-ups per question)
- Store follow-up Q&A in transcript

### Multi-Perspective Evaluation
**Priority**: Low
**Complexity**: High
**Description**: Multiple evaluator personas ("Technical Expert", "Communication Coach", "Culture Fit Assessor") that each evaluate the same answer and contribute different scores/feedback.

**Implementation ideas**:
- Define evaluator personas with different criteria weights
- Run parallel evaluations
- Aggregate scores with configurable weights
- Show breakdown by perspective in reports

### Research-Augmented Evaluation
**Priority**: Low
**Complexity**: Medium
**Description**: Agent that searches documentation/web for relevant context before evaluating technical answers (e.g., checking if cited APIs actually exist).

**Implementation ideas**:
- Integrate web search tool (Tavily, SerpAPI)
- Allow reference material uploads per template
- Cache research results to reduce API calls

### Dynamic Question Generation
**Priority**: Medium
**Complexity**: High
**Description**: Agent crew that collaborates to create new interview questions based on job requirements, competency frameworks, or existing question patterns.

**Implementation ideas**:
- Input: job description, competency list, difficulty distribution
- Output: new TemplateQuestions with keypoints
- Human-in-the-loop review before adding to bank
- Quality scoring based on existing high-performing questions

### Collaborative Debrief Generation
**Priority**: Low
**Complexity**: High
**Description**: Multiple agent personas (Hiring Manager, Technical Lead, HR) that each contribute to final assessment, simulating a hiring committee discussion.

**Implementation ideas**:
- Define persona prompts with different priorities
- Sequential or consensus-based deliberation
- Generate meeting-style summary document
- Include dissenting opinions if present

---

## Technical Improvements

### Async/Parallel Lens Execution
**Priority**: High
**Complexity**: Low
**Description**: Execute multiple lenses on a session concurrently instead of sequentially.

```python
import asyncio

async def execute_all_lenses_parallel(session_id, lens_ids):
    tasks = [execute_lens(session_id, lid) for lid in lens_ids]
    return await asyncio.gather(*tasks)
```

### Session Context Memory
**Priority**: Medium
**Complexity**: Medium
**Description**: Allow evaluators to reference previous answers in the same session for better context-aware evaluation.

**Implementation ideas**:
- Include summary of previous Q&A in evaluation prompt
- Track competency coverage across questions
- Adjust difficulty based on performance

### Streaming LLM Responses
**Priority**: Low
**Complexity**: Medium
**Description**: Stream evaluation results to UI as they're generated instead of waiting for full response.

**Implementation ideas**:
- Use OpenAI/Anthropic streaming APIs
- Progressive UI updates
- Better perceived performance

### Evaluation Caching
**Priority**: Medium
**Complexity**: Low
**Description**: Cache LLM evaluation results to avoid re-evaluation of identical question/answer pairs.

**Implementation ideas**:
- Hash question + answer for cache key
- TTL-based expiration
- Invalidate on prompt template changes

---

## UI/UX Improvements

### Real-time Collaboration
**Priority**: Low
**Complexity**: High
**Description**: Multiple interviewers can observe and annotate a live interview session.

### Interview Recording/Playback
**Priority**: Medium
**Complexity**: Medium
**Description**: Record interview sessions with timestamps and allow playback with synchronized transcript.

### Candidate Self-Service Portal
**Priority**: Medium
**Complexity**: Medium
**Description**: Candidates can access their scheduled interviews, complete them asynchronously, and view sanitized feedback.

### Mobile-Responsive UI
**Priority**: Low
**Complexity**: Low
**Description**: Optimize Streamlit layout for tablet/mobile devices.

---

## Analytics & Reporting

### Competency Gap Analysis
**Priority**: Medium
**Complexity**: Medium
**Description**: Aggregate analysis across candidates to identify common knowledge gaps for training recommendations.

### Interviewer Calibration
**Priority**: Low
**Complexity**: High
**Description**: Compare human evaluations vs. LLM evaluations to identify interviewer bias or calibration issues.

### Question Effectiveness Metrics
**Priority**: Medium
**Complexity**: Low
**Description**: Track which questions best differentiate candidate performance levels.

---

## Integration Ideas

### ATS Integration
**Priority**: High
**Complexity**: High
**Description**: Integrate with Applicant Tracking Systems (Greenhouse, Lever, etc.) to pull candidate info and push results.

### Calendar Integration
**Priority**: Medium
**Complexity**: Medium
**Description**: Schedule interviews via Google Calendar/Outlook integration.

### Slack/Teams Notifications
**Priority**: Low
**Complexity**: Low
**Description**: Notify hiring team when interviews complete or need review.

---

## Framework Considerations

### CrewAI Migration
**Status**: Not recommended for current use case
**Revisit when**: Adding adaptive interviewing or multi-agent collaboration features
**Notes**: Current architecture is simpler, more testable, and appropriate for linear interview flows. CrewAI would add complexity without proportional benefit for current requirements.

### LangGraph Alternative
**Status**: Worth exploring
**Use case**: If we need stateful, graph-based conversation flows
**Notes**: Better fit than CrewAI for structured interview flows with conditional branching.

---

*Last updated: 2025-11-26*
