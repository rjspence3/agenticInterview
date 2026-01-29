"""
SQLAlchemy ORM models for the Agentic Interview System.

This module defines the database schema using SQLAlchemy ORM.
All models inherit from Base (defined in database.py).
"""

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Enum, Float
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum


# ============================================================================
# Enums
# ============================================================================

class PersonStatus(str, enum.Enum):
    """Status of a person in the system."""
    ACTIVE = "active"
    INACTIVE = "inactive"


class SessionStatus(str, enum.Enum):
    """Status of an interview session."""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class SpeakerType(str, enum.Enum):
    """Type of speaker in a transcript."""
    SYSTEM = "system"
    PARTICIPANT = "participant"
    ADMIN = "admin"  # Admin/moderator messages during raise hand


class EvaluatorType(str, enum.Enum):
    """Type of evaluator used."""
    HEURISTIC = "heuristic"
    LLM = "llm"
    DSPY = "dspy"


class MasteryLabel(str, enum.Enum):
    """Mastery level assessment."""
    STRONG = "strong"
    MIXED = "mixed"
    WEAK = "weak"


# ============================================================================
# Organization & People
# ============================================================================

class Organization(Base):
    """
    Represents an organization/company.

    Even if running single-tenant, this enables future multi-tenancy.
    """
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    settings = Column(JSON, default={})  # Flexible JSON for org-specific settings
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    people = relationship("Person", back_populates="organization")
    templates = relationship("InterviewTemplate", back_populates="organization")
    sessions = relationship("InterviewSession", back_populates="organization")
    lenses = relationship("Lens", back_populates="organization")

    def __repr__(self):
        return f"<Organization(id={self.id}, name='{self.name}')>"


class Person(Base):
    """
    Represents a person (interviewee, candidate, employee).

    Attributes:
        id: Primary key
        name: Full name
        email: Email address (unique within organization)
        role: Job role/title (e.g., "Software Engineer", "Product Manager")
        department: Department/team (e.g., "Engineering", "Sales")
        tags: Flexible JSON array for categorization (e.g., ["python", "senior"])
        status: Active or inactive
        organization_id: Foreign key to organization
    """
    __tablename__ = "people"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    role = Column(String(255), nullable=True)
    department = Column(String(255), nullable=True, index=True)
    tags = Column(JSON, default=[])  # Array of strings: ["python", "senior", "remote"]
    status = Column(Enum(PersonStatus), default=PersonStatus.ACTIVE, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    organization = relationship("Organization", back_populates="people")
    sessions = relationship("InterviewSession", back_populates="person")

    def __repr__(self):
        return f"<Person(id={self.id}, name='{self.name}', email='{self.email}')>"


# ============================================================================
# Interview Templates
# ============================================================================

class InterviewTemplate(Base):
    """
    Represents a reusable interview template/blueprint.

    A template defines a set of questions to be asked in a specific order.
    Examples: "Python Developer L2", "Product Manager Screening"
    """
    __tablename__ = "interview_templates"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    version = Column(Integer, default=1)  # Simple versioning for now
    active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    organization = relationship("Organization", back_populates="templates")
    questions = relationship(
        "TemplateQuestion",
        back_populates="template",
        order_by="TemplateQuestion.order_index",
        cascade="all, delete-orphan"
    )
    sessions = relationship("InterviewSession", back_populates="template")

    def __repr__(self):
        return f"<InterviewTemplate(id={self.id}, name='{self.name}', version={self.version})>"


class TemplateQuestion(Base):
    """
    Represents a question within an interview template.

    Attributes:
        id: Primary key
        template_id: Foreign key to template
        order_index: Position in the question sequence (0-based)
        question_text: The actual question
        competency: Area being tested (e.g., "Python", "System Design")
        difficulty: Difficulty level ("Easy", "Medium", "Hard")
        keypoints: JSON array of ground-truth concepts
    """
    __tablename__ = "template_questions"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("interview_templates.id"), nullable=False)
    order_index = Column(Integer, nullable=False)  # 0-based ordering
    question_text = Column(Text, nullable=False)
    competency = Column(String(255), nullable=False, index=True)
    difficulty = Column(String(50), nullable=False)  # "Easy", "Medium", "Hard"
    keypoints = Column(JSON, nullable=False)  # Array of strings
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    template = relationship("InterviewTemplate", back_populates="questions")
    evaluations = relationship("QuestionEvaluation", back_populates="template_question")

    def __repr__(self):
        return f"<TemplateQuestion(id={self.id}, template_id={self.template_id}, order={self.order_index})>"


# ============================================================================
# Interview Sessions
# ============================================================================

