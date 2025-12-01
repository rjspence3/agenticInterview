"""
Streamlit UI for the Agentic Interview System.

Provides two views:
- Interviewer: Create and manage questions
- Interviewee: Take the interview and see results
"""

from typing import Any, List, Optional, Union

import streamlit as st
from streamlit_autorefresh import st_autorefresh
from models import Question, InterviewState
from agents import QuestionsAgent, EvaluatorAgent, OrchestratorAgent
from logging_config import get_logger
import settings

logger = get_logger(__name__)

# Phase 5: LLM Integration
try:
    from llm_evaluator import LLMEvaluatorAgent
    from llm_client import get_llm_client
    LLM_AVAILABLE = True
except ImportError as e:
    LLM_AVAILABLE = False
    logger.warning(f"LLM features not available: {e}")

# Phase 6: Database Integration
try:
    from database import get_db_session, init_db
    from db_models import (
        Organization, Person, PersonStatus,
        InterviewTemplate, TemplateQuestion,
        InterviewSession, SessionStatus, EvaluatorType,
        TranscriptEntry, SpeakerType,
        QuestionEvaluation, MasteryLabel,
        Lens
    )
    from sqlalchemy import select, func
    DATABASE_AVAILABLE = True
except ImportError as e:
    DATABASE_AVAILABLE = False
    logger.warning(f"Database features not available: {e}")


# Page configuration
st.set_page_config(
    page_title="Agentic Interview System",
    page_icon="🎯",
    layout="wide"
)


def initialize_session_state() -> None:
    """Initialize session state variables if they don't exist."""
    if "questions" not in st.session_state:
        st.session_state.questions = []

    if "interview_state" not in st.session_state:
        st.session_state.interview_state = InterviewState()

    if "next_question_id" not in st.session_state:
        st.session_state.next_question_id = 1

    if "evaluator_mode" not in st.session_state:
        st.session_state.evaluator_mode = "Heuristic"

    # Phase 6: Initialize database
    if DATABASE_AVAILABLE and "db_initialized" not in st.session_state:
        try:
            init_db()
            st.session_state.db_initialized = True
        except Exception as e:
            st.error(f"Database initialization failed: {e}")
            st.session_state.db_initialized = False

    # Chat Interview session state
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []  # List of message dicts

    if "chat_interview_phase" not in st.session_state:
        st.session_state.chat_interview_phase = "setup"  # "setup", "active", "complete"

    if "chat_session_id" not in st.session_state:
        st.session_state.chat_session_id = None

    if "chat_current_question_index" not in st.session_state:
        st.session_state.chat_current_question_index = 0

    if "chat_questions_data" not in st.session_state:
        st.session_state.chat_questions_data = []

    if "chat_person_data" not in st.session_state:
        st.session_state.chat_person_data = None

    if "chat_template_data" not in st.session_state:
        st.session_state.chat_template_data = None

    # Raise Hand feature - Interviewee side
    if "chat_hand_raised" not in st.session_state:
        st.session_state.chat_hand_raised = False

    if "chat_hand_raised_reason" not in st.session_state:
        st.session_state.chat_hand_raised_reason = ""

    if "chat_admin_present" not in st.session_state:
        st.session_state.chat_admin_present = False

    if "chat_interview_paused" not in st.session_state:
        st.session_state.chat_interview_paused = False

    if "chat_last_poll_count" not in st.session_state:
        st.session_state.chat_last_poll_count = 0

    if "chat_last_transcript_seq" not in st.session_state:
        st.session_state.chat_last_transcript_seq = -1

    # Raise Hand feature - Admin side
    if "admin_viewing_session_id" not in st.session_state:
        st.session_state.admin_viewing_session_id = None

    if "admin_last_poll_count" not in st.session_state:
        st.session_state.admin_last_poll_count = 0


def get_evaluator_agent() -> EvaluatorAgent:
    """
    Get the appropriate evaluator based on selected mode.

    Returns:
        EvaluatorAgent or LLMEvaluatorAgent instance
    """
    mode = st.session_state.get("evaluator_mode", "Heuristic")

    if mode == "Heuristic":
        return EvaluatorAgent()

    # LLM mode selected
    if not LLM_AVAILABLE:
        st.sidebar.error("❌ LLM dependencies not installed")
        st.sidebar.info("Install with: pip install -r requirements.txt")
        return EvaluatorAgent()

    # Validate configuration
    is_valid, error_msg = settings.validate_llm_config()

    if not is_valid:
        st.sidebar.error(f"❌ {error_msg}")
        st.sidebar.info("📝 Setup: Copy .env.example to .env and add your API key")
        return EvaluatorAgent()

    # Try to create LLM evaluator
    try:
        provider = settings.LLM_PROVIDER
        api_key = settings.get_api_key_for_provider(provider)
        client = get_llm_client(provider, api_key)

        return LLMEvaluatorAgent(
            client,
            settings.LLM_MODEL,
            settings.LLM_TEMPERATURE
        )
    except Exception as e:
        st.sidebar.error(f"❌ LLM initialization failed: {e}")
        st.sidebar.info("Falling back to heuristic evaluator")
        return EvaluatorAgent()


# ==============================================================================
# Raise Hand Feature - Helper Functions
# ==============================================================================

def update_session_metadata(session_id: int, updates: dict) -> bool:
    """
    Merge updates into session_metadata JSON field.

    Args:
        session_id: Interview session ID
        updates: Dict of key-value pairs to merge into metadata

    Returns:
        True if successful, False otherwise
    """
    from db_models import InterviewSession
    from sqlalchemy.orm.attributes import flag_modified
    try:
        with get_db_session() as db:
            session = db.get(InterviewSession, session_id)
            if not session:
                return False

            # Get existing metadata or empty dict
            metadata = dict(session.session_metadata or {})
            # Merge updates
            metadata.update(updates)
            session.session_metadata = metadata
            # Explicitly mark JSON field as modified
            flag_modified(session, "session_metadata")
            db.flush()
        return True
    except Exception as e:
        print(f"Error updating session metadata: {e}")
        return False


def get_session_metadata(session_id: int) -> dict:
    """
    Retrieve session_metadata dict for a session.

    Args:
        session_id: Interview session ID

    Returns:
        Metadata dict or empty dict if not found
    """
    from db_models import InterviewSession
    try:
        with get_db_session() as db:
            session = db.get(InterviewSession, session_id)
            if session and session.session_metadata:
                return dict(session.session_metadata)
        return {}
    except Exception:
        return {}


def get_active_sessions_summary() -> list:
    """
    Query all IN_PROGRESS sessions with summary info for admin view.

    Returns:
        List of session summary dicts with hand_raised status
    """
    from db_models import InterviewSession, SessionStatus, Person, InterviewTemplate
    from sqlalchemy import select

    sessions_data = []
    try:
        with get_db_session() as db:
            query = select(InterviewSession).where(
                InterviewSession.status == SessionStatus.IN_PROGRESS
            ).order_by(InterviewSession.started_at.desc())

            sessions = db.execute(query).scalars().all()

            for session in sessions:
                metadata = session.session_metadata or {}
                sessions_data.append({
                    "id": session.id,
                    "person_id": session.person_id,
                    "person_name": session.person.name if session.person else "Unknown",
                    "template_id": session.template_id,
                    "template_name": session.template.name if session.template else "Unknown",
                    "started_at": session.started_at,
                    "hand_raised": metadata.get("hand_raised", False),
                    "hand_raised_at": metadata.get("hand_raised_at"),
                    "hand_raised_reason": metadata.get("hand_raised_reason"),
                    "admin_joined": metadata.get("admin_joined", False),
                    "admin_user": metadata.get("admin_user"),
                    "current_question_index": metadata.get("current_question_index", 0)
                })
    except Exception as e:
        print(f"Error getting active sessions: {e}")

    return sessions_data


def raise_hand(session_id: int, reason: str = "") -> bool:
    """
    Mark hand as raised for a session.

    Args:
        session_id: Interview session ID
        reason: Optional reason for raising hand

    Returns:
        True if successful
    """
    from datetime import datetime
    return update_session_metadata(session_id, {
        "hand_raised": True,
        "hand_raised_at": datetime.now().isoformat(),
        "hand_raised_reason": reason
    })


def lower_hand(session_id: int) -> bool:
    """
    Cancel raised hand for a session.

    Args:
        session_id: Interview session ID

    Returns:
        True if successful
    """
    return update_session_metadata(session_id, {
        "hand_raised": False,
        "hand_raised_at": None,
        "hand_raised_reason": None
    })


def join_session_as_admin(session_id: int, admin_user: str = "Admin") -> bool:
    """
    Admin joins and pauses interview.

    Args:
        session_id: Interview session ID
        admin_user: Admin identifier for logging

    Returns:
        True if successful
    """
    from datetime import datetime
    from db_models import TranscriptEntry, SpeakerType

    success = update_session_metadata(session_id, {
        "admin_joined": True,
        "admin_joined_at": datetime.now().isoformat(),
        "admin_user": admin_user
    })

    if success:
        # Add system message to transcript
        try:
            with get_db_session() as db:
                # Get next sequence index
                from sqlalchemy import func, select
                from db_models import TranscriptEntry
                max_seq = db.execute(
                    select(func.max(TranscriptEntry.sequence_index)).where(
                        TranscriptEntry.session_id == session_id
                    )
                ).scalar() or 0

                entry = TranscriptEntry(
                    session_id=session_id,
                    sequence_index=max_seq + 1,
                    speaker=SpeakerType.SYSTEM,
                    text="🎧 An administrator has joined the session. Interview is paused."
                )
                db.add(entry)
                db.flush()
        except Exception as e:
            print(f"Error adding admin join message: {e}")

    return success


def leave_session_as_admin(session_id: int, resume: bool = True) -> bool:
    """
    Admin leaves session, optionally resuming the interview.

    Args:
        session_id: Interview session ID
        resume: If True, resume the interview; if False, keep paused

    Returns:
        True if successful
    """
    from db_models import TranscriptEntry, SpeakerType

    success = update_session_metadata(session_id, {
        "admin_joined": False,
        "admin_joined_at": None,
        "admin_user": None,
        "hand_raised": False,  # Clear raised hand when admin leaves
        "hand_raised_at": None,
        "hand_raised_reason": None
    })

    if success:
        # Add system message to transcript
        try:
            with get_db_session() as db:
                from sqlalchemy import func, select
                max_seq = db.execute(
                    select(func.max(TranscriptEntry.sequence_index)).where(
                        TranscriptEntry.session_id == session_id
                    )
                ).scalar() or 0

                msg = "✅ Administrator has left. Interview resumed." if resume else "⏸️ Administrator has left. Interview remains paused."
                entry = TranscriptEntry(
                    session_id=session_id,
                    sequence_index=max_seq + 1,
                    speaker=SpeakerType.SYSTEM,
                    text=msg
                )
                db.add(entry)
                db.flush()
        except Exception as e:
            print(f"Error adding admin leave message: {e}")

    return success


def admin_send_message(session_id: int, message: str) -> bool:
    """
    Send message as ADMIN speaker to transcript.

    Args:
        session_id: Interview session ID
        message: Message text

    Returns:
        True if successful
    """
    from db_models import TranscriptEntry, SpeakerType

    try:
        with get_db_session() as db:
            from sqlalchemy import func, select
            max_seq = db.execute(
                select(func.max(TranscriptEntry.sequence_index)).where(
                    TranscriptEntry.session_id == session_id
                )
            ).scalar() or 0

            entry = TranscriptEntry(
                session_id=session_id,
                sequence_index=max_seq + 1,
                speaker=SpeakerType.ADMIN,
                text=message
            )
            db.add(entry)
            db.flush()
        return True
    except Exception as e:
        print(f"Error sending admin message: {e}")
        return False


def get_transcript_since(session_id: int, since_seq: int) -> list:
    """
    Get transcript entries after a sequence index.

    Args:
        session_id: Interview session ID
        since_seq: Sequence index to start after

    Returns:
        List of transcript entry dicts
    """
    from db_models import TranscriptEntry
    from sqlalchemy import select

    entries = []
    try:
        with get_db_session() as db:
            query = select(TranscriptEntry).where(
                TranscriptEntry.session_id == session_id,
                TranscriptEntry.sequence_index > since_seq
            ).order_by(TranscriptEntry.sequence_index)

            results = db.execute(query).scalars().all()
            for entry in results:
                entries.append({
                    "sequence_index": entry.sequence_index,
                    "speaker": entry.speaker.value,
                    "text": entry.text,
                    "timestamp": entry.timestamp
                })
    except Exception as e:
        print(f"Error getting transcript: {e}")

    return entries


def poll_session_status(session_id: int) -> dict:
    """
    Poll for session status changes (admin presence, new messages).

    Args:
        session_id: Interview session ID

    Returns:
        Dict with admin_joined, hand_raised, and new_messages count
    """
    metadata = get_session_metadata(session_id)
    last_seq = st.session_state.get("chat_last_transcript_seq", -1)
    new_entries = get_transcript_since(session_id, last_seq)

    return {
        "admin_joined": metadata.get("admin_joined", False),
        "hand_raised": metadata.get("hand_raised", False),
        "new_messages": len(new_entries),
        "new_entries": new_entries
    }


