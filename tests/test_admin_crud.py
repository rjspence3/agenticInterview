"""
Tests for Admin CRUD operations.

Tests basic CRUD operations for:
- Person records
- InterviewTemplate and TemplateQuestion records
- Lens records with configuration validation

Uses in-memory database for testing.
"""

import pytest
from datetime import datetime

from db_models import (
    Organization, Person, PersonStatus,
    InterviewTemplate, TemplateQuestion,
    Lens,
    Base
)
from lens_prompt_builder import validate_lens_config, get_example_lens_config


class TestPersonCRUD:
    """Test Person CRUD operations."""

    @pytest.fixture
    def db_session(self):
        """Create an in-memory database session for testing."""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        # Create in-memory database
        engine = create_engine("sqlite:///:memory:")
        Session = sessionmaker(bind=engine)

        # Initialize schema
        Base.metadata.create_all(engine)

        session = Session()
        yield session
        session.close()

    @pytest.fixture
    def organization(self, db_session):
        """Create a test organization."""
        org = Organization(name="Test Org", settings={})
        db_session.add(org)
        db_session.flush()
        return org

    def test_create_person(self, db_session, organization):
        """Test creating a Person record."""
        person = Person(
            organization_id=organization.id,
            name="John Doe",
            email="john.doe@example.com",
            role="Software Engineer",
            department="Engineering",
            tags=["python", "backend"],
            status=PersonStatus.ACTIVE
        )
        db_session.add(person)
        db_session.flush()

        # Verify person was created
        assert person.id is not None
        assert person.name == "John Doe"
        assert person.email == "john.doe@example.com"
        assert person.role == "Software Engineer"
        assert person.department == "Engineering"
        assert person.tags == ["python", "backend"]
        assert person.status == PersonStatus.ACTIVE
        assert person.organization_id == organization.id

    def test_fetch_person_by_id(self, db_session, organization):
        """Test fetching a Person by ID."""
        person = Person(
            organization_id=organization.id,
            name="Jane Smith",
            email="jane@example.com",
            status=PersonStatus.ACTIVE
        )
        db_session.add(person)
        db_session.flush()

        person_id = person.id

        # Fetch by ID
        fetched_person = db_session.get(Person, person_id)

        assert fetched_person is not None
        assert fetched_person.id == person_id
        assert fetched_person.name == "Jane Smith"
        assert fetched_person.email == "jane@example.com"

    def test_update_person(self, db_session, organization):
        """Test updating a Person record."""
        person = Person(
            organization_id=organization.id,
            name="Bob Wilson",
            email="bob@example.com",
            role="Junior Developer",
            status=PersonStatus.ACTIVE
        )
        db_session.add(person)
        db_session.flush()

        # Update person
        person.role = "Senior Developer"
        person.department = "Engineering"
        person.tags = ["python", "leadership"]
        db_session.flush()

        # Verify updates
        fetched = db_session.get(Person, person.id)
        assert fetched.role == "Senior Developer"
        assert fetched.department == "Engineering"
        assert fetched.tags == ["python", "leadership"]

    def test_list_active_persons(self, db_session, organization):
        """Test fetching all active persons."""
        # Create multiple persons with different statuses
        person1 = Person(
            organization_id=organization.id,
            name="Person 1",
            email="person1@example.com",
            status=PersonStatus.ACTIVE
        )
        person2 = Person(
            organization_id=organization.id,
            name="Person 2",
            email="person2@example.com",
            status=PersonStatus.ACTIVE
        )
        person3 = Person(
            organization_id=organization.id,
            name="Person 3",
            email="person3@example.com",
            status=PersonStatus.INACTIVE
        )

        db_session.add_all([person1, person2, person3])
        db_session.flush()

        # Fetch only active persons
        from sqlalchemy import select
        query = select(Person).where(
            Person.organization_id == organization.id,
            Person.status == PersonStatus.ACTIVE
        )
        active_persons = db_session.execute(query).scalars().all()

        assert len(active_persons) == 2
        assert all(p.status == PersonStatus.ACTIVE for p in active_persons)


