import React, { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';

const resolveSessionId = (searchParams) => (
  searchParams.get('session_id')
  || searchParams.get('sessionId')
  || searchParams.get('sid')
  || ''
);

const resolvePortalAfterLogin = (role) => {
  if (role === 'dealer') return '/dealer/overview';
  if (['super_admin', 'admin', 'country_admin', 'support', 'moderator', 'finance'].includes(role)) {
    return '/admin/countries';
  }
  return '/account';
};

export default function GoogleCallbackPage() {
  const navigate = useNavigate();
  const { loginWithEmergentGoogleSession } = useAuth();
  const [status, setStatus] = useState('loading');
  const [errorMessage, setErrorMessage] = useState('');

  const portalScope = useMemo(() => {
    const stored = localStorage.getItem('oauth_portal_scope');
    return stored === 'dealer' ? 'dealer' : 'account';
  }, []);

  useEffect(() => {
    let active = true;

    const run = async () => {
      const params = new URLSearchParams(window.location.search);
      const sessionId = resolveSessionId(params);
      if (!sessionId) {
        if (!active) return;
        setStatus('error');
        setErrorMessage('Google oturum bilgisi alınamadı. Lütfen tekrar deneyin.');
        return;
      }

      try {
        const user = await loginWithEmergentGoogleSession(sessionId, portalScope);
        localStorage.removeItem('oauth_portal_scope');
        const target = resolvePortalAfterLogin(user?.role);
        if (active) {
          setStatus('success');
          navigate(target, { replace: true });
        }
      } catch (error) {
        localStorage.removeItem('oauth_portal_scope');
        if (!active) return;

        const detail = error?.response?.data?.detail;
        const message =
          (typeof detail === 'string' && detail)
          || (detail?.code === 'PORTAL_MISMATCH' ? 'Seçtiğiniz portal ile bu hesap tipi uyuşmuyor.' : '')
          || 'Google ile giriş tamamlanamadı. Lütfen tekrar deneyin.';
        setStatus('error');
        setErrorMessage(message);
      }
    };

    run();
    return () => {
      active = false;
    };
  }, [loginWithEmergentGoogleSession, navigate, portalScope]);

  return (
    <div className="min-h-screen bg-slate-50 px-4 py-16" data-testid="google-callback-page">
      <div className="mx-auto max-w-md rounded-2xl border bg-white p-8 text-center shadow-sm" data-testid="google-callback-card">
        {status === 'loading' ? (
          <>
            <h1 className="text-xl font-semibold" data-testid="google-callback-loading-title">Google hesabı doğrulanıyor...</h1>
            <p className="mt-2 text-sm text-slate-600" data-testid="google-callback-loading-subtitle">Lütfen bu sayfayı kapatmayın.</p>
          </>
        ) : null}

        {status === 'error' ? (
          <>
            <h1 className="text-xl font-semibold text-rose-700" data-testid="google-callback-error-title">Google giriş başarısız</h1>
            <p className="mt-2 text-sm text-slate-700" data-testid="google-callback-error-message">{errorMessage}</p>
            <Link
              to="/login"
              className="mt-5 inline-flex rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-800 hover:bg-slate-100"
              data-testid="google-callback-back-login"
            >
              Giriş sayfasına dön
            </Link>
          </>
        ) : null}

        {status === 'success' ? (
          <div className="text-sm text-emerald-700" data-testid="google-callback-success">Yönlendiriliyorsunuz...</div>
        ) : null}
      </div>
    </div>
  );
}
