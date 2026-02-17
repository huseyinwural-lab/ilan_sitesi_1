from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

# Extension for Listing Model (Location)
# Added Columns:
# zip_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
# latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
# longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
# location_accuracy: Mapped[str] = mapped_column(String(20), default="approximate")
