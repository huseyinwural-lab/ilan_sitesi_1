import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import axios from 'axios';
import { Lock, Mail, ShieldCheck } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function AdminInviteAccept() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const [loading, setLoading] = useState(true);
  const [invite, setInvite] = useState(null);
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    const fetchInvite = async () => {
      if (!token) {
        setError('Davet tokeni bulunamadı.');
        setLoading(false);
        return;
      }
      try {
        const res = await axios.get(`${API}/admin/invite/preview?token=${encodeURIComponent(token)}`);
        setInvite(res.data);
      } catch (err) {
        setError('Davet bağlantısı geçersiz veya süresi dolmuş.');
      } finally {
        setLoading(false);
      }
    };
    fetchInvite();
  }, [token]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    if (!password || password.length < 8) {
      setError('Şifre en az 8 karakter olmalı.');
      return;
    }
    if (password !== confirmPassword) {
      setError('Şifreler eşleşmiyor.');
      return;
    }
    try {
      await axios.post(`${API}/admin/invite/accept`, { token, password });
      setSuccess('Şifreniz oluşturuldu. Artık giriş yapabilirsiniz.');
    } catch (err) {
      const message = err.response?.data?.detail || 'Şifre oluşturulamadı.';
      setError(typeof message === 'string' ? message : 'Şifre oluşturulamadı.');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" data-testid="invite-loading">
        Yükleniyor...
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4" data-testid="invite-accept-page">
      <div className="bg-white rounded-lg shadow-lg w-full max-w-md p-6">
        <div className="flex items-center gap-2 mb-4">
          <ShieldCheck className="text-primary" size={20} />
          <h1 className="text-xl font-semibold" data-testid="invite-accept-title">Admin Daveti</h1>
        </div>
        {invite && (
          <div className="space-y-2 text-sm text-muted-foreground" data-testid="invite-accept-details">
            <div className="flex items-center gap-2">
              <Mail size={14} /> {invite.email}
            </div>
            <div>Rol: {invite.role}</div>
            <div>Son tarih: {invite.expires_at || '-'}</div>
          </div>
        )}

        {error && (
          <div className="mt-4 text-sm text-rose-600" data-testid="invite-accept-error">{error}</div>
        )}
        {success && (
          <div className="mt-4 text-sm text-emerald-600" data-testid="invite-accept-success">{success}</div>
        )}

        <form onSubmit={handleSubmit} className="mt-6 space-y-3">
          <label className="text-xs text-muted-foreground">Yeni Şifre</label>
          <div className="flex items-center gap-2 border rounded-md px-3 h-10">
            <Lock size={14} className="text-muted-foreground" />
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full text-sm outline-none"
              data-testid="invite-accept-password"
            />
          </div>
          <label className="text-xs text-muted-foreground">Şifre Tekrar</label>
          <div className="flex items-center gap-2 border rounded-md px-3 h-10">
            <Lock size={14} className="text-muted-foreground" />
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full text-sm outline-none"
              data-testid="invite-accept-password-confirm"
            />
          </div>
          <button
            type="submit"
            className="w-full h-10 rounded-md bg-primary text-primary-foreground text-sm font-medium"
            data-testid="invite-accept-submit"
          >
            Şifreyi Oluştur
          </button>
        </form>
        <div className="mt-4 text-sm text-muted-foreground">
          <Link to="/admin/login" className="text-primary" data-testid="invite-accept-login-link">
            Admin girişine dön
          </Link>
        </div>
      </div>
    </div>
  );
}