class InterviewSession(Base):
    """
    Represents a single interview session instance.

    Links a person to a template and captures the full interview lifecycle.
    """
    __tablename__ = "interview_sessions"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    template_id = Column(Integer, ForeignKey("interview_templates.id"), nullable=False)
    person_id = Column(Integer, ForeignKey("people.id"), nullable=False)
    status = Column(Enum(SessionStatus), default=SessionStatus.SCHEDULED, index=True)
    evaluator_type = Column(Enum(EvaluatorType), nullable=True)  # Set when interview starts
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    summary = Column(Text, nullable=True)  # Final summary generated by orchestrator
    session_metadata = Column(JSON, default={})  # Flexible field for additional data
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    organization = relationship("Organization", back_populates="sessions")
    template = relationship("InterviewTemplate", back_populates="sessions")
    person = relationship("Person", back_populates="sessions")
    transcript = relationship(
        "TranscriptEntry",
        back_populates="session",
        order_by="TranscriptEntry.sequence_index",
        cascade="all, delete-orphan"
    )
    evaluations = relationship(
        "QuestionEvaluation",
        back_populates="session",
        cascade="all, delete-orphan"
    )
    lens_results = relationship(
        "LensResult",
        back_populates="session",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<InterviewSession(id={self.id}, person_id={self.person_id}, status='{self.status.value}')>"


class TranscriptEntry(Base):
    """
    Represents a single entry in the interview transcript.

    Captures the full conversation: questions asked, answers given, system messages.
    """
    __tablename__ = "transcript_entries"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id"), nullable=False)
    sequence_index = Column(Integer, nullable=False)  # Order within session (0-based)
    speaker = Column(Enum(SpeakerType), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session = relationship("InterviewSession", back_populates="transcript")

    def __repr__(self):
        return f"<TranscriptEntry(id={self.id}, session_id={self.session_id}, speaker='{self.speaker.value}')>"


class QuestionEvaluation(Base):
    """
    Represents the evaluation of a single question-answer pair.

    Aligns with the EvaluationResult dataclass structure from models.py.
    Captures which evaluator was used for traceability.
    """
    __tablename__ = "question_evaluations"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id"), nullable=False)
    template_question_id = Column(Integer, ForeignKey("template_questions.id"), nullable=False)
    evaluator_type = Column(Enum(EvaluatorType), nullable=False)
    score_0_100 = Column(Integer, nullable=False)
    mastery_label = Column(Enum(MasteryLabel), nullable=False)
    raw_answer = Column(Text, nullable=False)
    short_feedback = Column(Text, nullable=False)
    keypoints_coverage = Column(JSON, nullable=False)  # Array of {keypoint, covered, evidence}
    suggested_followup = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session = relationship("InterviewSession", back_populates="evaluations")
    template_question = relationship("TemplateQuestion", back_populates="evaluations")

    def __repr__(self):
        return f"<QuestionEvaluation(id={self.id}, session_id={self.session_id}, score={self.score_0_100})>"


# ============================================================================
# Lenses (Phase 7)
# ============================================================================

class Lens(Base):
    """
    Represents an analytical framework applied to interview transcripts.

    A Lens defines criteria for structured analysis (e.g., "Debugging Process",
    "Communication Skills") with specific scoring scales and output schemas.
    """
    __tablename__ = "lenses"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    config = Column(JSON, nullable=False)  # Criteria definitions, scoring scales, prompt templates
    active = Column(Boolean, default=True, index=True)
    version = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    organization = relationship("Organization", back_populates="lenses")
    lens_results = relationship("LensResult", back_populates="lens", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Lens(id={self.id}, name={self.name}, version={self.version})>"


class LensResultStatus(enum.Enum):
    """Status of a lens execution."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class LensResult(Base):
    """
    Represents one application of a Lens to a completed InterviewSession.

    Stores metadata about the lens execution (status, timing, LLM used)
    and links to individual criterion results.
    """
    __tablename__ = "lens_results"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id"), nullable=False)
    lens_id = Column(Integer, ForeignKey("lenses.id"), nullable=False)
    status = Column(Enum(LensResultStatus), default=LensResultStatus.PENDING, index=True)
    llm_provider = Column(String(50), nullable=True)  # e.g., "openai", "anthropic"
    llm_model = Column(String(100), nullable=True)    # e.g., "gpt-4", "claude-3-5-sonnet"
    error_message = Column(Text, nullable=True)       # If status=failed, why?
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    session = relationship("InterviewSession", back_populates="lens_results")
    lens = relationship("Lens", back_populates="lens_results")
    criterion_results = relationship("LensCriterionResult", back_populates="lens_result", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<LensResult(id={self.id}, session_id={self.session_id}, lens_id={self.lens_id}, status={self.status.value})>"


class LensCriterionResult(Base):
    """
    Captures results for one criterion within a lens analysis.

    Each criterion has:
    - A numeric score (scale defined in lens config)
    - Boolean flags (observations like "unclear_explanation")
    - Extracted items (structured data like ["process: requirements gathering"])
    - Supporting quotes (transcript snippets with references)
    - Free-form notes
    """
    __tablename__ = "lens_criterion_results"

    id = Column(Integer, primary_key=True, index=True)
    lens_result_id = Column(Integer, ForeignKey("lens_results.id"), nullable=False)
    criterion_name = Column(String(255), nullable=False, index=True)
    score = Column(Float, nullable=True)              # e.g., 4.5 on a 0-5 scale
    scale = Column(String(50), nullable=True)         # e.g., "0-5", "0-10"
    flags = Column(JSON, default=[])                  # Boolean indicators
    extracted_items = Column(JSON, default=[])        # Structured data extracted
    supporting_quotes = Column(JSON, default=[])      # Transcript snippets with references
    notes = Column(Text, nullable=True)               # Free-form explanation
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    lens_result = relationship("LensResult", back_populates="criterion_results")

    def __repr__(self):
        return f"<LensCriterionResult(id={self.id}, criterion={self.criterion_name}, score={self.score})>"
