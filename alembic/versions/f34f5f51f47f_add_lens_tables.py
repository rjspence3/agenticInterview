"""add_lens_tables

Revision ID: f34f5f51f47f
Revises: 001_initial
Create Date: 2025-11-25 11:40:49.336031

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f34f5f51f47f'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create lenses table
    op.create_table(
        'lenses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('config', sa.JSON(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_lenses_id'), 'lenses', ['id'], unique=False)
    op.create_index(op.f('ix_lenses_name'), 'lenses', ['name'], unique=False)
    op.create_index(op.f('ix_lenses_active'), 'lenses', ['active'], unique=False)

    # Create lens_results table
    op.create_table(
        'lens_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('lens_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('pending', 'in_progress', 'completed', 'failed', name='lensresultstatus'), nullable=True),
        sa.Column('llm_provider', sa.String(50), nullable=True),
        sa.Column('llm_model', sa.String(100), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['interview_sessions.id'], ),
        sa.ForeignKeyConstraint(['lens_id'], ['lenses.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_lens_results_id'), 'lens_results', ['id'], unique=False)
    op.create_index(op.f('ix_lens_results_status'), 'lens_results', ['status'], unique=False)

    # Create lens_criterion_results table
    op.create_table(
        'lens_criterion_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lens_result_id', sa.Integer(), nullable=False),
        sa.Column('criterion_name', sa.String(255), nullable=False),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('scale', sa.String(50), nullable=True),
        sa.Column('flags', sa.JSON(), nullable=True),
        sa.Column('extracted_items', sa.JSON(), nullable=True),
        sa.Column('supporting_quotes', sa.JSON(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['lens_result_id'], ['lens_results.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_lens_criterion_results_id'), 'lens_criterion_results', ['id'], unique=False)
    op.create_index(op.f('ix_lens_criterion_results_criterion_name'), 'lens_criterion_results', ['criterion_name'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f('ix_lens_criterion_results_criterion_name'), table_name='lens_criterion_results')
    op.drop_index(op.f('ix_lens_criterion_results_id'), table_name='lens_criterion_results')
    op.drop_table('lens_criterion_results')

    op.drop_index(op.f('ix_lens_results_status'), table_name='lens_results')
    op.drop_index(op.f('ix_lens_results_id'), table_name='lens_results')
    op.drop_table('lens_results')

    op.drop_index(op.f('ix_lenses_active'), table_name='lenses')
    op.drop_index(op.f('ix_lenses_name'), table_name='lenses')
    op.drop_index(op.f('ix_lenses_id'), table_name='lenses')
    op.drop_table('lenses')
