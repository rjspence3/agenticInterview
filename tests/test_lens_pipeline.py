"""
Tests for Phase 7 Lens Analysis Pipeline.

Tests the complete lens analysis workflow:
- Lens configuration validation
- Prompt building
- LLM response parsing
- Database storage of results
"""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, MagicMock

# Import modules to test
from lens_prompt_builder import (
    build_lens_prompt,
    validate_lens_config,
    get_example_lens_config,
    _format_transcript,
    _format_criteria,
    _format_output_schema
)
from lens_executor import LensExecutor
from db_models import (
    Lens, LensResult, LensCriterionResult, LensResultStatus,
    InterviewSession, SessionStatus, TranscriptEntry, SpeakerType,
    Organization, Person, PersonStatus, InterviewTemplate
)


class TestLensConfiguration:
    """Test lens configuration validation and examples."""

    def test_valid_lens_config(self):
        """Test that valid lens configurations pass validation."""
        config = {
            "criteria": [
                {
                    "name": "test_criterion",
                    "definition": "A test criterion",
                    "examples": ["example1", "example2"]
                }
            ],
            "scoring_scale": "0-5"
        }

        is_valid, error_msg = validate_lens_config(config)
        assert is_valid
        assert error_msg == ""

    def test_missing_criteria(self):
        """Test that config without criteria fails validation."""
        config = {"scoring_scale": "0-5"}

        is_valid, error_msg = validate_lens_config(config)
        assert not is_valid
        assert "criteria" in error_msg.lower()

    def test_empty_criteria_list(self):
        """Test that config with empty criteria list fails validation."""
        config = {
            "criteria": [],
            "scoring_scale": "0-5"
        }

        is_valid, error_msg = validate_lens_config(config)
        assert not is_valid
        assert "at least one criterion" in error_msg.lower()

    def test_criterion_missing_name(self):
        """Test that criterion without name fails validation."""
        config = {
            "criteria": [
                {
                    "definition": "A test criterion",
                    "examples": ["example1"]
                }
            ],
            "scoring_scale": "0-5"
        }

        is_valid, error_msg = validate_lens_config(config)
        assert not is_valid
        assert "name" in error_msg.lower()

    def test_criterion_missing_definition(self):
        """Test that criterion without definition fails validation."""
        config = {
            "criteria": [
                {
                    "name": "test_criterion",
                    "examples": ["example1"]
                }
            ],
            "scoring_scale": "0-5"
        }

        is_valid, error_msg = validate_lens_config(config)
        assert not is_valid
        assert "definition" in error_msg.lower()

    def test_example_lens_configs(self):
        """Test that all example lens configs are valid."""
        lens_types = ["debugging", "communication", "system_design"]

        for lens_type in lens_types:
            config = get_example_lens_config(lens_type)
            is_valid, error_msg = validate_lens_config(config)
            assert is_valid, f"{lens_type} lens config invalid: {error_msg}"

            # Check structure
            assert "criteria" in config
            assert len(config["criteria"]) > 0
            assert "scoring_scale" in config


