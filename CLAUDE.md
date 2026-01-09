# Agentic Interview

AI-powered interview system with multi-agent evaluation.

---

## Environment Setup

```bash
# Activate virtual environment (REQUIRED before any Python commands)
source .venv/bin/activate

# Install dependencies (if needed)
pip install -r requirements.txt
```

---

## Local Access

| Service | Domain | Port |
|---------|--------|------|
| Streamlit UI | http://agentic-interview.test | 8501 |

Port assignments are defined in `~/Development/dev/ports.json` (authoritative).

---

## Commands

```bash
# Start Streamlit app
streamlit run app.py --server.port 8501 --server.address 127.0.0.1 --server.headless true

# Run tests
pytest
```

---

## Notes

- Streamlit app for conducting AI-powered interviews
- Uses session state for runtime storage
- Multi-agent architecture (Orchestrator, Questions, Evaluator)

---

## Structure

```
alembic/
  versions/
demo_audio/
scripts/
tests/
```
