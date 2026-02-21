"""
P34: add gdpr_deleted_at to dealer_profiles
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'p34_dealer_gdpr_deleted_at'
down_revision: Union[str, Sequence[str], None] = 'p33_eu_profiles'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'dealer_profiles' not in inspector.get_table_names():
        return
    columns = [column['name'] for column in inspector.get_columns('dealer_profiles')]
    if 'gdpr_deleted_at' not in columns:
        op.add_column('dealer_profiles', sa.Column('gdpr_deleted_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'dealer_profiles' not in inspector.get_table_names():
        return
    columns = [column['name'] for column in inspector.get_columns('dealer_profiles')]
    if 'gdpr_deleted_at' in columns:
        op.drop_column('dealer_profiles', 'gdpr_deleted_at')
