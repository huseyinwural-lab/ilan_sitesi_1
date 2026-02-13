import React from 'react';
import { Button } from '@/components/ui/button';
import { Layout } from '@/components/Layout';
import { useNavigate } from 'react-router-dom';

export default function HomePage() {
  const navigate = useNavigate();

  return (
    <Layout>
      <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-4">
        <h1 className="text-4xl font-bold">Hoş Geldiniz</h1>
        <p className="text-muted-foreground">İlanlarınızı arayın ve keşfedin.</p>
        <Button onClick={() => navigate('/search')}>İlanları Görüntüle</Button>
      </div>
    </Layout>
  );
}
