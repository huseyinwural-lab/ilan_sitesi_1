import { useMemo } from 'react';
import { useParams } from 'react-router-dom';

const SEGMENT_LABELS = {
  'otomobil': 'Otomobil',
  'arazi-suv-pickup': 'Arazi / SUV / Pickup',
  'motosiklet': 'Motosiklet',
  'minivan-panelvan': 'Minivan / Panelvan',
  'ticari-arac': 'Ticari Araç',
  'karavan-camper': 'Karavan / Camper',
  // 'elektrikli': 'Elektrikli', // removed per request
};

export default function VehicleSegmentPage() {
  const { country, segment } = useParams();

  const label = useMemo(() => SEGMENT_LABELS[segment] || segment, [segment]);

  return (
    <div className="space-y-3" data-testid="vehicle-segment">
      <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight">{label}</h1>
      <p className="text-sm sm:text-base text-muted-foreground">
        {(country || 'de').toLowerCase()} / vasita / {segment} (şimdilik placeholder)
      </p>
      <div className="h-40 rounded bg-muted" />
    </div>
  );
}