class TestPromptBuilder:
    """Test lens prompt building functionality."""

    def test_format_transcript(self):
        """Test transcript formatting."""
        transcript = [
            Mock(speaker=SpeakerType.SYSTEM, text="What is Python?"),
            Mock(speaker=SpeakerType.PARTICIPANT, text="Python is a programming language")
        ]

        formatted = _format_transcript(transcript)

        assert "INTERVIEWER" in formatted
        assert "CANDIDATE" in formatted
        assert "What is Python?" in formatted
        assert "Python is a programming language" in formatted

    def test_format_transcript_with_admin(self):
        """Admin speakers should be labeled distinctly."""
        transcript = [
            Mock(speaker=SpeakerType.ADMIN, text="Please keep answers concise."),
            Mock(speaker=SpeakerType.PARTICIPANT, text="Understood."),
        ]

        formatted = _format_transcript(transcript)

        assert "[ADMIN]: Please keep answers concise." in formatted
        assert "[CANDIDATE]: Understood." in formatted

    def test_format_criteria(self):
        """Test criteria formatting."""
        criteria = [
            {
                "name": "clarity",
                "definition": "Clear explanation",
                "examples": ["simple language", "concrete examples"]
            }
        ]

        formatted = _format_criteria(criteria, "0-5")

        assert "clarity" in formatted
        assert "Clear explanation" in formatted
        assert "simple language" in formatted
        assert "0-5" in formatted

    def test_format_output_schema(self):
        """Test output schema formatting."""
        schema = _format_output_schema("0-10")

        assert "criteria_results" in schema
        assert "criterion" in schema
        assert "score" in schema
        assert "0-10" in schema

    def test_build_complete_prompt(self):
        """Test building a complete lens prompt."""
        # Create mock lens
        lens = Mock()
        lens.name = "Test Lens"
        lens.description = "A test lens"
        lens.config = {
            "criteria": [
                {
                    "name": "test_criterion",
                    "definition": "A test",
                    "examples": ["example"]
                }
            ],
            "scoring_scale": "0-5",
            "examples": []
        }

        # Create mock session and transcript
        session = Mock()
        transcript = [
            Mock(speaker=SpeakerType.SYSTEM, text="Question"),
            Mock(speaker=SpeakerType.PARTICIPANT, text="Answer")
        ]

        prompt = build_lens_prompt(lens, session, transcript)

        # Check all key sections are present
        assert "Test Lens" in prompt
        assert "A test lens" in prompt
        assert "TRANSCRIPT:" in prompt
        assert "ASSESSMENT CRITERIA:" in prompt
        assert "test_criterion" in prompt
        assert "OUTPUT FORMAT" in prompt
        assert "Question" in prompt
        assert "Answer" in prompt

    def test_build_prompt_with_admin_messages(self):
        """Prompt should preserve admin speaker labels."""
        lens = Mock()
        lens.name = "Admin Lens"
        lens.description = "Lens with admin messages"
        lens.config = {
            "criteria": [
                {
                    "name": "test_criterion",
                    "definition": "A test",
                    "examples": ["example"]
                }
            ],
            "scoring_scale": "0-5",
            "examples": []
        }

        session = Mock()
        transcript = [
            Mock(speaker=SpeakerType.ADMIN, text="Reminder to stay on topic."),
            Mock(speaker=SpeakerType.SYSTEM, text="Primary question"),
            Mock(speaker=SpeakerType.PARTICIPANT, text="Primary answer"),
        ]

        prompt = build_lens_prompt(lens, session, transcript)

        assert "[ADMIN]: Reminder to stay on topic." in prompt
        assert "[INTERVIEWER]: Primary question" in prompt
        assert "[CANDIDATE]: Primary answer" in prompt


