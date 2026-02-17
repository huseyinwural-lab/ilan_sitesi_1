from sqlalchemy import Index, text
from app.models.moderation import Listing

# Note: This is a representation of indexes to be added via Alembic.
# We don't add them to the class directly if we use Alembic's op.create_index

# 1. Main Search Index
# Index('ix_listings_search_core', Listing.status, Listing.country, Listing.module, Listing.is_premium, Listing.created_at)

# 2. JSONB Attribute Index (GIN)
# Index('ix_listings_attributes_gin', Listing.attributes, postgresql_using='gin')

# 3. Location Index (Simple Lat/Lon for now, PostGIS later if needed)
# Index('ix_listings_lat_lon', Listing.latitude, Listing.longitude)
