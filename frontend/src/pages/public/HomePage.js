import React from 'react';
import { Button } from '@/components/ui/button';
import PublicLayout from '@/layouts/PublicLayout';
import AdSlot from '@/components/public/AdSlot';
import { useNavigate } from 'react-router-dom';

export default function HomePage() {
  const navigate = useNavigate();

  return (
    <PublicLayout>
      <div className="mb-6" data-testid="home-ad-slot">
        <AdSlot placement="AD_HOME_TOP" />
      </div>
      <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-6">
        <h1 className="text-4xl font-bold text-center">Hoş Geldiniz</h1>
        <p className="text-muted-foreground text-center">İlanlarınızı arayın ve keşfedin.</p>
        
        <div className="flex flex-col sm:flex-row gap-4 w-full max-w-md justify-center">
          <Button 
            className="w-full sm:w-auto bg-blue-600 hover:bg-blue-700 text-white" 
            onClick={() => navigate('/search')}
          >
            İlanları Görüntüle
          </Button>
          
          <Button 
            className="w-full sm:w-auto bg-gray-800 hover:bg-gray-900 text-white border border-gray-700" 
            onClick={() => navigate('/login')}
          >
            Admin / Giriş Yap
          </Button>
        </div>
      </div>
    </PublicLayout>
  );
}
