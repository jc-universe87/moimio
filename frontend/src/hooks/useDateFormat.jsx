import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { preferences as prefsApi, getToken } from '../services/api';

const DateFormatContext = createContext(null);

export function DateFormatProvider({ children }) {
  const [dateFormat, setDateFormat] = useState('DD/MM/YYYY');

  const loadPrefs = useCallback(async () => {
    // Only try if we have a token
    if (!getToken()) return;
    try {
      const data = await prefsApi.get();
      if (data?.date_format) setDateFormat(data.date_format);
    } catch {
      // Not logged in or prefs not available
    }
  }, []);

  // Try loading on mount (token may already be set from sessionStorage)
  useEffect(() => {
    // Small delay to let AuthProvider set the token first
    const timer = setTimeout(loadPrefs, 100);
    return () => clearTimeout(timer);
  }, [loadPrefs]);

  const formatDate = useCallback((dateStr) => {
    if (!dateStr) return '';
    const d = new Date(dateStr + (dateStr.includes('T') ? '' : 'T00:00:00'));
    if (isNaN(d.getTime())) return dateStr;
    const day = String(d.getDate()).padStart(2, '0');
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const year = d.getFullYear();
    switch (dateFormat) {
      case 'MM/DD/YYYY': return `${month}/${day}/${year}`;
      case 'YYYY-MM-DD': return `${year}-${month}-${day}`;
      // v1.0.0k: locale-specific numeric presets. Long-form (with month
      // name) is intentionally not handled here — it requires
      // Intl.DateTimeFormat integration and is deferred.
      case 'DD.MM.YYYY': return `${day}.${month}.${year}`;
      case 'YYYY.MM.DD': return `${year}.${month}.${day}`;
      case 'YYYY년 MM월 DD일': return `${year}년 ${month}월 ${day}일`;
      default: return `${day}/${month}/${year}`;
    }
  }, [dateFormat]);

  const updateFormat = (newFormat) => {
    setDateFormat(newFormat);
  };

  return (
    <DateFormatContext.Provider value={{ dateFormat, formatDate, updateFormat, reloadPrefs: loadPrefs }}>
      {children}
    </DateFormatContext.Provider>
  );
}

export function useDateFormat() {
  const ctx = useContext(DateFormatContext);
  if (!ctx) return { dateFormat: 'DD/MM/YYYY', formatDate: (d) => d, updateFormat: () => {}, reloadPrefs: () => {} };
  return ctx;
}
