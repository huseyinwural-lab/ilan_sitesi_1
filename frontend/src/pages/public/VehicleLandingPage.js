import { useEffect, useMemo } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useCountry } from '@/contexts/CountryContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

const SEGMENTS = [
  { slug: 'otomobil', title: 'Otomobil', desc: 'Sedan, hatchback ve daha fazlası' },
  { slug: 'arazi-suv-pickup', title: 'Arazi / SUV / Pickup', desc: 'SUV, 4x4, pickup' },
  { slug: 'motosiklet', title: 'Motosiklet', desc: 'Scooter, naked, touring' },
  { slug: 'minivan-panelvan', title: 'Minivan / Panelvan', desc: 'Aile ve iş için' },
  { slug: 'ticari-arac', title: 'Ticari Araç', desc: 'KOBİ ve filo' },
  { slug: 'karavan-camper', title: 'Karavan / Camper', desc: 'Seyahat ve kamp' },
  // { slug: 'elektrikli', title: 'Elektrikli', desc: 'EV ve hibrit' }, // removed per request
];

export default function VehicleLandingPage() {
  const { country } = useParams();
  const { selectedCountry, setSelectedCountry } = useCountry();

  useEffect(() => {
    if (country) {
      const upper = country.toUpperCase();
      if (upper !== selectedCountry) {
        setSelectedCountry(upper);
      }
    }
  }, [country, selectedCountry, setSelectedCountry]);

  const base = useMemo(() => {
    const slug = (country || selectedCountry || 'DE').toLowerCase();
    return `/${slug}/vasita`;
  }, [country, selectedCountry]);

  return (
    <div className="space-y-8" data-testid="vehicle-landing">
      <div className="space-y-2">
        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight">Vasıta</h1>
        <p className="text-sm sm:text-base text-muted-foreground max-w-2xl">
          Segment seç, filtrele ve ilanları keşfet. (Bu sayfa FAZ‑V3 kapsamında kilitlenmiştir.)
        </p>
      </div>

      {/* Segment cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {SEGMENTS.map((s) => (
          <Link key={s.slug} to={`${base}/${s.slug}`} className="block">
            <Card className="h-full hover:bg-muted/30 transition-colors">
              <CardHeader>
                <CardTitle className="text-base">{s.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">{s.desc}</p>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

      {/* Featured listings placeholder */}
      <div className="space-y-3">
        <h2 className="text-lg md:text-lg font-semibold">Öne Çıkan İlanlar</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <CardHeader>
                <CardTitle className="text-base">İlan #{i}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-28 rounded bg-muted" />
                <p className="text-sm text-muted-foreground mt-3">Placeholder</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Popular makes placeholder */}
      <div className="space-y-3">
        <h2 className="text-lg md:text-lg font-semibold">Popüler Markalar</h2>
        <div className="flex flex-wrap gap-2">
          {['BMW', 'Mercedes', 'Audi', 'Volkswagen', 'Toyota', 'Renault', 'Peugeot', 'Ford', 'Opel', 'Tesla'].map((m) => (
            <span key={m} className="text-xs px-2 py-1 rounded bg-muted">{m}</span>
          ))}
        </div>
      </div>
    </div>
  );
}
