"""
P37: create moderation_queue table + indexes
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'p37_moderation_queue'
down_revision: Union[str, Sequence[str], None] = 'p36_listings_search_index'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'moderation_queue' in inspector.get_table_names():
        return

    op.create_table(
        'moderation_queue',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('listing_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('moderator_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text("timezone('utc', now())")),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text("timezone('utc', now())")),
        sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['listing_id'], ['listings.id'], ondelete='CASCADE'),
    )

    op.create_index('ix_moderation_queue_status_created', 'moderation_queue', ['status', 'created_at'])
    op.create_index('ix_moderation_queue_listing', 'moderation_queue', ['listing_id'])


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'moderation_queue' not in inspector.get_table_names():
        return

    op.drop_index('ix_moderation_queue_listing', table_name='moderation_queue')
    op.drop_index('ix_moderation_queue_status_created', table_name='moderation_queue')
    op.drop_table('moderation_queue')
