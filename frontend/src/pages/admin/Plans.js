import React, { useState } from 'react';
import Layout from '@/components/Layout';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Check, Loader2 } from 'lucide-react';
import { useToast } from "@/components/ui/use-toast";

const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

const PLANS = [
  {
    code: "TR_DEALER_BASIC",
    name: "Temel Paket",
    price: "1000 TL",
    features: ["10 İlan Hakkı", "Temel Destek", "Vitrin Hakkı Yok"]
  },
  {
    code: "TR_DEALER_PRO",
    name: "Profesyonel Paket",
    price: "2500 TL",
    features: ["50 İlan Hakkı", "Öncelikli Destek", "5 Vitrin Hakkı", "Rozetler"]
  },
  {
    code: "TR_DEALER_ENTERPRISE",
    name: "Kurumsal Paket",
    price: "10000 TL",
    features: ["500 İlan Hakkı", "7/24 Destek", "50 Vitrin Hakkı", "API Erişimi"]
  }
];

export default function PlansPage() {
  const [loading, setLoading] = useState(null);
  const { toast } = useToast();

  const handleSubscribe = async (planCode) => {
    setLoading(planCode);
    try {
      const res = await fetch(`${API_URL}/api/v1/billing/checkout`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ plan_code: planCode })
      });

      if (!res.ok) throw new Error('Checkout failed');
      
      const { url } = await res.json();
      window.location.href = url; // Redirect to Stripe

    } catch (e) {
      toast({ title: "Hata", description: "Ödeme sayfası açılamadı.", variant: "destructive" });
      setLoading(null);
    }
  };

  return (
    <Layout>
      <div className="space-y-8 py-8">
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-bold">Planınızı Seçin</h1>
          <p className="text-muted-foreground">İşletmeniz için en uygun paketi seçin.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto px-4">
          {PLANS.map((plan) => (
            <Card key={plan.code} className="flex flex-col border-2 hover:border-primary transition-colors">
              <CardHeader>
                <CardTitle>{plan.name}</CardTitle>
                <div className="text-3xl font-bold mt-2">{plan.price}<span className="text-sm font-normal text-muted-foreground">/ay</span></div>
              </CardHeader>
              <CardContent className="flex-1">
                <ul className="space-y-2">
                  {plan.features.map((f, i) => (
                    <li key={i} className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-green-500" />
                      <span className="text-sm">{f}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
              <CardFooter>
                <Button 
                  className="w-full" 
                  onClick={() => handleSubscribe(plan.code)}
                  disabled={loading !== null}
                >
                  {loading === plan.code ? <Loader2 className="animate-spin" /> : "Satın Al"}
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      </div>
    </Layout>
  );
}