class TestLensExecutor:
    """Test lens executor with mocked LLM."""

    def test_parse_llm_response_valid_json(self):
        """Test parsing valid JSON response."""
        lens = Mock()
        lens.config = {
            "criteria": [
                {"name": "clarity", "definition": "Clear explanation"},
                {"name": "depth", "definition": "Deep understanding"}
            ],
            "scoring_scale": "0-5"
        }

        response = json.dumps({
            "criteria_results": [
                {
                    "criterion": "clarity",
                    "score": 4,
                    "flags": ["clear"],
                    "extracted_items": ["used examples"],
                    "supporting_quotes": [{"speaker": "candidate", "text": "For example..."}],
                    "notes": "Good clarity"
                },
                {
                    "criterion": "depth",
                    "score": 3,
                    "flags": [],
                    "extracted_items": [],
                    "supporting_quotes": [],
                    "notes": "Moderate depth"
                }
            ]
        })

        mock_client = Mock()
        executor = LensExecutor(mock_client)

        results = executor._parse_llm_response(response, lens)

        assert len(results) == 2
        assert results[0]["criterion"] == "clarity"
        assert results[0]["score"] == 4
        assert results[1]["criterion"] == "depth"
        assert results[1]["score"] == 3

    def test_parse_llm_response_with_markdown(self):
        """Test parsing JSON wrapped in markdown code blocks."""
        lens = Mock()
        lens.config = {
            "criteria": [{"name": "test", "definition": "Test"}],
            "scoring_scale": "0-5"
        }

        response = """```json
{
  "criteria_results": [
    {
      "criterion": "test",
      "score": 5,
      "notes": "Excellent"
    }
  ]
}
```"""

        mock_client = Mock()
        executor = LensExecutor(mock_client)

        results = executor._parse_llm_response(response, lens)

        assert len(results) == 1
        assert results[0]["criterion"] == "test"
        assert results[0]["score"] == 5

    def test_parse_llm_response_missing_criteria_results(self):
        """Test that response missing criteria_results raises error."""
        lens = Mock()
        lens.config = {"criteria": [], "scoring_scale": "0-5"}

        response = json.dumps({"wrong_key": []})

        mock_client = Mock()
        executor = LensExecutor(mock_client)

        with pytest.raises(ValueError, match="criteria_results"):
            executor._parse_llm_response(response, lens)

    def test_parse_llm_response_invalid_json(self):
        """Test that invalid JSON raises error."""
        lens = Mock()
        lens.config = {"criteria": [], "scoring_scale": "0-5"}

        response = "This is not valid JSON"

        mock_client = Mock()
        executor = LensExecutor(mock_client)

        with pytest.raises(ValueError, match="JSON"):
            executor._parse_llm_response(response, lens)

    def test_get_provider_name(self):
        """Test provider name detection."""
        # Test OpenAI
        mock_client = Mock()
        mock_client.__class__.__name__ = "OpenAIClient"
        executor = LensExecutor(mock_client)
        assert executor._get_provider_name() == "openai"

        # Test Anthropic
        mock_client.__class__.__name__ = "AnthropicClient"
        executor = LensExecutor(mock_client)
        assert executor._get_provider_name() == "anthropic"

        # Test Mock
        mock_client.__class__.__name__ = "MockLLMClient"
        executor = LensExecutor(mock_client)
        assert executor._get_provider_name() == "mock"

        # Test unknown
        mock_client.__class__.__name__ = "UnknownClient"
        executor = LensExecutor(mock_client)
        assert executor._get_provider_name() == "unknown"