def admin_skip_question(session_id: int) -> bool:
    """
    Skip current question and advance to next.

    Args:
        session_id: Interview session ID

    Returns:
        True if successful
    """
    from db_models import TranscriptEntry, SpeakerType

    try:
        with get_db_session() as db:
            from sqlalchemy import func, select
            max_seq = db.execute(
                select(func.max(TranscriptEntry.sequence_index)).where(
                    TranscriptEntry.session_id == session_id
                )
            ).scalar() or 0

            entry = TranscriptEntry(
                session_id=session_id,
                sequence_index=max_seq + 1,
                speaker=SpeakerType.SYSTEM,
                text="⏭️ Question skipped by administrator."
            )
            db.add(entry)
            db.flush()
        return True
    except Exception as e:
        print(f"Error skipping question: {e}")
        return False


def admin_end_interview(session_id: int) -> bool:
    """
    Force-end interview early.

    Args:
        session_id: Interview session ID

    Returns:
        True if successful
    """
    from db_models import InterviewSession, SessionStatus, TranscriptEntry, SpeakerType
    from datetime import datetime

    try:
        with get_db_session() as db:
            session = db.get(InterviewSession, session_id)
            if session:
                session.status = SessionStatus.COMPLETED
                session.completed_at = datetime.now()

                # Add system message
                from sqlalchemy import func, select
                max_seq = db.execute(
                    select(func.max(TranscriptEntry.sequence_index)).where(
                        TranscriptEntry.session_id == session_id
                    )
                ).scalar() or 0

                entry = TranscriptEntry(
                    session_id=session_id,
                    sequence_index=max_seq + 1,
                    speaker=SpeakerType.SYSTEM,
                    text="🛑 Interview ended early by administrator."
                )
                db.add(entry)
                db.flush()

        # Clear admin session state
        update_session_metadata(session_id, {
            "admin_joined": False,
            "admin_joined_at": None,
            "admin_user": None,
            "hand_raised": False
        })
        return True
    except Exception as e:
        print(f"Error ending interview: {e}")
        return False


def render_interviewer_view() -> None:
    """Render the interviewer view for creating and managing questions."""
    st.header("Interviewer View")
    st.write("Create and manage interview questions with keypoints.")

    # Form to add new questions
    with st.form("add_question_form", clear_on_submit=True):
        st.subheader("Add New Question")

        question_text = st.text_area(
            "Question Text",
            placeholder="Enter your interview question here...",
            height=100
        )

        col1, col2 = st.columns(2)
        with col1:
            competency = st.text_input(
                "Competency",
                placeholder="e.g., Python, System Design, Algorithms"
            )

        with col2:
            difficulty = st.selectbox(
                "Difficulty",
                options=["Easy", "Medium", "Hard"]
            )

        keypoints_text = st.text_area(
            "Keypoints (comma-separated)",
            placeholder="e.g., list comprehension, time complexity, error handling",
            height=80,
            help="Enter ground-truth concepts that should appear in a good answer, separated by commas"
        )

        submit_button = st.form_submit_button("Add Question")

        if submit_button:
            # Validate inputs
            if not question_text.strip():
                st.error("Question text cannot be empty")
            elif not competency.strip():
                st.error("Competency cannot be empty")
            elif not keypoints_text.strip():
                st.error("Keypoints cannot be empty")
            else:
                # Parse keypoints
                keypoints = [kp.strip() for kp in keypoints_text.split(",") if kp.strip()]

                if not keypoints:
                    st.error("Please provide at least one keypoint")
                else:
                    # Create new question
                    new_question = Question(
                        id=st.session_state.next_question_id,
                        text=question_text.strip(),
                        competency=competency.strip(),
                        difficulty=difficulty,
                        keypoints=keypoints
                    )

                    # Add to question bank
                    st.session_state.questions.append(new_question)
                    st.session_state.next_question_id += 1

                    st.success(f"Added question #{new_question.id}")
                    st.rerun()

    # Display question bank
    st.subheader("Question Bank")

    if not st.session_state.questions:
        st.info("No questions yet. Add your first question above!")
    else:
        st.write(f"Total Questions: {len(st.session_state.questions)}")

        for question in st.session_state.questions:
            with st.expander(f"Q{question.id}: {question.text[:60]}..."):
                st.write(f"**Full Question:** {question.text}")
                st.write(f"**Competency:** {question.competency}")
                st.write(f"**Difficulty:** {question.difficulty}")
                st.write(f"**Keypoints:** {', '.join(question.keypoints)}")

    # Reset interview button
    st.divider()
    if st.button("Reset Interview State"):
        st.session_state.interview_state = InterviewState()
        st.success("Interview state reset. Interviewee can start fresh.")
        st.rerun()


def render_interviewee_view() -> None:
    """Render the interviewee view for taking the interview."""
    st.header("Interviewee View")

    # Use database-backed interviews if available
    if DATABASE_AVAILABLE and st.session_state.get("db_initialized"):
        render_db_interview()
    else:
        # Fallback to legacy in-memory interview
        render_legacy_interview()


def render_db_interview() -> None:
    """Render database-backed interview flow."""
    # Check if there's an active session
    if "active_session_id" not in st.session_state:
        render_interview_setup()
    else:
        render_active_interview()


def render_interview_setup() -> None:
    """Render the interview setup page (select person and template)."""
    st.subheader("Start New Interview")

    # Get people and templates from database
    # Extract data while in session context to avoid DetachedInstanceError
    with get_db_session() as db:
        people_objs = db.execute(
            select(Person).where(Person.status == PersonStatus.ACTIVE).order_by(Person.name)
        ).scalars().all()

        # Extract data to simple dict
        people = [(p.id, p.name) for p in people_objs]

        template_objs = db.execute(
            select(InterviewTemplate).where(InterviewTemplate.active == True).order_by(InterviewTemplate.name)
        ).scalars().all()

        # Extract data including question count
        templates = [(t.id, t.name, t.version, len(list(t.questions)), t.description) for t in template_objs]

    if not people:
        st.warning("No active people in the system. Please add people in the Admin view.")
        return

    if not templates:
        st.warning("No active templates in the system. Please add templates in the Admin view.")
        return

    # Selection form
    col1, col2 = st.columns(2)

    with col1:
        selected_person_id = st.selectbox(
            "Select Interviewee",
            options=[p[0] for p in people],
            format_func=lambda pid: next(p[1] for p in people if p[0] == pid)
        )

    with col2:
        selected_template_id = st.selectbox(
            "Select Interview Template",
            options=[t[0] for t in templates],
            format_func=lambda tid: next(f"{t[1]} (v{t[2]}) - {t[3]} questions" for t in templates if t[0] == tid)
        )

    # Show template preview
    selected_template = next(t for t in templates if t[0] == selected_template_id)
    with st.expander("📋 Template Preview"):
        st.write(f"**{selected_template[1]}** (v{selected_template[2]})")
        if selected_template[4]:  # description
            st.write(selected_template[4])

        with get_db_session() as db:
            db_template = db.get(InterviewTemplate, selected_template_id)
            # Extract question data while in session
            questions = [(q.order_index, q.competency, q.question_text)
                        for q in sorted(db_template.questions, key=lambda q: q.order_index)]

        st.write(f"**Questions ({len(questions)}):**")
        for q in questions:
            st.write(f"{q[0] + 1}. [{q[1]}] {q[2][:80]}...")

    # Start button
    if st.button("🚀 Start Interview", type="primary"):
        try:
            # Create interview session
            with get_db_session() as db:
                db_template = db.get(InterviewTemplate, selected_template_id)
                org_id = db_template.organization_id

                new_session = InterviewSession(
                    organization_id=org_id,
                    template_id=selected_template_id,
                    person_id=selected_person_id,
                    status=SessionStatus.IN_PROGRESS,
                    evaluator_type=EvaluatorType.HEURISTIC if st.session_state.evaluator_mode == "Heuristic" else EvaluatorType.LLM,
                    started_at=func.now(),
                    session_metadata={}
                )
                db.add(new_session)
                db.flush()

                session_id = new_session.id
                evaluator_type = "heuristic" if st.session_state.evaluator_mode == "Heuristic" else "llm"
                logger.info(f"Interview session started: session_id={session_id}, person_id={selected_person_id}, template_id={selected_template_id}, evaluator_type={evaluator_type}")

            # Store session ID and initialize state
            st.session_state.active_session_id = session_id
            st.session_state.current_question_index = 0

            st.success("Interview started!")
            st.rerun()

        except Exception as e:
            st.error(f"Error starting interview: {e}")


def render_active_interview() -> None:
    """Render the active interview (Q&A flow)."""
    session_id = st.session_state.active_session_id

    # Load session from database and extract data while in session context
    with get_db_session() as db:
        session = db.get(InterviewSession, session_id)
        if not session:
            st.error("Session not found")
            del st.session_state.active_session_id
            st.rerun()
            return

        # Extract all needed data into plain Python objects to avoid DetachedInstanceError
        person_data = {
            "id": session.person.id,
            "name": session.person.name,
            "email": session.person.email,
            "role": session.person.role,
            "department": session.person.department,
        }
        template_data = {
            "id": session.template.id,
            "name": session.template.name,
            "version": session.template.version,
            "description": session.template.description,
        }
        # Extract questions data
        questions_data = [
            {
                "id": q.id,
                "question_text": q.question_text,
                "competency": q.competency,
                "difficulty": q.difficulty,
                "keypoints": q.keypoints or [],
                "order_index": q.order_index,
            }
            for q in sorted(session.template.questions, key=lambda q: q.order_index)
        ]

    # Check if interview is complete
    current_index = st.session_state.get("current_question_index", 0)

    if current_index >= len(questions_data):
        render_db_interview_complete(session_id, person_data, template_data, questions_data)
    else:
        render_db_current_question(session_id, person_data, template_data, questions_data, current_index)


def render_db_current_question(session_id: int, person: dict, template: dict, questions: List[dict], current_index: int) -> None:
    """Render the current question in database-backed interview."""
    current_question = questions[current_index]

    # Progress
    progress = current_index / len(questions)
    st.progress(progress)
    st.write(f"Question {current_index + 1} of {len(questions)}")

    # Display question
    st.subheader(f"Question {current_index + 1}")
    st.write(f"**Interviewee:** {person['name']}")
    st.write(f"**Competency:** {current_question['competency']}")
    st.write(f"**Difficulty:** {current_question['difficulty']}")
    st.divider()
    st.markdown(f"### {current_question['question_text']}")

    # Answer form
    with st.form(key=f"answer_form_{session_id}_{current_index}", clear_on_submit=True):
        answer = st.text_area(
            "Your Answer",
            placeholder="Type your answer here...",
            height=200,
            key=f"answer_input_{session_id}_{current_index}"
        )

        submit_button = st.form_submit_button("Submit Answer")

        if submit_button:
            if not answer.strip():
                st.error("Please provide an answer before submitting")
            else:
                try:
                    # Get evaluator
                    evaluator = get_evaluator_agent()

                    # Convert question dict to Question for evaluation
                    question_obj = Question(
                        id=current_question['id'],
                        text=current_question['question_text'],
                        competency=current_question['competency'],
                        difficulty=current_question['difficulty'],
                        keypoints=current_question['keypoints']
                    )

                    # Evaluate answer with loading indicator
                    eval_mode = st.session_state.get('evaluator_mode', 'Heuristic')
                    spinner_msg = "🤖 AI is evaluating your answer..." if eval_mode == "LLM-Powered" else "Evaluating answer..."
                    with st.spinner(spinner_msg):
                        evaluation = evaluator.evaluate(question_obj, answer.strip())

                    # Store in database
                    with get_db_session() as db:
                        # Add transcript entries
                        max_seq = db.execute(
                            select(func.max(TranscriptEntry.sequence_index)).where(
                                TranscriptEntry.session_id == session_id
                            )
                        ).scalar() or -1

                        # System question
                        db.add(TranscriptEntry(
                            session_id=session_id,
                            sequence_index=max_seq + 1,
                            speaker=SpeakerType.SYSTEM,
                            text=current_question['question_text']
                        ))

                        # Participant answer
                        db.add(TranscriptEntry(
                            session_id=session_id,
                            sequence_index=max_seq + 2,
                            speaker=SpeakerType.PARTICIPANT,
                            text=answer.strip()
                        ))

                        # Store evaluation
                        mastery_map = {"strong": MasteryLabel.STRONG, "mixed": MasteryLabel.MIXED, "weak": MasteryLabel.WEAK}

                        db.add(QuestionEvaluation(
                            session_id=session_id,
                            template_question_id=current_question['id'],
                            evaluator_type=EvaluatorType.HEURISTIC if st.session_state.evaluator_mode == "Heuristic" else EvaluatorType.LLM,
                            score_0_100=evaluation.score_0_100,
                            mastery_label=mastery_map[evaluation.mastery_label],
                            raw_answer=answer.strip(),
                            short_feedback=evaluation.short_feedback,
                            keypoints_coverage=[{"keypoint": kp.keypoint, "covered": kp.covered, "evidence": kp.evidence} for kp in evaluation.keypoints_coverage],
                            suggested_followup=evaluation.suggested_followup
                        ))

                        db.flush()

                    # Show immediate feedback
                    if evaluation.mastery_label == "strong":
                        st.success(f"Score: {evaluation.score_0_100}/100 - {evaluation.short_feedback}")
                    elif evaluation.mastery_label == "mixed":
                        st.warning(f"Score: {evaluation.score_0_100}/100 - {evaluation.short_feedback}")
                    else:
                        st.error(f"Score: {evaluation.score_0_100}/100 - {evaluation.short_feedback}")

                    if evaluation.suggested_followup:
                        st.info(f"💡 Follow-up: {evaluation.suggested_followup}")

                    # Advance to next question
                    st.session_state.current_question_index += 1
                    st.rerun()

                except Exception as e:
                    st.error(f"Error processing answer: {e}")
                    import traceback
                    st.code(traceback.format_exc())


