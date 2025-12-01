"""Authentication tests for the Streamlit UI."""

import sys
from pathlib import Path

import streamlit as st

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import app  # noqa: E402


class FakeSt:
    """Minimal stand-in for Streamlit state used by the auth flow."""

    def __init__(self, password_input: str, should_submit: bool):
        self.password_input = password_input
        self.should_submit = should_submit
        self.session_state = {}
        self.last_error = None
        self.rerun_called = False

    def title(self, *args, **kwargs):
        return None

    def subheader(self, *args, **kwargs):
        return None

    def form(self, *args, **kwargs):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def text_input(self, *args, **kwargs):
        return self.password_input

    def form_submit_button(self, *args, **kwargs):
        return self.should_submit

    def rerun(self):
        self.rerun_called = True

    def error(self, message):
        self.last_error = message


def test_password_required_even_without_llm(monkeypatch):
    """Authentication must still run when LLM dependencies are missing."""

    monkeypatch.setattr(app, "LLM_AVAILABLE", False)
    monkeypatch.setattr(app.settings, "APP_PASSWORD", "secret")
    fake_st = FakeSt(password_input="", should_submit=False)
    monkeypatch.setattr(app, "st", fake_st)

    assert app.check_password() is False
    assert not fake_st.session_state.get("authenticated")


def test_authenticated_only_after_correct_password(monkeypatch):
    """Session authentication flag should only be set on correct password."""

    monkeypatch.setattr(app.settings, "APP_PASSWORD", "secret")
    fake_st = FakeSt(password_input="wrong", should_submit=True)
    monkeypatch.setattr(app, "st", fake_st)

    assert app.check_password() is False
    assert not fake_st.session_state.get("authenticated")
    assert fake_st.last_error is not None

    fake_st.password_input = "secret"
    fake_st.should_submit = True
    assert app.check_password() is False
    assert fake_st.session_state.get("authenticated") is True
    assert fake_st.rerun_called is True
