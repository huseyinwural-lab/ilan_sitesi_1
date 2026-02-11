import { createContext, useContext, useState, useEffect } from 'react';

const CountryContext = createContext(null);

const countryFlags = {
  DE: '🇩🇪',
  CH: '🇨🇭',
  FR: '🇫🇷',
  AT: '🇦🇹'
};

const countryCurrencies = {
  DE: 'EUR',
  CH: 'CHF',
  FR: 'EUR',
  AT: 'EUR'
};

export function CountryProvider({ children }) {
  const [selectedCountry, setSelectedCountry] = useState(() => {
    return localStorage.getItem('selected_country') || 'DE';
  });

  useEffect(() => {
    localStorage.setItem('selected_country', selectedCountry);
  }, [selectedCountry]);

  const getFlag = (code) => countryFlags[code] || '🌍';
  const getCurrency = (code) => countryCurrencies[code] || 'EUR';

  return (
    <CountryContext.Provider value={{ 
      selectedCountry, 
      setSelectedCountry, 
      getFlag, 
      getCurrency,
      countryFlags,
      countryCurrencies
    }}>
      {children}
    </CountryContext.Provider>
  );
}

export function useCountry() {
  const context = useContext(CountryContext);
  if (!context) {
    throw new Error('useCountry must be used within a CountryProvider');
  }
  return context;
}
