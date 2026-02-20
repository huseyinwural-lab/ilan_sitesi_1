"""
P23: Vehicle type dimension for vehicle models
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'p23_vehicle_type_dimension'
down_revision: Union[str, Sequence[str], None] = 'p22_campaigns_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if not inspector.has_table('vehicle_models'):
        return

    columns = {col['name'] for col in inspector.get_columns('vehicle_models')}
    if 'vehicle_type' not in columns:
        op.add_column('vehicle_models', sa.Column('vehicle_type', sa.String(20), nullable=True))

    op.execute("UPDATE vehicle_models SET vehicle_type = 'car' WHERE vehicle_type IS NULL")

    op.alter_column('vehicle_models', 'vehicle_type', nullable=False)

    indexes = {idx['name'] for idx in inspector.get_indexes('vehicle_models')}
    if 'country_code' in columns:
        if 'ix_vehicle_models_country_type_make' not in indexes:
            op.create_index('ix_vehicle_models_country_type_make', 'vehicle_models', ['country_code', 'vehicle_type', 'make_id'])
    else:
        if 'ix_vehicle_models_type_make' not in indexes:
            op.create_index('ix_vehicle_models_type_make', 'vehicle_models', ['vehicle_type', 'make_id'])



def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if not inspector.has_table('vehicle_models'):
        return

    indexes = {idx['name'] for idx in inspector.get_indexes('vehicle_models')}
    if 'ix_vehicle_models_country_type_make' in indexes:
        op.drop_index('ix_vehicle_models_country_type_make', table_name='vehicle_models')
    if 'ix_vehicle_models_type_make' in indexes:
        op.drop_index('ix_vehicle_models_type_make', table_name='vehicle_models')
