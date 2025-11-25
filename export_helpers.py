"""
Export helpers for generating CSV and JSON exports of interview data.

This module provides functions to:
- Export filtered session lists as CSV
- Export individual session details as JSON
"""

import json
import csv
from io import StringIO
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from db_models import InterviewSession, Person, InterviewTemplate


def export_sessions_csv(sessions: List[Dict[str, Any]]) -> str:
    """
    Export a list of session summaries as CSV.

    Args:
        sessions: List of session dict summaries (from reports view)

    Returns:
        CSV string ready for download
    """
    output = StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Session ID",
        "Person Name",
        "Role",
        "Department",
        "Template",
        "Status",
        "Started",
        "Completed",
        "Evaluator Type",
        "Avg Score",
        "Question Count",
        "Lens Analyses"
    ])

    # Rows
    for session in sessions:
        writer.writerow([
            session.get('id', ''),
            session.get('person_name', ''),
            session.get('role', ''),
            session.get('department', ''),
            session.get('template_name', ''),
            session.get('status', ''),
            session.get('started_at', ''),
            session.get('completed_at', ''),
            session.get('evaluator_type', ''),
            f"{session.get('avg_score', 0):.1f}" if session.get('avg_score') else '',
            session.get('question_count', 0),
            session.get('lens_count', 0)
        ])

    return output.getvalue()


def export_session_json(db: Session, session_id: int) -> str:
    """
    Export complete session data as JSON.

    Args:
        db: Database session
        session_id: ID of the InterviewSession to export

    Returns:
        JSON string with complete session data
    """
    from db_models import QuestionEvaluation, TranscriptEntry, LensResult, LensCriterionResult

    # Fetch session
    session = db.get(InterviewSession, session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    # Build complete data structure
    data = {
        "export_metadata": {
            "exported_at": datetime.now().isoformat(),
            "export_version": "1.0"
        },
        "session": {
            "id": session.id,
            "status": session.status.value,
            "evaluator_type": session.evaluator_type.value,
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            "summary": session.summary
        },
        "person": {
            "id": session.person.id,
            "name": session.person.name,
            "email": session.person.email,
            "role": session.person.role,
            "department": session.person.department,
            "tags": session.person.tags or []
        },
        "template": {
            "id": session.template.id,
            "name": session.template.name,
            "version": session.template.version,
            "description": session.template.description
        },
        "transcript": [
            {
                "sequence": t.sequence_index,
                "speaker": t.speaker.value,
                "text": t.text,
                "timestamp": t.created_at.isoformat() if t.created_at else None
            }
            for t in sorted(session.transcript, key=lambda x: x.sequence_index)
        ],
        "evaluations": [
            {
                "question_id": e.template_question_id,
                "question_text": e.template_question.question_text if e.template_question else None,
                "competency": e.template_question.competency if e.template_question else None,
                "difficulty": e.template_question.difficulty if e.template_question else None,
                "keypoints": e.template_question.keypoints if e.template_question else [],
                "raw_answer": e.raw_answer,
                "score": e.score_0_100,
                "mastery_label": e.mastery_label.value,
                "short_feedback": e.short_feedback,
                "keypoints_coverage": e.keypoints_coverage or [],
                "suggested_followup": e.suggested_followup,
                "evaluator_type": e.evaluator_type.value,
                "created_at": e.created_at.isoformat() if e.created_at else None
            }
            for e in sorted(session.evaluations, key=lambda x: x.created_at or datetime.min)
        ],
        "lens_results": [
            {
                "lens_id": lr.lens_id,
                "lens_name": lr.lens.name if lr.lens else None,
                "lens_description": lr.lens.description if lr.lens else None,
                "status": lr.status.value,
                "llm_provider": lr.llm_provider,
                "llm_model": lr.llm_model,
                "created_at": lr.created_at.isoformat() if lr.created_at else None,
                "completed_at": lr.completed_at.isoformat() if lr.completed_at else None,
                "error_message": lr.error_message,
                "criteria": [
                    {
                        "criterion_name": cr.criterion_name,
                        "score": cr.score,
                        "scale": cr.scale,
                        "flags": cr.flags or [],
                        "extracted_items": cr.extracted_items or [],
                        "supporting_quotes": cr.supporting_quotes or [],
                        "notes": cr.notes
                    }
                    for cr in lr.criterion_results
                ]
            }
            for lr in session.lens_results
        ]
    }

    return json.dumps(data, indent=2, ensure_ascii=False)
