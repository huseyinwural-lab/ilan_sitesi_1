import React, { useEffect, useState } from 'react';
import Layout from '@/components/Layout';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { useToast } from "@/components/ui/toaster";
import { Loader2, Check, AlertTriangle, CreditCard } from 'lucide-react';
import { useNavigate, useSearchParams } from 'react-router-dom';

const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

export default function BillingPage() {
  const [loading, setLoading] = useState(true);
  const [subData, setSubData] = useState(null);
  const [portalLoading, setPortalLoading] = useState(false);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { toast } = useToast();

  useEffect(() => {
    // Check Success Return
    const status = searchParams.get('checkout');
    if (status === 'success') {
      toast({
        title: "Ödeme Başarılı",
        description: "Aboneliğiniz aktif edildi ve limitleriniz artırıldı.",
        variant: "default",
      });
      // Remove param
      navigate('/admin/billing', { replace: true });
    } else if (status === 'cancel') {
        toast({
            title: "İşlem İptal",
            description: "Ödeme işlemi iptal edildi.",
            variant: "destructive",
        });
    }

    fetchSubscription();
  }, []);

  const fetchSubscription = async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/billing/subscription`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      if (res.ok) {
        setSubData(await res.json());
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handlePortal = async () => {
    setPortalLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/v1/billing/portal`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      if (res.ok) {
        const { url } = await res.json();
        window.location.href = url;
      } else {
        throw new Error('Portal error');
      }
    } catch (e) {
      toast({ title: "Hata", description: "Yönetim paneli açılamadı", variant: "destructive" });
    } finally {
      setPortalLoading(false);
    }
  };

  if (loading) return <Layout><div>Loading...</div></Layout>;

  // Mock data if API not ready (for UI dev)
  const sub = subData || {
    plan: { name: { tr: "Free Plan" }, code: "FREE" },
    status: "active",
    usage: { listing_active: 2 },
    limits: { listing: 3 },
    current_period_end: null
  };

  const percent = (sub.usage.listing_active / sub.limits.listing) * 100;

  return (
    <Layout>
      <div className="space-y-6">
        <h1 className="text-3xl font-bold">Abonelik ve Faturalandırma</h1>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Current Plan */}
          <Card>
            <CardHeader>
              <CardTitle className="flex justify-between items-center">
                Mevcut Plan
                <Badge variant={sub.status === 'active' ? 'default' : 'destructive'}>
                  {sub.status.toUpperCase()}
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="text-2xl font-bold">{sub.plan.name.tr || sub.plan.name.en}</div>
              
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>İlan Kullanımı</span>
                  <span>{sub.usage.listing_active} / {sub.limits.listing}</span>
                </div>
                <Progress value={percent} className={percent > 90 ? "bg-red-100" : ""} />
              </div>

              {sub.current_period_end && (
                <p className="text-sm text-muted-foreground">
                  Yenileme Tarihi: {new Date(sub.current_period_end).toLocaleDateString('tr-TR')}
                </p>
              )}
            </CardContent>
            <CardFooter className="gap-2">
              <Button onClick={() => navigate('/admin/plans')}>Planı Değiştir</Button>
              {sub.code !== 'FREE' && (
                <Button variant="outline" onClick={handlePortal} disabled={portalLoading}>
                  {portalLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  Ödeme Yöntemini Yönet
                </Button>
              )}
            </CardFooter>
          </Card>

          {/* Payment History (Placeholder) */}
          <Card>
            <CardHeader>
              <CardTitle>Geçmiş Ödemeler</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-sm text-muted-foreground">
                Henüz fatura bulunmuyor.
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </Layout>
  );
}