def render_db_interview_complete(session_id: int, person: dict, template: dict, questions: List[dict]) -> None:
    """Render completion page for database-backed interview."""
    # Update session status
    with get_db_session() as db:
        session = db.get(InterviewSession, session_id)
        if session and session.status != SessionStatus.COMPLETED:
            session.status = SessionStatus.COMPLETED
            session.completed_at = func.now()

            # Generate summary
            evaluations = list(session.evaluations)
            if evaluations:
                avg_score = sum(e.score_0_100 for e in evaluations) / len(evaluations)
                strong_count = sum(1 for e in evaluations if e.mastery_label.value == "strong")
                weak_count = sum(1 for e in evaluations if e.mastery_label.value == "weak")

                summary = f"""Interview Summary for {person['name']}
Template: {template['name']} (v{template['version']})
Questions: {len(evaluations)}
Average Score: {avg_score:.1f}/100
Strong: {strong_count}, Weak: {weak_count}
"""
                session.summary = summary
                logger.info(f"Interview session completed: session_id={session_id}, person='{person['name']}', template='{template['name']}', avg_score={avg_score:.1f}, questions={len(evaluations)}")
            else:
                logger.info(f"Interview session completed: session_id={session_id}, person='{person['name']}', template='{template['name']}', no_evaluations=True")

            db.flush()

    st.success("🎉 Interview Complete!")

    # Execute lens analysis if LLM is available
    if LLM_AVAILABLE and st.session_state.evaluator_mode == "LLM-Powered":
        # Check if lenses have already been executed
        with get_db_session() as db:
            session = db.get(InterviewSession, session_id)
            existing_lens_results = list(session.lens_results)

        if not existing_lens_results:
            # Check if there are active lenses
            with get_db_session() as db:
                session = db.get(InterviewSession, session_id)
                org_id = session.organization_id
                active_lenses = db.execute(
                    select(Lens).where(Lens.organization_id == org_id, Lens.active == True)
                ).scalars().all()

            if active_lenses:
                st.info(f"🔍 Running {len(active_lenses)} lens analyses...")

                # Execute lenses
                try:
                    from lens_executor import LensExecutor
                    from llm_client import get_llm_client
                    import settings

                    # Get LLM client
                    provider = settings.LLM_PROVIDER
                    api_key = settings.get_api_key_for_provider(provider)
                    client = get_llm_client(provider, api_key)

                    # Create executor
                    executor = LensExecutor(
                        llm_client=client,
                        model=settings.LLM_MODEL,
                        temperature=settings.LLM_TEMPERATURE
                    )

                    # Execute all lenses
                    with st.spinner("Analyzing interview with lenses..."):
                        with get_db_session() as db:
                            lens_results = executor.execute_all_lenses(db, session_id, active_only=True)
                            # Extract counts before session closes (avoid DetachedInstanceError)
                            completed_count = sum(1 for lr in lens_results if lr.status.value == "completed")
                            failed_count = sum(1 for lr in lens_results if lr.status.value == "failed")

                    if completed_count > 0:
                        st.success(f"✅ Lens analysis complete! {completed_count} lenses executed successfully.")
                    if failed_count > 0:
                        st.warning(f"⚠️ {failed_count} lens(es) failed. Check Reports view for details.")

                except Exception as e:
                    st.error(f"Error executing lenses: {e}")
                    import traceback
                    st.caption("Lens analysis failed, but interview results are saved.")
                    with st.expander("Error details"):
                        st.code(traceback.format_exc())
            else:
                st.info("ℹ️ No active lenses configured. Visit Admin > Lens Management to add lenses.")
        else:
            st.info(f"ℹ️ Lens analysis already completed ({len(existing_lens_results)} lenses).")
    elif not LLM_AVAILABLE:
        st.info("ℹ️ Lens analysis requires LLM features. Install dependencies to enable.")
    else:
        st.info("ℹ️ Lens analysis is only available in LLM-Powered mode. Switch mode in sidebar to enable.")

    # Load evaluations and summary
    with get_db_session() as db:
        session = db.get(InterviewSession, session_id)
        session_summary = session.summary
        # Extract evaluation data while in session context
        evaluations_data = [
            {
                "template_question_id": e.template_question_id,
                "score_0_100": e.score_0_100,
                "mastery_label": e.mastery_label.value,
                "raw_answer": e.raw_answer,
                "short_feedback": e.short_feedback,
                "keypoints_coverage": e.keypoints_coverage or [],
                "suggested_followup": e.suggested_followup,
            }
            for e in session.evaluations
        ]

    # Display summary
    if session_summary:
        st.markdown(f"```\n{session_summary}\n```")

    st.divider()

    # Detailed results
    st.subheader("Detailed Results")

    for i, question in enumerate(questions):
        # Find evaluation for this question
        evaluation = next((e for e in evaluations_data if e["template_question_id"] == question["id"]), None)

        if evaluation:
            with st.expander(f"Q{i+1}: {question['question_text'][:50]}... - Score: {evaluation['score_0_100']}/100"):
                st.write(f"**Question:** {question['question_text']}")
                st.write(f"**Competency:** {question['competency']}")
                st.write(f"**Difficulty:** {question['difficulty']}")
                st.divider()

                st.write(f"**Your Answer:**")
                st.text(evaluation['raw_answer'])
                st.divider()

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Score", f"{evaluation['score_0_100']}/100")
                with col2:
                    st.metric("Mastery", evaluation['mastery_label'].upper())

                st.write(f"**Feedback:** {evaluation['short_feedback']}")

                # Keypoint coverage
                st.write("**Keypoint Coverage:**")
                for kp in evaluation['keypoints_coverage']:
                    if kp.get("covered"):
                        st.success(f"✓ {kp['keypoint']}")
                        if kp.get("evidence"):
                            st.caption(f"Evidence: {kp['evidence']}")
                    else:
                        st.error(f"✗ {kp['keypoint']}")

                if evaluation['suggested_followup']:
                    st.info(f"💡 {evaluation['suggested_followup']}")

    # Buttons
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Start New Interview"):
            del st.session_state.active_session_id
            del st.session_state.current_question_index
            st.rerun()
    with col2:
        if st.button("View Past Sessions"):
            st.info("Session history coming in Phase 7")


def render_legacy_interview() -> None:
    """Fallback to legacy in-memory interview flow."""
    # Check if questions exist
    if not st.session_state.questions:
        st.warning("No questions available. Please ask the interviewer to add some questions first.")
        return

    # Initialize agents (evaluator selected based on mode)
    questions_agent = QuestionsAgent(st.session_state.questions)
    evaluator_agent = get_evaluator_agent()
    orchestrator_agent = OrchestratorAgent(questions_agent, evaluator_agent)

    state = st.session_state.interview_state

    # Check if interview is finished
    if state.finished:
        render_interview_summary(state, questions_agent, orchestrator_agent)
    else:
        render_current_question(state, questions_agent, orchestrator_agent)


def render_current_question(state: InterviewState, questions_agent: QuestionsAgent, orchestrator_agent: OrchestratorAgent):
    """Render the current question and answer form."""
    current_question = questions_agent.get_next_question(state.current_index)

    if not current_question:
        st.error("Error: Could not retrieve current question")
        return

    # Progress indicator
    total_questions = questions_agent.count()
    st.progress((state.current_index) / total_questions)
    st.write(f"Question {state.current_index + 1} of {total_questions}")

    # Display question
    st.subheader(f"Question {state.current_index + 1}")
    st.write(f"**Competency:** {current_question.competency}")
    st.write(f"**Difficulty:** {current_question.difficulty}")
    st.divider()
    st.markdown(f"### {current_question.text}")

    # Answer form
    with st.form(key=f"answer_form_{state.current_index}", clear_on_submit=True):
        answer = st.text_area(
            "Your Answer",
            placeholder="Type your answer here...",
            height=200,
            key=f"answer_input_{state.current_index}"
        )

        submit_button = st.form_submit_button("Submit Answer")

        if submit_button:
            if not answer.strip():
                st.error("Please provide an answer before submitting")
            else:
                # Process answer through orchestrator with loading indicator
                eval_mode = st.session_state.get('evaluator_mode', 'Heuristic')
                spinner_msg = "🤖 AI is evaluating your answer..." if eval_mode == "LLM-Powered" else "Evaluating answer..."
                with st.spinner(spinner_msg):
                    updated_state = orchestrator_agent.step(state, answer)
                st.session_state.interview_state = updated_state

                # Show immediate feedback
                if current_question.id in updated_state.evaluations:
                    evaluation = updated_state.evaluations[current_question.id]

                    # Use color based on mastery level
                    if evaluation.mastery_label == "strong":
                        st.success(f"Score: {evaluation.score_0_100}/100 - {evaluation.short_feedback}")
                    elif evaluation.mastery_label == "mixed":
                        st.warning(f"Score: {evaluation.score_0_100}/100 - {evaluation.short_feedback}")
                    else:
                        st.error(f"Score: {evaluation.score_0_100}/100 - {evaluation.short_feedback}")

                    if evaluation.suggested_followup:
                        st.info(f"💡 Follow-up: {evaluation.suggested_followup}")

                # Rerun to show next question or summary
                st.rerun()


def render_interview_summary(state: InterviewState, questions_agent: QuestionsAgent, orchestrator_agent: OrchestratorAgent):
    """Render the final interview summary with all results."""
    st.success("Interview Complete!")

    # Generate and display summary
    summary = orchestrator_agent.generate_summary(state)
    st.markdown(f"```\n{summary}\n```")

    st.divider()

    # Detailed per-question results
    st.subheader("Detailed Results")

    for question in st.session_state.questions:
        if question.id in state.evaluations:
            evaluation = state.evaluations[question.id]

            with st.expander(f"Q{question.id}: {question.text[:50]}... - Score: {evaluation.score_0_100}/100"):
                st.write(f"**Question:** {question.text}")
                st.write(f"**Competency:** {question.competency}")
                st.write(f"**Difficulty:** {question.difficulty}")
                st.divider()

                st.write(f"**Your Answer:**")
                st.text(evaluation.raw_answer)
                st.divider()

                # Score and mastery
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Score", f"{evaluation.score_0_100}/100")
                with col2:
                    st.metric("Mastery", evaluation.mastery_label.upper())

                st.write(f"**Feedback:** {evaluation.short_feedback}")

                # Keypoint coverage
                st.write("**Keypoint Coverage:**")
                for kp_coverage in evaluation.keypoints_coverage:
                    if kp_coverage.covered:
                        st.success(f"✓ {kp_coverage.keypoint}")
                        if kp_coverage.evidence:
                            st.caption(f"Evidence: {kp_coverage.evidence}")
                    else:
                        st.error(f"✗ {kp_coverage.keypoint}")

                if evaluation.suggested_followup:
                    st.info(f"💡 {evaluation.suggested_followup}")

    # Restart button
    st.divider()
    if st.button("Start New Interview"):
        st.session_state.interview_state = InterviewState()
        st.rerun()


