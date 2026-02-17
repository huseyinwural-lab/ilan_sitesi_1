from sqlalchemy import Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

# Extension for Listing Model (U6)
# Added Columns:
# contact_option_phone: Mapped[bool] = mapped_column(Boolean, default=True)
# contact_option_message: Mapped[bool] = mapped_column(Boolean, default=True)
