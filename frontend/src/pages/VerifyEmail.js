import { useEffect, useMemo, useRef, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Sun, Moon, Globe } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { useTheme } from '@/contexts/ThemeContext';
import { toast } from '@/components/ui/use-toast';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const OTP_LENGTH = 6;
const RESEND_COOLDOWN = 90;

export default function VerifyEmail({ portalContext = 'account' }) {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, applySession } = useAuth();
  const { language, setLanguage } = useLanguage();
  const { theme, toggleTheme } = useTheme();

  const initialEmail = location.state?.email || sessionStorage.getItem('pending_email') || user?.email || '';

  const [email, setEmail] = useState(initialEmail);
  const [codeDigits, setCodeDigits] = useState(Array(OTP_LENGTH).fill(''));
  const [loading, setLoading] = useState(false);
  const [resendLoading, setResendLoading] = useState(false);
  const [cooldown, setCooldown] = useState(0);
  const [error, setError] = useState('');
  const [attemptsLeft, setAttemptsLeft] = useState(null);
  const [helpOpen, setHelpOpen] = useState(false);
  const [helpLogged, setHelpLogged] = useState(false);

  const inputsRef = useRef([]);

  const verifyPath = portalContext === 'dealer' ? '/dealer/verify-email' : '/verify-email';
  const loginPath = portalContext === 'dealer' ? '/dealer/login' : '/login';
  const supportPath = `/support?reason=email_verification`;

  useEffect(() => {
    if (user && user.is_verified) {
      navigate(portalContext === 'dealer' ? '/dealer' : '/account', { replace: true });
    }
  }, [user, portalContext, navigate]);

  useEffect(() => {
    if (cooldown <= 0) return undefined;
    const timer = setTimeout(() => setCooldown((prev) => Math.max(0, prev - 1)), 1000);
    return () => clearTimeout(timer);
  }, [cooldown]);

  useEffect(() => {
    if (!email) return;
    sessionStorage.setItem('pending_email', email);
    sessionStorage.setItem('pending_portal', portalContext);
  }, [email, portalContext]);

  const codeValue = useMemo(() => codeDigits.join(''), [codeDigits]);

  const handleDigitChange = (index, value) => {
    const cleaned = value.replace(/\D/g, '');
    if (!cleaned) {
      const nextDigits = [...codeDigits];
      nextDigits[index] = '';
      setCodeDigits(nextDigits);
      return;
    }

    const digit = cleaned[cleaned.length - 1];
    const nextDigits = [...codeDigits];
    nextDigits[index] = digit;
    setCodeDigits(nextDigits);

    if (index < OTP_LENGTH - 1) {
      inputsRef.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (index, event) => {
    if (event.key === 'Backspace' && !codeDigits[index] && index > 0) {
      inputsRef.current[index - 1]?.focus();
    }
  };

  const handlePaste = (event) => {
    const pasted = event.clipboardData.getData('text').replace(/\D/g, '').slice(0, OTP_LENGTH);
    if (!pasted) return;
    const nextDigits = Array(OTP_LENGTH).fill('');
    pasted.split('').forEach((digit, idx) => {
      nextDigits[idx] = digit;
    });
    setCodeDigits(nextDigits);
    const lastIndex = Math.min(pasted.length, OTP_LENGTH) - 1;
    if (lastIndex >= 0) {
      inputsRef.current[lastIndex]?.focus();
    }
  };

  const handleVerify = async (event) => {
    event.preventDefault();
    setError('');
    setAttemptsLeft(null);

    if (!email.trim()) {
      setError('E-posta zorunludur.');
      return;
    }

    if (codeValue.length !== OTP_LENGTH) {
      setError('6 haneli kodu girin.');
      return;
    }

    setLoading(true);

    try {
      const res = await fetch(`${API}/auth/verify-email`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim().toLowerCase(), code: codeValue }),
      });

      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        if (detail?.remaining_attempts !== undefined) {
          setAttemptsLeft(detail.remaining_attempts);
        }
        if (res.status === 429) {
          const retry = detail?.retry_after_seconds || 0;
          setCooldown(retry);
          throw new Error('Çok fazla deneme yapıldı. Lütfen bekleyip tekrar deneyin.');
        }
        throw new Error(detail?.detail || 'Kod doğrulanamadı.');
      }

      const data = await res.json().catch(() => ({}));
      const userData = applySession(data);

      toast({ title: 'Doğrulama tamamlandı', description: 'Hesabınız onaylandı.' });
      if (userData) {
        navigate(portalContext === 'dealer' ? '/dealer' : '/account');
      } else {
        navigate(loginPath);
      }
    } catch (err) {
      setError(err?.message || 'Kod doğrulanamadı.');
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    if (cooldown > 0 || resendLoading) return;
    if (!email.trim()) {
      setError('E-posta zorunludur.');
      return;
    }

    setResendLoading(true);
    setError('');
    setAttemptsLeft(null);

    try {
      const res = await fetch(`${API}/auth/resend-verification`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim().toLowerCase() }),
      });

      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        if (res.status === 429) {
          const retry = detail?.retry_after_seconds || RESEND_COOLDOWN;
          setCooldown(retry);
          throw new Error('Kısa süre önce gönderildi. Lütfen bekleyin.');
        }
        throw new Error(detail?.detail || 'Kod gönderilemedi.');
      }

      const data = await res.json().catch(() => ({}));
      const nextCooldown = data?.cooldown_seconds || RESEND_COOLDOWN;
      setCooldown(nextCooldown);

      toast({ title: 'Kod yeniden gönderildi', description: 'Lütfen e-postanızı kontrol edin.' });
    } catch (err) {
      setError(err?.message || 'Kod gönderilemedi.');
    } finally {
      setResendLoading(false);
    }
  };

  const handleHelpToggle = async () => {
    const nextState = !helpOpen;
    setHelpOpen(nextState);

    if (nextState && !helpLogged) {
      setHelpLogged(true);
      try {
        await fetch(`${API}/auth/verify-email/help-opened`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: email.trim().toLowerCase(), reason: 'email_verification' }),
        });
      } catch (err) {
        // ignore logging errors
      }
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--bg-warm)] p-4" data-testid="verify-page">
      <div className="absolute top-4 right-4 flex items-center gap-2">
        <button
          onClick={toggleTheme}
          className="p-2 rounded-md hover:bg-muted transition-colors"
          data-testid="verify-theme-toggle"
        >
          {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
        </button>
        <button
          className="flex items-center gap-1 p-2 rounded-md hover:bg-muted transition-colors"
          onClick={() => {
            const langs = ['tr', 'de', 'fr'];
            const idx = langs.indexOf(language);
            setLanguage(langs[(idx + 1) % langs.length]);
          }}
          data-testid="verify-language-toggle"
        >
          <Globe size={20} />
          <span className="uppercase text-xs font-medium">{language}</span>
        </button>
      </div>

      <div className="w-full max-w-lg space-y-4" data-testid="verify-content">
        <div className="rounded-lg border border-amber-200 bg-amber-50 px-5 py-4 text-sm text-amber-900" data-testid="verify-info-banner">
          Avrupa'nın en yeni ve geniş ilan platformu <strong>Annoncia</strong>'ya Hoşgeldiniz.
          Lütfen e-posta doğrulama kodunu girin.
        </div>

        <div className="bg-white rounded-lg shadow-lg border p-8 text-slate-900" data-testid="verify-card">
          <div className="text-center mb-6" data-testid="verify-header">
            <h1 className="text-2xl font-bold tracking-tight">E-posta doğrulama</h1>
            <p className="text-slate-600 text-sm mt-2">6 haneli kodu girerek hesabınızı doğrulayın.</p>
          </div>

          <form onSubmit={handleVerify} className="space-y-5" data-testid="verify-form">
            <div className="space-y-2" data-testid="verify-email-field">
              <label className="text-sm font-medium" htmlFor="verify-email">E-posta</label>
              <input
                id="verify-email"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                className="w-full h-11 rounded-md border px-3 text-sm"
                placeholder="mail@ornek.com"
                data-testid="verify-email"
              />
            </div>

            <div className="space-y-2" data-testid="verify-code-field">
              <label className="text-sm font-medium">Doğrulama kodu</label>
              <div className="flex items-center justify-center gap-2" onPaste={handlePaste} data-testid="verify-code-inputs">
                {codeDigits.map((digit, index) => (
                  <input
                    key={index}
                    type="text"
                    inputMode="numeric"
                    maxLength={1}
                    value={digit}
                    onChange={(event) => handleDigitChange(index, event.target.value)}
                    onKeyDown={(event) => handleKeyDown(index, event)}
                    ref={(el) => {
                      inputsRef.current[index] = el;
                    }}
                    className="h-12 w-12 rounded-md border text-center text-lg font-semibold"
                    data-testid={`verify-code-digit-${index}`}
                  />
                ))}
              </div>
            </div>


            {attemptsLeft !== null && (
              <div className="text-xs text-slate-500" data-testid="verify-attempts-left">
                Kalan deneme: {attemptsLeft}
              </div>
            )}

            {error && (
              <div className="rounded-md bg-destructive/10 text-destructive text-sm px-3 py-2" data-testid="verify-error">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full h-11 rounded-md bg-primary text-primary-foreground font-medium text-sm hover:bg-primary/90 disabled:opacity-50"
              data-testid="verify-submit"
            >
              {loading ? 'Doğrulanıyor...' : 'Doğrula'}
            </button>

            <div className="flex flex-wrap items-center justify-between gap-3 text-sm" data-testid="verify-actions">
              <button
                type="button"
                onClick={handleResend}
                disabled={cooldown > 0 || resendLoading}
                className="text-blue-600 underline underline-offset-2 disabled:opacity-60"
                data-testid="verify-resend"
              >
                {cooldown > 0 ? `Kodu tekrar gönder (${cooldown}s)` : 'Kodu tekrar gönder'}
              </button>
              <button
                type="button"
                onClick={handleHelpToggle}
                className="text-slate-600 underline underline-offset-2"
                data-testid="verify-help-toggle"
              >
                Kod gelmedi mi?
              </button>
              <button
                type="button"
                onClick={() => navigate(loginPath)}
                className="text-slate-600 underline underline-offset-2"
                data-testid="verify-login-link"
              >
                Girişe dön
              </button>
            </div>

            {helpOpen && (
              <div className="rounded-md border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700" data-testid="verify-help-panel">
                <p className="font-medium" data-testid="verify-help-title">Yardım</p>
                <ul className="mt-2 space-y-1 list-disc list-inside" data-testid="verify-help-list">
                  <li data-testid="verify-help-item-spam">Spam veya gereksiz klasörünü kontrol edin.</li>
                  <li data-testid="verify-help-item-resend">90 saniye sonra yeniden gönderme butonunu kullanın.</li>
                  <li data-testid="verify-help-item-support">
                    Sorun devam ederse{' '}
                    <a
                      href={supportPath}
                      className="text-blue-600 underline underline-offset-2"
                      data-testid="verify-help-support-link"
                    >
                      destekle iletişime geçin
                    </a>
                    .
                  </li>
                </ul>
              </div>
            )}
          </form>
        </div>
      </div>
    </div>
  );
}
