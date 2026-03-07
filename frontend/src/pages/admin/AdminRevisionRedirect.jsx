import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const REDIRECT_FAILURE_MESSAGES = {
  REVISION_NOT_FOUND: 'İlgili revizyon bulunamadı.',
  REVISION_NOT_PUBLISHED: 'Revizyon yayınlanmamış durumda.',
  PERMISSION_DENIED: 'Bu revizyona erişim yetkiniz bulunmuyor.',
  TARGET_ROUTE_INVALID: 'Hedef route bilgisi geçersiz veya eksik.',
};

const normalizeFailureCode = (value) => {
  const normalized = String(value || '').trim().toUpperCase();
  if (Object.prototype.hasOwnProperty.call(REDIRECT_FAILURE_MESSAGES, normalized)) return normalized;
  return 'TARGET_ROUTE_INVALID';
};

export default function AdminRevisionRedirect() {
  const navigate = useNavigate();
  const { revisionId } = useParams();
  const [loading, setLoading] = useState(true);
  const [retryCount, setRetryCount] = useState(0);
  const [errorInfo, setErrorInfo] = useState(null);

  const authHeaders = useMemo(() => {
    const pathLocale = String(window.location.pathname || '').split('/').filter(Boolean)[0]?.toLowerCase();
    const locale = ['tr', 'de', 'fr'].includes(pathLocale)
      ? pathLocale
      : String(localStorage.getItem('language') || 'tr').toLowerCase();
    return {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`,
      'Accept-Language': locale,
      'X-URL-Locale': locale,
    };
  }, []);

  useEffect(() => {
    let mounted = true;

    setLoading(true);
    setErrorInfo(null);

    const sendTelemetryEvent = async ({
      status,
      failureReason = null,
      redirectTarget = null,
      startedAtIso,
      completedAtIso,
      durationMs,
    }) => {
      try {
        await axios.post(
          `${API}/admin/revision-redirect-telemetry/events`,
          {
            revision_id: revisionId || null,
            redirect_target: redirectTarget,
            redirect_started_at: startedAtIso,
            redirect_completed_at: completedAtIso,
            redirect_duration_ms: durationMs,
            status,
            failure_reason: failureReason,
          },
          {
            headers: authHeaders,
            timeout: 8000,
          },
        );
      } catch {
        // telemetry best-effort
      }
    };

    const run = async () => {
      const redirectStartTimestamp = Date.now();
      const startedAtIso = new Date(redirectStartTimestamp).toISOString();

      if (!revisionId) {
        const failureReason = 'REVISION_NOT_FOUND';
        setErrorInfo({
          code: failureReason,
          message: REDIRECT_FAILURE_MESSAGES[failureReason],
        });
        const completedAtIso = new Date().toISOString();
        await sendTelemetryEvent({
          status: 'failed',
          failureReason,
          startedAtIso,
          completedAtIso,
          durationMs: Math.max(0, Date.now() - redirectStartTimestamp),
        });
        setLoading(false);
        return;
      }

      try {
        const response = await axios.get(`${API}/admin/layouts/${revisionId}`, {
          headers: authHeaders,
          timeout: 20000,
        });
        if (!mounted) return;

        const page = response.data?.page;
        const revisionStatus = String(response.data?.item?.status || '').toLowerCase();

        if (revisionStatus !== 'published') {
          const failureReason = 'REVISION_NOT_PUBLISHED';
          setErrorInfo({
            code: failureReason,
            message: REDIRECT_FAILURE_MESSAGES[failureReason],
          });
          const completedAtIso = new Date().toISOString();
          await sendTelemetryEvent({
            status: 'failed',
            failureReason,
            startedAtIso,
            completedAtIso,
            durationMs: Math.max(0, Date.now() - redirectStartTimestamp),
          });
          setLoading(false);
          return;
        }

        if (!page?.id) {
          const failureReason = 'TARGET_ROUTE_INVALID';
          setErrorInfo({
            code: failureReason,
            message: REDIRECT_FAILURE_MESSAGES[failureReason],
          });
          const completedAtIso = new Date().toISOString();
          await sendTelemetryEvent({
            status: 'failed',
            failureReason,
            startedAtIso,
            completedAtIso,
            durationMs: Math.max(0, Date.now() - redirectStartTimestamp),
          });
          setLoading(false);
          return;
        }

        const params = new URLSearchParams();
        params.set('autoload_page_id', page.id);
        params.set('autoload_revision_id', revisionId);
        params.set('page_type', page.page_type || 'home');
        params.set('country', String(page.country || 'TR').toUpperCase());
        params.set('module', String(page.module || 'global'));
        if (page.category_id) {
          params.set('category_id', page.category_id);
        }

        const redirectTarget = `/admin/site-design/content-builder?${params.toString()}`;
        if (!redirectTarget.startsWith('/admin/site-design/content-builder?')) {
          const failureReason = 'TARGET_ROUTE_INVALID';
          setErrorInfo({
            code: failureReason,
            message: REDIRECT_FAILURE_MESSAGES[failureReason],
          });
          const completedAtIso = new Date().toISOString();
          await sendTelemetryEvent({
            status: 'failed',
            failureReason,
            redirectTarget,
            startedAtIso,
            completedAtIso,
            durationMs: Math.max(0, Date.now() - redirectStartTimestamp),
          });
          setLoading(false);
          return;
        }

        const completedAtIso = new Date().toISOString();
        await sendTelemetryEvent({
          status: 'success',
          redirectTarget,
          startedAtIso,
          completedAtIso,
          durationMs: Math.max(0, Date.now() - redirectStartTimestamp),
        });

        navigate(redirectTarget, { replace: true });
      } catch (requestError) {
        if (!mounted) return;
        const detail = requestError?.response?.data?.detail;
        const detailCode = typeof detail === 'object' && detail?.code ? String(detail.code) : detail;
        const httpStatus = Number(requestError?.response?.status || 0);
        const failureReason = normalizeFailureCode(
          httpStatus === 403
            ? 'PERMISSION_DENIED'
            : httpStatus === 404
              ? 'REVISION_NOT_FOUND'
              : detailCode,
        );

        const message = typeof detail === 'string' && detail.trim()
          ? detail
          : REDIRECT_FAILURE_MESSAGES[failureReason] || requestError?.message || 'Revision açılamadı';
        setErrorInfo({
          code: failureReason,
          message: String(message),
          httpStatus,
        });

        const completedAtIso = new Date().toISOString();
        await sendTelemetryEvent({
          status: 'failed',
          failureReason,
          startedAtIso,
          completedAtIso,
          durationMs: Math.max(0, Date.now() - redirectStartTimestamp),
        });
        setLoading(false);
      }
    };

    run();
    return () => {
      mounted = false;
    };
  }, [authHeaders, navigate, revisionId, retryCount]);

  return (
    <section className="rounded-lg border bg-white p-4" data-testid="admin-revision-redirect-page">
      {errorInfo ? (
        <div data-testid="admin-revision-redirect-error-wrap">
          <div className="rounded border border-rose-200 bg-rose-50 p-3" data-testid="admin-revision-redirect-error-card">
            <p className="text-xs text-rose-800" data-testid="admin-revision-redirect-error-code">Hata kodu: {errorInfo.code}</p>
            <p className="mt-1 text-sm text-rose-700" data-testid="admin-revision-redirect-error-message">{errorInfo.message}</p>
          </div>

          <div className="mt-3 flex flex-wrap items-center gap-2" data-testid="admin-revision-redirect-actions-wrap">
            <button
              type="button"
              className="h-9 rounded border px-3 text-xs"
              onClick={() => setRetryCount((previous) => previous + 1)}
              data-testid="admin-revision-redirect-retry-button"
            >
              Yeniden Dene
            </button>
            <button
              type="button"
              className="h-9 rounded border px-3 text-xs"
              onClick={() => navigate('/')}
              data-testid="admin-revision-redirect-go-home-button"
            >
              Ana Sayfaya Dön
            </button>
            <button
              type="button"
              className="h-9 rounded border px-3 text-xs"
              onClick={() => navigate('/admin/dashboard')}
              data-testid="admin-revision-redirect-go-dashboard-button"
            >
              Admin Dashboard'a Git
            </button>
            <a
              href={`/support?reason=revision_redirect&code=${encodeURIComponent(String(errorInfo.code || 'TARGET_ROUTE_INVALID'))}&revision_id=${encodeURIComponent(String(revisionId || ''))}`}
              className="inline-flex h-9 items-center rounded border px-3 text-xs"
              data-testid="admin-revision-redirect-support-link"
            >
              Destek
            </a>
          </div>
        </div>
      ) : (
        <p className="text-sm text-slate-600" data-testid="admin-revision-redirect-loading">{loading ? 'Revision açılıyor...' : 'İşlem tamamlandı.'}</p>
      )}
    </section>
  );
}
