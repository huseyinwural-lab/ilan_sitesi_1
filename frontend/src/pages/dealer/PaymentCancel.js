import React from 'react';
import { Link } from 'react-router-dom';

export default function PaymentCancel() {
  return (
    <div className="p-8 space-y-4" data-testid="dealer-payment-cancel">
      <h1 className="text-2xl font-semibold" data-testid="dealer-payment-cancel-title">Ödeme İptal</h1>
      <p className="text-sm text-muted-foreground" data-testid="dealer-payment-cancel-message">
        Ödeme işlemi iptal edildi. İsterseniz tekrar deneyebilirsiniz.
      </p>
      <Link className="text-sm text-primary" to="/dealer/purchase" data-testid="dealer-payment-cancel-back">
        Satın Al sayfasına dön
      </Link>
    </div>
  );
}
