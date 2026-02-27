import React, { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { Link, useLocation } from 'react-router-dom';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function PaymentSuccess() {
  const location = useLocation();
  const [status, setStatus] = useState('pending');
  const [paymentStatus, setPaymentStatus] = useState('');
  const [error, setError] = useState('');

  const authHeader = useMemo(() => ({
    Authorization: `Bearer ${localStorage.getItem('access_token')}`,
  }), []);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const sessionId = params.get('session_id');
    if (!sessionId) {
      setError('session_id bulunamadı');
      return;
    }

    const fetchStatus = async () => {
      try {
        const res = await axios.get(`${API}/payments/checkout/status/${sessionId}`, { headers: authHeader });
        setStatus(res.data.status || 'unknown');
        setPaymentStatus(res.data.payment_status || '');
      } catch (e) {
        setError('Ödeme durumu alınamadı');
      }
    };

    fetchStatus();
  }, [location.search, authHeader]);

  return (
    <div className="p-8 space-y-4" data-testid="dealer-payment-success">
      <h1 className="text-2xl font-semibold" data-testid="dealer-payment-success-title">Ödeme Sonucu</h1>
      {error ? (
        <div className="text-sm text-red-600" data-testid="dealer-payment-success-error">{error}</div>
      ) : (
        <div className="text-sm text-muted-foreground" data-testid="dealer-payment-success-status">
          Checkout status: {status} / Payment: {paymentStatus || '-'}
        </div>
      )}
      <Link className="text-sm text-primary" to="/dealer/purchase" data-testid="dealer-payment-success-back">
        Satın Al sayfasına dön
      </Link>
    </div>
  );
}
