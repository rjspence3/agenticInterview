"""add_performance_indexes

Revision ID: 002_performance_indexes
Revises: f34f5f51f47f
Create Date: 2025-11-26

Add indexes on frequently queried columns for performance optimization:
- interview_sessions: person_id, template_id, organization_id+status
- transcript_entries: session_id+sequence_index
- question_evaluations: session_id
- lens_results: session_id (composite)
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '002_performance_indexes'
down_revision: Union[str, None] = 'f34f5f51f47f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # InterviewSession indexes
    op.create_index(
        'ix_interview_sessions_person_id',
        'interview_sessions',
        ['person_id'],
        unique=False
    )
    op.create_index(
        'ix_interview_sessions_template_id',
        'interview_sessions',
        ['template_id'],
        unique=False
    )
    op.create_index(
        'ix_interview_sessions_org_status',
        'interview_sessions',
        ['organization_id', 'status'],
        unique=False
    )

    # TranscriptEntry index for ordered queries
    op.create_index(
        'ix_transcript_entries_session_seq',
        'transcript_entries',
        ['session_id', 'sequence_index'],
        unique=False
    )

    # QuestionEvaluation index
    op.create_index(
        'ix_question_evaluations_session_id',
        'question_evaluations',
        ['session_id'],
        unique=False
    )

    # LensResult composite index for session queries
    op.create_index(
        'ix_lens_results_session_id',
        'lens_results',
        ['session_id'],
        unique=False
    )


def downgrade() -> None:
    # Drop indexes in reverse order
    op.drop_index('ix_lens_results_session_id', table_name='lens_results')
    op.drop_index('ix_question_evaluations_session_id', table_name='question_evaluations')
    op.drop_index('ix_transcript_entries_session_seq', table_name='transcript_entries')
    op.drop_index('ix_interview_sessions_org_status', table_name='interview_sessions')
    op.drop_index('ix_interview_sessions_template_id', table_name='interview_sessions')
    op.drop_index('ix_interview_sessions_person_id', table_name='interview_sessions')
