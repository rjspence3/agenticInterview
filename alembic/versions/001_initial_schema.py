"""Initial schema - Organizations, People, Templates, Sessions

Revision ID: 001_initial
Revises:
Create Date: 2025-11-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create organizations table
    op.create_table(
        'organizations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('settings', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organizations_id'), 'organizations', ['id'], unique=False)
    op.create_index(op.f('ix_organizations_name'), 'organizations', ['name'], unique=False)

    # Create people table
    op.create_table(
        'people',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('role', sa.String(255), nullable=True),
        sa.Column('department', sa.String(255), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('status', sa.Enum('active', 'inactive', name='personstatus'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_people_id'), 'people', ['id'], unique=False)
    op.create_index(op.f('ix_people_name'), 'people', ['name'], unique=False)
    op.create_index(op.f('ix_people_email'), 'people', ['email'], unique=False)
    op.create_index(op.f('ix_people_department'), 'people', ['department'], unique=False)
    op.create_index(op.f('ix_people_status'), 'people', ['status'], unique=False)

    # Create interview_templates table
    op.create_table(
        'interview_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_interview_templates_id'), 'interview_templates', ['id'], unique=False)
    op.create_index(op.f('ix_interview_templates_name'), 'interview_templates', ['name'], unique=False)
    op.create_index(op.f('ix_interview_templates_active'), 'interview_templates', ['active'], unique=False)

    # Create template_questions table
    op.create_table(
        'template_questions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('competency', sa.String(255), nullable=False),
        sa.Column('difficulty', sa.String(50), nullable=False),
        sa.Column('keypoints', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['template_id'], ['interview_templates.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_template_questions_id'), 'template_questions', ['id'], unique=False)
    op.create_index(op.f('ix_template_questions_competency'), 'template_questions', ['competency'], unique=False)

    # Create interview_sessions table
    op.create_table(
        'interview_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=False),
        sa.Column('person_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('scheduled', 'in_progress', 'completed', 'cancelled', name='sessionstatus'), nullable=True),
        sa.Column('evaluator_type', sa.Enum('heuristic', 'llm', name='evaluatortype'), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('session_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['person_id'], ['people.id'], ),
        sa.ForeignKeyConstraint(['template_id'], ['interview_templates.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_interview_sessions_id'), 'interview_sessions', ['id'], unique=False)
    op.create_index(op.f('ix_interview_sessions_status'), 'interview_sessions', ['status'], unique=False)

    # Create transcript_entries table
    op.create_table(
        'transcript_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('sequence_index', sa.Integer(), nullable=False),
        sa.Column('speaker', sa.Enum('system', 'participant', name='speakertype'), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['interview_sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_transcript_entries_id'), 'transcript_entries', ['id'], unique=False)

    # Create question_evaluations table
    op.create_table(
        'question_evaluations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('template_question_id', sa.Integer(), nullable=False),
        sa.Column('evaluator_type', sa.Enum('heuristic', 'llm', name='evaluatortype'), nullable=False),
        sa.Column('score_0_100', sa.Integer(), nullable=False),
        sa.Column('mastery_label', sa.Enum('strong', 'mixed', 'weak', name='masterylabel'), nullable=False),
        sa.Column('raw_answer', sa.Text(), nullable=False),
        sa.Column('short_feedback', sa.Text(), nullable=False),
        sa.Column('keypoints_coverage', sa.JSON(), nullable=False),
        sa.Column('suggested_followup', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['interview_sessions.id'], ),
        sa.ForeignKeyConstraint(['template_question_id'], ['template_questions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_question_evaluations_id'), 'question_evaluations', ['id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f('ix_question_evaluations_id'), table_name='question_evaluations')
    op.drop_table('question_evaluations')

    op.drop_index(op.f('ix_transcript_entries_id'), table_name='transcript_entries')
    op.drop_table('transcript_entries')

    op.drop_index(op.f('ix_interview_sessions_status'), table_name='interview_sessions')
    op.drop_index(op.f('ix_interview_sessions_id'), table_name='interview_sessions')
    op.drop_table('interview_sessions')

    op.drop_index(op.f('ix_template_questions_competency'), table_name='template_questions')
    op.drop_index(op.f('ix_template_questions_id'), table_name='template_questions')
    op.drop_table('template_questions')

    op.drop_index(op.f('ix_interview_templates_active'), table_name='interview_templates')
    op.drop_index(op.f('ix_interview_templates_name'), table_name='interview_templates')
    op.drop_index(op.f('ix_interview_templates_id'), table_name='interview_templates')
    op.drop_table('interview_templates')

    op.drop_index(op.f('ix_people_status'), table_name='people')
    op.drop_index(op.f('ix_people_department'), table_name='people')
    op.drop_index(op.f('ix_people_email'), table_name='people')
    op.drop_index(op.f('ix_people_name'), table_name='people')
    op.drop_index(op.f('ix_people_id'), table_name='people')
    op.drop_table('people')

    op.drop_index(op.f('ix_organizations_name'), table_name='organizations')
    op.drop_index(op.f('ix_organizations_id'), table_name='organizations')
    op.drop_table('organizations')