class TestInterviewTemplateCRUD:
    """Test InterviewTemplate and TemplateQuestion CRUD operations."""

    @pytest.fixture
    def db_session(self):
        """Create an in-memory database session for testing."""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        engine = create_engine("sqlite:///:memory:")
        Session = sessionmaker(bind=engine)
        Base.metadata.create_all(engine)

        session = Session()
        yield session
        session.close()

    @pytest.fixture
    def organization(self, db_session):
        """Create a test organization."""
        org = Organization(name="Test Org", settings={})
        db_session.add(org)
        db_session.flush()
        return org

    def test_create_template_with_questions(self, db_session, organization):
        """Test creating an InterviewTemplate with questions."""
        # Create template
        template = InterviewTemplate(
            organization_id=organization.id,
            name="Python Backend Interview",
            version=1,
            description="Interview for Python backend developers",
            active=True
        )
        db_session.add(template)
        db_session.flush()

        # Add questions
        question1 = TemplateQuestion(
            template_id=template.id,
            question_text="What is a decorator in Python?",
            competency="Python",
            difficulty="Medium",
            keypoints=["wrapper function", "@ syntax", "function modification"],
            order_index=0
        )
        question2 = TemplateQuestion(
            template_id=template.id,
            question_text="Explain the GIL in Python.",
            competency="Python",
            difficulty="Hard",
            keypoints=["Global Interpreter Lock", "thread safety", "performance implications"],
            order_index=1
        )

        db_session.add_all([question1, question2])
        db_session.flush()

        # Verify template
        assert template.id is not None
        assert template.name == "Python Backend Interview"
        assert template.active is True

        # Verify questions
        assert question1.id is not None
        assert question2.id is not None
        assert question1.template_id == template.id
        assert question2.template_id == template.id

    def test_fetch_template_with_questions_in_order(self, db_session, organization):
        """Test fetching template and questions in correct order."""
        # Create template
        template = InterviewTemplate(
            organization_id=organization.id,
            name="Test Template",
            version=1,
            active=True
        )
        db_session.add(template)
        db_session.flush()

        # Add questions in specific order
        questions_data = [
            ("Question 3", 2),
            ("Question 1", 0),
            ("Question 2", 1)
        ]

        for text, order in questions_data:
            question = TemplateQuestion(
                template_id=template.id,
                question_text=text,
                competency="Test",
                difficulty="Easy",
                keypoints=["test"],
                order_index=order
            )
            db_session.add(question)

        db_session.flush()

        # Fetch template
        fetched_template = db_session.get(InterviewTemplate, template.id)

        # Get questions ordered by order_index
        from sqlalchemy import select
        query = select(TemplateQuestion).where(
            TemplateQuestion.template_id == template.id
        ).order_by(TemplateQuestion.order_index)

        ordered_questions = db_session.execute(query).scalars().all()

        # Verify order
        assert len(ordered_questions) == 3
        assert ordered_questions[0].question_text == "Question 1"
        assert ordered_questions[1].question_text == "Question 2"
        assert ordered_questions[2].question_text == "Question 3"
        assert ordered_questions[0].order_index == 0
        assert ordered_questions[1].order_index == 1
        assert ordered_questions[2].order_index == 2

    def test_update_template_question(self, db_session, organization):
        """Test updating a template question."""
        template = InterviewTemplate(
            organization_id=organization.id,
            name="Test Template",
            version=1,
            active=True
        )
        db_session.add(template)
        db_session.flush()

        question = TemplateQuestion(
            template_id=template.id,
            question_text="Original question",
            competency="Test",
            difficulty="Easy",
            keypoints=["original"],
            order_index=0
        )
        db_session.add(question)
        db_session.flush()

        # Update question
        question.question_text = "Updated question"
        question.difficulty = "Hard"
        question.keypoints = ["updated", "improved"]
        db_session.flush()

        # Verify update
        fetched = db_session.get(TemplateQuestion, question.id)
        assert fetched.question_text == "Updated question"
        assert fetched.difficulty == "Hard"
        assert fetched.keypoints == ["updated", "improved"]

    def test_delete_template_question(self, db_session, organization):
        """Test deleting a template question."""
        template = InterviewTemplate(
            organization_id=organization.id,
            name="Test Template",
            version=1,
            active=True
        )
        db_session.add(template)
        db_session.flush()

        question = TemplateQuestion(
            template_id=template.id,
            question_text="Question to delete",
            competency="Test",
            difficulty="Easy",
            keypoints=["test"],
            order_index=0
        )
        db_session.add(question)
        db_session.flush()

        question_id = question.id

        # Delete question
        db_session.delete(question)
        db_session.flush()

        # Verify deletion
        fetched = db_session.get(TemplateQuestion, question_id)
        assert fetched is None


