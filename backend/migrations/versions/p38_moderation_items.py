"""
P38: create moderation_items table
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'p38_moderation_items'
down_revision: Union[str, Sequence[str], None] = 'p37_moderation_queue'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'moderation_items' in inspector.get_table_names():
        return

    op.create_table(
        'moderation_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('listing_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('moderator_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('audit_ref', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text("timezone('utc', now())")),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text("timezone('utc', now())")),
        sa.ForeignKeyConstraint(['listing_id'], ['listings.id'], ondelete='CASCADE'),
    )

    op.create_index('ix_moderation_items_status_created', 'moderation_items', ['status', 'created_at'])
    op.create_index('ix_moderation_items_listing', 'moderation_items', ['listing_id'])


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'moderation_items' not in inspector.get_table_names():
        return

    op.drop_index('ix_moderation_items_listing', table_name='moderation_items')
    op.drop_index('ix_moderation_items_status_created', table_name='moderation_items')
    op.drop_table('moderation_items')
