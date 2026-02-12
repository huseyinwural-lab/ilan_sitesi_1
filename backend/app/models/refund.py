
class Refund(Base):
    """Refund records"""
    __tablename__ = "refunds"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    invoice_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False, index=True)
    payment_attempt_id: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("payment_attempts.id"), nullable=True)
    
    stripe_refund_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    
    amount: Mapped[Numeric] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(5), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    status: Mapped[str] = mapped_column(String(20), default="requested") # requested, succeeded, failed
    failure_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    created_by_admin_id: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
