import { Navigate, useParams } from 'react-router-dom';
import { useCountry } from '@/contexts/CountryContext';

export default function RedirectToCountry({ to }) {
  const { selectedCountry } = useCountry();
  const params = useParams();
  const country = (params.country || selectedCountry || 'DE').toLowerCase();
  const target = to.replace('{country}', country);
  return <Navigate to={target} replace />;
}
