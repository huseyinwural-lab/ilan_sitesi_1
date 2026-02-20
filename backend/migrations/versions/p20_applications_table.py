"""
P20: Applications table
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'p20_applications_table'
down_revision: Union[str, Sequence[str], None] = 'p19_feature_flag_config'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'applications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('application_type', sa.String(length=20), nullable=False),
        sa.Column('request_type', sa.String(length=20), nullable=False, server_default='complaint'),
        sa.Column('subject', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('attachment_name', sa.String(length=255), nullable=True),
        sa.Column('attachment_url', sa.String(length=1024), nullable=True),
        sa.Column('priority', sa.String(length=20), nullable=False, server_default='medium'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='open'),
        sa.Column('assigned_admin_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['assigned_admin_id'], ['users.id']),
    )
    op.create_index('ix_applications_user_id', 'applications', ['user_id'])
    op.create_index('ix_applications_application_type', 'applications', ['application_type'])
    op.create_index('ix_applications_status', 'applications', ['status'])


def downgrade() -> None:
    op.drop_index('ix_applications_status', table_name='applications')
    op.drop_index('ix_applications_application_type', table_name='applications')
    op.drop_index('ix_applications_user_id', table_name='applications')
    op.drop_table('applications')