def render_session_detail_view(session_id: int) -> None:
    """Render detailed view of a single interview session."""
    from db_models import LensResult, LensCriterionResult, LensResultStatus

    # Load session
    with get_db_session() as db:
        session = db.get(InterviewSession, session_id)
        if not session:
            st.error(f"Session {session_id} not found")
            st.session_state.view_session_id = None
            st.rerun()
            return

        # Extract all data while in session to avoid DetachedInstanceError
        person_data = {
            'id': session.person.id,
            'name': session.person.name,
            'role': session.person.role,
            'department': session.person.department
        }

        template_data = {
            'id': session.template.id,
            'name': session.template.name,
            'version': session.template.version,
            'description': session.template.description
        }

        session_data = {
            'id': session.id,
            'status': session.status,
            'started_at': session.started_at,
            'completed_at': session.completed_at
        }

        # Extract evaluations with all needed data
        evaluations = [
            {
                'id': e.id,
                'template_question_id': e.template_question_id,
                'score_0_100': e.score_0_100,
                'mastery_label': e.mastery_label,
                'short_feedback': e.short_feedback,
                'raw_answer': e.raw_answer,
                'evaluator_type': e.evaluator_type,
                'keypoints_coverage': e.keypoints_coverage,
                'suggested_followup': e.suggested_followup,
                'created_at': e.created_at
            }
            for e in sorted(session.evaluations, key=lambda e: e.created_at)
        ]

        # Extract transcript
        transcript = [
            {
                'id': t.id,
                'sequence_index': t.sequence_index,
                'speaker': t.speaker,
                'text': t.text
            }
            for t in sorted(session.transcript, key=lambda t: t.sequence_index)
        ]

        # Extract lens results with IDs for later lookup
        lens_result_ids = [lr.id for lr in session.lens_results]

    # Header with back button and export
    col1, col2, col3 = st.columns([1, 4, 1])
    with col1:
        if st.button("← Back to Reports"):
            st.session_state.view_session_id = None
            st.rerun()
    with col2:
        st.header(f"📄 Session Detail: {person_data['name']}")
    with col3:
        # JSON Export button
        if st.button("📥 Export JSON", key="export_json_button"):
            try:
                from export_helpers import export_session_json
                from datetime import datetime

                # Generate JSON export
                with get_db_session() as db:
                    json_data = export_session_json(db, session_id)

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

                st.download_button(
                    label="⬇️ Download JSON",
                    data=json_data,
                    file_name=f"session_{session_id}_{timestamp}.json",
                    mime="application/json",
                    key="download_json"
                )
            except Exception as e:
                st.error(f"Error exporting JSON: {e}")

    st.divider()

    # Session overview
    st.subheader("📋 Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.write(f"**Interviewee:** {person_data['name']}")
        if person_data['role']:
            st.caption(f"Role: {person_data['role']}")
        if person_data['department']:
            st.caption(f"Department: {person_data['department']}")

    with col2:
        st.write(f"**Template:** {template_data['name']}")
        st.caption(f"Version: {template_data['version']}")
        if template_data['description']:
            st.caption(template_data['description'][:100])

    with col3:
        st.write(f"**Status:** {session_data['status'].value}")
        if session_data['started_at']:
            st.caption(f"Started: {session_data['started_at'].strftime('%Y-%m-%d %H:%M')}")
        if session_data['completed_at']:
            st.caption(f"Completed: {session_data['completed_at'].strftime('%Y-%m-%d %H:%M')}")

    with col4:
        if evaluations:
            avg_score = sum(e['score_0_100'] for e in evaluations) / len(evaluations)
            st.metric("Average Score", f"{avg_score:.1f}/100")
        st.caption(f"Questions: {len(evaluations)}")
        st.caption(f"Lens Analyses: {len(lens_result_ids)}")

    st.divider()

    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["💬 Transcript", "✅ Evaluations", "🔍 Lens Results"])

    # Tab 1: Full Transcript
    with tab1:
        st.subheader("Complete Transcript")

        if not transcript:
            st.info("No transcript available for this session")
        else:
            for entry in transcript:
                speaker_label = "🤖 SYSTEM" if entry['speaker'] == SpeakerType.SYSTEM else "👤 CANDIDATE"
                speaker_color = "blue" if entry['speaker'] == SpeakerType.SYSTEM else "green"

                with st.container():
                    st.markdown(f":{speaker_color}[**{speaker_label}**]")
                    st.write(entry['text'])
                    st.caption(f"Sequence: {entry['sequence_index']}")
                    st.divider()

    # Tab 2: Question Evaluations
    with tab2:
        st.subheader("Question-by-Question Evaluations")

        if not evaluations:
            st.info("No evaluations available for this session")
        else:
            for i, evaluation in enumerate(evaluations, 1):
                # Get the question
                with get_db_session() as db:
                    question = db.get(TemplateQuestion, evaluation['template_question_id'])

                # Color based on mastery
                mastery_color = {
                    MasteryLabel.STRONG: "🟢",
                    MasteryLabel.MIXED: "🟡",
                    MasteryLabel.WEAK: "🔴"
                }.get(evaluation['mastery_label'], "⚪")

                with st.expander(f"Q{i}: {mastery_color} {question.question_text[:60]}... - {evaluation['score_0_100']}/100", expanded=False):
                    st.write(f"**Question:** {question.question_text}")
                    st.caption(f"Competency: {question.competency} | Difficulty: {question.difficulty}")

                    st.divider()

                    st.write(f"**Candidate's Answer:**")
                    st.text_area("", evaluation['raw_answer'], height=150, disabled=True, key=f"answer_{evaluation['id']}")

                    st.divider()

                    # Metrics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Score", f"{evaluation['score_0_100']}/100")
                    with col2:
                        st.metric("Mastery", evaluation['mastery_label'].value.upper())
                    with col3:
                        st.metric("Evaluator", evaluation['evaluator_type'].value)

                    st.write(f"**Feedback:** {evaluation['short_feedback']}")

                    # Keypoint coverage
                    st.write("**Keypoint Coverage:**")
                    for kp in evaluation['keypoints_coverage']:
                        if kp.get("covered"):
                            st.success(f"✓ {kp['keypoint']}")
                            if kp.get("evidence"):
                                st.caption(f"Evidence: {kp['evidence']}")
                        else:
                            st.error(f"✗ {kp['keypoint']}")

                    if evaluation['suggested_followup']:
                        st.info(f"💡 Suggested follow-up: {evaluation['suggested_followup']}")

    # Tab 3: Lens Analysis Results
    with tab3:
        st.subheader("Lens Analysis Results")

        if not lens_result_ids:
            st.info("No lens analyses have been run on this session yet")
        else:
            for lens_result_id in lens_result_ids:
                with get_db_session() as db:
                    db_lens_result = db.get(LensResult, lens_result_id)

                    # Extract all data while in session
                    lens_result_data = {
                        'id': db_lens_result.id,
                        'status': db_lens_result.status,
                        'llm_provider': db_lens_result.llm_provider,
                        'llm_model': db_lens_result.llm_model,
                        'created_at': db_lens_result.created_at,
                        'error_message': db_lens_result.error_message,
                        'lens_name': db_lens_result.lens.name,
                        'lens_description': db_lens_result.lens.description,
                        'lens_version': db_lens_result.lens.version,
                        'lens_config': dict(db_lens_result.lens.config) if db_lens_result.lens.config else {}
                    }

                    criterion_results = [
                        {
                            'criterion_name': cr.criterion_name,
                            'score': cr.score,
                            'scale': cr.scale,
                            'notes': cr.notes,
                            'flags': list(cr.flags) if cr.flags else [],
                            'extracted_items': list(cr.extracted_items) if cr.extracted_items else [],
                            'supporting_quotes': cr.supporting_quotes
                        }
                        for cr in db_lens_result.criterion_results
                    ]

                # Status indicator
                status_emoji = {
                    LensResultStatus.COMPLETED: "✅",
                    LensResultStatus.IN_PROGRESS: "🔄",
                    LensResultStatus.FAILED: "❌",
                    LensResultStatus.PENDING: "⏳"
                }.get(lens_result_data['status'], "❓")

                with st.expander(f"{status_emoji} {lens_result_data['lens_name']} - {lens_result_data['status'].value}", expanded=True):
                    st.write(f"**Description:** {lens_result_data['lens_description'] or 'No description'}")
                    st.caption(f"Version: {lens_result_data['lens_version']} | Scoring Scale: {lens_result_data['lens_config'].get('scoring_scale', 'N/A')}")
                    st.caption(f"Provider: {lens_result_data['llm_provider']} | Model: {lens_result_data['llm_model']}")

                    if lens_result_data['created_at']:
                        st.caption(f"Executed: {lens_result_data['created_at'].strftime('%Y-%m-%d %H:%M')}")

                    if lens_result_data['status'] == LensResultStatus.FAILED:
                        st.error(f"Error: {lens_result_data['error_message']}")
                        continue

                    if lens_result_data['status'] != LensResultStatus.COMPLETED:
                        st.warning(f"Analysis is {lens_result_data['status'].value}")
                        continue

                    st.divider()

                    # Display criterion results
                    st.write(f"**Criteria Results ({len(criterion_results)}):**")

                    for cr in criterion_results:
                        st.markdown(f"### {cr['criterion_name']}")

                        col1, col2 = st.columns([1, 3])

                        with col1:
                            if cr['score'] is not None:
                                st.metric("Score", f"{cr['score']}/{cr['scale']}")

                        with col2:
                            if cr['notes']:
                                st.write(f"**Assessment:** {cr['notes']}")

                        # Flags
                        if cr['flags']:
                            st.write("**Flags:**")
                            for flag in cr['flags']:
                                st.caption(f"🚩 {flag}")

                        # Extracted items
                        if cr['extracted_items']:
                            st.write("**Observed Behaviors:**")
                            for item in cr['extracted_items']:
                                st.caption(f"• {item}")

                        # Supporting quotes
                        if cr['supporting_quotes']:
                            st.write("**Supporting Evidence:**")
                            for quote in cr['supporting_quotes']:
                                speaker = quote.get('speaker', 'unknown')
                                text = quote.get('text', '')
                                speaker_emoji = "🤖" if speaker == "interviewer" else "👤"
                                st.info(f"{speaker_emoji} \"{text}\"")

                        st.divider()


