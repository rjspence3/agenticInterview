# Agentic Interview System

**An AI-powered technical interview platform with intelligent evaluation and lens-based analysis.**

The Agentic Interview System enables organizations to conduct structured technical interviews with automated evaluation, sophisticated lens-based analysis, and comprehensive reporting. Built with modular AI agents, the system supports both heuristic and LLM-powered evaluation strategies.

---

## Key Features

- **People & Organization Management**: Track candidates, roles, and departments
- **Interview Templates**: Create reusable interview templates with questions, competencies, and keypoints
- **Dual Evaluation System**: Choose between fast heuristic evaluation or sophisticated LLM-based assessment
- **Chat Interview Mode**: Conversational chat-based interview experience with real-time feedback
- **Raise Hand + Admin Chat**: Real-time interviewee-to-admin communication during interviews
- **Live Session Monitoring**: Admins can monitor, join, and control active interview sessions
- **Lens-Based Analysis**: Apply customizable analytical lenses to extract structured insights from interview transcripts
- **Reports & Analytics**: View performance trends, score distributions, and department breakdowns
- **Export Functionality**: Export session data as JSON and filtered reports as CSV
- **Multi-Tenant Architecture**: Organization-scoped data with proper isolation
- **Full Audit Trail**: Complete transcript recording and traceability

## Evaluation roadmap and current heuristic limitations

The default `EvaluatorAgent` uses a lightweight substring-based heuristic to stay fast and deterministic. This approach is acceptable for smoke-testing but has important limitations:
- Misses paraphrased or synonymous concepts because it only checks for literal keypoint strings
- Cannot judge answer accuracy or depth, which can over-score shallow responses
- Generates at most one generic follow-up question and cannot probe multiple gaps
- Treats any keyword hit as equal, under-weighting explanation quality and context

To mitigate these gaps, the `LLMEvaluatorAgent` is the planned default whenever LLM credentials are configured. The transition plan is tracked in **parking_lot.md → LLM Evaluator Rollout** and will:
- Auto-select the LLM evaluator when API keys are present while preserving heuristic fallback behavior
- Provide semantic coverage, richer feedback, and keypoint-specific follow-ups for missing concepts
- Add regression tests that cover both modes and the routing logic

---

## 🚀 Quick Start

### Prerequisites

- **Python**: 3.10 or higher
- **pip**: Package installer for Python
- **Virtual environment** (recommended)

### Installation

1. **Clone the repository**:
   ```bash
   cd agenticInterview
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables** (for LLM evaluation - optional):
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys:
   # OPENAI_API_KEY=sk-...
   # or
   # ANTHROPIC_API_KEY=sk-ant-...
   ```

5. **Initialize the database**:
   ```bash
   python3 -c "from database import init_db; init_db()"
   ```

6. **Seed with sample data** (optional but recommended):
   ```bash
   python3 seed_data.py
   ```

7. **Run the application**:
   ```bash
   streamlit run app.py
   ```

8. **Open your browser** to `http://http://agentic-interview.test`

---

## 📖 Usage Guide

### Admin Dashboard

1. **Navigate to the Admin view** from the sidebar
2. **Add People**: Create profiles for interviewees with roles, departments, and tags
3. **Create Templates**: Build interview templates with questions, keypoints, and difficulty levels
4. **Configure Lenses**: Define analytical lenses with custom criteria for post-interview analysis
5. **Live Sessions**: Monitor active interviews, see raised hands, and join sessions to assist

### Conducting Interviews

1. **Navigate to the Interviewee view** from the sidebar
2. **Select Evaluator Mode**: Choose between Heuristic (fast, offline) or LLM-Powered (requires API key)
3. **Choose Person and Template**: Select the interviewee and interview template
4. **Select Interview Mode**: Classic (step-by-step) or Chat (conversational experience)
5. **Start Interview**: Answer questions with immediate feedback
6. **Raise Hand** (optional): Request admin assistance if you need help
7. **View Summary**: See overall performance and lens analysis results (if LLM mode enabled)

### Reports & Analytics

1. **Navigate to the Reports view** from the sidebar
2. **Apply Filters**: Filter by date range, department, role, template, or status
3. **View Metrics**: See total sessions, completion rate, average scores, and lens analysis count
4. **Analyze Charts**: Review score distribution histogram and department performance breakdown
5. **Drill Down**: Click any session to view detailed transcript, evaluations, and lens results
6. **Export Data**: Download filtered sessions as CSV or individual session details as JSON

