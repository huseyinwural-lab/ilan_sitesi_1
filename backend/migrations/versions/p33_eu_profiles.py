"""
P33: EU consumer/dealer profiles
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'p33_eu_profiles'
down_revision: Union[str, Sequence[str], None] = 'p32_listing_category_required'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'consumer_profiles' not in inspector.get_table_names():
        op.create_table(
            'consumer_profiles',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('language', sa.String(length=10), nullable=False, server_default='tr'),
            sa.Column('country_code', sa.String(length=5), nullable=False, server_default='DE'),
            sa.Column('display_name_mode', sa.String(length=30), nullable=False, server_default='full_name'),
            sa.Column('marketing_consent', sa.Boolean(), nullable=False, server_default=sa.text('false')),
            sa.Column('gdpr_deleted_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('totp_secret', sa.String(length=64), nullable=True),
            sa.Column('totp_enabled', sa.Boolean(), nullable=False, server_default=sa.text('false')),
            sa.Column('totp_enabled_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('totp_recovery_codes', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.UniqueConstraint('user_id', name='uq_consumer_profiles_user_id'),
        )
        op.create_index('ix_consumer_profiles_user', 'consumer_profiles', ['user_id'])

    op.add_column('dealer_profiles', sa.Column('vat_id', sa.String(length=50), nullable=True))
    op.add_column('dealer_profiles', sa.Column('trade_register_no', sa.String(length=80), nullable=True))
    op.add_column('dealer_profiles', sa.Column('authorized_person', sa.String(length=255), nullable=True))
    op.add_column('dealer_profiles', sa.Column('address_json', sa.JSON(), nullable=True))
    op.add_column('dealer_profiles', sa.Column('logo_url', sa.String(length=500), nullable=True))

    op.execute('UPDATE dealer_profiles SET vat_id = vat_number WHERE vat_id IS NULL')


def downgrade() -> None:
    op.drop_column('dealer_profiles', 'logo_url')
    op.drop_column('dealer_profiles', 'address_json')
    op.drop_column('dealer_profiles', 'authorized_person')
    op.drop_column('dealer_profiles', 'trade_register_no')
    op.drop_column('dealer_profiles', 'vat_id')
    op.drop_index('ix_consumer_profiles_user', table_name='consumer_profiles')
    op.drop_table('consumer_profiles')
