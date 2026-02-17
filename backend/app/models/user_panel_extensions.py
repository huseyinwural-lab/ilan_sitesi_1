from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base
# We will use Alembic to add this column to existing User model, 
# but for ORM completeness we pretend it's in the User class mixin or added via migration.
# Since User is already defined in app/models/user.py, we will modify that file.
