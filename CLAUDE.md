<!-- AUTO-GENERATED from ports.json — do not edit manually -->
<!-- Regenerate: python3 ~/Development/generate_claude_md.py --apply -->

# Agentic Interview

Python project.

---

## Environment Setup

```bash
# Activate virtual environment (REQUIRED)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## Local Access

| Service | Domain | Port |
|---------|--------|------|
| Ui | http://agentic-interview.test | 8501 |

Port assignments defined in `~/Development/dev/ports.json`.

---

## Commands

```bash
# Start UI
streamlit run app.py --server.port 8501 --server.address 127.0.0.1 --server.headless true

# Run tests
pytest
```

---

## Structure

```
alembic/
  versions/
demo_audio/
scripts/
tests/
```

---

## Notes

- Tech: Python