def render_reports_view() -> None:
    """Render the reports dashboard with analytics and filtering."""
    if not DATABASE_AVAILABLE:
        st.error("Database features not available. Please install database dependencies.")
        st.code("pip install sqlalchemy alembic", language="bash")
        return

    # Check if viewing a specific session
    if "view_session_id" in st.session_state and st.session_state.view_session_id:
        render_session_detail_view(st.session_state.view_session_id)
        return

    st.header("📊 Reports Dashboard")
    st.write("Analyze interview sessions, performance trends, and lens results.")

    # Import necessary models for lens results
    from db_models import LensResult, LensCriterionResult, LensResultStatus

    # Get filter options from database
    # Extract data while in session context to avoid DetachedInstanceError
    with get_db_session() as db:
        people_objs = db.execute(select(Person).order_by(Person.name)).scalars().all()
        template_objs = db.execute(select(InterviewTemplate).order_by(InterviewTemplate.name)).scalars().all()
        lens_objs = db.execute(select(Lens).order_by(Lens.name)).scalars().all()

        # Extract to simple data structures
        all_people = [(p.id, p.name) for p in people_objs]
        all_templates = [(t.id, t.name) for t in template_objs]
        all_lenses = [(l.id, l.name) for l in lens_objs]

        # Get unique departments and roles
        departments = sorted(set(p.department for p in people_objs if p.department))
        roles = sorted(set(p.role for p in people_objs if p.role))

    # Filters in sidebar expander
    with st.expander("🔍 Filters", expanded=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            filter_person = st.multiselect(
                "Person",
                options=[p[0] for p in all_people],
                format_func=lambda pid: next(p[1] for p in all_people if p[0] == pid),
                default=[]
            )

            filter_department = st.multiselect(
                "Department",
                options=departments,
                default=[]
            )

        with col2:
            filter_template = st.multiselect(
                "Template",
                options=[t[0] for t in all_templates],
                format_func=lambda tid: next(t[1] for t in all_templates if t[0] == tid),
                default=[]
            )

            filter_role = st.multiselect(
                "Role",
                options=roles,
                default=[]
            )

        with col3:
            filter_status = st.multiselect(
                "Status",
                options=["completed", "in_progress", "cancelled"],
                default=["completed"]
            )

            filter_lens = st.multiselect(
                "Lens (for lens results)",
                options=[l[0] for l in all_lenses],
                format_func=lambda lid: next(l[1] for l in all_lenses if l[0] == lid),
                default=[]
            )

    # Build query with filters
    with get_db_session() as db:
        query = select(InterviewSession).join(Person).join(InterviewTemplate)

        # Apply filters
        if filter_person:
            query = query.where(InterviewSession.person_id.in_(filter_person))

        if filter_department:
            query = query.where(Person.department.in_(filter_department))

        if filter_role:
            query = query.where(Person.role.in_(filter_role))

        if filter_template:
            query = query.where(InterviewSession.template_id.in_(filter_template))

        if filter_status:
            status_map = {
                "completed": SessionStatus.COMPLETED,
                "in_progress": SessionStatus.IN_PROGRESS,
                "cancelled": SessionStatus.CANCELLED
            }
            status_enums = [status_map[s] for s in filter_status]
            query = query.where(InterviewSession.status.in_(status_enums))

        # Order by most recent first
        query = query.order_by(InterviewSession.created_at.desc())

        session_objs = db.execute(query).scalars().all()

        # Extract session data to dicts to avoid DetachedInstanceError
        sessions = [
            {
                'id': s.id,
                'status': s.status,
                'created_at': s.created_at,
                'started_at': s.started_at,
                'completed_at': s.completed_at
            }
            for s in session_objs
        ]

    st.divider()

    # Overview metrics
    st.subheader("📈 Overview")

    if not sessions:
        st.info("No sessions match the current filters.")
        return

    # Calculate metrics
    total_sessions = len(sessions)
    completed_sessions = [s for s in sessions if s['status'] == SessionStatus.COMPLETED]
    completed_count = len(completed_sessions)

    # Calculate average scores from evaluations
    all_scores = []
    for session in completed_sessions:
        with get_db_session() as db:
            db_session = db.get(InterviewSession, session['id'])
            evaluations = list(db_session.evaluations)
            if evaluations:
                scores = [e.score_0_100 for e in evaluations]
                all_scores.extend(scores)

    avg_score = sum(all_scores) / len(all_scores) if all_scores else 0

    # Display metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Sessions", total_sessions)

    with col2:
        st.metric("Completed", completed_count)

    with col3:
        st.metric("Average Score", f"{avg_score:.1f}/100" if all_scores else "N/A")

    with col4:
        # Count sessions with lens results
        lens_analysis_count = 0
        for session in completed_sessions:
            with get_db_session() as db:
                db_session = db.get(InterviewSession, session['id'])
                if list(db_session.lens_results):
                    lens_analysis_count += 1
        st.metric("With Lens Analysis", lens_analysis_count)

    st.divider()

    # Score distribution
    if all_scores:
        st.subheader("📊 Score Distribution")

        # Create bins for scores
        bins = [0, 50, 70, 80, 90, 100]
        bin_labels = ["0-49 (Weak)", "50-69 (Fair)", "70-79 (Good)", "80-89 (Strong)", "90-100 (Excellent)"]
        bin_counts = [0] * len(bin_labels)

        for score in all_scores:
            if score >= 90:
                bin_counts[4] += 1  # 90-100 (Excellent)
            elif score >= 80:
                bin_counts[3] += 1  # 80-89 (Strong)
            elif score >= 70:
                bin_counts[2] += 1  # 70-79 (Good)
            elif score >= 50:
                bin_counts[1] += 1  # 50-69 (Fair)
            else:
                bin_counts[0] += 1  # 0-49 (Weak)

        # Display as columns with metrics
        cols = st.columns(len(bin_labels))
        for i, (label, count) in enumerate(zip(bin_labels, bin_counts)):
            with cols[i]:
                percentage = (count / len(all_scores) * 100) if all_scores else 0
                st.metric(label, count, f"{percentage:.1f}%")

        # Add visual bar chart (only if there's data to display)
        if any(bin_counts):
            import pandas as pd
            chart_data = pd.DataFrame({
                'Score Range': bin_labels,
                'Count': bin_counts
            }).set_index('Score Range')
            st.bar_chart(chart_data)

        st.divider()

    # Average score by department
    if completed_sessions and departments:
        st.subheader("📈 Average Score by Department")

        department_scores = {}
        for dept in departments:
            dept_sessions = [s for s in completed_sessions if s.get('department') == dept]
            dept_scores_list = []

            for session in dept_sessions:
                with get_db_session() as db:
                    db_session = db.get(InterviewSession, session['id'])
                    evaluations = list(db_session.evaluations)
                    if evaluations:
                        session_avg = sum(e.score_0_100 for e in evaluations) / len(evaluations)
                        dept_scores_list.append(session_avg)

            if dept_scores_list:
                department_scores[dept] = sum(dept_scores_list) / len(dept_scores_list)

        if department_scores:
            import pandas as pd
            dept_chart_data = pd.DataFrame({
                'Department': list(department_scores.keys()),
                'Average Score': list(department_scores.values())
            }).set_index('Department')

            st.bar_chart(dept_chart_data)
            st.caption(f"Average scores across {len(department_scores)} departments")

        st.divider()

    # Sessions table
    col_header, col_export = st.columns([3, 1])
    with col_header:
        st.subheader("📋 Interview Sessions")
    with col_export:
        # CSV Export button
        if st.button("📥 Export as CSV", key="export_csv"):
            try:
                from export_helpers import export_sessions_csv
                from datetime import datetime

                # Prepare session data for export
                export_data = []
                for session in sessions:
                    # Fetch evaluation data for each session
                    with get_db_session() as db:
                        db_session = db.get(InterviewSession, session['id'])
                        person_data = {
                            'name': db_session.person.name,
                            'role': db_session.person.role,
                            'department': db_session.person.department
                        }
                        template_data = {
                            'name': db_session.template.name
                        }
                        evaluations = list(db_session.evaluations)
                        lens_results = list(db_session.lens_results)

                        avg_score = sum(e.score_0_100 for e in evaluations) / len(evaluations) if evaluations else 0

                        export_data.append({
                            'id': session['id'],
                            'person_name': person_data['name'],
                            'role': person_data.get('role', ''),
                            'department': person_data.get('department', ''),
                            'template_name': template_data['name'],
                            'status': session['status'].value,
                            'started_at': session['started_at'].strftime("%Y-%m-%d %H:%M") if session['started_at'] else '',
                            'completed_at': session['completed_at'].strftime("%Y-%m-%d %H:%M") if session['completed_at'] else '',
                            'evaluator_type': session['evaluator_type'].value,
                            'avg_score': avg_score,
                            'question_count': len(evaluations),
                            'lens_count': len(lens_results)
                        })

                # Generate CSV
                csv_data = export_sessions_csv(export_data)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

                st.download_button(
                    label="⬇️ Download CSV",
                    data=csv_data,
                    file_name=f"interview_sessions_{timestamp}.csv",
                    mime="text/csv",
                    key="download_csv"
                )
            except Exception as e:
                st.error(f"Error exporting CSV: {e}")

    # Display sessions in a table-like format
    for session in sessions[:20]:  # Limit to 20 most recent
        with get_db_session() as db:
            db_session = db.get(InterviewSession, session['id'])

            # Extract all data while in session to avoid DetachedInstanceError
            person_data = {
                'name': db_session.person.name,
                'role': db_session.person.role,
                'department': db_session.person.department
            }

            template_data = {
                'name': db_session.template.name,
                'version': db_session.template.version
            }

            evaluations = [{'score_0_100': e.score_0_100} for e in db_session.evaluations]

            lens_result_data = [
                {
                    'id': lr.id,
                    'status': lr.status,
                    'lens_name': lr.lens.name
                }
                for lr in db_session.lens_results
            ]

        # Calculate session average score
        if evaluations:
            session_avg = sum(e['score_0_100'] for e in evaluations) / len(evaluations)
        else:
            session_avg = None

        # Status emoji (fixed: ABANDONED -> CANCELLED)
        status_emoji = {
            SessionStatus.COMPLETED: "✅",
            SessionStatus.IN_PROGRESS: "🔄",
            SessionStatus.CANCELLED: "❌"
        }.get(session['status'], "❓")

        with st.expander(f"{status_emoji} {person_data['name']} - {template_data['name']} ({session['created_at'].strftime('%Y-%m-%d %H:%M')})"):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.write(f"**Interviewee:** {person_data['name']}")
                if person_data['role']:
                    st.caption(f"Role: {person_data['role']}")
                if person_data['department']:
                    st.caption(f"Department: {person_data['department']}")

                st.write(f"**Template:** {template_data['name']} (v{template_data['version']})")
                st.write(f"**Status:** {session['status'].value}")

                if session['started_at']:
                    st.caption(f"Started: {session['started_at'].strftime('%Y-%m-%d %H:%M')}")
                if session['completed_at']:
                    st.caption(f"Completed: {session['completed_at'].strftime('%Y-%m-%d %H:%M')}")

            with col2:
                if session_avg is not None:
                    st.metric("Average Score", f"{session_avg:.1f}/100")

                st.metric("Questions", len(evaluations))
                st.metric("Lens Analyses", len(lens_result_data))

            # Show lens results if any
            if lens_result_data:
                st.divider()
                st.write("**Lens Analysis Results:**")

                for lens_result in lens_result_data:
                    with get_db_session() as db:
                        db_lens_result = db.get(LensResult, lens_result['id'])
                        criterion_results = [
                            {
                                'criterion_name': cr.criterion_name,
                                'score': cr.score,
                                'scale': cr.scale
                            }
                            for cr in db_lens_result.criterion_results
                        ]

                    status_text = lens_result['status'].value
                    status_color = {
                        LensResultStatus.COMPLETED: "🟢",
                        LensResultStatus.IN_PROGRESS: "🟡",
                        LensResultStatus.FAILED: "🔴",
                        LensResultStatus.PENDING: "⚪"
                    }.get(lens_result['status'], "❓")

                    st.write(f"{status_color} **{lens_result['lens_name']}** ({status_text})")

                    if lens_result['status'] == LensResultStatus.COMPLETED and criterion_results:
                        # Show criterion scores
                        criterion_cols = st.columns(min(len(criterion_results), 4))
                        for i, cr in enumerate(criterion_results[:4]):
                            with criterion_cols[i]:
                                if cr['score'] is not None:
                                    st.caption(f"{cr['criterion_name']}: {cr['score']}/{cr['scale']}")

                        if len(criterion_results) > 4:
                            st.caption(f"...and {len(criterion_results) - 4} more criteria")

            # Action buttons
            st.divider()
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("View Details", key=f"view_{session['id']}"):
                    st.session_state.view_session_id = session['id']
                    st.rerun()
            with col_b:
                if st.button("Export", key=f"export_{session['id']}"):
                    st.info("Export functionality coming soon")

    if len(sessions) > 20:
        st.caption(f"Showing 20 most recent sessions out of {len(sessions)} total. Use filters to narrow down results.")


def render_admin_view() -> None:
    """Render the admin view for managing people and templates."""
    if not DATABASE_AVAILABLE:
        st.error("Database features not available. Please install database dependencies.")
        st.code("pip install sqlalchemy alembic", language="bash")
        return

    st.header("Admin Dashboard")
    st.write("Manage people, interview templates, lenses, and monitor live sessions.")

    # Create tabs for different admin functions
    tab1, tab2, tab3, tab4 = st.tabs(["👥 People Management", "📋 Template Management", "🔍 Lens Management", "🎧 Live Sessions"])

    with tab1:
        render_people_management()

    with tab2:
        render_template_management()

    with tab3:
        render_lens_management()

    with tab4:
        render_live_sessions()


def render_people_management() -> None:
    """Render the people management interface."""
    st.subheader("People Management")

    # Get or create default organization
    with get_db_session() as db:
        org = db.execute(select(Organization)).scalars().first()
        if not org:
            org = Organization(name="Default Organization", settings={})
            db.add(org)
            db.flush()
        org_id = org.id  # Extract ID while in session

    # Form to add new person
    with st.expander("➕ Add New Person", expanded=False):
        with st.form("add_person_form", clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                name = st.text_input("Name *", placeholder="John Doe")
                email = st.text_input("Email *", placeholder="john.doe@example.com")
                role = st.text_input("Role", placeholder="Software Engineer")

            with col2:
                department = st.text_input("Department", placeholder="Engineering")
                tags_input = st.text_input(
                    "Tags (comma-separated)",
                    placeholder="python, backend, senior"
                )
                status = st.selectbox("Status", options=["active", "inactive"])

            submit = st.form_submit_button("Add Person")

            if submit:
                if not name.strip():
                    st.error("Name is required")
                elif not email.strip():
                    st.error("Email is required")
                else:
                    # Parse tags
                    tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()]

                    try:
                        with get_db_session() as db:
                            new_person = Person(
                                organization_id=org_id,
                                name=name.strip(),
                                email=email.strip(),
                                role=role.strip() if role.strip() else None,
                                department=department.strip() if department.strip() else None,
                                tags=tags,
                                status=PersonStatus.ACTIVE if status == "active" else PersonStatus.INACTIVE
                            )
                            db.add(new_person)
                            db.flush()
                            # Save name before session closes (object detaches after context exits)
                            person_name = new_person.name

                        st.success(f"Added {person_name}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error adding person: {e}")

    st.divider()

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        filter_department = st.selectbox(
            "Filter by Department",
            options=["All"],
            key="filter_dept"
        )

    with col2:
        filter_role = st.selectbox(
            "Filter by Role",
            options=["All"],
            key="filter_role"
        )

    with col3:
        filter_status = st.selectbox(
            "Filter by Status",
            options=["All", "active", "inactive"],
            key="filter_status"
        )

    # Get all people and extract data while in session context
    with get_db_session() as db:
        query = select(Person).order_by(Person.created_at.desc())
        people_objs = db.execute(query).scalars().all()

        # Extract data to dicts to avoid DetachedInstanceError
        people = [
            {
                'id': p.id,
                'name': p.name,
                'email': p.email,
                'role': p.role,
                'department': p.department,
                'tags': list(p.tags) if p.tags else [],
                'status': p.status,
                'created_at': p.created_at
            }
            for p in people_objs
        ]

    if not people:
        st.info("No people in the system yet. Add your first person above!")
    else:
        st.write(f"**Total People: {len(people)}**")

        # Display people in a table-like format
        for person in people:
            with st.expander(f"👤 {person['name']} - {person['email']}"):
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.write(f"**Email:** {person['email']}")
                    if person['role']:
                        st.write(f"**Role:** {person['role']}")
                    if person['department']:
                        st.write(f"**Department:** {person['department']}")
                    if person['tags']:
                        st.write(f"**Tags:** {', '.join(person['tags'])}")
                    st.caption(f"Status: {person['status'].value}")
                    st.caption(f"Added: {person['created_at'].strftime('%Y-%m-%d %H:%M')}")

                with col2:
                    # Toggle status button
                    current_status = person['status']
                    new_status = PersonStatus.INACTIVE if current_status == PersonStatus.ACTIVE else PersonStatus.ACTIVE

                    if st.button(
                        f"Set {new_status.value}",
                        key=f"toggle_{person['id']}",
                        type="secondary"
                    ):
                        try:
                            with get_db_session() as db:
                                db_person = db.get(Person, person['id'])
                                if db_person:
                                    db_person.status = new_status
                                    db.flush()
                            st.success(f"Status updated to {new_status.value}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error updating status: {e}")


def render_template_management() -> None:
    """Render the template management interface."""
    st.subheader("Template Management")

    # Get or create default organization
    with get_db_session() as db:
        org = db.execute(select(Organization)).scalars().first()
        if not org:
            org = Organization(name="Default Organization", settings={})
            db.add(org)
            db.flush()
        org_id = org.id  # Extract ID while in session

    # Form to add new template
    with st.expander("➕ Add New Interview Template", expanded=False):
        with st.form("add_template_form", clear_on_submit=True):
            name = st.text_input("Template Name *", placeholder="Python Developer - L2")
            description = st.text_area(
                "Description",
                placeholder="Technical interview for mid-level Python developers...",
                height=100
            )

            col1, col2 = st.columns(2)
            with col1:
                version = st.number_input("Version", min_value=1, value=1)
            with col2:
                active = st.checkbox("Active", value=True)

            submit = st.form_submit_button("Create Template")

            if submit:
                if not name.strip():
                    st.error("Template name is required")
                else:
                    try:
                        with get_db_session() as db:
                            new_template = InterviewTemplate(
                                organization_id=org_id,
                                name=name.strip(),
                                description=description.strip() if description.strip() else None,
                                version=version,
                                active=active
                            )
                            db.add(new_template)
                            db.flush()
                            # Save name before session closes (object detaches after context exits)
                            template_name = new_template.name

                        st.success(f"Created template: {template_name}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error creating template: {e}")

    st.divider()

    # Get all templates and extract data while in session context
    with get_db_session() as db:
        query = select(InterviewTemplate).order_by(InterviewTemplate.created_at.desc())
        template_objs = db.execute(query).scalars().all()

        # Extract data to dicts to avoid DetachedInstanceError
        templates = [
            {
                'id': t.id,
                'name': t.name,
                'description': t.description,
                'version': t.version,
                'active': t.active,
                'created_at': t.created_at,
                'questions': [
                    {
                        'id': q.id,
                        'order_index': q.order_index,
                        'question_text': q.question_text,
                        'competency': q.competency,
                        'difficulty': q.difficulty,
                        'keypoints': list(q.keypoints) if q.keypoints else []
                    }
                    for q in t.questions
                ]
            }
            for t in template_objs
        ]

    if not templates:
        st.info("No templates in the system yet. Create your first template above!")
    else:
        st.write(f"**Total Templates: {len(templates)}**")

        # Display templates
        for template in templates:
            questions = template['questions']

            status_emoji = "✅" if template['active'] else "⏸️"
            with st.expander(f"{status_emoji} {template['name']} (v{template['version']}) - {len(questions)} questions"):
                # Template details
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.write(f"**Name:** {template['name']}")
                    if template['description']:
                        st.write(f"**Description:** {template['description']}")
                    st.caption(f"Version: {template['version']}")
                    st.caption(f"Status: {'Active' if template['active'] else 'Inactive'}")
                    st.caption(f"Created: {template['created_at'].strftime('%Y-%m-%d %H:%M')}")

                with col2:
                    # Toggle active status
                    new_active = not template['active']
                    if st.button(
                        f"Set {'Active' if new_active else 'Inactive'}",
                        key=f"toggle_template_{template['id']}",
                        type="secondary"
                    ):
                        try:
                            with get_db_session() as db:
                                db_template = db.get(InterviewTemplate, template['id'])
                                if db_template:
                                    db_template.active = new_active
                                    db.flush()
                            st.success(f"Status updated")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error updating status: {e}")

                st.divider()

                # Questions section
                st.write(f"**Questions ({len(questions)}):**")

                if questions:
                    for q in sorted(questions, key=lambda x: x['order_index']):
                        with st.container():
                            st.write(f"**{q['order_index'] + 1}.** {q['question_text']}")
                            col_a, col_b, col_c = st.columns(3)
                            with col_a:
                                st.caption(f"📚 {q['competency']}")
                            with col_b:
                                st.caption(f"⚡ {q['difficulty']}")
                            with col_c:
                                st.caption(f"🎯 {len(q['keypoints'])} keypoints")
                            st.caption(f"Keypoints: {', '.join(q['keypoints'])}")
                            st.divider()
                else:
                    st.info("No questions yet. Add questions below.")

                # Add question form
                st.divider()
                st.write(f"**➕ Add Question to {template['name']}**")
                with st.form(f"add_question_to_template_{template['id']}", clear_on_submit=True):
                    question_text = st.text_area(
                        "Question *",
                        placeholder="What is the difference between...",
                        height=100
                    )

                    col_q1, col_q2 = st.columns(2)
                    with col_q1:
                        competency = st.text_input(
                            "Competency *",
                            placeholder="Python Fundamentals"
                        )
                    with col_q2:
                        difficulty = st.selectbox(
                            "Difficulty *",
                            options=["Easy", "Medium", "Hard"]
                        )

                    keypoints_text = st.text_area(
                        "Keypoints (comma-separated) *",
                        placeholder="mutable vs immutable, syntax differences, use cases",
                        height=80
                    )

                    submit_q = st.form_submit_button("Add Question")

                    if submit_q:
                        if not question_text.strip():
                            st.error("Question text is required")
                        elif not competency.strip():
                            st.error("Competency is required")
                        elif not keypoints_text.strip():
                            st.error("Keypoints are required")
                        else:
                            keypoints = [kp.strip() for kp in keypoints_text.split(",") if kp.strip()]
                            if not keypoints:
                                st.error("Please provide at least one keypoint")
                            else:
                                try:
                                    with get_db_session() as db:
                                        # Get current max order_index
                                        db_template = db.get(InterviewTemplate, template['id'])
                                        max_order = max([q.order_index for q in db_template.questions], default=-1)

                                        new_question = TemplateQuestion(
                                            template_id=template['id'],
                                            order_index=max_order + 1,
                                            question_text=question_text.strip(),
                                            competency=competency.strip(),
                                            difficulty=difficulty,
                                            keypoints=keypoints
                                        )
                                        db.add(new_question)
                                        db.flush()

                                    st.success(f"Added question to {template['name']}")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error adding question: {e}")


def render_lens_management() -> None:
    """Render the lens management interface."""
    st.subheader("Lens Management")
    st.write("Lenses define analytical frameworks for evaluating interview transcripts.")

    # Get or create default organization
    with get_db_session() as db:
        org = db.execute(select(Organization)).scalars().first()
        if not org:
            org = Organization(name="Default Organization", settings={})
            db.add(org)
            db.flush()
        org_id = org.id  # Extract ID while in session

    # Import lens prompt builder for examples
    from lens_prompt_builder import get_example_lens_config, validate_lens_config

    # Form to add new lens
    with st.expander("➕ Add New Lens", expanded=False):
        st.write("Create a lens from a template or define custom criteria.")

        with st.form("add_lens_form", clear_on_submit=True):
            name = st.text_input(
                "Lens Name *",
                placeholder="Communication Clarity"
            )
            description = st.text_area(
                "Description",
                placeholder="Assesses how clearly and effectively the candidate explains technical concepts",
                height=80
            )

            col1, col2 = st.columns(2)
            with col1:
                lens_template = st.selectbox(
                    "Use Template",
                    options=["Custom", "Debugging", "Communication", "System Design"],
                    help="Select a predefined lens template or create custom"
                )
            with col2:
                active = st.checkbox("Active", value=True)

            # Configuration section
            st.divider()
            st.write("**Configuration**")

            if lens_template == "Custom":
                st.info("Custom lens creation requires JSON configuration. For now, use a template.")
                config_json = st.text_area(
                    "Configuration JSON",
                    placeholder='{"criteria": [...], "scoring_scale": "0-5"}',
                    height=200,
                    help="Advanced: Paste lens configuration JSON"
                )
            else:
                # Show template preview
                template_map = {
                    "Debugging": "debugging",
                    "Communication": "communication",
                    "System Design": "system_design"
                }
                example_config = get_example_lens_config(template_map[lens_template])

                st.write(f"**Criteria ({len(example_config['criteria'])}):**")
                for criterion in example_config['criteria']:
                    st.write(f"- **{criterion['name']}**: {criterion['definition']}")

                st.caption(f"Scoring Scale: {example_config['scoring_scale']}")

                config_json = None  # Will use example_config

            submit = st.form_submit_button("Create Lens")

            if submit:
                if not name.strip():
                    st.error("Lens name is required")
                else:
                    try:
                        # Determine configuration
                        if lens_template != "Custom":
                            template_map = {
                                "Debugging": "debugging",
                                "Communication": "communication",
                                "System Design": "system_design"
                            }
                            config = get_example_lens_config(template_map[lens_template])
                        else:
                            if not config_json or not config_json.strip():
                                st.error("Configuration JSON is required for custom lenses")
                                config = None
                            else:
                                import json
                                config = json.loads(config_json)

                        if config:
                            # Validate configuration
                            is_valid, error_msg = validate_lens_config(config)
                            if not is_valid:
                                st.error(f"Invalid lens configuration: {error_msg}")
                            else:
                                # Create lens
                                with get_db_session() as db:
                                    new_lens = Lens(
                                        organization_id=org_id,
                                        name=name.strip(),
                                        description=description.strip() if description.strip() else None,
                                        config=config,
                                        active=active,
                                        version=1
                                    )
                                    db.add(new_lens)
                                    db.flush()
                                    # Save name before session closes (object detaches after context exits)
                                    lens_name = new_lens.name

                                st.success(f"Created lens: {lens_name}")
                                st.rerun()

                    except json.JSONDecodeError as e:
                        st.error(f"Invalid JSON: {e}")
                    except Exception as e:
                        st.error(f"Error creating lens: {e}")

    st.divider()

    # Get all lenses and extract data while in session context
    with get_db_session() as db:
        query = select(Lens).order_by(Lens.created_at.desc())
        lens_objs = db.execute(query).scalars().all()

        # Extract data to dicts to avoid DetachedInstanceError
        lenses = [
            {
                'id': l.id,
                'name': l.name,
                'description': l.description,
                'version': l.version,
                'active': l.active,
                'config': dict(l.config) if l.config else {},
                'created_at': l.created_at
            }
            for l in lens_objs
        ]

    if not lenses:
        st.info("No lenses in the system yet. Create your first lens above!")
    else:
        st.write(f"**Total Lenses: {len(lenses)}**")

        # Display lenses
        for lens in lenses:
            status_emoji = "✅" if lens['active'] else "⏸️"
            criteria_count = len(lens['config'].get("criteria", []))
            scoring_scale = lens['config'].get("scoring_scale", "0-5")

            with st.expander(f"{status_emoji} {lens['name']} (v{lens['version']}) - {criteria_count} criteria"):
                # Lens details
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.write(f"**Name:** {lens['name']}")
                    if lens['description']:
                        st.write(f"**Description:** {lens['description']}")
                    st.caption(f"Version: {lens['version']}")
                    st.caption(f"Status: {'Active' if lens['active'] else 'Inactive'}")
                    st.caption(f"Scoring Scale: {scoring_scale}")
                    st.caption(f"Created: {lens['created_at'].strftime('%Y-%m-%d %H:%M')}")

                with col2:
                    # Toggle active status
                    new_active = not lens['active']
                    if st.button(
                        f"Set {'Active' if new_active else 'Inactive'}",
                        key=f"toggle_lens_{lens['id']}",
                        type="secondary"
                    ):
                        try:
                            with get_db_session() as db:
                                db_lens = db.get(Lens, lens['id'])
                                if db_lens:
                                    db_lens.active = new_active
                                    db.flush()
                            st.success(f"Status updated")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error updating status: {e}")

                st.divider()

                # Criteria section
                criteria = lens['config'].get("criteria", [])
                st.write(f"**Criteria ({len(criteria)}):**")

                if criteria:
                    for i, criterion in enumerate(criteria, 1):
                        with st.container():
                            st.write(f"**{i}. {criterion.get('name', 'Unnamed')}**")
                            st.caption(f"Definition: {criterion.get('definition', 'No definition')}")

                            examples = criterion.get('examples', [])
                            if examples:
                                st.caption(f"What to look for: {', '.join(examples)}")
                            st.divider()
                else:
                    st.info("No criteria defined")

                # Show raw config for advanced users
                st.divider()
                st.write("**🔧 Raw Configuration (JSON)**")
                import json
                st.json(lens['config'])


# ==============================================================================
# LIVE SESSIONS (ADMIN CHAT)
# ==============================================================================

def render_live_sessions() -> None:
    """Render the live sessions dashboard for admins to monitor and join sessions."""
    st.subheader("🎧 Live Sessions")

    # Check if we're viewing a specific session
    if st.session_state.admin_viewing_session_id:
        render_admin_session_view()
        return

    # Auto-refresh for live monitoring
    poll_count = st_autorefresh(interval=3000, key="admin_sessions_poll")

    # Get active sessions
    sessions = get_active_sessions_summary()

    if not sessions:
        st.info("No active interview sessions at the moment.")
        st.caption("Sessions will appear here when interviewees start interviews.")
        return

    st.write(f"**{len(sessions)} Active Session{'s' if len(sessions) != 1 else ''}**")

    # Display sessions in a table-like format
    for session in sessions:
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 1, 1])

            with col1:
                st.write(f"**{session['person_name']}**")
                st.caption(f"Session #{session['id']}")

            with col2:
                st.write(session['template_name'])

            with col3:
                st.caption(f"Q {session.get('current_question_index', 0) + 1}")

            with col4:
                if session['hand_raised']:
                    st.markdown("🙋 **HAND**")
                elif session.get('admin_joined'):
                    st.markdown("👨‍💼 Admin")
                else:
                    st.caption("-")

            with col5:
                button_key = f"join_session_{session['id']}"
                if session.get('admin_joined'):
                    if st.button("View", key=button_key, use_container_width=True):
                        st.session_state.admin_viewing_session_id = session['id']
                        st.rerun()
                else:
                    if st.button("Join", key=button_key, use_container_width=True, type="primary" if session['hand_raised'] else "secondary"):
                        if join_session_as_admin(session['id'], "admin"):
                            st.session_state.admin_viewing_session_id = session['id']
                            st.rerun()
                        else:
                            st.error("Failed to join session. Another admin may already be in the session.")

            st.divider()

    # Legend
    with st.expander("Legend"):
        st.write("🙋 **HAND** - Interviewee has raised their hand requesting assistance")
        st.write("👨‍💼 **Admin** - An admin is currently in the session")
        st.write("**Join** - Join the session and pause the interview")
        st.write("**View** - View an active session you're already in")


