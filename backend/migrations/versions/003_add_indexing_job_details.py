"""003_add_indexing_job_details

Enriches ``indexing_jobs`` so a job links to the document it produced and is
self-describing in the admin UI: adds ``document_id`` (FK -> documents),
``chunk_count``, and ``original_filename``.

Revision ID: 003_add_indexing_job_details
Revises: 002_add_missing_tables
Create Date: 2026-08-25 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '003_add_indexing_job_details'
down_revision = '002_add_missing_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'indexing_jobs',
        sa.Column(
            'document_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('documents.id', ondelete='SET NULL'),
            nullable=True,
        ),
    )
    op.add_column(
        'indexing_jobs',
        sa.Column('chunk_count', sa.Integer(), nullable=False, server_default='0'),
    )
    op.add_column(
        'indexing_jobs',
        sa.Column('original_filename', sa.String(255), nullable=True),
    )
    op.create_index(
        'ix_indexing_jobs_document_id', 'indexing_jobs', ['document_id']
    )


def downgrade() -> None:
    op.drop_index('ix_indexing_jobs_document_id', table_name='indexing_jobs')
    op.drop_column('indexing_jobs', 'original_filename')
    op.drop_column('indexing_jobs', 'chunk_count')
    op.drop_column('indexing_jobs', 'document_id')