class TestLensCRUD:
    """Test Lens CRUD operations with configuration validation."""

    @pytest.fixture
    def db_session(self):
        """Create an in-memory database session for testing."""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        engine = create_engine("sqlite:///:memory:")
        Session = sessionmaker(bind=engine)
        Base.metadata.create_all(engine)

        session = Session()
        yield session
        session.close()

    @pytest.fixture
    def organization(self, db_session):
        """Create a test organization."""
        org = Organization(name="Test Org", settings={})
        db_session.add(org)
        db_session.flush()
        return org

    def test_create_lens_with_valid_config(self, db_session, organization):
        """Test creating a Lens with valid configuration."""
        config = {
            "criteria": [
                {
                    "name": "clarity",
                    "definition": "Clear communication and explanation",
                    "examples": ["uses simple language", "provides concrete examples"]
                },
                {
                    "name": "depth",
                    "definition": "Deep technical understanding",
                    "examples": ["explains underlying concepts", "considers edge cases"]
                }
            ],
            "scoring_scale": "0-5"
        }

        # Validate config
        is_valid, error_msg = validate_lens_config(config)
        assert is_valid, f"Config should be valid: {error_msg}"

        # Create lens
        lens = Lens(
            organization_id=organization.id,
            name="Communication Quality Lens",
            description="Evaluates clarity and depth of technical communication",
            config=config,
            active=True,
            version=1
        )
        db_session.add(lens)
        db_session.flush()

        # Verify lens
        assert lens.id is not None
        assert lens.name == "Communication Quality Lens"
        assert lens.config == config
        assert lens.active is True
        assert len(lens.config["criteria"]) == 2

    def test_create_lens_with_example_config(self, db_session, organization):
        """Test creating lenses with example configurations."""
        lens_types = ["debugging", "communication", "system_design"]

        for lens_type in lens_types:
            config = get_example_lens_config(lens_type)

            # Validate config
            is_valid, error_msg = validate_lens_config(config)
            assert is_valid, f"{lens_type} config should be valid: {error_msg}"

            # Create lens
            lens = Lens(
                organization_id=organization.id,
                name=f"{lens_type.title()} Lens",
                description=f"Test {lens_type} lens",
                config=config,
                active=True,
                version=1
            )
            db_session.add(lens)
            db_session.flush()

            assert lens.id is not None
            assert lens.config == config

    def test_fetch_active_lenses(self, db_session, organization):
        """Test fetching only active lenses."""
        # Create active lens
        lens1 = Lens(
            organization_id=organization.id,
            name="Active Lens",
            description="Active",
            config=get_example_lens_config("debugging"),
            active=True,
            version=1
        )

        # Create inactive lens
        lens2 = Lens(
            organization_id=organization.id,
            name="Inactive Lens",
            description="Inactive",
            config=get_example_lens_config("communication"),
            active=False,
            version=1
        )

        db_session.add_all([lens1, lens2])
        db_session.flush()

        # Fetch only active lenses
        from sqlalchemy import select
        query = select(Lens).where(
            Lens.organization_id == organization.id,
            Lens.active == True
        )
        active_lenses = db_session.execute(query).scalars().all()

        assert len(active_lenses) == 1
        assert active_lenses[0].name == "Active Lens"
        assert active_lenses[0].active is True

    def test_update_lens_config(self, db_session, organization):
        """Test updating a lens configuration."""
        original_config = get_example_lens_config("debugging")

        lens = Lens(
            organization_id=organization.id,
            name="Test Lens",
            description="Original",
            config=original_config,
            active=True,
            version=1
        )
        db_session.add(lens)
        db_session.flush()

        # Update config
        new_config = get_example_lens_config("communication")
        lens.config = new_config
        lens.description = "Updated to communication lens"
        lens.version = 2
        db_session.flush()

        # Verify update
        fetched = db_session.get(Lens, lens.id)
        assert fetched.config == new_config
        assert fetched.description == "Updated to communication lens"
        assert fetched.version == 2

    def test_lens_config_validation_rejects_invalid(self, db_session, organization):
        """Test that invalid lens configurations are rejected by validation."""
        invalid_configs = [
            # Missing criteria
            {"scoring_scale": "0-5"},
            # Empty criteria list
            {"criteria": [], "scoring_scale": "0-5"},
            # Criterion missing name
            {
                "criteria": [
                    {"definition": "test", "examples": []}
                ],
                "scoring_scale": "0-5"
            },
            # Criterion missing definition
            {
                "criteria": [
                    {"name": "test", "examples": []}
                ],
                "scoring_scale": "0-5"
            }
        ]

        for config in invalid_configs:
            is_valid, error_msg = validate_lens_config(config)
            assert not is_valid, f"Config should be invalid: {config}"
            assert error_msg != "", "Error message should be provided"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
