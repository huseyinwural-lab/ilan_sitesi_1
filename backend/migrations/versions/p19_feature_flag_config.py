
"""
P19: Country specific config in feature flags
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'p19_feature_flag_config'
down_revision: Union[str, Sequence[str], None] = 'f83f2eddec93' # Using last known good revision to avoid conflicts if head moved
# Wait, head is e0a5c6256c36 (Growth) -> f83f2eddec93 (Abuse) -> p19_country_layer
# Let's check current heads. 
# p19_country_layer is the latest for P19.1.
down_revision = 'p19_country_layer'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Add country_config to FeatureFlag
    op.add_column('feature_flags', sa.Column('country_config', postgresql.JSON(astext_type=sa.Text()), nullable=True))

def downgrade() -> None:
    op.drop_column('feature_flags', 'country_config')
