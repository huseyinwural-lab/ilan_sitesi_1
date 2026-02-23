import React, { useEffect } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import SearchPage from './SearchPage';
import { useSearchState } from '../../hooks/useSearchState';

const VehicleMakeModelPage = () => {
  const { make, model } = useParams();
  const [searchParams] = useSearchParams();
  const [searchState, setSearchState] = useSearchState();
  const year = searchParams.get('year');

  useEffect(() => {
    if (!make || !model) return;
    if (searchState.make === make && searchState.model === model && (!year || searchState.filters?.year === year)) return;
    setSearchState({
      ...searchState,
      category: 'otomobil',
      make,
      model,
      page: 1,
      filters: year ? { ...searchState.filters, year } : searchState.filters,
    });
  }, [make, model, year, searchState, setSearchState]);

  return <SearchPage />;
};

export default VehicleMakeModelPage;