---

## 🏗️ Architecture Overview

### Core Components

- **models.py**: Data classes for questions, evaluations, and interview state
- **agents.py**: Core business logic agents (Questions, Evaluator, Orchestrator)
- **db_models.py**: SQLAlchemy ORM models for all database entities
- **app.py**: Streamlit UI with Admin, Interviewee, and Reports views
- **llm_client.py**: Provider-agnostic LLM interface (OpenAI, Anthropic)
- **llm_evaluator.py**: LLM-powered evaluation agent
- **lens_executor.py**: Lens analysis execution pipeline
- **lens_prompt_builder.py**: Prompt construction for lens analysis

### Database Schema

The system uses SQLAlchemy with Alembic migrations and supports both SQLite (dev) and PostgreSQL (production):

- **Organization**: Multi-tenant org container
- **Person**: Interviewee profiles
- **InterviewTemplate**: Reusable interview blueprints
- **TemplateQuestion**: Questions within templates
- **InterviewSession**: Individual interview instances
- **TranscriptEntry**: Full conversation records
- **QuestionEvaluation**: Per-question assessment results
- **Lens**: Analytical lens configurations
- **LensResult**: Lens analysis outcomes
- **LensCriterionResult**: Per-criterion scores and notes

---

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_basic_flow.py -v
pytest tests/test_llm_evaluator.py -v
pytest tests/test_lens_pipeline.py -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

**Test Coverage**:
- ✅ Core agent logic (QuestionsAgent, EvaluatorAgent, OrchestratorAgent)
- ✅ LLM evaluation pipeline (with mocked responses)
- ✅ Lens analysis system (prompt building, execution, parsing)
- ✅ Database models and relationships
- ✅ Full interview flow simulation

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file (see `.env.example` for template):

```env
# LLM Provider (openai or anthropic)
LLM_PROVIDER=openai

# API Keys (provide one based on provider)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# LLM Model Configuration
LLM_MODEL=gpt-4  # or: gpt-3.5-turbo, claude-3-5-sonnet-20241022
LLM_TEMPERATURE=0.3

# Logging (optional)
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### Database Configuration

By default, the system uses SQLite (`interview_system.db`). For production, configure PostgreSQL connection in `database.py`.

---

## 📚 Documentation

For detailed architectural context and development guidance:

- **[CLAUDE.md](CLAUDE.md)**: Project context, architecture decisions, and LLM evaluator design
- **[plan.md](plan.md)**: Implementation plan with phases 0-7
- **[STATUS.md](STATUS.md)**: Current implementation status and metrics
- **[NEXT_STEPS.md](NEXT_STEPS.md)**: Phase 7 progress and remaining enhancements

---

## Current Limitations

- **No Voice/Video**: Text-based interviews only
- **Single-Tenant UI**: Multi-tenant data model exists but no UI for org switching
- **No Authentication**: Security and user management not implemented
- **SQLite for MVP**: Production deployment requires PostgreSQL
- **Single Admin Per Session**: Only one admin can control a session at a time
- **Heuristic Evaluator Only**: The default `EvaluatorAgent` uses simple substring checks against keypoints and does not generate personalized follow-up questions or clarifications.

---

## 🔮 Future Roadmap

### Planned Enhancements

- **Advanced Analytics**: Trend analysis, comparative reports, custom report builder
- **Lens Improvements**: Versioning, A/B testing, performance benchmarking
- **Integration & Automation**: Webhooks, email reports, API endpoints
- **UI Enhancements**: Dark mode, customizable dashboards, saved filter presets
- **Performance**: Async lens execution, caching, query optimization
- **Multi-Tenancy**: User authentication, role-based permissions, audit logging

---

## 🤝 Contributing

This is an MVP system. For questions or issues:

1. Review `CLAUDE.md` for architectural decisions
2. Check `HISTORY.md` for implementation details
3. Run tests to verify system integrity
4. Consult `seed_data.py` for example data structures

---

## 📄 License

[Specify your license here]

---

## 🙏 Acknowledgments

Built with:
- **Streamlit**: Modern web UI framework
- **SQLAlchemy**: Python SQL toolkit and ORM
- **OpenAI / Anthropic**: LLM providers for intelligent evaluation
- **Alembic**: Database migration tool

---

**The system is production-ready for MVP deployment with core lens functionality complete!**

For support and detailed documentation, see the project docs in the repository.