class TestLensExecutorIntegration:
    """Integration tests for lens executor with database."""

    @pytest.fixture
    def db_session(self):
        """Create an in-memory database session for testing."""
        from database import init_db, get_db_session
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        # Create in-memory database
        engine = create_engine("sqlite:///:memory:")
        Session = sessionmaker(bind=engine)

        # Initialize schema
        from db_models import Base
        Base.metadata.create_all(engine)

        session = Session()
        yield session
        session.close()

    @pytest.fixture
    def sample_session(self, db_session):
        """Create a sample completed interview session."""
        # Create organization
        org = Organization(name="Test Org", settings={})
        db_session.add(org)
        db_session.flush()

        # Create person
        person = Person(
            organization_id=org.id,
            name="Test Person",
            email="test@example.com",
            status=PersonStatus.ACTIVE
        )
        db_session.add(person)
        db_session.flush()

        # Create template
        template = InterviewTemplate(
            organization_id=org.id,
            name="Test Template",
            version=1,
            active=True
        )
        db_session.add(template)
        db_session.flush()

        # Create session
        session = InterviewSession(
            organization_id=org.id,
            template_id=template.id,
            person_id=person.id,
            status=SessionStatus.COMPLETED
        )
        db_session.add(session)
        db_session.flush()

        # Add transcript
        db_session.add(TranscriptEntry(
            session_id=session.id,
            sequence_index=0,
            speaker=SpeakerType.SYSTEM,
            text="What is Python?"
        ))
        db_session.add(TranscriptEntry(
            session_id=session.id,
            sequence_index=1,
            speaker=SpeakerType.PARTICIPANT,
            text="Python is a high-level programming language."
        ))
        db_session.flush()

        return session.id, org.id

    @pytest.fixture
    def sample_lens(self, db_session, sample_session):
        """Create a sample lens."""
        _, org_id = sample_session

        lens = Lens(
            organization_id=org_id,
            name="Test Lens",
            description="A test lens",
            config=get_example_lens_config("debugging"),
            active=True,
            version=1
        )
        db_session.add(lens)
        db_session.flush()

        return lens.id

    def test_execute_lens_with_mock_llm(self, db_session, sample_session, sample_lens):
        """Test executing a lens with mocked LLM response."""
        session_id, org_id = sample_session

        # Create mock LLM client
        mock_client = Mock()
        mock_client.__class__.__name__ = "MockLLMClient"

        # Mock LLM response
        mock_response = json.dumps({
            "criteria_results": [
                {
                    "criterion": "systematic_approach",
                    "score": 4,
                    "flags": ["methodical"],
                    "extracted_items": ["formed hypothesis"],
                    "supporting_quotes": [{"speaker": "candidate", "text": "Python is..."}],
                    "notes": "Good systematic thinking"
                },
                {
                    "criterion": "tool_usage",
                    "score": 3,
                    "flags": [],
                    "extracted_items": [],
                    "supporting_quotes": [],
                    "notes": "Limited tool discussion"
                },
                {
                    "criterion": "root_cause_analysis",
                    "score": 3,
                    "flags": [],
                    "extracted_items": [],
                    "supporting_quotes": [],
                    "notes": "Some analysis"
                }
            ]
        })
        mock_client.call_llm.return_value = mock_response

        # Create executor
        executor = LensExecutor(mock_client, model="test-model", temperature=0.3)

        # Execute lens
        lens_result = executor.execute_lens(db_session, session_id, sample_lens)

        # Verify results
        assert lens_result.status == LensResultStatus.COMPLETED
        assert lens_result.llm_model == "test-model"
        assert lens_result.llm_provider == "mock"

        # Check criterion results
        criterion_results = list(lens_result.criterion_results)
        assert len(criterion_results) == 3

        # Verify first criterion
        cr1 = next(cr for cr in criterion_results if cr.criterion_name == "systematic_approach")
        assert cr1.score == 4
        assert "methodical" in cr1.flags
        assert "formed hypothesis" in cr1.extracted_items
        assert len(cr1.supporting_quotes) == 1
        assert cr1.notes == "Good systematic thinking"

    def test_execute_lens_sanitizes_error_and_marks_failed(self, db_session, sample_session, sample_lens, caplog):
        """Test that errors are sanitized and status transitions to FAILED."""
        session_id, _ = sample_session

        # Capture logs to ensure only sanitized content is emitted
        caplog.set_level("DEBUG", logger="lens_executor")

        # Create mock LLM client that raises an error containing a secret
        mock_client = Mock()
        mock_client.__class__.__name__ = "MockLLMClient"
        mock_client.call_llm.side_effect = ValueError("API key sk-12345678901234567890 is invalid")

        executor = LensExecutor(mock_client)

        with pytest.raises(ValueError):
            executor.execute_lens(db_session, session_id, sample_lens)

        lens_result = (
            db_session.query(LensResult)
            .filter_by(session_id=session_id, lens_id=sample_lens)
            .one()
        )

        assert lens_result.status == LensResultStatus.FAILED
        assert "[REDACTED]" in lens_result.error_message
        assert "sk-12345678901234567890" not in lens_result.error_message

        # Ensure sanitized message is logged while secret is not present in standard logs
        assert any("[REDACTED]" in message for message in caplog.messages)
        assert all("sk-12345678901234567890" not in message for message in caplog.messages)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
