"""
Shared pytest fixtures for the Agentic Interview System tests.

This module provides reusable fixtures for database sessions,
test organizations, and common test objects.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db_models import (
    Base, Organization, Person, PersonStatus,
    InterviewTemplate, TemplateQuestion,
    Lens
)


# ==============================================================================
# Database Fixtures
# ==============================================================================

@pytest.fixture
def db_engine():
    """Create an in-memory SQLite engine for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        echo=False
    )
    return engine


@pytest.fixture
def db_session(db_engine):
    """
    Create an in-memory database session for testing.

    This fixture:
    - Creates all tables in an in-memory SQLite database
    - Yields a session for use in tests
    - Automatically cleans up after the test
    """
    # Create all tables
    Base.metadata.create_all(db_engine)

    # Create session
    Session = sessionmaker(bind=db_engine)
    session = Session()

    yield session

    # Cleanup
    session.close()


# ==============================================================================
# Organization Fixtures
# ==============================================================================

@pytest.fixture
def organization(db_session):
    """Create a test organization."""
    org = Organization(name="Test Organization", settings={})
    db_session.add(org)
    db_session.flush()
    return org


# ==============================================================================
# Person Fixtures
# ==============================================================================

@pytest.fixture
def person_factory(db_session, organization):
    """
    Factory fixture to create Person objects.

    Usage:
        def test_something(person_factory):
            person1 = person_factory(name="Alice", email="alice@test.com")
            person2 = person_factory(name="Bob", email="bob@test.com", role="Engineer")
    """
    def _create_person(
        name: str = "Test Person",
        email: str = "test@example.com",
        role: str = None,
        department: str = None,
        tags: list = None,
        status: PersonStatus = PersonStatus.ACTIVE
    ) -> Person:
        person = Person(
            organization_id=organization.id,
            name=name,
            email=email,
            role=role,
            department=department,
            tags=tags or [],
            status=status
        )
        db_session.add(person)
        db_session.flush()
        return person

    return _create_person


@pytest.fixture
def sample_person(person_factory):
    """Create a sample person for tests that need one."""
    return person_factory(
        name="John Doe",
        email="john.doe@example.com",
        role="Software Engineer",
        department="Engineering",
        tags=["python", "backend"]
    )


# ==============================================================================
# Template Fixtures
# ==============================================================================

@pytest.fixture
def template_factory(db_session, organization):
    """
    Factory fixture to create InterviewTemplate objects.

    Usage:
        def test_something(template_factory):
            template = template_factory(name="Python Interview")
    """
    def _create_template(
        name: str = "Test Template",
        description: str = "A test interview template",
        version: int = 1,
        active: bool = True
    ) -> InterviewTemplate:
        template = InterviewTemplate(
            organization_id=organization.id,
            name=name,
            description=description,
            version=version,
            active=active
        )
        db_session.add(template)
        db_session.flush()
        return template

    return _create_template


@pytest.fixture
def sample_template(template_factory):
    """Create a sample template for tests that need one."""
    return template_factory(
        name="Python Backend Interview",
        description="Interview for Python backend developers"
    )


# ==============================================================================
# Question Fixtures
# ==============================================================================

@pytest.fixture
def question_factory(db_session):
    """
    Factory fixture to create TemplateQuestion objects.

    Usage:
        def test_something(question_factory, sample_template):
            question = question_factory(
                template=sample_template,
                question_text="What is Python?",
                keypoints=["interpreted", "high-level"]
            )
    """
    def _create_question(
        template: InterviewTemplate,
        question_text: str = "Test question?",
        competency: str = "General",
        difficulty: str = "Medium",
        keypoints: list = None,
        order_index: int = 0
    ) -> TemplateQuestion:
        question = TemplateQuestion(
            template_id=template.id,
            question_text=question_text,
            competency=competency,
            difficulty=difficulty,
            keypoints=keypoints or ["test keypoint"],
            order_index=order_index
        )
        db_session.add(question)
        db_session.flush()
        return question

    return _create_question


# ==============================================================================
# Lens Fixtures
# ==============================================================================

@pytest.fixture
def lens_factory(db_session, organization):
    """
    Factory fixture to create Lens objects.

    Usage:
        def test_something(lens_factory):
            lens = lens_factory(name="Communication Lens")
    """
    def _create_lens(
        name: str = "Test Lens",
        description: str = "A test lens",
        config: dict = None,
        active: bool = True,
        version: int = 1
    ) -> Lens:
        if config is None:
            config = {
                "criteria": [
                    {
                        "name": "clarity",
                        "definition": "Clear communication",
                        "examples": ["uses simple language"]
                    }
                ],
                "scoring_scale": "0-5"
            }

        lens = Lens(
            organization_id=organization.id,
            name=name,
            description=description,
            config=config,
            active=active,
            version=version
        )
        db_session.add(lens)
        db_session.flush()
        return lens

    return _create_lens


@pytest.fixture
def sample_lens(lens_factory):
    """Create a sample lens for tests that need one."""
    return lens_factory(
        name="Communication Quality Lens",
        description="Evaluates clarity and depth of communication"
    )