def render_admin_session_view() -> None:
    """Render the admin view when joined to a session."""
    session_id = st.session_state.admin_viewing_session_id

    # Auto-refresh for messages
    poll_count = st_autorefresh(interval=2000, key="admin_session_poll")

    # Get session info
    from db_models import InterviewSession, Person, InterviewTemplate, TranscriptEntry

    with get_db_session() as db:
        session = db.get(InterviewSession, session_id)
        if not session:
            st.error("Session not found.")
            st.session_state.admin_viewing_session_id = None
            st.rerun()
            return

        person_name = session.person.name if session.person else "Unknown"
        template_name = session.template.name if session.template else "Unknown"
        metadata = session.session_metadata or {}

        # Get transcript
        transcript = db.execute(
            select(TranscriptEntry)
            .where(TranscriptEntry.session_id == session_id)
            .order_by(TranscriptEntry.sequence_index)
        ).scalars().all()

        transcript_list = [
            {
                "speaker": entry.speaker.value,
                "text": entry.text,
                "seq": entry.sequence_index
            }
            for entry in transcript
        ]

    # Back button
    col_back, col_title = st.columns([1, 4])
    with col_back:
        if st.button("← Back to Dashboard", use_container_width=True):
            st.session_state.admin_viewing_session_id = None
            st.rerun()

    with col_title:
        st.write(f"### {person_name} - {template_name}")

    # Status indicator
    if metadata.get("admin_joined"):
        st.success("🔴 LIVE - You are in this session. Interview is paused.")
    else:
        st.warning("Viewing session (not joined)")

    st.divider()

    # Transcript display
    st.write("**Transcript**")

    transcript_container = st.container()
    with transcript_container:
        if not transcript_list:
            st.info("No transcript entries yet.")
        else:
            for entry in transcript_list:
                speaker = entry["speaker"]
                text = entry["text"]

                if speaker == "system":
                    with st.chat_message("assistant", avatar="🤖"):
                        st.write(text)
                elif speaker == "participant":
                    with st.chat_message("user", avatar="👤"):
                        st.write(text)
                elif speaker == "admin":
                    with st.chat_message("assistant", avatar="👨‍💼"):
                        st.info(f"**Admin:** {text}")

    st.divider()

    # Admin message input
    if metadata.get("admin_joined"):
        st.write("**Send Message**")
        admin_message = st.text_input("Message to interviewee:", key="admin_message_input", placeholder="Type your message here...")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📤 Send Message", use_container_width=True, type="primary"):
                if admin_message.strip():
                    if admin_send_message(session_id, admin_message.strip()):
                        st.rerun()
                    else:
                        st.error("Failed to send message.")
                else:
                    st.warning("Please enter a message.")

        st.divider()

        # Admin controls
        st.write("**Session Controls**")
        ctrl_col1, ctrl_col2, ctrl_col3 = st.columns(3)

        with ctrl_col1:
            if st.button("⏭️ Skip Question", use_container_width=True, help="Skip the current question and move to next"):
                if admin_skip_question(session_id):
                    st.success("Question skipped!")
                    st.rerun()
                else:
                    st.error("Failed to skip question.")

        with ctrl_col2:
            if st.button("🛑 End Interview", use_container_width=True, type="secondary", help="End the interview early"):
                if admin_end_interview(session_id):
                    st.success("Interview ended.")
                    st.session_state.admin_viewing_session_id = None
                    st.rerun()
                else:
                    st.error("Failed to end interview.")

        with ctrl_col3:
            if st.button("▶️ Resume & Leave", use_container_width=True, type="primary", help="Resume interview and leave session"):
                if leave_session_as_admin(session_id, resume=True):
                    st.success("Interview resumed!")
                    st.session_state.admin_viewing_session_id = None
                    st.rerun()
                else:
                    st.error("Failed to leave session.")


def check_password() -> bool:
    """
    Check if the user has entered the correct password.

    Returns True if:
    - No password is configured (APP_PASSWORD is empty), or
    - User has entered the correct password

    Returns False if password is required but not yet entered correctly.
    """
    # If no password is configured, allow access
    if not hasattr(settings, 'APP_PASSWORD') or not settings.APP_PASSWORD:
        return True

    # Check if already authenticated in session
    if st.session_state.get("authenticated", False):
        return True

    # Show login form
    st.title("Agentic Interview System")
    st.subheader("Login Required")

    with st.form("login_form"):
        password = st.text_input("Password", type="password", key="password_input")
        submit = st.form_submit_button("Login")

        if submit:
            if password == settings.APP_PASSWORD:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Incorrect password. Please try again.")

    return False


# ==============================================================================
# CHAT INTERVIEW VIEW
# ==============================================================================

def reset_chat_interview_state() -> None:
    """Reset all chat interview session state."""
    st.session_state.chat_messages = []
    st.session_state.chat_interview_phase = "setup"
    st.session_state.chat_session_id = None
    st.session_state.chat_current_question_index = 0
    st.session_state.chat_questions_data = []
    st.session_state.chat_person_data = None
    st.session_state.chat_template_data = None


def add_chat_message(role: str, content: str, msg_type: str = "", metadata: dict = None) -> None:
    """Add a message to the chat history."""
    st.session_state.chat_messages.append({
        "role": role,
        "content": content,
        "type": msg_type,
        "metadata": metadata or {}
    })


def render_chat_message(message: dict) -> None:
    """Render a single chat message using Streamlit's chat_message."""
    role = message.get("role", "assistant")
    content = message.get("content", "")
    msg_type = message.get("type", "")
    metadata = message.get("metadata", {})

    # Map role to Streamlit avatar
    if msg_type == "admin":
        avatar = "👨‍💼"
        display_role = "assistant"  # Streamlit only supports user/assistant
    elif role == "assistant":
        avatar = "🤖"
        display_role = role
    else:
        avatar = "👤"
        display_role = role

    with st.chat_message(display_role, avatar=avatar):
        if msg_type == "evaluation":
            # Color-coded evaluation based on mastery
            mastery = metadata.get("mastery", "mixed")
            score = metadata.get("score", 0)

            # Show score prominently
            score_text = f"**Score: {score}/100**"
            if mastery == "strong":
                st.success(f"{score_text} - {content}")
            elif mastery == "mixed":
                st.warning(f"{score_text} - {content}")
            else:
                st.error(f"{score_text} - {content}")

            # Show keypoint coverage if available
            keypoints = metadata.get("keypoints_coverage", [])
            if keypoints:
                with st.expander("Keypoint Coverage"):
                    for kp in keypoints:
                        icon = "✅" if kp.get("covered") else "❌"
                        st.write(f"{icon} {kp.get('keypoint', '')}")

            # Show follow-up suggestion if available
            followup = metadata.get("suggested_followup")
            if followup:
                st.info(f"💡 **Follow-up:** {followup}")

        elif msg_type == "question":
            # Question with metadata badges
            q_idx = metadata.get("question_index", 0)
            competency = metadata.get("competency", "")
            difficulty = metadata.get("difficulty", "")

            # Header with badges
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.markdown(f"**Question {q_idx + 1}**")
            with col2:
                st.caption(f"📚 {competency}")
            with col3:
                st.caption(f"⚡ {difficulty}")

            st.markdown(content)

        elif msg_type == "summary":
            # Summary with formatted stats
            st.markdown(content)

        elif msg_type == "admin":
            # Admin message with distinct styling
            st.info(f"**Admin:** {content}")

        elif msg_type == "paused":
            # Interview paused notification
            st.warning(content)

        else:
            # Default message rendering
            st.markdown(content)


def render_chat_progress_indicator() -> None:
    """Show progress indicator for chat interview."""
    current = st.session_state.chat_current_question_index
    total = len(st.session_state.chat_questions_data)

    if total > 0:
        progress = min(current / total, 1.0)
        col1, col2 = st.columns([4, 1])
        with col1:
            st.progress(progress)
        with col2:
            st.caption(f"Q {min(current + 1, total)}/{total}")


def handle_chat_setup_phase() -> None:
    """Handle the setup phase of chat interview with conversational selection."""
    from db_models import Person, InterviewTemplate, TemplateQuestion, PersonStatus

    # Initialize welcome message if chat is empty
    if not st.session_state.chat_messages:
        add_chat_message(
            "assistant",
            "Welcome to the Interview! 👋 I'll guide you through the process. Let's get started.",
            "welcome"
        )

    # Check what step we're at in setup
    person_selected = st.session_state.chat_person_data is not None
    template_selected = st.session_state.chat_template_data is not None

    if not person_selected:
        # Need to select person
        # Show prompt if not already shown
        last_msg = st.session_state.chat_messages[-1] if st.session_state.chat_messages else {}
        if last_msg.get("type") != "person_prompt":
            add_chat_message(
                "assistant",
                "Who will be taking this interview today?",
                "person_prompt"
            )
            st.rerun()

        # Show person selection buttons
        with get_db_session() as db:
            people = db.execute(
                select(Person).where(Person.status == PersonStatus.ACTIVE).order_by(Person.name)
            ).scalars().all()
            people_data = [(p.id, p.name, p.role, p.department) for p in people]

        if not people_data:
            st.warning("No active people found. Please add people in Admin view first.")
            if st.button("Go to Admin"):
                st.session_state.chat_interview_phase = "setup"
                reset_chat_interview_state()
            return

        st.write("**Select participant:**")
        cols = st.columns(min(len(people_data), 3))
        for i, (pid, name, role, dept) in enumerate(people_data):
            with cols[i % 3]:
                if st.button(f"👤 {name}", key=f"person_{pid}", use_container_width=True):
                    st.session_state.chat_person_data = {
                        "id": pid, "name": name, "role": role, "department": dept
                    }
                    add_chat_message("user", f"I'm {name}", "person_selection")
                    st.rerun()

    elif not template_selected:
        # Need to select template
        # Show prompt if not already shown
        last_msg = st.session_state.chat_messages[-1] if st.session_state.chat_messages else {}
        if last_msg.get("type") != "template_prompt":
            person_name = st.session_state.chat_person_data["name"]
            add_chat_message(
                "assistant",
                f"Great to meet you, {person_name}! Which interview template would you like to use?",
                "template_prompt"
            )
            st.rerun()

        # Show template selection
        with get_db_session() as db:
            templates = db.execute(
                select(InterviewTemplate).where(InterviewTemplate.active == True).order_by(InterviewTemplate.name)
            ).scalars().all()
            templates_data = []
            for t in templates:
                question_count = db.execute(
                    select(func.count()).where(TemplateQuestion.template_id == t.id)
                ).scalar()
                templates_data.append({
                    "id": t.id,
                    "name": t.name,
                    "description": t.description,
                    "version": t.version,
                    "question_count": question_count
                })

        if not templates_data:
            st.warning("No active templates found. Please create templates in Admin view first.")
            if st.button("Go to Admin"):
                reset_chat_interview_state()
            return

        st.write("**Select template:**")
        for t in templates_data:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{t['name']}** (v{t['version']})")
                if t['description']:
                    st.caption(t['description'])
            with col2:
                if st.button(f"Select ({t['question_count']} Q)", key=f"template_{t['id']}"):
                    st.session_state.chat_template_data = t
                    add_chat_message("user", f"I'll take the {t['name']} interview", "template_selection")
                    st.rerun()

    else:
        # Both selected - show confirmation
        last_msg = st.session_state.chat_messages[-1] if st.session_state.chat_messages else {}
        if last_msg.get("type") != "confirmation":
            person = st.session_state.chat_person_data
            template = st.session_state.chat_template_data
            add_chat_message(
                "assistant",
                f"Perfect! Ready to begin **{template['name']}** with {template['question_count']} questions.",
                "confirmation"
            )
            st.rerun()

        # Show start button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Start Interview", use_container_width=True, type="primary"):
                start_chat_interview()


def start_chat_interview() -> None:
    """Initialize the chat interview session and load questions."""
    from db_models import InterviewSession, InterviewTemplate, TemplateQuestion, SessionStatus

    person = st.session_state.chat_person_data
    template = st.session_state.chat_template_data

    # Create session in database
    with get_db_session() as db:
        # Get organization ID (use person's org or default to 1)
        org_id = 1  # Default org

        session = InterviewSession(
            person_id=person["id"],
            template_id=template["id"],
            organization_id=org_id,
            status=SessionStatus.IN_PROGRESS
        )
        db.add(session)
        db.flush()
        session_id = session.id

        # Load questions for the template
        questions = db.execute(
            select(TemplateQuestion)
            .where(TemplateQuestion.template_id == template["id"])
            .order_by(TemplateQuestion.order_index)
        ).scalars().all()

        questions_data = [{
            "id": q.id,
            "question_text": q.question_text,
            "competency": q.competency,
            "difficulty": q.difficulty,
            "keypoints": q.keypoints or []
        } for q in questions]

    # Store in session state
    st.session_state.chat_session_id = session_id
    st.session_state.chat_questions_data = questions_data
    st.session_state.chat_current_question_index = 0
    st.session_state.chat_interview_phase = "active"

    # Add first question
    if questions_data:
        q = questions_data[0]
        add_chat_message(
            "assistant",
            q["question_text"],
            "question",
            {
                "question_index": 0,
                "competency": q["competency"],
                "difficulty": q["difficulty"]
            }
        )

    st.rerun()


def handle_chat_active_phase() -> None:
    """Handle the active interview phase with chat input."""
    questions = st.session_state.chat_questions_data
    current_idx = st.session_state.chat_current_question_index

    if current_idx >= len(questions):
        # All questions answered - move to complete phase
        complete_chat_interview()
        return

    session_id = st.session_state.chat_session_id
    is_paused = st.session_state.chat_interview_paused

    # Paused banner when admin is present
    if is_paused:
        st.warning("⏸️ **Interview Paused** - An administrator is reviewing your session. Please wait for instructions.")

    # Chat input for answer (disabled when paused)
    if not is_paused:
        if prompt := st.chat_input("Type your answer here...", key="chat_answer_input"):
            if prompt.strip():
                # Add user's answer to chat
                add_chat_message("user", prompt.strip(), "answer")

                # Process the answer
                process_chat_answer(prompt.strip())
    else:
        # Show disabled input message
        st.chat_input("Chat paused - waiting for administrator...", key="chat_paused_input", disabled=True)

    # Raise/Lower Hand buttons
    st.divider()
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        if st.session_state.chat_hand_raised:
            st.info("🙋 Hand raised - waiting for administrator to join...")
        elif is_paused:
            st.info("👨‍💼 Administrator is in the session")

    with col2:
        if not st.session_state.chat_hand_raised and not is_paused:
            if st.button("🙋 Raise Hand", use_container_width=True, help="Request administrator assistance"):
                if raise_hand(session_id):
                    st.session_state.chat_hand_raised = True
                    add_chat_message(
                        "assistant",
                        "🙋 You've raised your hand. An administrator will join shortly.",
                        "paused"
                    )
                    st.rerun()
                else:
                    st.error("Failed to raise hand. Please try again.")

    with col3:
        if st.session_state.chat_hand_raised and not is_paused:
            if st.button("✋ Lower Hand", use_container_width=True, help="Cancel assistance request"):
                if lower_hand(session_id):
                    st.session_state.chat_hand_raised = False
                    add_chat_message(
                        "assistant",
                        "✋ You've lowered your hand. Assistance request cancelled.",
                        "paused"
                    )
                    st.rerun()
                else:
                    st.error("Failed to lower hand. Please try again.")


def process_chat_answer(answer: str) -> None:
    """Process the user's answer: evaluate, store, and advance."""
    from db_models import TranscriptEntry, QuestionEvaluation, SpeakerType, MasteryLabel, EvaluatorType

    questions = st.session_state.chat_questions_data
    current_idx = st.session_state.chat_current_question_index
    session_id = st.session_state.chat_session_id

    if current_idx >= len(questions):
        return

    current_question = questions[current_idx]

    # Get evaluator
    evaluator = get_evaluator_agent()

    # Convert to Question object for evaluation
    question_obj = Question(
        id=current_question["id"],
        text=current_question["question_text"],
        competency=current_question["competency"],
        difficulty=current_question["difficulty"],
        keypoints=current_question["keypoints"]
    )

    # Evaluate with loading indicator
    eval_mode = st.session_state.get('evaluator_mode', 'Heuristic')
    spinner_msg = "🤖 AI is evaluating your answer..." if eval_mode == "LLM-Powered" else "Evaluating answer..."

    # Note: We can't use spinner inside chat flow easily, evaluation happens synchronously
    evaluation = evaluator.evaluate(question_obj, answer)

    # Store in database
    with get_db_session() as db:
        # Get max sequence index
        max_seq = db.execute(
            select(func.max(TranscriptEntry.sequence_index)).where(
                TranscriptEntry.session_id == session_id
            )
        ).scalar() or -1

        # Store question as SYSTEM transcript entry
        db.add(TranscriptEntry(
            session_id=session_id,
            sequence_index=max_seq + 1,
            speaker=SpeakerType.SYSTEM,
            text=current_question["question_text"]
        ))

        # Store answer as PARTICIPANT transcript entry
        db.add(TranscriptEntry(
            session_id=session_id,
            sequence_index=max_seq + 2,
            speaker=SpeakerType.PARTICIPANT,
            text=answer
        ))

        # Store evaluation
        mastery_map = {"strong": MasteryLabel.STRONG, "mixed": MasteryLabel.MIXED, "weak": MasteryLabel.WEAK}

        db.add(QuestionEvaluation(
            session_id=session_id,
            template_question_id=current_question["id"],
            evaluator_type=EvaluatorType.HEURISTIC if eval_mode == "Heuristic" else EvaluatorType.LLM,
            score_0_100=evaluation.score_0_100,
            mastery_label=mastery_map[evaluation.mastery_label],
            raw_answer=answer,
            short_feedback=evaluation.short_feedback,
            keypoints_coverage=[
                {"keypoint": kp.keypoint, "covered": kp.covered, "evidence": kp.evidence}
                for kp in evaluation.keypoints_coverage
            ],
            suggested_followup=evaluation.suggested_followup
        ))

        db.flush()

    # Add evaluation message to chat
    add_chat_message(
        "assistant",
        evaluation.short_feedback,
        "evaluation",
        {
            "score": evaluation.score_0_100,
            "mastery": evaluation.mastery_label,
            "keypoints_coverage": [
                {"keypoint": kp.keypoint, "covered": kp.covered}
                for kp in evaluation.keypoints_coverage
            ],
            "suggested_followup": evaluation.suggested_followup
        }
    )

    # Advance to next question
    st.session_state.chat_current_question_index += 1
    next_idx = st.session_state.chat_current_question_index

    if next_idx < len(questions):
        # Add next question
        q = questions[next_idx]
        add_chat_message(
            "assistant",
            q["question_text"],
            "question",
            {
                "question_index": next_idx,
                "competency": q["competency"],
                "difficulty": q["difficulty"]
            }
        )
    else:
        # All questions done - complete interview
        complete_chat_interview()

    st.rerun()


def complete_chat_interview() -> None:
    """Complete the chat interview and show summary."""
    from db_models import InterviewSession, QuestionEvaluation, SessionStatus

    session_id = st.session_state.chat_session_id
    st.session_state.chat_interview_phase = "complete"

    # Update session status and calculate summary
    with get_db_session() as db:
        session = db.get(InterviewSession, session_id)
        if session:
            session.status = SessionStatus.COMPLETED

            # Get evaluations for summary
            evaluations = db.execute(
                select(QuestionEvaluation).where(QuestionEvaluation.session_id == session_id)
            ).scalars().all()

            if evaluations:
                scores = [e.score_0_100 for e in evaluations]
                avg_score = sum(scores) / len(scores)
                strong_count = sum(1 for e in evaluations if e.mastery_label.value == "strong")
                weak_count = sum(1 for e in evaluations if e.mastery_label.value == "weak")

                summary = f"""
## 🎉 Interview Complete!

**Summary for {st.session_state.chat_person_data['name']}**

- **Template:** {st.session_state.chat_template_data['name']}
- **Questions:** {len(evaluations)}
- **Average Score:** {avg_score:.1f}/100
- **Strong Answers:** {strong_count}
- **Weak Answers:** {weak_count}

{'Great job! 🌟' if avg_score >= 80 else 'Good effort! Keep practicing.' if avg_score >= 50 else 'Room for improvement. Review the feedback above.'}
"""
                session.summary = summary
            else:
                summary = "## 🎉 Interview Complete!\n\nNo evaluations recorded."

            db.flush()

    # Add summary message
    add_chat_message("assistant", summary, "summary")
    st.rerun()


def handle_chat_complete_phase() -> None:
    """Handle the completion phase with action buttons."""
    # Action buttons
    st.divider()
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔄 Start New Interview", use_container_width=True):
            reset_chat_interview_state()
            st.rerun()

    with col2:
        if st.button("📊 View Reports", use_container_width=True):
            # This will need user to manually navigate
            st.info("Navigate to Reports view to see detailed session history")

    with col3:
        if st.button("🏠 Go Home", use_container_width=True):
            reset_chat_interview_state()
            st.rerun()


def render_chat_interview_view() -> None:
    """Main entry point for the chat interview view."""
    if not DATABASE_AVAILABLE:
        st.error("Chat Interview requires database features. Please ensure database is properly configured.")
        return

    st.header("💬 Chat Interview")

    # Polling during active phase - check for admin presence and new messages
    if st.session_state.chat_interview_phase == "active" and st.session_state.chat_session_id:
        # Auto-refresh every 3 seconds
        poll_count = st_autorefresh(interval=3000, key="chat_poll")

        # Poll for changes when count increases
        if poll_count > st.session_state.chat_last_poll_count:
            st.session_state.chat_last_poll_count = poll_count
            session_id = st.session_state.chat_session_id

            # Check for status changes and new messages
            state_changed = poll_session_status(session_id)

            if state_changed:
                # Check if admin joined/left
                metadata = get_session_metadata(session_id)
                admin_present = metadata.get("admin_joined", False)

                if admin_present and not st.session_state.chat_admin_present:
                    # Admin just joined
                    st.session_state.chat_admin_present = True
                    st.session_state.chat_interview_paused = True
                    add_chat_message(
                        "assistant",
                        "⏸️ Interview paused - An administrator has joined the session.",
                        "paused"
                    )
                elif not admin_present and st.session_state.chat_admin_present:
                    # Admin just left
                    st.session_state.chat_admin_present = False
                    st.session_state.chat_interview_paused = False
                    add_chat_message(
                        "assistant",
                        "▶️ Interview resumed - Administrator has left the session.",
                        "paused"
                    )

                # Fetch any new admin messages
                new_entries = get_transcript_since(session_id, st.session_state.chat_last_transcript_seq)
                for entry in new_entries:
                    if entry["speaker"] == "admin":
                        add_chat_message("assistant", entry["text"], "admin")
                    st.session_state.chat_last_transcript_seq = entry["sequence_index"]

                st.rerun()

    # Progress indicator (only during active phase)
    if st.session_state.chat_interview_phase == "active":
        render_chat_progress_indicator()
        st.divider()

    # Display all chat messages
    for message in st.session_state.chat_messages:
        render_chat_message(message)

    # Phase-specific handling
    if st.session_state.chat_interview_phase == "setup":
        handle_chat_setup_phase()
    elif st.session_state.chat_interview_phase == "active":
        handle_chat_active_phase()
    elif st.session_state.chat_interview_phase == "complete":
        handle_chat_complete_phase()


def main() -> None:
    """Main application entry point."""
    # Check authentication first
    if not check_password():
        return

    st.title("Agentic Interview System")

    # Add logout button if password is configured
    if LLM_AVAILABLE and hasattr(settings, 'APP_PASSWORD') and settings.APP_PASSWORD:
        if st.sidebar.button("Logout"):
            st.session_state.authenticated = False
            st.rerun()

    # Initialize session state
    initialize_session_state()

    # Sidebar: Evaluator Configuration
    st.sidebar.title("⚙️ Configuration")

    if LLM_AVAILABLE:
        evaluator_mode = st.sidebar.radio(
            "Evaluation Method",
            options=["Heuristic", "LLM-Powered"],
            index=0 if st.session_state.evaluator_mode == "Heuristic" else 1,
            help="""
            **Heuristic**: Simple keyword matching
            - ✓ Fast, instant results
            - ✓ No API costs
            - ✓ Works offline
            - ✗ Limited semantic understanding

            **LLM-Powered**: AI semantic analysis
            - ✓ Understands context and nuance
            - ✓ Richer, detailed feedback
            - ✗ Requires API key
            - ✗ Costs money per evaluation
            """
        )

        # Update session state if changed
        if evaluator_mode != st.session_state.evaluator_mode:
            st.session_state.evaluator_mode = evaluator_mode
            st.rerun()

        # Show evaluator status
        st.sidebar.divider()
        st.sidebar.subheader("Current Status")

        if evaluator_mode == "Heuristic":
            st.sidebar.info("✓ Using: **Heuristic** (keyword matching)")
        else:
            # Check if LLM is properly configured
            is_valid, error_msg = settings.validate_llm_config()
            if is_valid:
                st.sidebar.success(f"✓ Using: **LLM** ({settings.LLM_MODEL})")
                st.sidebar.caption(f"Provider: {settings.LLM_PROVIDER}")
                st.sidebar.caption(f"Temperature: {settings.LLM_TEMPERATURE}")
            else:
                st.sidebar.warning("⚠️ LLM not configured")
                st.sidebar.caption("Falling back to heuristic")
                with st.sidebar.expander("📝 Setup Instructions"):
                    st.markdown("""
                    1. Copy `.env.example` to `.env`
                    2. Add your API key:
                       - OpenAI: https://platform.openai.com/api-keys
                       - Anthropic: https://console.anthropic.com/settings/keys
                    3. Restart the app
                    """)
    else:
        st.sidebar.info("Using: **Heuristic** (keyword matching)")
        st.sidebar.caption("LLM features not available")
        with st.sidebar.expander("📦 Install LLM Support"):
            st.code("pip install -r requirements.txt", language="bash")

    st.sidebar.divider()

    # Sidebar: Navigation
    st.sidebar.title("Navigation")

    # Show Admin and Reports options only if database is available
    nav_options = ["Interviewer", "Interviewee"]
    if DATABASE_AVAILABLE:
        nav_options.insert(2, "Chat Interview")  # Add after Interviewee
        nav_options.extend(["Reports", "Admin"])

    view = st.sidebar.radio(
        "Select View",
        options=nav_options,
        help="Switch between creating questions, taking interviews, viewing reports, or managing data"
    )

    # Render selected view
    if view == "Interviewer":
        render_interviewer_view()
    elif view == "Interviewee":
        render_interviewee_view()
    elif view == "Chat Interview":
        render_chat_interview_view()
    elif view == "Reports":
        render_reports_view()
    elif view == "Admin":
        render_admin_view()


if __name__ == "__main__":
    main()
